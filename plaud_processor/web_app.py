"""
Plaud Processor – Web-Oberfläche
Aufruf: http://localhost:8080
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Form
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
