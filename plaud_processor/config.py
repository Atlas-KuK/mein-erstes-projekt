"""
Zentrale Konfiguration – alle Werte werden aus Umgebungsvariablen gelesen.
Eine .env-Datei wird automatisch geladen, wenn python-dotenv installiert ist.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Plaud.ai
# ---------------------------------------------------------------------------
PLAUD_API_TOKEN: str = os.getenv("PLAUD_API_TOKEN", "")
# Alternativ: lokaler Ordner, in den die Plaud-App Aufnahmen exportiert
PLAUD_WATCH_FOLDER: str = os.getenv("PLAUD_WATCH_FOLDER", "")

# ---------------------------------------------------------------------------
# Transkription – lokales Whisper (kostenlos, bevorzugt)
# ---------------------------------------------------------------------------
# Modell: tiny (schnell), base, small, medium (empfohlen), large (beste Qualität)
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "medium")
# OpenAI API nur als Fallback (kostenpflichtig)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# KI-Analyse (Anthropic / Claude)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ---------------------------------------------------------------------------
# Ausgabe-Ordner für PDFs
# Einfachste Option: lokaler Ordner, der von OneDrive/Google Drive/Dropbox
# automatisch synchronisiert wird – kein API, keine Kosten.
# ---------------------------------------------------------------------------
# Lokaler Pfad, in den die PDFs gespeichert werden.
# Beispiele:
#   Windows OneDrive:   C:\Users\IhrName\OneDrive\Plaud Berichte
#   Windows Google Drive: C:\Users\IhrName\Google Drive\Plaud Berichte
#   Mac OneDrive:       /Users/IhrName/OneDrive/Plaud Berichte
PDF_OUTPUT_FOLDER: str = os.getenv("PDF_OUTPUT_FOLDER", "")

# ---------------------------------------------------------------------------
# E-Mail (SMTP)
# ---------------------------------------------------------------------------
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM: str = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO: str = os.getenv("EMAIL_TO", "")          # Komma-getrennt für mehrere
EMAIL_RATE_LIMIT_MINUTES: int = int(os.getenv("EMAIL_RATE_LIMIT_MINUTES", "60"))

# ---------------------------------------------------------------------------
# Allgemein
# ---------------------------------------------------------------------------
# Lokales Verzeichnis für temporäre Dateien und den letzten E-Mail-Zeitstempel
WORK_DIR: Path = Path(os.getenv("WORK_DIR", "/tmp/plaud_processor"))
# Wie oft wird nach neuen Plaud-Aufnahmen gesucht (Sekunden)
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
# Sprache der Transkription (leer = automatisch)
TRANSCRIPTION_LANGUAGE: str = os.getenv("TRANSCRIPTION_LANGUAGE", "")

WORK_DIR.mkdir(parents=True, exist_ok=True)
