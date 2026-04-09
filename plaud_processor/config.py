"""Konfiguration aus Umgebungsvariablen (.env Datei)."""

import os
from pathlib import Path

# Basis-Verzeichnisse
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Audioquelle
PLAUD_WATCH_FOLDER = os.getenv("PLAUD_WATCH_FOLDER", "")
PLAUD_API_TOKEN = os.getenv("PLAUD_API_TOKEN", "")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # 5 Min

# Ausgabe
PDF_OUTPUT_FOLDER = os.getenv("PDF_OUTPUT_FOLDER", str(DATA_DIR / "output"))

# Transkription
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
TRANSCRIPTION_LANGUAGE = os.getenv("TRANSCRIPTION_LANGUAGE", "de")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# KI – Ollama (lokal, kostenlos)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Fallback KI – Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

# E-Mail (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_RATE_LIMIT_MINUTES = int(os.getenv("EMAIL_RATE_LIMIT_MINUTES", "60"))

# Web-UI
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

# Datenbank
DB_PATH = DATA_DIR / "plaud.db"

# Upload-Ordner
UPLOAD_FOLDER = DATA_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Sprecher-Erkennung
SPEAKER_PAUSE_THRESHOLD = float(os.getenv("SPEAKER_PAUSE_THRESHOLD", "1.5"))
