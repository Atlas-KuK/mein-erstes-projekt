"""
Audio-Transkription via OpenAI Whisper API.

Fallback: Falls openai nicht installiert ist, wird ein lokales
          whisper-CLI-Tool versucht (pip install openai-whisper).
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from config import OPENAI_API_KEY, TRANSCRIPTION_LANGUAGE, WHISPER_MODEL

log = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB – Limit der Whisper-API


class TranscriptionError(Exception):
    pass


def transcribe(audio_path: Path) -> tuple[str, list]:
    """
    Transkribiert eine Audiodatei.
    Gibt (text, segments) zurück.
    segments = [{"text": "...", "speaker": "Sprecher A", "start": 0.0, "end": 3.5}, ...]
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audiodatei nicht gefunden: {audio_path}")

    if OPENAI_API_KEY:
        return _transcribe_via_api(audio_path)
    else:
        log.warning("OPENAI_API_KEY nicht gesetzt – versuche lokales Whisper-CLI")
        text = _transcribe_via_cli(audio_path)
        return text, _split_into_segments(text)


def _transcribe_via_api(audio_path: Path) -> tuple[str, list]:
    """Nutzt die OpenAI Whisper REST-API mit verbose_json für Segmente."""
    try:
        from openai import OpenAI
    except ImportError:
        raise TranscriptionError(
            "openai-Paket nicht installiert. Bitte: pip install openai"
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    file_size = audio_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        log.info("Datei %.1f MB – wird in Segmente aufgeteilt", file_size / 1024 / 1024)
        text = _transcribe_large_file(audio_path, client)
        return text, _split_into_segments(text)

    log.info("Transkribiere via API: %s", audio_path.name)
    kwargs: dict = {"model": WHISPER_MODEL, "response_format": "verbose_json"}
    if TRANSCRIPTION_LANGUAGE:
        kwargs["language"] = TRANSCRIPTION_LANGUAGE

    with open(audio_path, "rb") as fh:
        response = client.audio.transcriptions.create(file=fh, **kwargs)

    raw_segments = getattr(response, "segments", None) or []
    segments = _assign_speakers(raw_segments, response.text)
    return response.text, segments


def _transcribe_large_file(audio_path: Path, client) -> str:
    """
    Teilt große Dateien mit ffmpeg in 10-Minuten-Segmente auf
    und transkribiert jedes Segment separat.
    """
    try:
        import shutil
        if not shutil.which("ffmpeg"):
            raise TranscriptionError("ffmpeg nicht gefunden – große Dateien nicht unterstützt")

        segments_dir = Path(tempfile.mkdtemp())
        segment_pattern = str(segments_dir / "seg_%03d.mp3")

        subprocess.run(
            [
                "ffmpeg", "-i", str(audio_path),
                "-f", "segment", "-segment_time", "540",
                "-ar", "16000", "-ac", "1",
                "-c:a", "libmp3lame", "-q:a", "4",
                segment_pattern,
            ],
            check=True,
            capture_output=True,
        )

        texts = []
        kwargs: dict = {"model": WHISPER_MODEL}
        if TRANSCRIPTION_LANGUAGE:
            kwargs["language"] = TRANSCRIPTION_LANGUAGE

        for seg in sorted(segments_dir.glob("seg_*.mp3")):
            log.info("  Segment: %s", seg.name)
            with open(seg, "rb") as fh:
                resp = client.audio.transcriptions.create(file=fh, **kwargs)
            texts.append(resp.text)
            seg.unlink()

        return "\n".join(texts)

    except subprocess.CalledProcessError as exc:
        raise TranscriptionError(f"ffmpeg Fehler: {exc.stderr.decode()}")


def _transcribe_via_cli(audio_path: Path) -> str:
    """Fallback: Nutzt das lokale openai-whisper CLI."""
    import shutil
    if not shutil.which("whisper"):
        raise TranscriptionError(
            "Weder openai-Paket noch whisper-CLI gefunden.\n"
            "Bitte installieren: pip install openai  (empfohlen)\n"
            "oder:               pip install openai-whisper"
        )

    out_dir = Path(tempfile.mkdtemp())
    cmd = ["whisper", str(audio_path), "--output_dir", str(out_dir), "--output_format", "txt"]
    if TRANSCRIPTION_LANGUAGE:
        cmd += ["--language", TRANSCRIPTION_LANGUAGE]

    log.info("Transkribiere via lokales Whisper-CLI: %s", audio_path.name)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise TranscriptionError(f"Whisper-CLI Fehler: {result.stderr}")

    txt_file = out_dir / (audio_path.stem + ".txt")
    if txt_file.exists():
        return txt_file.read_text(encoding="utf-8")

    raise TranscriptionError("Whisper-CLI hat keine Ausgabedatei erzeugt")


# ---------------------------------------------------------------------------
# Sprecher-Erkennung (heuristisch via Claude)
# ---------------------------------------------------------------------------

def _assign_speakers(raw_segments: list, full_text: str) -> list:
    """
    Versucht Sprecherwechsel via Claude zu erkennen.
    Gibt Segmente mit speaker-Feld zurück.
    Fallback: einfache Absatz-Aufteilung mit generischen Namen.
    """
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

    # Basis-Segmente aus Whisper aufbereiten
    base = []
    for s in raw_segments:
        text = s.get("text", "").strip() if isinstance(s, dict) else getattr(s, "text", "").strip()
        if not text:
            continue
        start = s.get("start", 0) if isinstance(s, dict) else getattr(s, "start", 0)
        end   = s.get("end",   0) if isinstance(s, dict) else getattr(s, "end",   0)
        base.append({"text": text, "start": float(start), "end": float(end), "speaker": ""})

    if not base:
        return _split_into_segments(full_text)

    if not ANTHROPIC_API_KEY:
        return _generic_speaker_labels(base)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Nur ersten 3000 Zeichen analysieren (Kosten sparen)
        sample = full_text[:3000]
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system="Du erkennst Sprecherwechsel in Transkripten. Antworte NUR mit JSON.",
            messages=[{"role": "user", "content": f"""Analysiere dieses Transkript und erkenne Sprecherwechsel.
Gib für jeden der {len(base)} Sätze einen Sprecher an (Sprecher A, Sprecher B, etc.).
Antworte mit einem JSON-Array der gleichen Länge wie die Eingabe:
[{{"speaker": "Sprecher A"}}, {{"speaker": "Sprecher B"}}, ...]

Transkript-Sätze:
{chr(10).join(f'{i+1}. {s["text"]}' for i,s in enumerate(base[:50]))}"""}],
        )

        import json, re
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        labels = json.loads(raw)

        for i, seg in enumerate(base):
            if i < len(labels):
                seg["speaker"] = labels[i].get("speaker", f"Sprecher {chr(65+i%4)}")
            else:
                seg["speaker"] = "Sprecher A"

        log.info("Sprecher-Erkennung: %d Segmente analysiert",  len(base))
        return base

    except Exception as exc:
        log.warning("Sprecher-Erkennung via Claude fehlgeschlagen: %s", exc)
        return _generic_speaker_labels(base)


def _generic_speaker_labels(segments: list) -> list:
    """Weist generische Sprecher-Labels zu (wechselt bei langen Pausen)."""
    speaker_idx = 0
    prev_end = 0.0
    for seg in segments:
        gap = seg.get("start", 0) - prev_end
        if gap > 2.0:  # > 2 Sekunden Pause = möglicher Sprecherwechsel
            speaker_idx = (speaker_idx + 1) % 4
        seg["speaker"] = f"Sprecher {chr(65 + speaker_idx)}"
        prev_end = seg.get("end", 0)
    return segments


def _split_into_segments(text: str) -> list:
    """Teilt reinen Text in Absätze auf (Fallback ohne Timestamps)."""
    segments = []
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            segments.append({"text": para, "start": 0.0, "end": 0.0, "speaker": "Sprecher A"})
    if not segments and text.strip():
        segments = [{"text": text.strip(), "start": 0.0, "end": 0.0, "speaker": "Sprecher A"}]
    return segments
