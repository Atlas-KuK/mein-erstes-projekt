"""
Audio-Transkription mit lokalem Whisper (offline, kostenlos).

Priorität:
  1. Lokales whisper-CLI  (pip install openai-whisper) – kostenlos, offline
  2. OpenAI Whisper API   – nur als Fallback wenn OPENAI_API_KEY gesetzt

Lokales Whisper gibt JSON mit Timestamps aus → direkte Segment-Erkennung.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from config import OPENAI_API_KEY, TRANSCRIPTION_LANGUAGE, WHISPER_MODEL

log = logging.getLogger(__name__)

MAX_API_SIZE = 25 * 1024 * 1024  # 25 MB – Limit der OpenAI-API


class TranscriptionError(Exception):
    pass


def transcribe(audio_path: Path) -> tuple[str, list]:
    """
    Transkribiert eine Audiodatei.
    Gibt (volltext, segmente) zurück.
    Segmente: [{"text": "...", "speaker": "Sprecher A", "start": 0.0, "end": 3.5}]
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audiodatei nicht gefunden: {audio_path}")

    # Lokales Whisper bevorzugen (kostenlos)
    if shutil.which("whisper"):
        return _transkribiere_lokal(audio_path)

    # Fallback: OpenAI API
    if OPENAI_API_KEY:
        log.warning("Lokales Whisper nicht gefunden – nutze OpenAI API (kostenpflichtig)")
        return _transkribiere_api(audio_path)

    raise TranscriptionError(
        "Kein Whisper gefunden.\n"
        "Lokale Installation: pip install openai-whisper\n"
        "Oder: OPENAI_API_KEY in .env setzen"
    )


# ---------------------------------------------------------------------------
# Lokales Whisper CLI (kostenlos)
# ---------------------------------------------------------------------------

def _transkribiere_lokal(audio_path: Path) -> tuple[str, list]:
    """
    Nutzt das installierte whisper-CLI mit JSON-Ausgabe für Timestamps.
    Modell aus .env: WHISPER_MODEL (Standard: medium für gute Qualität/Geschwindigkeit)
    """
    out_dir = Path(tempfile.mkdtemp())

    # Modell: lokal heißt "medium", nicht "whisper-1" wie bei der API
    modell = WHISPER_MODEL if WHISPER_MODEL != "whisper-1" else "medium"

    cmd = [
        "whisper", str(audio_path),
        "--model", modell,
        "--output_dir", str(out_dir),
        "--output_format", "json",
    ]
    if TRANSCRIPTION_LANGUAGE:
        cmd += ["--language", TRANSCRIPTION_LANGUAGE]

    log.info("Transkribiere lokal (Modell: %s): %s", modell, audio_path.name)
    ergebnis = subprocess.run(cmd, capture_output=True, text=True)

    if ergebnis.returncode != 0:
        raise TranscriptionError(
            f"Whisper-Fehler:\n{ergebnis.stderr[-1000:]}"
        )

    # JSON-Ausgabe auslesen
    json_datei = out_dir / (audio_path.stem + ".json")
    if not json_datei.exists():
        # Fallback: .txt lesen
        txt_datei = out_dir / (audio_path.stem + ".txt")
        if txt_datei.exists():
            text = txt_datei.read_text(encoding="utf-8").strip()
            return text, _segmente_aus_text(text)
        raise TranscriptionError("Whisper hat keine Ausgabedatei erzeugt")

    daten = json.loads(json_datei.read_text(encoding="utf-8"))
    text = daten.get("text", "").strip()
    roh_segmente = daten.get("segments", [])

    log.info("  ✓ %d Wörter, %d Segmente erkannt", len(text.split()), len(roh_segmente))

    # Segmente aufbereiten und Sprecher zuweisen
    segmente = _sprecherzuweisung(roh_segmente, text)
    return text, segmente


# ---------------------------------------------------------------------------
# OpenAI API (Fallback, kostenpflichtig)
# ---------------------------------------------------------------------------

def _transkribiere_api(audio_path: Path) -> tuple[str, list]:
    try:
        from openai import OpenAI
    except ImportError:
        raise TranscriptionError("openai nicht installiert: pip install openai")

    client = OpenAI(api_key=OPENAI_API_KEY)

    if audio_path.stat().st_size > MAX_API_SIZE:
        log.info("Datei zu groß für API – splitte mit ffmpeg")
        text = _api_grosse_datei(audio_path, client)
        return text, _segmente_aus_text(text)

    log.info("Transkribiere via OpenAI API: %s", audio_path.name)
    kwargs: dict = {"model": "whisper-1", "response_format": "verbose_json"}
    if TRANSCRIPTION_LANGUAGE:
        kwargs["language"] = TRANSCRIPTION_LANGUAGE

    with open(audio_path, "rb") as fh:
        antwort = client.audio.transcriptions.create(file=fh, **kwargs)

    roh = getattr(antwort, "segments", None) or []
    return antwort.text, _sprecherzuweisung(roh, antwort.text)


def _api_grosse_datei(audio_path: Path, client) -> str:
    if not shutil.which("ffmpeg"):
        raise TranscriptionError("ffmpeg fehlt – große Dateien nicht möglich")

    seg_dir = Path(tempfile.mkdtemp())
    subprocess.run([
        "ffmpeg", "-i", str(audio_path),
        "-f", "segment", "-segment_time", "540",
        "-ar", "16000", "-ac", "1", "-c:a", "libmp3lame", "-q:a", "4",
        str(seg_dir / "seg_%03d.mp3"),
    ], check=True, capture_output=True)

    texte = []
    kwargs: dict = {"model": "whisper-1"}
    if TRANSCRIPTION_LANGUAGE:
        kwargs["language"] = TRANSCRIPTION_LANGUAGE

    for seg in sorted(seg_dir.glob("seg_*.mp3")):
        with open(seg, "rb") as fh:
            texte.append(client.audio.transcriptions.create(file=fh, **kwargs).text)
        seg.unlink()

    return "\n".join(texte)


# ---------------------------------------------------------------------------
# Sprecher-Zuweisung (heuristisch via Pausen, kein extra API-Aufruf)
# ---------------------------------------------------------------------------

def _sprecherzuweisung(roh_segmente: list, volltext: str) -> list:
    """
    Erkennt Sprecherwechsel anhand von Pausen zwischen Segmenten.
    Kein Claude-Aufruf nötig → keine Zusatzkosten.
    Im Web-UI können Sprecher manuell umbenannt werden.
    """
    if not roh_segmente:
        return _segmente_aus_text(volltext)

    segmente = []
    sprecher_idx = 0
    letztes_ende = 0.0

    for s in roh_segmente:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        start = float(s.get("start", 0))
        ende  = float(s.get("end",   0))

        # Pause > 1.5 Sekunden → Sprecherwechsel wahrscheinlich
        if start - letztes_ende > 1.5:
            sprecher_idx = (sprecher_idx + 1) % 6

        segmente.append({
            "text":    text,
            "start":   start,
            "end":     ende,
            "speaker": f"Sprecher {chr(65 + sprecher_idx)}",
        })
        letztes_ende = ende

    return segmente


def _segmente_aus_text(text: str) -> list:
    """Teilt reinen Text in Absätze auf (wenn keine Timestamps vorhanden)."""
    segs = []
    for absatz in text.split("\n\n"):
        absatz = absatz.strip()
        if absatz:
            segs.append({"text": absatz, "start": 0.0, "end": 0.0, "speaker": "Sprecher A"})
    if not segs and text.strip():
        segs = [{"text": text.strip(), "start": 0.0, "end": 0.0, "speaker": "Sprecher A"}]
    return segs
