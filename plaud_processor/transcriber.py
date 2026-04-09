"""Transkription: Whisper lokal (kostenlos) mit OpenAI API als Fallback."""

import json
import logging
import subprocess
import tempfile
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def transcribe(audio_path: str) -> tuple[str, list]:
    """Audiodatei transkribieren. Gibt (text, segments) zurueck.

    Versucht zuerst lokales Whisper, dann OpenAI API als Fallback.
    """
    # 1. Versuch: Lokales Whisper (kostenlos)
    try:
        text, segments = _transcribe_whisper_local(audio_path)
        if text.strip():
            logger.info("Transkription erfolgreich (Whisper lokal): %d Zeichen", len(text))
            return text, segments
    except Exception as e:
        logger.warning("Lokales Whisper fehlgeschlagen: %s", e)

    # 2. Fallback: OpenAI API
    if config.OPENAI_API_KEY:
        try:
            text, segments = _transcribe_openai_api(audio_path)
            if text.strip():
                logger.info("Transkription erfolgreich (OpenAI API): %d Zeichen", len(text))
                return text, segments
        except Exception as e:
            logger.error("OpenAI API Transkription fehlgeschlagen: %s", e)

    logger.error("Transkription komplett fehlgeschlagen fuer: %s", audio_path)
    return "", []


def _transcribe_whisper_local(audio_path: str) -> tuple[str, list]:
    """Lokales Whisper via CLI ausfuehren."""
    model = config.WHISPER_MODEL
    lang = config.TRANSCRIPTION_LANGUAGE

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "whisper",
            audio_path,
            "--model", model,
            "--output_format", "json",
            "--output_dir", tmpdir,
        ]
        if lang:
            cmd.extend(["--language", lang])

        logger.info("Starte Whisper lokal: Modell=%s, Sprache=%s", model, lang or "auto")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode != 0:
            raise RuntimeError(f"Whisper Fehler: {result.stderr[:500]}")

        # JSON-Ausgabe lesen
        json_files = list(Path(tmpdir).glob("*.json"))
        if not json_files:
            raise RuntimeError("Keine JSON-Ausgabe von Whisper gefunden.")

        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        text = data.get("text", "")
        segments = data.get("segments", [])

        # Segmente bereinigen
        clean_segments = []
        for seg in segments:
            clean_segments.append({
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", "").strip(),
            })

        return text.strip(), clean_segments


def _transcribe_openai_api(audio_path: str) -> tuple[str, list]:
    """Transkription ueber OpenAI Whisper API (Fallback)."""
    import openai

    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    with open(audio_path, "rb") as audio_file:
        params = {
            "model": "whisper-1",
            "file": audio_file,
            "response_format": "verbose_json",
        }
        if config.TRANSCRIPTION_LANGUAGE:
            params["language"] = config.TRANSCRIPTION_LANGUAGE

        response = client.audio.transcriptions.create(**params)

    text = response.text
    segments = []
    if hasattr(response, "segments") and response.segments:
        for seg in response.segments:
            segments.append({
                "start": seg.get("start", 0) if isinstance(seg, dict) else getattr(seg, "start", 0),
                "end": seg.get("end", 0) if isinstance(seg, dict) else getattr(seg, "end", 0),
                "text": (seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", "")).strip(),
            })

    return text.strip(), segments


def detect_speakers(segments: list, pause_threshold: float = None) -> list[dict]:
    """Einfache Sprecher-Erkennung via Pausen-Heuristik (>1.5 Sek = Sprecherwechsel).

    Kostenlos, keine API noetig.
    """
    if pause_threshold is None:
        pause_threshold = config.SPEAKER_PAUSE_THRESHOLD

    if not segments:
        return []

    speakers = []
    current_speaker = 1
    current_segments = []

    for i, seg in enumerate(segments):
        if i > 0:
            pause = seg["start"] - segments[i - 1]["end"]
            if pause > pause_threshold:
                # Sprecherwechsel
                if current_segments:
                    speakers.append({
                        "label": f"Sprecher {current_speaker}",
                        "segments": current_segments,
                    })
                current_speaker = (current_speaker % 2) + 1  # Wechsel zwischen 1 und 2
                current_segments = []

        current_segments.append(seg)

    # Letzten Sprecher hinzufuegen
    if current_segments:
        speakers.append({
            "label": f"Sprecher {current_speaker}",
            "segments": current_segments,
        })

    return speakers
