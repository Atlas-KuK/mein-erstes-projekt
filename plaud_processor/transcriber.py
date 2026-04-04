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


def transcribe(audio_path: Path) -> str:
    """
    Transkribiert eine Audiodatei und gibt den Text zurück.
    Versucht zuerst die OpenAI Whisper API, dann das lokale CLI.
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audiodatei nicht gefunden: {audio_path}")

    if OPENAI_API_KEY:
        return _transcribe_via_api(audio_path)
    else:
        log.warning("OPENAI_API_KEY nicht gesetzt – versuche lokales Whisper-CLI")
        return _transcribe_via_cli(audio_path)


def _transcribe_via_api(audio_path: Path) -> str:
    """Nutzt die OpenAI Whisper REST-API."""
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
        return _transcribe_large_file(audio_path, client)

    log.info("Transkribiere via API: %s", audio_path.name)
    kwargs: dict = {"model": WHISPER_MODEL}
    if TRANSCRIPTION_LANGUAGE:
        kwargs["language"] = TRANSCRIPTION_LANGUAGE

    with open(audio_path, "rb") as fh:
        response = client.audio.transcriptions.create(file=fh, **kwargs)

    return response.text


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
