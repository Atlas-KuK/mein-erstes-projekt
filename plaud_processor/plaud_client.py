"""Audiodateien erkennen: Watch-Ordner Polling oder Plaud.ai API."""

import logging
import shutil
from pathlib import Path

import config
import storage

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4", ".aac"}


def scan_watch_folder() -> list[dict]:
    """Watch-Ordner nach neuen Audiodateien durchsuchen."""
    watch = config.PLAUD_WATCH_FOLDER
    if not watch:
        logger.debug("Kein PLAUD_WATCH_FOLDER konfiguriert.")
        return []

    watch_path = Path(watch)
    if not watch_path.exists():
        logger.warning("Watch-Ordner existiert nicht: %s", watch)
        return []

    neue_dateien = []
    for f in watch_path.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        # Bereits bekannt?
        existing = storage.list_recordings()
        known_files = {r["filename"] for r in existing}
        if f.name in known_files:
            continue

        # In Upload-Ordner kopieren
        dest = config.UPLOAD_FOLDER / f.name
        if not dest.exists():
            shutil.copy2(str(f), str(dest))
            logger.info("Neue Audiodatei gefunden: %s", f.name)

        rec_id = storage.add_recording(
            filename=f.name,
            filepath=str(dest),
            filesize=f.stat().st_size,
        )
        neue_dateien.append({"id": rec_id, "filename": f.name, "filepath": str(dest)})

    if neue_dateien:
        logger.info("%d neue Audiodatei(en) gefunden.", len(neue_dateien))
    return neue_dateien


def get_pending_recordings() -> list[dict]:
    """Alle Aufnahmen mit Status 'neu' zurueckgeben."""
    return storage.list_recordings(status="neu")
