"""
Intelligente Analyse des Transkripts via Claude (Anthropic API).

Erstellt aus einem Rohtext ein strukturiertes AnalysisResult mit:
  - Zusammenfassung
  - Schlüsselpunkte
  - Aufgaben / Action Items
  - Entscheidungen
  - Stimmung / Ton
  - Tags / Kategorien
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du bist ein professioneller Assistent, der Besprechungs- und
Gesprächsaufzeichnungen auswertet. Analysiere das übergebene Transkript und
antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt in exakt dieser Struktur:

{
  "title":       "Kurzer, prägnanter Titel der Aufnahme (max. 80 Zeichen)",
  "summary":     "Zusammenfassung in 3–5 Sätzen",
  "key_points":  ["Kernaussage 1", "Kernaussage 2", "..."],
  "action_items":["Aufgabe 1 (Verantwortlicher, falls bekannt)", "..."],
  "decisions":   ["Entscheidung 1", "..."],
  "sentiment":   "positiv | neutral | negativ | gemischt",
  "language":    "Erkannte Sprache (z. B. Deutsch, Englisch)",
  "tags":        ["Tag1", "Tag2", "..."],
  "duration_hint":"Geschätzte Gesprächsdauer in Minuten basierend auf dem Textumfang"
}

Antworte NUR mit dem JSON, ohne Markdown-Blöcke, ohne Erklärungen.
"""


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
    """
    Analysiert ein Transkript mit Claude und gibt ein AnalysisResult zurück.
    """
    if not transcript.strip():
        log.warning("Leeres Transkript – überspringe Analyse")
        return AnalysisResult(title=recording_title, raw_transcript=transcript)

    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY nicht gesetzt – Analyse nicht möglich")
        return _fallback_result(transcript, recording_title)

    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic-Paket nicht installiert. Bitte: pip install anthropic"
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = f"Titel der Aufnahme: {recording_title}\n\nTranskript:\n{transcript}"

    log.info("Analysiere Transkript mit Claude (%s)…", CLAUDE_MODEL)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_json = message.content[0].text.strip()
    # JSON aus möglichen Markdown-Blöcken befreien
    raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json)
    raw_json = re.sub(r"\n?```$", "", raw_json)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        log.error("JSON-Parsing fehlgeschlagen: %s\nRohantwort: %s", exc, raw_json[:500])
        return _fallback_result(transcript, recording_title)

    return AnalysisResult(
        title=data.get("title") or recording_title,
        summary=data.get("summary", ""),
        key_points=data.get("key_points", []),
        action_items=data.get("action_items", []),
        decisions=data.get("decisions", []),
        sentiment=data.get("sentiment", "neutral"),
        language=data.get("language", ""),
        tags=data.get("tags", []),
        duration_hint=str(data.get("duration_hint", "")),
        raw_transcript=transcript,
    )


def _fallback_result(transcript: str, title: str) -> AnalysisResult:
    """Gibt ein minimales Ergebnis zurück, wenn die KI-Analyse nicht verfügbar ist."""
    words = transcript.split()
    estimated_minutes = max(1, len(words) // 130)  # ~130 Wörter/Minute
    return AnalysisResult(
        title=title or "Aufnahme",
        summary="(Automatische Analyse nicht verfügbar – Rohtransskript beigefügt)",
        duration_hint=str(estimated_minutes),
        raw_transcript=transcript,
    )
