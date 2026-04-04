"""
Plaud Processor – Hauptprogramm

Ablauf für jede neue Aufnahme:
  1. Audiodatei von Plaud.ai holen (API oder Ordner-Watch)
  2. Transkription via OpenAI Whisper (inkl. Sprecher-Erkennung)
  3. In Datenbank speichern (für Web-UI)
  4. KI-Analyse via Claude → Zusammenfassungs-PDF
  5. PDF in Ausgabe-Ordner (OneDrive synct automatisch)
  6. E-Mail-Benachrichtigung senden (max. 1x / Stunde)

Ausführung:
  python main.py              # einmaliger Lauf
  python main.py --loop       # dauerhafter Polling-Betrieb
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import analyzer
import email_notifier
import pdf_generator
import plaud_client
import storage
import transcriber
from config import POLL_INTERVAL_SECONDS, WORK_DIR
from email_notifier import NotificationItem, queue_notification
from onedrive_client import OneDriveError, upload_to_onedrive

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FILE = WORK_DIR / "plaud_processor.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Kernlogik
# ---------------------------------------------------------------------------

def process_recording(recording: plaud_client.Recording) -> bool:
    log.info("━━━ Verarbeite: %s ━━━", recording.title)

    # In DB registrieren
    rec_id = storage.upsert_recording(
        filename=recording.local_path.name,
        title=recording.title,
        audio_path=str(recording.local_path),
        created_at=recording.created_at,
        duration=recording.duration_seconds,
    )
    storage.set_recording_status(rec_id, "processing")

    # 1. Transkription
    try:
        log.info("  ▶ Transkription …")
        transcript_text, segments = transcriber.transcribe(recording.local_path)
        log.info("  ✓ Transkript (%d Wörter, %d Segmente)",
                 len(transcript_text.split()), len(segments))
        storage.save_transcript(rec_id, transcript_text, segments)
    except Exception as exc:
        log.error("  ✗ Transkription fehlgeschlagen: %s", exc)
        storage.set_recording_status(rec_id, "error")
        return False

    # 2. KI-Analyse (für automatisches Zusammenfassungs-PDF)
    try:
        log.info("  ▶ KI-Analyse …")
        result = analyzer.analyze(transcript_text, recording.title)
        log.info("  ✓ Analyse: %s", result.title)
        result.raw_transcript = transcript_text
    except Exception as exc:
        log.error("  ✗ Analyse fehlgeschlagen: %s", exc)
        result = analyzer.AnalysisResult(
            title=recording.title,
            raw_transcript=transcript_text,
        )

    # 3. Zusammenfassungs-PDF erstellen
    try:
        log.info("  ▶ PDF wird erstellt …")
        pdf_path = pdf_generator.generate_pdf(
            result,
            recording_title=recording.title,
            created_at=recording.created_at,
        )
        log.info("  ✓ PDF: %s", pdf_path.name)
    except Exception as exc:
        log.error("  ✗ PDF-Erstellung fehlgeschlagen: %s", exc)
        pdf_path = None

    # 4. Ausgabe-Ordner (OneDrive)
    output_url = ""
    if pdf_path:
        try:
            log.info("  ▶ Speichern in Ausgabe-Ordner …")
            output_url = upload_to_onedrive(pdf_path)
            log.info("  ✓ Gespeichert: %s", output_url)
        except Exception as exc:
            log.error("  ✗ Ausgabe fehlgeschlagen: %s", exc)

    # 5. E-Mail
    try:
        item = NotificationItem(
            title=result.title,
            onedrive_url=output_url,
            pdf_filename=pdf_path.name if pdf_path else "",
            recorded_at=recording.created_at,
        )
        queue_notification(item)
    except Exception as exc:
        log.error("  ✗ E-Mail fehlgeschlagen: %s", exc)

    storage.set_recording_status(rec_id, "done")
    plaud_client.mark_as_processed(recording)
    log.info("  ✓ Fertig – Web-UI: http://localhost:8080/recording/%d", rec_id)
    return True


def run_once() -> int:
    log.info("Suche nach neuen Plaud-Aufnahmen …")
    recordings = plaud_client.fetch_new_recordings()

    if not recordings:
        log.info("Keine neuen Aufnahmen gefunden.")
        return 0

    log.info("%d neue Aufnahme(n) gefunden.", len(recordings))
    success = sum(1 for rec in recordings if process_recording(rec))
    email_notifier.flush_queue()
    log.info("Fertig: %d/%d erfolgreich.", success, len(recordings))
    return success


def run_loop() -> None:
    log.info("Plaud Processor gestartet (Polling alle %ds). Abbruch mit Ctrl+C.",
             POLL_INTERVAL_SECONDS)
    try:
        while True:
            run_once()
            log.info("Warte %d Sekunden …", POLL_INTERVAL_SECONDS)
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        log.info("Plaud Processor beendet.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plaud Processor – Audio transkribieren, analysieren, als PDF exportieren"
    )
    parser.add_argument("--loop", action="store_true",
                        help=f"Dauerhafter Polling-Betrieb (alle {POLL_INTERVAL_SECONDS}s)")
    args = parser.parse_args()

    if args.loop:
        run_loop()
    else:
        sys.exit(0 if run_once() >= 0 else 1)


if __name__ == "__main__":
    main()
