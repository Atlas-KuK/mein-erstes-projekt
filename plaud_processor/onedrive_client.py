"""
PDF-Ausgabe: Kopiert die fertige PDF in den konfigurierten Ausgabe-Ordner.

Kein API, keine Kosten, keine Azure-Registrierung nötig.
Der Ordner wird von OneDrive / Google Drive / Dropbox automatisch synchronisiert.

Konfiguration in .env:
  PDF_OUTPUT_FOLDER=C:\\Users\\IhrName\\OneDrive\\Plaud Berichte
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from config import PDF_OUTPUT_FOLDER, WORK_DIR

log = logging.getLogger(__name__)


class OneDriveError(Exception):
    """Beibehalten für Kompatibilität mit main.py."""


def upload_to_onedrive(local_path: Path) -> str:
    """
    Kopiert die PDF in den konfigurierten Ausgabe-Ordner.
    Gibt den Ziel-Pfad als String zurück (wird in der E-Mail angezeigt).
    """
    # Zielordner bestimmen
    if PDF_OUTPUT_FOLDER:
        dest_dir = Path(PDF_OUTPUT_FOLDER)
    else:
        # Fallback: Unterordner im Arbeitsverzeichnis
        dest_dir = WORK_DIR / "Plaud Berichte"

    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / local_path.name

    # Bereits vorhanden? Eindeutigen Namen vergeben
    if dest_path.exists():
        stem = local_path.stem
        suffix = local_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.copy2(local_path, dest_path)
    log.info("PDF gespeichert: %s", dest_path)
    return str(dest_path)
