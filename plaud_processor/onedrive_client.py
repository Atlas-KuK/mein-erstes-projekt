"""OneDrive-Sync: Kopiert PDF in lokalen Ordner, OneDrive Desktop synchronisiert automatisch."""

import logging
import shutil
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def sync_pdf(pdf_path: str) -> str | None:
    """PDF in den OneDrive-Ausgabeordner kopieren.

    OneDrive Desktop-App synchronisiert den Ordner automatisch in die Cloud.
    Kein Azure/SharePoint-API noetig.

    Returns: Pfad im Ausgabeordner oder None bei Fehler.
    """
    output_folder = config.PDF_OUTPUT_FOLDER
    if not output_folder:
        logger.warning("PDF_OUTPUT_FOLDER nicht konfiguriert.")
        return None

    try:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        src = Path(pdf_path)
        dest = output_path / src.name

        # Falls Datei bereits im Ausgabeordner liegt, nichts tun
        if src.resolve() == dest.resolve():
            logger.debug("PDF bereits im Ausgabeordner: %s", dest)
            return str(dest)

        shutil.copy2(str(src), str(dest))
        logger.info("PDF nach OneDrive-Ordner kopiert: %s", dest)
        return str(dest)

    except Exception as e:
        logger.error("Fehler beim Kopieren nach OneDrive: %s", e)
        return None
