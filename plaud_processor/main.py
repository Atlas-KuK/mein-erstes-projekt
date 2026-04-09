"""Haupt-Orchestrierung: Fetch → Transkription → Analyse → PDF → E-Mail."""

import logging
import sys
import time
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("plaud")

import config
import storage
from plaud_client import scan_watch_folder, get_pending_recordings
from transcriber import transcribe, detect_speakers
from analyzer import analyze, check_ollama_available
from pdf_generator import generate_pdf
from onedrive_client import sync_pdf
from email_notifier import queue_notification, process_queue


def process_recording(recording: dict):
    """Einzelne Aufnahme komplett verarbeiten."""
    rec_id = recording["id"]
    filename = recording["filename"]
    filepath = recording["filepath"]
    template = recording.get("template", "meeting")

    logger.info("=== Verarbeite: %s (ID: %d, Vorlage: %s) ===", filename, rec_id, template)

    # 1. Transkription
    try:
        storage.update_recording_status(rec_id, "transkribiert")
        text, segments = transcribe(filepath)

        if not text.strip():
            logger.error("Transkription leer fuer: %s", filename)
            storage.update_recording_status(rec_id, "fehler")
            return

        # Engine bestimmen
        engine = "whisper_local"
        if config.OPENAI_API_KEY and not _whisper_available():
            engine = "openai_api"

        storage.add_transcript(rec_id, text, segments, config.TRANSCRIPTION_LANGUAGE, engine)
        logger.info("Transkript gespeichert: %d Zeichen, %d Segmente", len(text), len(segments))

    except Exception as e:
        logger.error("Transkription fehlgeschlagen fuer %s: %s", filename, e)
        storage.update_recording_status(rec_id, "fehler")
        return

    # 2. Sprecher-Erkennung
    try:
        speakers = detect_speakers(segments)
        for speaker in speakers:
            storage.add_speaker(rec_id, speaker["label"], speaker["segments"])
        logger.info("%d Sprecher erkannt", len(speakers))
    except Exception as e:
        logger.warning("Sprecher-Erkennung fehlgeschlagen: %s", e)

    # 3. KI-Analyse
    try:
        storage.update_recording_status(rec_id, "verarbeitet")
        result = analyze(text, template)

        if not result.success:
            logger.error("Analyse fehlgeschlagen: %s", result.error)
            storage.update_recording_status(rec_id, "fehler")
            return

    except Exception as e:
        logger.error("KI-Analyse fehlgeschlagen fuer %s: %s", filename, e)
        storage.update_recording_status(rec_id, "fehler")
        return

    # 4. PDF erstellen
    try:
        pdf_path = generate_pdf(
            filename=filename,
            title=f"Protokoll: {filename}",
            content_text=result.content_text,
            template_name=template,
        )
    except Exception as e:
        logger.error("PDF-Erstellung fehlgeschlagen fuer %s: %s", filename, e)
        storage.update_recording_status(rec_id, "fehler")
        return

    # 5. Protokoll speichern
    storage.add_protocol(
        recording_id=rec_id,
        template=template,
        content_html=result.content_html,
        content_text=result.content_text,
        pdf_path=pdf_path,
        engine=result.engine,
    )

    # 6. OneDrive-Sync
    try:
        sync_pdf(pdf_path)
    except Exception as e:
        logger.warning("OneDrive-Sync fehlgeschlagen: %s (weiter mit naechstem Schritt)", e)

    # 7. E-Mail einreihen
    try:
        queue_notification(rec_id, pdf_path, filename)
    except Exception as e:
        logger.warning("E-Mail-Einreihung fehlgeschlagen: %s", e)

    # Status: Fertig
    storage.update_recording_status(rec_id, "fertig")
    logger.info("=== Fertig: %s ===", filename)


def run_processing_cycle():
    """Einen Verarbeitungszyklus durchfuehren."""
    # Neue Dateien suchen
    neue = scan_watch_folder()
    if neue:
        logger.info("%d neue Datei(en) im Watch-Ordner gefunden", len(neue))

    # Alle neuen Aufnahmen verarbeiten
    pending = get_pending_recordings()
    for recording in pending:
        try:
            process_recording(recording)
        except Exception as e:
            logger.error("Fehler bei Verarbeitung von %s: %s", recording["filename"], e)
            storage.update_recording_status(recording["id"], "fehler")

    # E-Mail-Warteschlange verarbeiten
    process_queue()


def _whisper_available() -> bool:
    """Pruefen ob lokales Whisper installiert ist."""
    import shutil
    return shutil.which("whisper") is not None


def main():
    """Hauptschleife: Polling alle X Minuten."""
    logger.info("=" * 60)
    logger.info("Plaud Audio Processor gestartet")
    logger.info("=" * 60)
    logger.info("Watch-Ordner: %s", config.PLAUD_WATCH_FOLDER or "(nicht konfiguriert)")
    logger.info("PDF-Ausgabe: %s", config.PDF_OUTPUT_FOLDER)
    logger.info("Whisper-Modell: %s", config.WHISPER_MODEL)
    logger.info("Ollama: %s (%s)", config.OLLAMA_URL, config.OLLAMA_MODEL)
    logger.info("Poll-Intervall: %d Sekunden", config.POLL_INTERVAL_SECONDS)

    # Datenbank initialisieren
    storage.init_db()

    # Ollama-Status pruefen
    if check_ollama_available():
        logger.info("Ollama erreichbar - KI-Analyse kostenlos verfuegbar")
    else:
        if config.ANTHROPIC_API_KEY:
            logger.warning("Ollama nicht erreichbar - verwende Claude Haiku als Fallback")
        else:
            logger.warning("Weder Ollama noch Claude verfuegbar - KI-Analyse deaktiviert")

    # Hauptschleife
    while True:
        try:
            run_processing_cycle()
        except Exception as e:
            logger.error("Fehler im Verarbeitungszyklus: %s", e)

        logger.debug("Warte %d Sekunden bis zum naechsten Zyklus...", config.POLL_INTERVAL_SECONDS)
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
