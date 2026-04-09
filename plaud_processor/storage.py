"""SQLite-Datenbankschicht mit WAL-Modus für gleichzeitigen Zugriff."""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    """Datenbank-Tabellen erstellen."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER DEFAULT 0,
            duration_seconds REAL DEFAULT 0,
            status TEXT DEFAULT 'neu',
            template TEXT DEFAULT 'meeting',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(filename)
        );

        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            segments TEXT DEFAULT '[]',
            language TEXT DEFAULT '',
            engine TEXT DEFAULT 'whisper_local',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (recording_id) REFERENCES recordings(id)
        );

        CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            speaker_label TEXT NOT NULL,
            speaker_name TEXT DEFAULT '',
            segments TEXT DEFAULT '[]',
            FOREIGN KEY (recording_id) REFERENCES recordings(id)
        );

        CREATE TABLE IF NOT EXISTS protocols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            template TEXT DEFAULT 'meeting',
            content_html TEXT DEFAULT '',
            content_text TEXT DEFAULT '',
            pdf_path TEXT DEFAULT '',
            engine TEXT DEFAULT 'ollama',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (recording_id) REFERENCES recordings(id)
        );

        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_ids TEXT DEFAULT '[]',
            subject TEXT DEFAULT '',
            sent_at TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'gesendet'
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Datenbank initialisiert: %s", DB_PATH)


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Recordings ---

def add_recording(filename: str, filepath: str, filesize: int = 0) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO recordings (filename, filepath, filesize) VALUES (?, ?, ?)",
            (filename, filepath, filesize),
        )
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            "SELECT id FROM recordings WHERE filename = ?", (filename,)
        ).fetchone()
        return row["id"]


def get_recording(recording_id: int) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
        return dict(row) if row else None


def list_recordings(status: str | None = None, limit: int = 100) -> list[dict]:
    with db_session() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM recordings WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM recordings ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def update_recording_status(recording_id: int, status: str):
    with db_session() as conn:
        conn.execute(
            "UPDATE recordings SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, recording_id),
        )


def update_recording_template(recording_id: int, template: str):
    with db_session() as conn:
        conn.execute(
            "UPDATE recordings SET template = ?, updated_at = datetime('now') WHERE id = ?",
            (template, recording_id),
        )


# --- Transcripts ---

def add_transcript(recording_id: int, text: str, segments: list, language: str, engine: str) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO transcripts (recording_id, text, segments, language, engine) VALUES (?, ?, ?, ?, ?)",
            (recording_id, text, json.dumps(segments, ensure_ascii=False), language, engine),
        )
        return cur.lastrowid


def get_transcript(recording_id: int) -> dict | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM transcripts WHERE recording_id = ? ORDER BY id DESC LIMIT 1",
            (recording_id,),
        ).fetchone()
        if row:
            result = dict(row)
            result["segments"] = json.loads(result["segments"])
            return result
        return None


# --- Speakers ---

def add_speaker(recording_id: int, speaker_label: str, segments: list) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO speakers (recording_id, speaker_label, segments) VALUES (?, ?, ?)",
            (recording_id, speaker_label, json.dumps(segments, ensure_ascii=False)),
        )
        return cur.lastrowid


def update_speaker_name(speaker_id: int, name: str):
    with db_session() as conn:
        conn.execute("UPDATE speakers SET speaker_name = ? WHERE id = ?", (name, speaker_id))


def get_speakers(recording_id: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM speakers WHERE recording_id = ? ORDER BY speaker_label",
            (recording_id,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["segments"] = json.loads(d["segments"])
            result.append(d)
        return result


# --- Protocols ---

def add_protocol(recording_id: int, template: str, content_html: str, content_text: str,
                 pdf_path: str, engine: str) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO protocols (recording_id, template, content_html, content_text, pdf_path, engine) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (recording_id, template, content_html, content_text, pdf_path, engine),
        )
        return cur.lastrowid


def get_protocol(recording_id: int) -> dict | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM protocols WHERE recording_id = ? ORDER BY id DESC LIMIT 1",
            (recording_id,),
        ).fetchone()
        return dict(row) if row else None


def list_protocols(limit: int = 100) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT p.*, r.filename FROM protocols p "
            "JOIN recordings r ON p.recording_id = r.id "
            "ORDER BY p.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


# --- E-Mail Log ---

def add_email_log(recording_ids: list[int], subject: str) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO email_log (recording_ids, subject) VALUES (?, ?)",
            (json.dumps(recording_ids), subject),
        )
        return cur.lastrowid


def get_last_email_time() -> datetime | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT sent_at FROM email_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return datetime.fromisoformat(row["sent_at"])
        return None
