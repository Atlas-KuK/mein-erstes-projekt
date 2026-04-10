"""FastAPI Web-UI auf Port 8080 – Dashboard, Sprecher-Zuweisung, Protokollvorlagen, Upload."""
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import storage
import analyzer
import protocol_templates
import pdf_generator
import onedrive_client
import email_notifier
from config import config
import transcriber
import plaud_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Plaud Audio Processor", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

UPLOAD_DIR = Path(config.DATA_FOLDER) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".opus", ".aac"}


@app.on_event("startup")
async def startup():
    storage.init_db()
    logger.info("Web-App gestartet auf Port 8080")


# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    recordings = storage.alle_recordings_holen(limit=50)
    recordings_list = [dict(r) for r in recordings]
    for rec in recordings_list:
        proto = storage.protokoll_holen(rec["id"])
        rec["protokoll"] = dict(proto) if proto else None
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recordings": recordings_list,
        "vorlagen": protocol_templates.VORLAGEN,
        "config_warnungen": config.validate(),
    })


# ── Aufnahme-Detail ────────────────────────────────────────────────────────────

@app.get("/aufnahme/{recording_id}", response_class=HTMLResponse)
async def aufnahme_detail(request: Request, recording_id: int):
    rec = storage.recording_holen(recording_id)
    if not rec:
        raise HTTPException(404, "Aufnahme nicht gefunden")
    transcript = storage.transcript_holen(recording_id)
    sprecher = storage.sprecher_holen(recording_id)
    protokoll = storage.protokoll_holen(recording_id)
    return templates.TemplateResponse("recording_detail.html", {
        "request": request,
        "rec": dict(rec),
        "transcript": dict(transcript) if transcript else None,
        "sprecher": [dict(s) for s in sprecher],
        "protokoll": dict(protokoll) if protokoll else None,
        "vorlagen": protocol_templates.VORLAGEN,
    })


# ── Sprecher-Namen aktualisieren ───────────────────────────────────────────────

@app.post("/aufnahme/{recording_id}/sprecher")
async def sprecher_aktualisieren(
    recording_id: int,
    sprecher_nr: int = Form(...),
    name: str = Form(...),
):
    storage.sprecher_name_aktualisieren(recording_id, sprecher_nr, name.strip())
    return RedirectResponse(f"/aufnahme/{recording_id}", status_code=303)


# ── Protokoll neu erstellen ────────────────────────────────────────────────────

@app.post("/aufnahme/{recording_id}/protokoll")
async def protokoll_erstellen(
    recording_id: int,
    vorlage: str = Form("meeting"),
):
    rec = storage.recording_holen(recording_id)
    if not rec:
        raise HTTPException(404, "Aufnahme nicht gefunden")
    transcript = storage.transcript_holen(recording_id)
    if not transcript:
        raise HTTPException(400, "Noch kein Transkript vorhanden")

    transkript_text = transcript["text"]
    analyse = analyzer.analysiere(transkript_text, vorlage)

    from datetime import datetime
    datum_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    html_inhalt = protocol_templates.protokoll_html_erstellen(
        vorlage_key=vorlage,
        result=analyse,
        transkript=transkript_text,
        datum=datum_str,
    )

    dateiname_basis = Path(dict(rec)["dateiname"]).stem
    pdf_pfad = ""
    try:
        pdf_pfad = pdf_generator.pdf_erstellen(html_inhalt, dateiname_basis)
        onedrive_client.pdf_in_onedrive_kopieren(pdf_pfad)
    except Exception as exc:
        logger.error("PDF-Fehler: %s", exc)

    storage.protokoll_speichern(
        recording_id=recording_id,
        vorlage=vorlage,
        inhalt_html=html_inhalt,
        pdf_pfad=pdf_pfad,
        ki_modell=analyse.ki_modell,
    )

    return RedirectResponse(f"/aufnahme/{recording_id}", status_code=303)


# ── PDF herunterladen ──────────────────────────────────────────────────────────

@app.get("/aufnahme/{recording_id}/pdf")
async def pdf_download(recording_id: int):
    protokoll = storage.protokoll_holen(recording_id)
    if not protokoll or not protokoll["pdf_pfad"]:
        raise HTTPException(404, "Kein PDF vorhanden")
    pdf_pfad = protokoll["pdf_pfad"]
    if not Path(pdf_pfad).exists():
        raise HTTPException(404, "PDF-Datei nicht gefunden")
    return FileResponse(pdf_pfad, media_type="application/pdf",
                        filename=Path(pdf_pfad).name)


# ── iPhone Upload ──────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def audio_upload(
    file: UploadFile = File(...),
    titel: Optional[str] = Form(None),
):
    """HTTP POST Endpunkt für iPhone Shortcuts."""
    suffix = Path(file.filename or "aufnahme.m4a").suffix.lower()
    if suffix not in AUDIO_EXTENSIONS:
        raise HTTPException(400, f"Ungültiges Dateiformat: {suffix}")

    dateiname = titel.strip().replace(" ", "_") + suffix if titel else file.filename
    ziel = UPLOAD_DIR / dateiname
    counter = 1
    while ziel.exists():
        stem = Path(dateiname).stem
        ziel = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    with open(ziel, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info("Upload: %s (%d Bytes)", ziel.name, ziel.stat().st_size)

    # Sofort in die Verarbeitung einspeisen
    import threading

    def verarbeite_im_hintergrund():
        import main as m
        audio = plaud_client.AudioDatei(dateiname=ziel.name, dateipfad=str(ziel))
        m.aufnahme_verarbeiten(audio)

    threading.Thread(target=verarbeite_im_hintergrund, daemon=True).start()

    return JSONResponse({"ok": True, "datei": ziel.name})


# ── API: Status ────────────────────────────────────────────────────────────────

@app.get("/api/status")
async def status():
    recordings = storage.alle_recordings_holen(limit=5)
    return {
        "status": "ok",
        "letzte_aufnahmen": len(recordings),
        "ollama_url": config.OLLAMA_URL,
        "whisper_modell": config.WHISPER_MODEL,
        "warnungen": config.validate(),
    }
