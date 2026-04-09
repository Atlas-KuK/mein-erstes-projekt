"""E-Mail-Benachrichtigung: SMTP mit Rate-Limiting und Warteschlange."""

import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from threading import Lock

import config
import storage

logger = logging.getLogger(__name__)

_send_lock = Lock()
_pending_queue: list[dict] = []


def queue_notification(recording_id: int, pdf_path: str, title: str):
    """Benachrichtigung in Warteschlange einreihen."""
    _pending_queue.append({
        "recording_id": recording_id,
        "pdf_path": pdf_path,
        "title": title,
        "queued_at": datetime.now(),
    })
    logger.info("E-Mail in Warteschlange: %s (insgesamt %d)", title, len(_pending_queue))


def process_queue():
    """Warteschlange verarbeiten (Rate-Limiting beachten)."""
    if not _pending_queue:
        return

    if not _is_smtp_configured():
        logger.debug("SMTP nicht konfiguriert, E-Mails werden uebersprungen.")
        return

    # Rate-Limiting pruefen
    last_sent = storage.get_last_email_time()
    if last_sent:
        next_allowed = last_sent + timedelta(minutes=config.EMAIL_RATE_LIMIT_MINUTES)
        if datetime.now() < next_allowed:
            remaining = (next_allowed - datetime.now()).seconds // 60
            logger.debug("Rate-Limit aktiv. Naechste E-Mail in %d Minuten.", remaining)
            return

    with _send_lock:
        items = list(_pending_queue)
        _pending_queue.clear()

    if not items:
        return

    try:
        _send_bundled_email(items)
    except Exception as e:
        logger.error("E-Mail-Versand fehlgeschlagen: %s", e)
        # Zurueck in die Warteschlange
        _pending_queue.extend(items)


def _send_bundled_email(items: list[dict]):
    """Gebuendelte E-Mail mit allen Berichten senden."""
    msg = MIMEMultipart()
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO

    if len(items) == 1:
        msg["Subject"] = f"Plaud Bericht: {items[0]['title']}"
    else:
        msg["Subject"] = f"Plaud Berichte: {len(items)} neue Protokolle"

    # HTML-Body
    body_lines = [
        "<html><body>",
        "<h2>Plaud Audio Processor - Neue Berichte</h2>",
        f"<p>{len(items)} Protokoll(e) erstellt:</p>",
        "<ul>",
    ]
    for item in items:
        body_lines.append(f"<li><strong>{item['title']}</strong></li>")
    body_lines.extend([
        "</ul>",
        "<p>Die PDF-Dateien sind als Anhang beigefuegt und im OneDrive-Ordner verfuegbar.</p>",
        "<hr>",
        "<p style='color: #999; font-size: 12px;'>Automatisch erstellt von Plaud Audio Processor</p>",
        "</body></html>",
    ])

    msg.attach(MIMEText("\n".join(body_lines), "html", "utf-8"))

    # PDFs anhaengen
    for item in items:
        pdf_path = Path(item["pdf_path"])
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition", "attachment", filename=pdf_path.name
                )
                msg.attach(attachment)

    # Senden
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)

    # Log speichern
    recording_ids = [item["recording_id"] for item in items]
    storage.add_email_log(recording_ids, msg["Subject"])
    logger.info("E-Mail gesendet: %s (%d Anhaenge)", msg["Subject"], len(items))


def _is_smtp_configured() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD)
