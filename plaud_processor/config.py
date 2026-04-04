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
# Transkription (OpenAI Whisper)
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")

# ---------------------------------------------------------------------------
# KI-Analyse (Anthropic / Claude)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ---------------------------------------------------------------------------
# OneDrive (Microsoft Graph)
# ---------------------------------------------------------------------------
ONEDRIVE_CLIENT_ID: str = os.getenv("ONEDRIVE_CLIENT_ID", "")
ONEDRIVE_CLIENT_SECRET: str = os.getenv("ONEDRIVE_CLIENT_SECRET", "")
ONEDRIVE_TENANT_ID: str = os.getenv("ONEDRIVE_TENANT_ID", "")
# Zielordner in OneDrive, z. B. "/Plaud Berichte"
ONEDRIVE_FOLDER: str = os.getenv("ONEDRIVE_FOLDER", "/Plaud Berichte")
# Für persönliche OneDrive-Konten (user principal name oder "me")
ONEDRIVE_USER: str = os.getenv("ONEDRIVE_USER", "me")

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
