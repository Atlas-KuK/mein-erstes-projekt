"""SQLite-Datenbank mit WAL-Modus für threadsicheren Zugriff aus zwei Docker-Containern."""
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from config import config

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_conn():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Datenbank-Schema erstellen, falls noch nicht vorhanden."""
    with db_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS recordings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                dateiname   TEXT NOT NULL UNIQUE,
                dateipfad   TEXT NOT NULL,
                dauer_sek   REAL,
                aufnahme_ts TEXT,
                verarbeitet INTEGER DEFAULT 0,
                fehler      TEXT,
                erstellt_am TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS transcripts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id  INTEGER NOT NULL REFERENCES recordings(id),
                text          TEXT NOT NULL,
                sprache       TEXT,
                modell        TEXT,
                erstellt_am   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS speakers (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id  INTEGER NOT NULL REFERENCES recordings(id),
                sprecher_nr   INTEGER NOT NULL,
                name          TEXT,
                segment_start REAL,
                segment_end   REAL
            );

            CREATE TABLE IF NOT EXISTS protocols (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id  INTEGER NOT NULL REFERENCES recordings(id),
                vorlage       TEXT NOT NULL,
                inhalt_html   TEXT,
                pdf_pfad      TEXT,
                ki_modell     TEXT,
                erstellt_am   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS email_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                gesendet_am TEXT NOT NULL,
                empfaenger  TEXT,
                betreff     TEXT
            );
        """)
    logger.info("Datenbank initialisiert: %s", config.DB_PATH)


# --- Recordings ---

def recording_existiert(dateiname: str) -> bool:
    with db_conn() as conn:
        row = conn.execute(
            "SELECT id FROM recordings WHERE dateiname = ?", (dateiname,)
        ).fetchone()
        return row is not None


def recording_anlegen(dateiname: str, dateipfad: str, dauer_sek: Optional[float] = None,
                      aufnahme_ts: Optional[str] = None) -> int:
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO recordings (dateiname, dateipfad, dauer_sek, aufnahme_ts) VALUES (?,?,?,?)",
            (dateiname, dateipfad, dauer_sek, aufnahme_ts),
        )
        return cur.lastrowid


def recording_als_verarbeitet_markieren(recording_id: int) -> None:
    with db_conn() as conn:
        conn.execute(
            "UPDATE recordings SET verarbeitet=1, fehler=NULL WHERE id=?", (recording_id,)
        )


def recording_fehler_setzen(recording_id: int, fehler: str) -> None:
    with db_conn() as conn:
        conn.execute(
            "UPDATE recordings SET fehler=? WHERE id=?", (fehler, recording_id)
        )


def alle_recordings_holen(limit: int = 50) -> list[sqlite3.Row]:
    with db_conn() as conn:
        return conn.execute(
            "SELECT * FROM recordings ORDER BY erstellt_am DESC LIMIT ?", (limit,)
        ).fetchall()


def recording_holen(recording_id: int) -> Optional[sqlite3.Row]:
    with db_conn() as conn:
        return conn.execute(
            "SELECT * FROM recordings WHERE id=?", (recording_id,)
        ).fetchone()


# --- Transcripts ---

def transcript_speichern(recording_id: int, text: str, sprache: str, modell: str) -> int:
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO transcripts (recording_id, text, sprache, modell) VALUES (?,?,?,?)",
            (recording_id, text, sprache, modell),
        )
        return cur.lastrowid


def transcript_holen(recording_id: int) -> Optional[sqlite3.Row]:
    with db_conn() as conn:
        return conn.execute(
            "SELECT * FROM transcripts WHERE recording_id=? ORDER BY id DESC LIMIT 1",
            (recording_id,),
        ).fetchone()


# --- Speakers ---

def sprecher_speichern(recording_id: int, sprecher_nr: int, name: Optional[str],
                       start: Optional[float], ende: Optional[float]) -> None:
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO speakers (recording_id, sprecher_nr, name, segment_start, segment_end) "
            "VALUES (?,?,?,?,?)",
            (recording_id, sprecher_nr, name, start, ende),
        )


def sprecher_holen(recording_id: int) -> list[sqlite3.Row]:
    with db_conn() as conn:
        return conn.execute(
            "SELECT * FROM speakers WHERE recording_id=? ORDER BY sprecher_nr",
            (recording_id,),
        ).fetchall()


def sprecher_name_aktualisieren(recording_id: int, sprecher_nr: int, name: str) -> None:
    with db_conn() as conn:
        conn.execute(
            "UPDATE speakers SET name=? WHERE recording_id=? AND sprecher_nr=?",
            (name, recording_id, sprecher_nr),
        )


# --- Protocols ---

def protokoll_speichern(recording_id: int, vorlage: str, inhalt_html: str,
                        pdf_pfad: str, ki_modell: str) -> int:
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO protocols (recording_id, vorlage, inhalt_html, pdf_pfad, ki_modell) "
            "VALUES (?,?,?,?,?)",
            (recording_id, vorlage, inhalt_html, pdf_pfad, ki_modell),
        )
        return cur.lastrowid


def protokoll_holen(recording_id: int) -> Optional[sqlite3.Row]:
    with db_conn() as conn:
        return conn.execute(
            "SELECT * FROM protocols WHERE recording_id=? ORDER BY id DESC LIMIT 1",
            (recording_id,),
        ).fetchone()


# --- E-Mail-Log ---

def letzten_email_zeitpunkt_holen() -> Optional[datetime]:
    with db_conn() as conn:
        row = conn.execute(
            "SELECT gesendet_am FROM email_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return datetime.fromisoformat(row["gesendet_am"])
        return None


def email_log_eintragen(empfaenger: str, betreff: str) -> None:
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO email_log (gesendet_am, empfaenger, betreff) VALUES (datetime('now'),?,?)",
            (empfaenger, betreff),
        )
