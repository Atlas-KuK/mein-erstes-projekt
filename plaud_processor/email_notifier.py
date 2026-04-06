"""
E-Mail-Benachrichtigung nach erfolgreichem PDF-Export.

Rate-Limiting: maximal 1 E-Mail pro konfiguriertem Intervall (Standard: 60 Min.).
Überschüssige Benachrichtigungen werden in einer Warteschlange gesammelt
und in der nächsten erlaubten E-Mail zusammengefasst.
"""
from __future__ import annotations

import json
import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from config import (
    EMAIL_FROM, EMAIL_RATE_LIMIT_MINUTES, EMAIL_TO,
    SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER, WORK_DIR,
)

log = logging.getLogger(__name__)

STATE_FILE = WORK_DIR / "email_state.json"


class NotificationItem:
    def __init__(self, title: str, onedrive_url: str, pdf_filename: str,
                 recorded_at: str = ""):
        self.title = title
        self.onedrive_url = onedrive_url
        self.pdf_filename = pdf_filename
        self.recorded_at = recorded_at
        self.queued_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, d: dict) -> "NotificationItem":
        obj = cls(
            title=d.get("title", ""),
            onedrive_url=d.get("onedrive_url", ""),
            pdf_filename=d.get("pdf_filename", ""),
            recorded_at=d.get("recorded_at", ""),
        )
        obj.queued_at = d.get("queued_at", obj.queued_at)
        return obj


# ---------------------------------------------------------------------------
# Statusverwaltung
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_sent": None, "queue": []}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Öffentliche Schnittstelle
# ---------------------------------------------------------------------------

def queue_notification(item: NotificationItem) -> None:
    """
    Fügt eine Benachrichtigung zur Warteschlange hinzu.
    Sendet sofort, wenn das Rate-Limit nicht überschritten ist.
    """
    state = _load_state()
    state["queue"].append(item.to_dict())
    _save_state(state)
    log.info("Benachrichtigung eingereiht: %s", item.title)
    _flush_if_allowed()


def _flush_if_allowed() -> None:
    """Sendet die Warteschlange, wenn das Rate-Limit es erlaubt."""
    state = _load_state()
    if not state["queue"]:
        return

    now = datetime.now()
    last_sent = state.get("last_sent")

    if last_sent:
        last_dt = datetime.fromisoformat(last_sent)
        cooldown = timedelta(minutes=EMAIL_RATE_LIMIT_MINUTES)
        if now - last_dt < cooldown:
            next_allowed = last_dt + cooldown
            log.info(
                "Rate-Limit aktiv – nächste E-Mail frühestens um %s",
                next_allowed.strftime("%H:%M"),
            )
            return

    items = [NotificationItem.from_dict(d) for d in state["queue"]]
    _send_email(items)

    state["last_sent"] = now.isoformat()
    state["queue"] = []
    _save_state(state)


def flush_queue() -> None:
    """Erzwingt das Leeren der Warteschlange (z. B. beim Programmende)."""
    _flush_if_allowed()


# ---------------------------------------------------------------------------
# E-Mail erstellen und senden
# ---------------------------------------------------------------------------

def _send_email(items: List[NotificationItem]) -> None:
    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_TO]):
        log.error(
            "E-Mail nicht konfiguriert – bitte SMTP_USER, SMTP_PASSWORD "
            "und EMAIL_TO in der .env-Datei setzen."
        )
        return

    recipients = [r.strip() for r in EMAIL_TO.split(",") if r.strip()]

    if len(items) == 1:
        subject = f"Plaud Bericht bereit: {items[0].title}"
    else:
        subject = f"Plaud Berichte bereit: {len(items)} neue Aufnahmen"

    html_body = _build_html(items)
    text_body = _build_text(items)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM or SMTP_USER
    msg["To"]      = ", ".join(recipients)

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM or SMTP_USER, recipients, msg.as_bytes())
        log.info("E-Mail gesendet an: %s (%d Bericht/e)", ", ".join(recipients), len(items))
    except Exception as exc:
        log.error("E-Mail-Versand fehlgeschlagen: %s", exc)


def _build_html(items: List[NotificationItem]) -> str:
    rows = ""
    for item in items:
        link = (f'<a href="{item.onedrive_url}">{item.pdf_filename}</a>'
                if item.onedrive_url else item.pdf_filename)
        recorded = f"<br><small>Aufgenommen: {item.recorded_at}</small>" if item.recorded_at else ""
        rows += f"""
        <tr>
          <td style="padding:8px 12px; border-bottom:1px solid #eee;">
            <strong>{item.title}</strong>{recorded}
          </td>
          <td style="padding:8px 12px; border-bottom:1px solid #eee;">{link}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;">
  <div style="background:#1a3a5c;padding:20px;border-radius:6px 6px 0 0;">
    <h2 style="color:#fff;margin:0;">Plaud Bericht{'' if len(items)==1 else 'e'} bereit</h2>
  </div>
  <div style="background:#f9f9f9;padding:20px;border:1px solid #ddd;border-top:none;">
    <p>Folgende Aufnahme{'' if len(items)==1 else 'n'} wurde{'n' if len(items)>1 else ''} verarbeitet
       und als PDF in OneDrive gespeichert:</p>
    <table style="width:100%;border-collapse:collapse;background:#fff;
                  border:1px solid #ddd;border-radius:4px;">
      <thead>
        <tr style="background:#2e86c1;color:#fff;">
          <th style="padding:10px 12px;text-align:left;">Aufnahme</th>
          <th style="padding:10px 12px;text-align:left;">PDF</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <p style="margin-top:20px;font-size:12px;color:#888;">
      Diese E-Mail wurde automatisch von Plaud Processor erstellt.
    </p>
  </div>
</body>
</html>"""


def _build_text(items: List[NotificationItem]) -> str:
    lines = [f"Plaud Bericht{'e' if len(items)>1 else ''} bereit\n{'='*40}\n"]
    for item in items:
        lines.append(f"Titel:    {item.title}")
        if item.recorded_at:
            lines.append(f"Aufnahme: {item.recorded_at}")
        lines.append(f"PDF:      {item.pdf_filename}")
        if item.onedrive_url:
            lines.append(f"Link:     {item.onedrive_url}")
        lines.append("")
    lines.append("Diese E-Mail wurde automatisch von Plaud Processor erstellt.")
    return "\n".join(lines)
