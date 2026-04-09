"""FastAPI Web-UI: Dashboard, Sprecher-Zuweisung, Protokollvorlagen."""

import logging
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
import storage
from analyzer import analyze, check_ollama_available
from protocol_templates import get_template_names

logger = logging.getLogger(__name__)

app = FastAPI(title="Plaud Audio Processor", version="1.0.0")

# Static files & Templates
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Hauptseite: Dashboard mit allen Aufnahmen."""
    recordings = storage.list_recordings(limit=50)
    protocols = storage.list_protocols(limit=20)
    ollama_ok = check_ollama_available()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recordings": recordings,
        "protocols": protocols,
        "templates": get_template_names(),
        "ollama_available": ollama_ok,
        "stats": _get_stats(),
    })


@app.get("/recording/{recording_id}", response_class=HTMLResponse)
async def recording_detail(request: Request, recording_id: int):
    """Detailseite einer Aufnahme."""
    recording = storage.get_recording(recording_id)
    if not recording:
        return HTMLResponse("<h1>Aufnahme nicht gefunden</h1>", status_code=404)

    transcript = storage.get_transcript(recording_id)
    speakers = storage.get_speakers(recording_id)
    protocol = storage.get_protocol(recording_id)

    return templates.TemplateResponse("recording_detail.html", {
        "request": request,
        "recording": recording,
        "transcript": transcript,
        "speakers": speakers,
        "protocol": protocol,
        "templates": get_template_names(),
    })


@app.post("/recording/{recording_id}/template")
async def set_template(recording_id: int, template: str = Form(...)):
    """Protokollvorlage fuer eine Aufnahme aendern."""
    storage.update_recording_template(recording_id, template)
    return RedirectResponse(f"/recording/{recording_id}", status_code=303)


@app.post("/recording/{recording_id}/reanalyze")
async def reanalyze(recording_id: int, template: str = Form("meeting")):
    """Aufnahme erneut analysieren mit anderer Vorlage."""
    transcript = storage.get_transcript(recording_id)
    if not transcript:
        return JSONResponse({"ok": False, "error": "Kein Transkript vorhanden"}, status_code=400)

    result = analyze(transcript["text"], template)
    if result.success:
        from pdf_generator import generate_pdf
        recording = storage.get_recording(recording_id)

        pdf_path = generate_pdf(
            filename=recording["filename"],
            title=f"Protokoll: {recording['filename']}",
            content_text=result.content_text,
            template_name=template,
        )

        storage.add_protocol(
            recording_id=recording_id,
            template=template,
            content_html=result.content_html,
            content_text=result.content_text,
            pdf_path=pdf_path,
            engine=result.engine,
        )
        storage.update_recording_status(recording_id, "fertig")

    return RedirectResponse(f"/recording/{recording_id}", status_code=303)


@app.post("/speaker/{speaker_id}/name")
async def update_speaker(speaker_id: int, name: str = Form(...)):
    """Sprechername zuweisen."""
    storage.update_speaker_name(speaker_id, name)
    return JSONResponse({"ok": True})


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...), titel: str = Form("")):
    """Audiodatei per HTTP POST hochladen (fuer iPhone Shortcut)."""
    if not file.filename:
        return JSONResponse({"ok": False, "error": "Keine Datei angegeben"}, status_code=400)

    dest = config.UPLOAD_FOLDER / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    filesize = dest.stat().st_size
    rec_id = storage.add_recording(
        filename=file.filename,
        filepath=str(dest),
        filesize=filesize,
    )

    logger.info("Upload empfangen: %s (%d Bytes)", file.filename, filesize)
    return JSONResponse({"ok": True, "datei": file.filename, "id": rec_id})


@app.get("/api/status")
async def api_status():
    """System-Status abfragen."""
    return JSONResponse({
        "ok": True,
        "ollama": check_ollama_available(),
        "stats": _get_stats(),
    })


@app.get("/api/recordings")
async def api_list_recordings():
    """Alle Aufnahmen als JSON."""
    return JSONResponse({"recordings": storage.list_recordings(limit=100)})


@app.get("/protocol/{recording_id}/pdf")
async def download_pdf(recording_id: int):
    """PDF herunterladen."""
    protocol = storage.get_protocol(recording_id)
    if not protocol or not protocol.get("pdf_path"):
        return JSONResponse({"error": "Kein PDF vorhanden"}, status_code=404)

    pdf_path = Path(protocol["pdf_path"])
    if not pdf_path.exists():
        return JSONResponse({"error": "PDF-Datei nicht gefunden"}, status_code=404)

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )


def _get_stats() -> dict:
    """Statistiken fuer das Dashboard."""
    all_recs = storage.list_recordings(limit=10000)
    return {
        "total": len(all_recs),
        "neu": sum(1 for r in all_recs if r["status"] == "neu"),
        "verarbeitet": sum(1 for r in all_recs if r["status"] == "verarbeitet"),
        "fertig": sum(1 for r in all_recs if r["status"] == "fertig"),
        "fehler": sum(1 for r in all_recs if r["status"] == "fehler"),
    }
