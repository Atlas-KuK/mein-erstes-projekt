"""
Plaud Processor – Web-Oberfläche
Aufruf: http://localhost:8080
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import shutil
import threading
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import protocol_templates as pt
import storage

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Plaud Processor")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    recordings = storage.get_all_recordings()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recordings": recordings,
        "total": len(recordings),
    })


# ---------------------------------------------------------------------------
# Aufnahme-Detail
# ---------------------------------------------------------------------------

@app.get("/recording/{recording_id}", response_class=HTMLResponse)
async def recording_detail(request: Request, recording_id: int):
    rec = storage.get_recording(recording_id)
    if not rec:
        raise HTTPException(404, "Aufnahme nicht gefunden")

    transcript = storage.get_transcript(recording_id)
    speakers = storage.get_speakers()
    protocols = storage.get_protocols(recording_id)
    template_list = pt.list_templates()

    return templates.TemplateResponse("recording.html", {
        "request": request,
        "recording": rec,
        "transcript": transcript,
        "speakers": speakers,
        "protocols": protocols,
        "templates": template_list,
    })


# ---------------------------------------------------------------------------
# API: Sprecher speichern
# ---------------------------------------------------------------------------

@app.post("/api/recording/{recording_id}/speakers")
async def save_speakers(recording_id: int, request: Request):
    body = await request.json()
    segments = body.get("segments", [])

    # Neue Sprecher in DB aufnehmen
    for seg in segments:
        name = seg.get("speaker", "").strip()
        if name and name not in ("Unbekannt", "Sprecher A", "Sprecher B"):
            storage.upsert_speaker(name)

    storage.update_segments(recording_id, segments)
    return {"ok": True}


# ---------------------------------------------------------------------------
# API: Protokoll generieren
# ---------------------------------------------------------------------------

@app.post("/api/recording/{recording_id}/generate")
async def generate_protocol(recording_id: int, request: Request):
    body = await request.json()
    template_key = body.get("template", "notiz")

    rec = storage.get_recording(recording_id)
    if not rec:
        raise HTTPException(404, "Aufnahme nicht gefunden")

    transcript = storage.get_transcript(recording_id)
    if not transcript:
        raise HTTPException(400, "Kein Transkript vorhanden")

    try:
        html_content = pt.generate_protocol_html(
            template_key=template_key,
            transcript_text=transcript["raw_text"],
            segments=transcript["segments"],
            recording_title=rec["title"] or rec["filename"],
        )
    except Exception as exc:
        log.error("Protokoll-Generierung fehlgeschlagen: %s", exc)
        raise HTTPException(500, str(exc))

    # PDF erzeugen
    try:
        template_obj = pt.get_template(template_key)
        pdf_path = pt.protocol_to_pdf(
            html_content=html_content,
            title=rec["title"] or rec["filename"],
            template_label=template_obj.label,
            recording_id=recording_id,
        )
        pdf_str = str(pdf_path)
    except Exception as exc:
        log.error("PDF-Erstellung fehlgeschlagen: %s", exc)
        pdf_str = ""

    protocol_id = storage.save_protocol(
        recording_id=recording_id,
        template_type=template_key,
        content_html=html_content,
        pdf_path=pdf_str,
    )

    return {"ok": True, "protocol_id": protocol_id, "template": template_key}


# ---------------------------------------------------------------------------
# Protokoll anzeigen
# ---------------------------------------------------------------------------

@app.get("/recording/{recording_id}/protocol/{template_key}",
         response_class=HTMLResponse)
async def view_protocol(request: Request, recording_id: int, template_key: str):
    rec = storage.get_recording(recording_id)
    protocol = storage.get_protocol(recording_id, template_key)
    if not protocol:
        raise HTTPException(404, "Protokoll noch nicht generiert")

    template_obj = pt.get_template(template_key)
    return templates.TemplateResponse("protocol.html", {
        "request": request,
        "recording": rec,
        "protocol": protocol,
        "template": template_obj,
    })


# ---------------------------------------------------------------------------
# PDF herunterladen
# ---------------------------------------------------------------------------

@app.get("/recording/{recording_id}/protocol/{template_key}/pdf")
async def download_pdf(recording_id: int, template_key: str):
    protocol = storage.get_protocol(recording_id, template_key)
    if not protocol or not protocol.get("pdf_path"):
        raise HTTPException(404, "PDF nicht gefunden")

    pdf_path = Path(protocol["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(404, "PDF-Datei nicht vorhanden")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )


# ---------------------------------------------------------------------------
# API: Sprecher-Vorschläge
# ---------------------------------------------------------------------------

@app.get("/api/speakers")
async def get_speakers():
    return storage.get_speakers()


@app.post("/api/speakers")
async def add_speaker(request: Request):
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Name darf nicht leer sein")
    speaker_id = storage.upsert_speaker(name)
    return {"ok": True, "id": speaker_id}


# ---------------------------------------------------------------------------
# iPhone Shortcut Upload
# ---------------------------------------------------------------------------

UPLOAD_DIR = WORK_DIR / "eingang"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ERLAUBTE_ENDUNGEN = {".mp3", ".m4a", ".mp4", ".wav", ".ogg", ".flac", ".aac", ".webm"}


@app.post("/api/upload")
async def upload_von_iphone(
    file: UploadFile = File(...),
    titel: str = "",
):
    """
    Empfängt Audiodatei vom iPhone Shortcut.
    URL für den Shortcut: http://<PC-IP>:8080/api/upload
    """
    endung = Path(file.filename).suffix.lower()
    if endung not in ERLAUBTE_ENDUNGEN:
        raise HTTPException(400, f"Format nicht unterstützt: {endung}")

    # Dateiname mit Zeitstempel (verhindert Duplikate)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sicherer_name = f"{ts}_{Path(file.filename).name}"
    ziel = UPLOAD_DIR / sicherer_name

    with open(ziel, "wb") as fh:
        shutil.copyfileobj(file.file, fh)

    datei_mb = ziel.stat().st_size / 1024 / 1024
    log.info("iPhone-Upload empfangen: %s (%.1f MB)", sicherer_name, datei_mb)

    # Verarbeitung im Hintergrund starten (blockiert den Shortcut nicht)
    threading.Thread(
        target=_verarbeite_upload,
        args=(ziel, titel or Path(file.filename).stem),
        daemon=True,
    ).start()

    return {
        "ok": True,
        "datei": sicherer_name,
        "groesse_mb": round(datei_mb, 1),
        "nachricht": "Datei empfangen – Verarbeitung läuft im Hintergrund",
    }


def _verarbeite_upload(audio_pfad: Path, titel: str) -> None:
    """Verarbeitet hochgeladene Datei (läuft in eigenem Thread)."""
    try:
        import main as hauptprogramm
        from plaud_client import Recording
        rec = Recording(
            recording_id=str(audio_pfad),
            title=titel,
            local_path=audio_pfad,
        )
        hauptprogramm.process_recording(rec)
    except Exception as exc:
        log.error("Verarbeitung des Uploads fehlgeschlagen: %s", exc)


# ---------------------------------------------------------------------------
# Status-Seite (für iPhone Shortcut Bestätigung)
# ---------------------------------------------------------------------------

@app.get("/status", response_class=HTMLResponse)
async def status(request: Request):
    """Einfache Status-Seite – zeigt ob der Server läuft."""
    aufnahmen = storage.get_all_recordings()
    letzte = aufnahmen[:5] if aufnahmen else []
    html = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Plaud Processor – Status</title>
<style>body{{font-family:system-ui;padding:20px;max-width:500px;margin:auto}}
.ok{{color:#27ae60;font-size:48px;text-align:center}}
.card{{background:#f5f7fa;border-radius:8px;padding:16px;margin:12px 0}}
h1{{color:#1a3a5c}}</style></head>
<body>
<div class="ok">✓</div>
<h1 style="text-align:center">Server läuft</h1>
<div class="card">
  <strong>Letzte Aufnahmen:</strong><br>
  {'<br>'.join(f"{'✅' if r['status']=='done' else '⏳'} {r['title'] or r['filename']}" for r in letzte) or 'Noch keine Aufnahmen'}
</div>
<p style="text-align:center;color:#888">
  <a href="/">Dashboard öffnen</a>
</p>
</body></html>"""
    return HTMLResponse(html)
