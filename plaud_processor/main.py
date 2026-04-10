"""Orchestrierung: Polling → Transkription → Analyse → PDF → OneDrive → E-Mail."""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import storage
import plaud_client
import transcriber
import analyzer
import protocol_templates
import pdf_generator
import onedrive_client
import email_notifier
from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def aufnahme_verarbeiten(datei: plaud_client.AudioDatei) -> bool:
    """
    Verarbeitet eine einzelne Audiodatei vollständig.
    Gibt True zurück bei Erfolg, False bei Fehler.
    Einzelne Fehler (z.B. E-Mail) brechen die Verarbeitung nicht ab.
    """
    recording_id = storage.recording_anlegen(
        dateiname=datei.dateiname,
        dateipfad=datei.dateipfad,
        dauer_sek=datei.dauer_sek,
        aufnahme_ts=datei.aufnahme_ts,
    )
    logger.info("Starte Verarbeitung: %s (ID %d)", datei.dateiname, recording_id)

    # --- Schritt 1: Transkription ---
    try:
        transkript_text, segmente = transcriber.transkribiere(datei.dateipfad)
    except Exception as exc:
        fehler = f"Transkription fehlgeschlagen: {exc}"
        logger.error(fehler)
        storage.recording_fehler_setzen(recording_id, fehler)
        return False

    storage.transcript_speichern(
        recording_id=recording_id,
        text=transkript_text,
        sprache=config.TRANSCRIPTION_LANGUAGE or "auto",
        modell=config.WHISPER_MODEL,
    )

    # Sprecher speichern
    for seg in segmente:
        storage.sprecher_speichern(
            recording_id=recording_id,
            sprecher_nr=seg.sprecher_nr,
            name=f"Sprecher {seg.sprecher_nr}",
            start=seg.start,
            ende=seg.ende,
        )

    # --- Schritt 2: KI-Analyse ---
    analyse = analyzer.analysiere(transkript_text, vorlage="meeting")

    # --- Schritt 3: Protokoll-HTML erstellen ---
    datum_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    html_inhalt = protocol_templates.protokoll_html_erstellen(
        vorlage_key="meeting",
        result=analyse,
        transkript=transkript_text,
        datum=datum_str,
    )

    # --- Schritt 4: PDF erstellen ---
    pdf_pfad = ""
    try:
        dateiname_basis = Path(datei.dateiname).stem
        pdf_pfad = pdf_generator.pdf_erstellen(html_inhalt, dateiname_basis)
    except Exception as exc:
        logger.error("PDF-Erstellung fehlgeschlagen: %s", exc)

    # Protokoll in DB speichern
    storage.protokoll_speichern(
        recording_id=recording_id,
        vorlage="meeting",
        inhalt_html=html_inhalt,
        pdf_pfad=pdf_pfad,
        ki_modell=analyse.ki_modell,
    )

    # --- Schritt 5: OneDrive-Sync ---
    if pdf_pfad:
        try:
            onedrive_client.pdf_in_onedrive_kopieren(pdf_pfad)
        except Exception as exc:
            logger.error("OneDrive-Kopie fehlgeschlagen: %s", exc)

    # --- Schritt 6: E-Mail in Warteschlange ---
    try:
        email_notifier.bericht_in_warteschlange_stellen(
            dateiname=datei.dateiname,
            zusammenfassung=analyse.zusammenfassung,
            vorlage="meeting",
            pdf_pfad=pdf_pfad,
        )
    except Exception as exc:
        logger.error("E-Mail-Warteschlange fehlgeschlagen: %s", exc)

    storage.recording_als_verarbeitet_markieren(recording_id)
    logger.info("Verarbeitung abgeschlossen: %s", datei.dateiname)
    return True


def polling_loop() -> None:
    """Polling-Schleife: alle POLL_INTERVAL_SECONDS auf neue Dateien prüfen."""
    logger.info("Plaud Audio Processor gestartet.")
    warnungen = config.validate()
    for w in warnungen:
        logger.warning("Konfigurationswarnung: %s", w)

    storage.init_db()

    while True:
        try:
            bekannte = {r["dateiname"] for r in storage.alle_recordings_holen(limit=10000)}
            neue_dateien = plaud_client.alle_neuen_dateien_holen(bekannte)

            if neue_dateien:
                logger.info("%d neue Aufnahme(n) gefunden.", len(neue_dateien))
                for datei in neue_dateien:
                    aufnahme_verarbeiten(datei)
                # Warteschlange nach Batch verarbeiten
                email_notifier.warteschlange_verarbeiten()
            else:
                logger.debug("Keine neuen Aufnahmen.")

        except Exception as exc:
            logger.error("Fehler in Polling-Loop: %s", exc)

        logger.info("Warte %d Sekunden bis zum nächsten Polling...", config.POLL_INTERVAL_SECONDS)
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    polling_loop()
