"""
SQLite Storage Layer – speichert Aufnahmen, Transkripte, Sprecher und Protokolle.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import WORK_DIR

DB_PATH = WORK_DIR / "plaud.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS recordings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                title       TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                status      TEXT DEFAULT 'pending',
                audio_path  TEXT,
                duration    INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transcripts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id    INTEGER UNIQUE NOT NULL,
                raw_text        TEXT,
                segments_json   TEXT DEFAULT '[]',
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (recording_id) REFERENCES recordings(id)
            );

            CREATE TABLE IF NOT EXISTS speakers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT UNIQUE NOT NULL,
                color       TEXT DEFAULT '#2e86c1',
                usage_count INTEGER DEFAULT 0,
                last_used   TEXT
            );

            CREATE TABLE IF NOT EXISTS protocols (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id    INTEGER NOT NULL,
                template_type   TEXT NOT NULL,
                content_html    TEXT,
                pdf_path        TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (recording_id) REFERENCES recordings(id)
            );
        """)


# ---------------------------------------------------------------------------
# Recordings
# ---------------------------------------------------------------------------

def upsert_recording(filename: str, title: str, audio_path: str,
                     created_at: str = "", duration: int = 0) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "SELECT id FROM recordings WHERE filename = ?", (filename,)
        )
        row = cur.fetchone()
        if row:
            conn.execute(
                "UPDATE recordings SET title=?, audio_path=?, duration=? WHERE id=?",
                (title, audio_path, duration, row["id"])
            )
            return row["id"]
        cur = conn.execute(
            "INSERT INTO recordings (filename, title, audio_path, created_at, duration, status) "
            "VALUES (?,?,?,?,?,'pending')",
            (filename, title, audio_path, created_at or datetime.now().isoformat(), duration)
        )
        return cur.lastrowid


def set_recording_status(recording_id: int, status: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE recordings SET status=? WHERE id=?", (status, recording_id)
        )


def get_all_recordings() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT r.*, t.id as transcript_id "
            "FROM recordings r "
            "LEFT JOIN transcripts t ON t.recording_id = r.id "
            "ORDER BY r.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_recording(recording_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM recordings WHERE id=?", (recording_id,)
        ).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Transcripts
# ---------------------------------------------------------------------------

def save_transcript(recording_id: int, raw_text: str,
                    segments: list) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO transcripts (recording_id, raw_text, segments_json) "
            "VALUES (?,?,?) "
            "ON CONFLICT(recording_id) DO UPDATE SET "
            "raw_text=excluded.raw_text, segments_json=excluded.segments_json",
            (recording_id, raw_text, json.dumps(segments, ensure_ascii=False))
        )
        conn.execute(
            "UPDATE recordings SET status='transcribed' WHERE id=?",
            (recording_id,)
        )


def get_transcript(recording_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM transcripts WHERE recording_id=?", (recording_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["segments"] = json.loads(d.get("segments_json") or "[]")
        return d


def update_segments(recording_id: int, segments: list) -> None:
    """Speichert manuell zugewiesene Sprecher für Segmente."""
    with get_db() as conn:
        conn.execute(
            "UPDATE transcripts SET segments_json=? WHERE recording_id=?",
            (json.dumps(segments, ensure_ascii=False), recording_id)
        )


# ---------------------------------------------------------------------------
# Speakers
# ---------------------------------------------------------------------------

def get_speakers() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM speakers ORDER BY usage_count DESC, name"
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_speaker(name: str) -> int:
    with get_db() as conn:
        cur = conn.execute("SELECT id FROM speakers WHERE name=?", (name,))
        row = cur.fetchone()
        if row:
            conn.execute(
                "UPDATE speakers SET usage_count=usage_count+1, last_used=datetime('now') WHERE id=?",
                (row["id"],)
            )
            return row["id"]
        cur = conn.execute(
            "INSERT INTO speakers (name, usage_count, last_used) VALUES (?,1,datetime('now'))",
            (name,)
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

def save_protocol(recording_id: int, template_type: str,
                  content_html: str, pdf_path: str) -> int:
    with get_db() as conn:
        # Altes Protokoll gleichen Typs ersetzen
        conn.execute(
            "DELETE FROM protocols WHERE recording_id=? AND template_type=?",
            (recording_id, template_type)
        )
        cur = conn.execute(
            "INSERT INTO protocols (recording_id, template_type, content_html, pdf_path) "
            "VALUES (?,?,?,?)",
            (recording_id, template_type, content_html, pdf_path)
        )
        conn.execute(
            "UPDATE recordings SET status='done' WHERE id=?", (recording_id,)
        )
        return cur.lastrowid


def get_protocols(recording_id: int) -> List[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM protocols WHERE recording_id=? ORDER BY created_at DESC",
            (recording_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_protocol(recording_id: int, template_type: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM protocols WHERE recording_id=? AND template_type=?",
            (recording_id, template_type)
        ).fetchone()
        return dict(row) if row else None


init_db()
