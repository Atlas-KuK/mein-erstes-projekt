"""OneDrive-Sync: Kopiert PDFs in den lokalen Ausgabe-Ordner.
OneDrive Desktop synchronisiert den Ordner automatisch – kein API nötig."""
import logging
import shutil
from pathlib import Path

from config import config

logger = logging.getLogger(__name__)


def pdf_in_onedrive_kopieren(pdf_pfad: str) -> str:
    """
    Kopiert eine PDF-Datei in PDF_OUTPUT_FOLDER.
    Da dieser Ordner direkt in OneDrive liegt, synchronisiert
    der OneDrive-Desktop-Client die Datei automatisch.
    Gibt den Zielpfad zurück.
    """
    quelle = Path(pdf_pfad)
    if not quelle.exists():
        logger.error("PDF nicht gefunden: %s", pdf_pfad)
        return pdf_pfad

    ziel_ordner = Path(config.PDF_OUTPUT_FOLDER)
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    ziel = ziel_ordner / quelle.name

    if ziel.resolve() == quelle.resolve():
        # Datei liegt bereits im Zielordner
        logger.info("PDF bereits in OneDrive-Ordner: %s", ziel)
        return str(ziel)

    shutil.copy2(str(quelle), str(ziel))
    logger.info("PDF in OneDrive-Ordner kopiert: %s → %s", quelle.name, ziel)
    return str(ziel)
