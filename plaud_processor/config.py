"""Konfiguration – alle Einstellungen aus .env laden."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Audioquelle ---
    PLAUD_WATCH_FOLDER: str = os.getenv("PLAUD_WATCH_FOLDER", "")
    PLAUD_API_TOKEN: str = os.getenv("PLAUD_API_TOKEN", "")

    # --- Ausgabe ---
    PDF_OUTPUT_FOLDER: str = os.getenv("PDF_OUTPUT_FOLDER", "/data/output")
    DATA_FOLDER: str = os.getenv("DATA_FOLDER", "/data")
    DB_PATH: str = os.path.join(os.getenv("DATA_FOLDER", "/data"), "plaud.db")

    # --- Transkription ---
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "medium")
    TRANSCRIPTION_LANGUAGE: str = os.getenv("TRANSCRIPTION_LANGUAGE", "de")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- KI (Ollama bevorzugt) ---
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # --- Fallback KI (Claude) ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

    # --- E-Mail ---
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")
    EMAIL_RATE_LIMIT_MINUTES: int = int(os.getenv("EMAIL_RATE_LIMIT_MINUTES", "60"))

    # --- Polling ---
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # 5 Min

    # --- Sprecher-Erkennung ---
    SPEAKER_PAUSE_THRESHOLD: float = float(os.getenv("SPEAKER_PAUSE_THRESHOLD", "1.5"))

    @classmethod
    def validate(cls) -> list[str]:
        """Gibt eine Liste von Warnungen zurück, wenn wichtige Einstellungen fehlen."""
        warnings = []
        if not cls.PLAUD_WATCH_FOLDER and not cls.PLAUD_API_TOKEN:
            warnings.append("Weder PLAUD_WATCH_FOLDER noch PLAUD_API_TOKEN gesetzt.")
        if not cls.PDF_OUTPUT_FOLDER:
            warnings.append("PDF_OUTPUT_FOLDER nicht gesetzt – verwende /data/output.")
        if not cls.SMTP_USER and not cls.SMTP_PASSWORD:
            warnings.append("E-Mail nicht konfiguriert (SMTP_USER/SMTP_PASSWORD fehlen).")
        return warnings


config = Config()
