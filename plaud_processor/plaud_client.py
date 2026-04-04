"""
Plaud.ai Client – holt neue Audioaufnahmen.

Strategie (Priorität):
  1. Plaud.ai API  – wenn PLAUD_API_TOKEN gesetzt ist
  2. Ordner-Watch  – wenn PLAUD_WATCH_FOLDER gesetzt ist

Bereits verarbeitete Dateien werden in einer lokalen Statusdatei vermerkt,
damit sie nicht doppelt verarbeitet werden.
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import List

import requests

from config import PLAUD_API_TOKEN, PLAUD_WATCH_FOLDER, WORK_DIR

log = logging.getLogger(__name__)

PROCESSED_IDS_FILE = WORK_DIR / "processed_ids.json"

# Plaud.ai API base URL (inoffiziell, kann sich ändern)
PLAUD_BASE_URL = "https://api.plaud.ai/v1"

# Unterstützte Audioformate
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".flac", ".webm", ".aac"}


def _load_processed_ids() -> set:
    if PROCESSED_IDS_FILE.exists():
        return set(json.loads(PROCESSED_IDS_FILE.read_text()))
    return set()


def _save_processed_ids(ids: set) -> None:
    PROCESSED_IDS_FILE.write_text(json.dumps(list(ids)))


class Recording:
    """Einheitliches Datenmodell für eine Aufnahme."""

    def __init__(self, recording_id: str, title: str, local_path: Path,
                 created_at: str = "", duration_seconds: int = 0):
        self.id = recording_id
        self.title = title
        self.local_path = local_path
        self.created_at = created_at
        self.duration_seconds = duration_seconds

    def __repr__(self) -> str:
        return f"Recording(id={self.id!r}, title={self.title!r})"


# ---------------------------------------------------------------------------
# Plaud.ai API (offizielle / inoffizielle REST-Schnittstelle)
# ---------------------------------------------------------------------------

class PlaudApiClient:
    """Kommuniziert mit der Plaud.ai REST-API."""

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })

    def _get(self, path: str, **kwargs) -> dict:
        url = f"{PLAUD_BASE_URL}{path}"
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def list_recordings(self) -> List[dict]:
        """Gibt alle Aufnahmen aus dem Plaud-Konto zurück."""
        try:
            data = self._get("/recordings")
            return data.get("recordings", data.get("items", []))
        except requests.HTTPError as exc:
            log.error("Plaud API Fehler beim Abrufen der Liste: %s", exc)
            return []

    def download_recording(self, recording: dict, dest_dir: Path) -> Path | None:
        """Lädt die Audiodatei herunter und gibt den lokalen Pfad zurück."""
        audio_url = recording.get("audio_url") or recording.get("file_url")
        if not audio_url:
            log.warning("Keine Audio-URL für Aufnahme %s", recording.get("id"))
            return None
        try:
            resp = self.session.get(audio_url, stream=True, timeout=120)
            resp.raise_for_status()
            # Dateinamen aus Content-Disposition oder URL ableiten
            filename = _extract_filename(resp, audio_url)
            dest = dest_dir / filename
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)
            log.info("Heruntergeladen: %s", dest)
            return dest
        except Exception as exc:
            log.error("Download fehlgeschlagen für %s: %s", recording.get("id"), exc)
            return None


def _extract_filename(response: requests.Response, url: str) -> str:
    cd = response.headers.get("content-disposition", "")
    if "filename=" in cd:
        part = cd.split("filename=")[-1].strip().strip('"').strip("'")
        if part:
            return part
    return Path(url.split("?")[0]).name or "recording.mp3"


# ---------------------------------------------------------------------------
# Ordner-Watch
# ---------------------------------------------------------------------------

class FolderWatcher:
    """Beobachtet einen lokalen Ordner auf neue Audiodateien."""

    def __init__(self, folder: str):
        self.folder = Path(folder)
        if not self.folder.exists():
            raise FileNotFoundError(f"Watch-Ordner existiert nicht: {self.folder}")

    def list_new_files(self, processed_ids: set) -> List[Path]:
        new_files = []
        for ext in AUDIO_EXTENSIONS:
            for p in self.folder.rglob(f"*{ext}"):
                if str(p) not in processed_ids:
                    new_files.append(p)
        return sorted(new_files, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Öffentliche Schnittstelle
# ---------------------------------------------------------------------------

def fetch_new_recordings() -> List[Recording]:
    """
    Gibt eine Liste neuer, noch nicht verarbeiteter Aufnahmen zurück.
    Kopiert die Audiodateien in WORK_DIR/audio/.
    """
    processed_ids = _load_processed_ids()
    audio_dir = WORK_DIR / "audio"
    audio_dir.mkdir(exist_ok=True)

    recordings: List[Recording] = []

    # --- Plaud API ---
    if PLAUD_API_TOKEN:
        client = PlaudApiClient(PLAUD_API_TOKEN)
        remote_list = client.list_recordings()
        for item in remote_list:
            rid = str(item.get("id", item.get("uuid", "")))
            if rid in processed_ids:
                continue
            local_path = client.download_recording(item, audio_dir)
            if local_path:
                rec = Recording(
                    recording_id=rid,
                    title=item.get("title") or item.get("name") or local_path.stem,
                    local_path=local_path,
                    created_at=item.get("created_at", ""),
                    duration_seconds=int(item.get("duration", 0)),
                )
                recordings.append(rec)
        return recordings

    # --- Ordner-Watch ---
    if PLAUD_WATCH_FOLDER:
        watcher = FolderWatcher(PLAUD_WATCH_FOLDER)
        new_files = watcher.list_new_files(processed_ids)
        for fp in new_files:
            dest = audio_dir / fp.name
            if not dest.exists():
                shutil.copy2(fp, dest)
            rec = Recording(
                recording_id=str(fp),
                title=fp.stem,
                local_path=dest,
            )
            recordings.append(rec)
        return recordings

    log.error(
        "Weder PLAUD_API_TOKEN noch PLAUD_WATCH_FOLDER konfiguriert. "
        "Bitte .env-Datei anpassen."
    )
    return []


def mark_as_processed(recording: Recording) -> None:
    """Markiert eine Aufnahme als verarbeitet."""
    ids = _load_processed_ids()
    ids.add(recording.id)
    _save_processed_ids(ids)
