"""
Plaud Processor – Hauptprogramm

Ablauf für jede neue Aufnahme:
  1. Audiodatei von Plaud.ai holen (API oder Ordner-Watch)
  2. Transkription via OpenAI Whisper
  3. KI-Analyse via Claude (Anthropic)
  4. PDF-Bericht erstellen
  5. PDF nach OneDrive hochladen
  6. E-Mail-Benachrichtigung senden (max. 1x / Stunde)

Ausführung:
  python main.py              # einmaliger Lauf
  python main.py --loop       # dauerhafter Polling-Betrieb
  python main.py --once       # gleichbedeutend mit Standard (kein Loop)
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Module dieses Projekts
import analyzer
import email_notifier
import pdf_generator
import plaud_client
import transcriber
from config import POLL_INTERVAL_SECONDS, WORK_DIR
from email_notifier import NotificationItem, queue_notification
from onedrive_client import OneDriveError, upload_to_onedrive

# ---------------------------------------------------------------------------
# Logging einrichten
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
    """
    Verarbeitet eine einzelne Aufnahme vollständig.
    Gibt True zurück, wenn die Verarbeitung erfolgreich war.
    """
    log.info("━━━ Verarbeite: %s ━━━", recording.title)

    # 1. Transkription
    try:
        log.info("  ▶ Transkription …")
        transcript = transcriber.transcribe(recording.local_path)
        log.info("  ✓ Transkript (%d Wörter)", len(transcript.split()))
    except Exception as exc:
        log.error("  ✗ Transkription fehlgeschlagen: %s", exc)
        return False

    # 2. KI-Analyse
    try:
        log.info("  ▶ KI-Analyse …")
        result = analyzer.analyze(transcript, recording.title)
        log.info("  ✓ Analyse abgeschlossen (Titel: %s)", result.title)
    except Exception as exc:
        log.error("  ✗ Analyse fehlgeschlagen: %s", exc)
        # Fallback: minimales Ergebnis
        result = analyzer.AnalysisResult(
            title=recording.title,
            raw_transcript=transcript,
        )

    # 3. PDF erstellen
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
        return False

    # 4. OneDrive Upload
    onedrive_url = ""
    try:
        log.info("  ▶ OneDrive Upload …")
        onedrive_url = upload_to_onedrive(pdf_path)
        log.info("  ✓ OneDrive: %s", onedrive_url)
    except OneDriveError as exc:
        log.error("  ✗ OneDrive Upload fehlgeschlagen: %s", exc)
        # Nicht kritisch – PDF ist lokal vorhanden
    except Exception as exc:
        log.error("  ✗ Unerwarteter OneDrive-Fehler: %s", exc)

    # 5. E-Mail benachrichtigen
    try:
        item = NotificationItem(
            title=result.title,
            onedrive_url=onedrive_url,
            pdf_filename=pdf_path.name,
            recorded_at=recording.created_at,
        )
        queue_notification(item)
    except Exception as exc:
        log.error("  ✗ E-Mail-Benachrichtigung fehlgeschlagen: %s", exc)

    # 6. Als verarbeitet markieren
    plaud_client.mark_as_processed(recording)
    log.info("  ✓ Aufnahme %s als verarbeitet markiert", recording.id)
    return True


def run_once() -> int:
    """Einmaliger Lauf – gibt die Anzahl verarbeiteter Aufnahmen zurück."""
    log.info("Suche nach neuen Plaud-Aufnahmen …")
    recordings = plaud_client.fetch_new_recordings()

    if not recordings:
        log.info("Keine neuen Aufnahmen gefunden.")
        return 0

    log.info("%d neue Aufnahme(n) gefunden.", len(recordings))
    success = 0
    for rec in recordings:
        if process_recording(rec):
            success += 1

    # Ausstehende E-Mails leeren
    email_notifier.flush_queue()

    log.info("Fertig: %d/%d Aufnahmen erfolgreich verarbeitet.", success, len(recordings))
    return success


def run_loop() -> None:
    """Dauerhafter Polling-Betrieb."""
    log.info(
        "Plaud Processor gestartet (Polling alle %d Sekunden). "
        "Abbruch mit Ctrl+C.",
        POLL_INTERVAL_SECONDS,
    )
    try:
        while True:
            run_once()
            log.info("Warte %d Sekunden …", POLL_INTERVAL_SECONDS)
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        log.info("Plaud Processor beendet.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plaud Processor – Audiodateien transkribieren, analysieren und als PDF exportieren"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help=f"Dauerhafter Polling-Betrieb (alle {POLL_INTERVAL_SECONDS}s)",
    )
    args = parser.parse_args()

    if args.loop:
        run_loop()
    else:
        count = run_once()
        sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
