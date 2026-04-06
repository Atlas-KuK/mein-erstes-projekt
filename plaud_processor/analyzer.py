"""
Intelligente Analyse des Transkripts.

Priorität (kostenoptimiert):
  1. Ollama lokal  – kostenlos, offline, kein Datenschutzrisiko
  2. Claude Haiku  – Fallback wenn Ollama nicht verfügbar
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List

import requests

from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    OLLAMA_MODEL, OLLAMA_URL,
)

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du bist ein professioneller Assistent, der Besprechungs- und
Gesprächsaufzeichnungen auswertet. Analysiere das übergebene Transkript und
antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt in exakt dieser Struktur:

{
  "title":       "Kurzer, prägnanter Titel der Aufnahme (max. 80 Zeichen)",
  "summary":     "Zusammenfassung in 3-5 Sätzen",
  "key_points":  ["Kernaussage 1", "Kernaussage 2"],
  "action_items":["Aufgabe 1", "Aufgabe 2"],
  "decisions":   ["Entscheidung 1"],
  "sentiment":   "positiv | neutral | negativ | gemischt",
  "language":    "Deutsch",
  "tags":        ["Tag1", "Tag2"],
  "duration_hint":"Geschätzte Dauer in Minuten"
}

Antworte NUR mit dem JSON, ohne Markdown-Blöcke, ohne Erklärungen."""


@dataclass
class AnalysisResult:
    title: str = ""
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    sentiment: str = "neutral"
    language: str = ""
    tags: List[str] = field(default_factory=list)
    duration_hint: str = ""
    raw_transcript: str = ""


def analyze(transcript: str, recording_title: str = "") -> AnalysisResult:
    """Analysiert ein Transkript – Ollama bevorzugt, Claude als Fallback."""
    if not transcript.strip():
        return AnalysisResult(title=recording_title, raw_transcript=transcript)

    # Ollama zuerst versuchen (kostenlos)
    if _ollama_verfuegbar():
        log.info("Analyse via Ollama (%s) …", OLLAMA_MODEL)
        ergebnis = _analysiere_mit_ollama(transcript, recording_title)
        if ergebnis:
            return ergebnis

    # Fallback: Claude
    if ANTHROPIC_API_KEY:
        log.info("Ollama nicht verfügbar – Fallback auf Claude (%s)", CLAUDE_MODEL)
        return _analysiere_mit_claude(transcript, recording_title)

    log.warning("Weder Ollama noch Claude verfügbar – einfaches Ergebnis")
    return _einfaches_ergebnis(transcript, recording_title)


# ---------------------------------------------------------------------------
# Ollama (lokal, kostenlos)
# ---------------------------------------------------------------------------

def _ollama_verfuegbar() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _analysiere_mit_ollama(transcript: str, titel: str) -> AnalysisResult | None:
    """Sendet Anfrage an lokales Ollama."""
    # Transkript kürzen um Tokens zu sparen (Ollama ist lokal, aber trotzdem effizienter)
    kurz = transcript[:4000] if len(transcript) > 4000 else transcript
    nutzer_nachricht = f"Titel: {titel}\n\nTranskript:\n{kurz}"

    try:
        antwort = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": nutzer_nachricht},
                ],
                "stream": False,
                "options": {"temperature": 0.1},  # niedrig für konsistentes JSON
            },
            timeout=120,  # lokale Modelle brauchen etwas länger
        )
        antwort.raise_for_status()
        roh_text = antwort.json()["message"]["content"].strip()
        return _parse_json_antwort(roh_text, transcript, titel)

    except Exception as exc:
        log.warning("Ollama Fehler: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Claude Haiku (Fallback, günstig)
# ---------------------------------------------------------------------------

def _analysiere_mit_claude(transcript: str, titel: str) -> AnalysisResult:
    try:
        import anthropic
    except ImportError:
        return _einfaches_ergebnis(transcript, titel)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    kurz = transcript[:4000] if len(transcript) > 4000 else transcript

    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Titel: {titel}\n\nTranskript:\n{kurz}"}],
    )
    roh = msg.content[0].text.strip()
    return _parse_json_antwort(roh, transcript, titel) or _einfaches_ergebnis(transcript, titel)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _parse_json_antwort(roh: str, transcript: str, titel: str) -> AnalysisResult | None:
    roh = re.sub(r"^```[a-z]*\n?", "", roh)
    roh = re.sub(r"\n?```$", "", roh)
    try:
        d = json.loads(roh)
        return AnalysisResult(
            title=d.get("title") or titel,
            summary=d.get("summary", ""),
            key_points=d.get("key_points", []),
            action_items=d.get("action_items", []),
            decisions=d.get("decisions", []),
            sentiment=d.get("sentiment", "neutral"),
            language=d.get("language", ""),
            tags=d.get("tags", []),
            duration_hint=str(d.get("duration_hint", "")),
            raw_transcript=transcript,
        )
    except json.JSONDecodeError as exc:
        log.warning("JSON-Parsing fehlgeschlagen: %s", exc)
        return None


def _einfaches_ergebnis(transcript: str, titel: str) -> AnalysisResult:
    woerter = transcript.split()
    return AnalysisResult(
        title=titel or "Aufnahme",
        summary="(KI-Analyse nicht verfügbar – Rohtransskript beigefügt)",
        duration_hint=str(max(1, len(woerter) // 130)),
        raw_transcript=transcript,
    )
