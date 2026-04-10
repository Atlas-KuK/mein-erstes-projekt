"""Audiodateien abrufen – aus Watch-Ordner (Polling) oder via Plaud.ai API."""
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from config import config

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".opus", ".aac"}


@dataclass
class AudioDatei:
    dateiname: str
    dateipfad: str
    dauer_sek: Optional[float] = None
    aufnahme_ts: Optional[str] = None


def neue_dateien_aus_ordner(bekannte_dateinamen: set[str]) -> list[AudioDatei]:
    """Scannt PLAUD_WATCH_FOLDER und gibt unbekannte Audiodateien zurück."""
    ordner = config.PLAUD_WATCH_FOLDER
    if not ordner:
        return []

    pfad = Path(ordner)
    if not pfad.exists():
        logger.warning("Watch-Ordner existiert nicht: %s", ordner)
        return []

    neue = []
    for datei in sorted(pfad.iterdir()):
        if datei.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        if datei.name in bekannte_dateinamen:
            continue
        neue.append(AudioDatei(
            dateiname=datei.name,
            dateipfad=str(datei),
        ))
    return neue


def neue_dateien_via_api(bekannte_dateinamen: set[str]) -> list[AudioDatei]:
    """Ruft neue Aufnahmen über die Plaud.ai API ab (sofern Token gesetzt)."""
    token = config.PLAUD_API_TOKEN
    if not token:
        return []

    try:
        resp = requests.get(
            "https://api.plaud.ai/v1/recordings",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
        daten = resp.json()
    except Exception as exc:
        logger.error("Plaud API-Fehler: %s", exc)
        return []

    neue = []
    for eintrag in daten.get("recordings", []):
        name = eintrag.get("filename") or f"{eintrag['id']}.m4a"
        if name in bekannte_dateinamen:
            continue

        # Datei herunterladen
        ziel = Path(config.DATA_FOLDER) / "incoming" / name
        ziel.parent.mkdir(parents=True, exist_ok=True)

        if not ziel.exists():
            try:
                dl = requests.get(eintrag["download_url"], timeout=60, stream=True)
                dl.raise_for_status()
                with open(ziel, "wb") as fh:
                    for chunk in dl.iter_content(8192):
                        fh.write(chunk)
                logger.info("Heruntergeladen: %s", name)
            except Exception as exc:
                logger.error("Download fehlgeschlagen (%s): %s", name, exc)
                continue

        neue.append(AudioDatei(
            dateiname=name,
            dateipfad=str(ziel),
            dauer_sek=eintrag.get("duration"),
            aufnahme_ts=eintrag.get("created_at"),
        ))
    return neue


def alle_neuen_dateien_holen(bekannte_dateinamen: set[str]) -> list[AudioDatei]:
    """Kombiniert Watch-Ordner und API."""
    dateien = neue_dateien_aus_ordner(bekannte_dateinamen)
    dateien += neue_dateien_via_api(bekannte_dateinamen)
    return dateien
