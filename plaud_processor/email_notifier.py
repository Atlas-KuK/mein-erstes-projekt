"""E-Mail-Benachrichtigung mit SMTP, Rate-Limiting und Warteschlange.
Maximal 1 E-Mail pro EMAIL_RATE_LIMIT_MINUTES – mehrere Berichte werden gebündelt."""
import logging
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

from config import config
import storage

logger = logging.getLogger(__name__)

_warteschlange: list[dict] = []
_lock = threading.Lock()


def _kann_email_senden() -> bool:
    """Prüft Rate-Limit: max. 1 E-Mail pro konfiguriertem Intervall."""
    letzter = storage.letzten_email_zeitpunkt_holen()
    if letzter is None:
        return True
    naechste_erlaubt = letzter + timedelta(minutes=config.EMAIL_RATE_LIMIT_MINUTES)
    return datetime.now() >= naechste_erlaubt


def _email_senden(betreff: str, html_body: str, anhang_pfade: list[str]) -> bool:
    """Sendet eine E-Mail via SMTP."""
    if not all([config.SMTP_USER, config.SMTP_PASSWORD, config.EMAIL_TO]):
        logger.warning("E-Mail nicht konfiguriert – überspringe.")
        return False

    msg = MIMEMultipart("mixed")
    msg["Subject"] = betreff
    msg["From"] = config.EMAIL_FROM or config.SMTP_USER
    msg["To"] = config.EMAIL_TO

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    for pfad_str in anhang_pfade:
        pfad = Path(pfad_str)
        if not pfad.exists():
            continue
        with open(pfad, "rb") as f:
            teil = MIMEBase("application", "octet-stream")
            teil.set_payload(f.read())
        encoders.encode_base64(teil)
        teil.add_header("Content-Disposition", "attachment", filename=pfad.name)
        msg.attach(teil)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(msg["From"], [config.EMAIL_TO], msg.as_string())

        storage.email_log_eintragen(config.EMAIL_TO, betreff)
        logger.info("E-Mail gesendet: %s → %s", betreff, config.EMAIL_TO)
        return True
    except Exception as exc:
        logger.error("E-Mail-Fehler: %s", exc)
        return False


def _warteschlange_html() -> tuple[str, list[str]]:
    """Baut HTML-Body und PDF-Anhänge aus der aktuellen Warteschlange."""
    with _lock:
        eintraege = list(_warteschlange)
        _warteschlange.clear()

    if not eintraege:
        return "", []

    html_teile = [
        "<html><body>",
        "<h2>Plaud Audio Processor – Neue Berichte</h2>",
        f"<p>Es liegen {len(eintraege)} neue Aufnahme(n) vor:</p>",
        "<hr>",
    ]
    pdf_pfade = []

    for e in eintraege:
        html_teile.append(f"<h3>{e.get('dateiname', 'Aufnahme')}</h3>")
        html_teile.append(f"<p><strong>Vorlage:</strong> {e.get('vorlage', '')}</p>")
        zusammenfassung = e.get("zusammenfassung", "")
        if zusammenfassung:
            html_teile.append(f"<p>{zusammenfassung}</p>")
        html_teile.append("<hr>")
        if pdf := e.get("pdf_pfad"):
            pdf_pfade.append(pdf)

    html_teile.append("</body></html>")
    return "\n".join(html_teile), pdf_pfade


def bericht_in_warteschlange_stellen(
    dateiname: str,
    zusammenfassung: str,
    vorlage: str,
    pdf_pfad: Optional[str] = None,
) -> None:
    """Fügt einen Bericht zur Warteschlange hinzu und sendet bei Gelegenheit."""
    with _lock:
        _warteschlange.append({
            "dateiname": dateiname,
            "zusammenfassung": zusammenfassung,
            "vorlage": vorlage,
            "pdf_pfad": pdf_pfad,
        })

    # Sofort senden, wenn Rate-Limit erlaubt
    warteschlange_verarbeiten()


def warteschlange_verarbeiten() -> None:
    """Sendet alle Berichte in der Warteschlange (gebündelt), wenn Rate-Limit ok."""
    with _lock:
        if not _warteschlange:
            return

    if not _kann_email_senden():
        naechste = storage.letzten_email_zeitpunkt_holen()
        if naechste:
            warte_bis = naechste + timedelta(minutes=config.EMAIL_RATE_LIMIT_MINUTES)
            logger.info(
                "Rate-Limit aktiv – nächste E-Mail frühestens %s (%d Berichte warten).",
                warte_bis.strftime("%H:%M"), len(_warteschlange),
            )
        return

    html_body, pdf_pfade = _warteschlange_html()
    if not html_body:
        return

    anzahl = html_body.count("<h3>")
    betreff = (
        f"Plaud: {anzahl} neue Aufnahme(n)" if anzahl > 1
        else "Plaud: Neue Aufnahme verarbeitet"
    )
    _email_senden(betreff, html_body, pdf_pfade)
