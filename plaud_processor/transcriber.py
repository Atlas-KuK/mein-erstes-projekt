"""Transkription: Whisper lokal (bevorzugt, kostenlos) → OpenAI API (Fallback)."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from config import config

logger = logging.getLogger(__name__)


@dataclass
class SprecherSegment:
    sprecher_nr: int
    text: str
    start: float
    ende: float


def _sprecher_segmente_aus_whisper(result: dict) -> list[SprecherSegment]:
    """
    Einfache Sprecher-Erkennung via Pausen-Heuristik:
    Pause > SPEAKER_PAUSE_THRESHOLD Sekunden → neuer Sprecher.
    Kein API-Aufruf, keine Kosten.
    """
    schwelle = config.SPEAKER_PAUSE_THRESHOLD
    segmente: list[SprecherSegment] = []
    aktueller_sprecher = 1
    letztes_ende: Optional[float] = None

    for seg in result.get("segments", []):
        start = seg.get("start", 0.0)
        ende = seg.get("end", 0.0)
        text = seg.get("text", "").strip()

        if letztes_ende is not None and (start - letztes_ende) > schwelle:
            aktueller_sprecher += 1

        if segmente and segmente[-1].sprecher_nr == aktueller_sprecher:
            # Segment beim gleichen Sprecher anhängen
            segmente[-1].text += " " + text
            segmente[-1].ende = ende
        else:
            segmente.append(SprecherSegment(
                sprecher_nr=aktueller_sprecher,
                text=text,
                start=start,
                ende=ende,
            ))
        letztes_ende = ende

    return segmente


def transkribiere_lokal(audiodatei: str) -> tuple[str, list[SprecherSegment]]:
    """Transkription mit lokalem Whisper (offline, kostenlos)."""
    import whisper  # lazy import – nur wenn verfügbar

    logger.info("Transkribiere lokal mit Whisper '%s': %s", config.WHISPER_MODEL, audiodatei)
    modell = whisper.load_model(config.WHISPER_MODEL)

    optionen: dict = {}
    if config.TRANSCRIPTION_LANGUAGE:
        optionen["language"] = config.TRANSCRIPTION_LANGUAGE

    result = modell.transcribe(audiodatei, **optionen)
    text = result.get("text", "").strip()
    segmente = _sprecher_segmente_aus_whisper(result)
    logger.info("Lokale Transkription abgeschlossen (%d Zeichen, %d Segmente)", len(text), len(segmente))
    return text, segmente


def transkribiere_via_api(audiodatei: str) -> tuple[str, list[SprecherSegment]]:
    """Transkription via OpenAI Whisper API (Fallback, ~€0.006/Min)."""
    from openai import OpenAI

    logger.warning("Nutze OpenAI Whisper API als Fallback – Kosten entstehen!")
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    with open(audiodatei, "rb") as f:
        kwargs: dict = {"model": "whisper-1", "file": f, "response_format": "verbose_json"}
        if config.TRANSCRIPTION_LANGUAGE:
            kwargs["language"] = config.TRANSCRIPTION_LANGUAGE
        result = client.audio.transcriptions.create(**kwargs)

    text = result.text.strip()
    # API liefert kein Segment-Timing für Sprecher-Heuristik → leere Segmentliste
    segmente: list[SprecherSegment] = []
    logger.info("API-Transkription abgeschlossen (%d Zeichen)", len(text))
    return text, segmente


def transkribiere(audiodatei: str) -> tuple[str, list[SprecherSegment]]:
    """
    Haupt-Einstiegspunkt:
    1. Lokales Whisper (kostenlos)
    2. OpenAI API (Fallback, nur wenn OPENAI_API_KEY gesetzt)
    Gibt immer tuple[str, list[SprecherSegment]] zurück.
    """
    if not Path(audiodatei).exists():
        raise FileNotFoundError(f"Audiodatei nicht gefunden: {audiodatei}")

    # Versuch 1: lokales Whisper
    try:
        return transkribiere_lokal(audiodatei)
    except ImportError:
        logger.warning("Whisper nicht installiert – versuche OpenAI API.")
    except Exception as exc:
        logger.error("Lokale Transkription fehlgeschlagen: %s", exc)

    # Versuch 2: OpenAI API
    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "Weder lokales Whisper noch OPENAI_API_KEY verfügbar. "
            "Bitte 'pip install openai-whisper' oder OPENAI_API_KEY setzen."
        )
    return transkribiere_via_api(audiodatei)
