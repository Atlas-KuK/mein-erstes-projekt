"""KI-Analyse: Ollama lokal (bevorzugt, kostenlos) → Claude Haiku (Fallback)."""
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

from config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_DE = (
    "Du bist ein präziser Assistent für Gesprächsanalyse. "
    "Antworte ausschließlich auf Deutsch. Sei klar und strukturiert."
)


@dataclass
class AnalysisResult:
    zusammenfassung: str
    kernpunkte: list[str] = field(default_factory=list)
    aufgaben: list[str] = field(default_factory=list)
    beschluesse: list[str] = field(default_factory=list)
    stimmung: str = ""
    ki_modell: str = ""
    roh_antwort: str = ""


def _analyse_prompt(transkript: str, vorlage: str) -> str:
    basis = f"""Analysiere das folgende Transkript und erstelle eine strukturierte Zusammenfassung.

Transkript:
{transkript[:6000]}

Antworte als JSON mit diesen Feldern:
{{
  "zusammenfassung": "...",
  "kernpunkte": ["...", "..."],
  "aufgaben": ["...", "..."],
  "beschluesse": ["...", "..."],
  "stimmung": "positiv|neutral|negativ"
}}"""
    return basis


def _parse_antwort(roh: str) -> dict:
    """Versucht JSON aus der KI-Antwort zu extrahieren."""
    roh = roh.strip()
    # JSON-Block aus Markdown herausschälen
    if "```json" in roh:
        roh = roh.split("```json", 1)[1].split("```")[0].strip()
    elif "```" in roh:
        roh = roh.split("```", 1)[1].split("```")[0].strip()

    try:
        return json.loads(roh)
    except json.JSONDecodeError:
        # Fallback: nur Zusammenfassung
        return {"zusammenfassung": roh, "kernpunkte": [], "aufgaben": [], "beschluesse": [], "stimmung": ""}


def analysiere_mit_ollama(transkript: str, vorlage: str = "meeting") -> AnalysisResult:
    """Analyse mit lokalem Ollama (kostenlos, offline)."""
    url = f"{config.OLLAMA_URL.rstrip('/')}/api/generate"
    prompt = _analyse_prompt(transkript, vorlage)

    logger.info("Ollama-Analyse mit Modell '%s'", config.OLLAMA_MODEL)
    resp = requests.post(
        url,
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "system": SYSTEM_PROMPT_DE,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    roh = resp.json().get("response", "")
    daten = _parse_antwort(roh)

    return AnalysisResult(
        zusammenfassung=daten.get("zusammenfassung", ""),
        kernpunkte=daten.get("kernpunkte", []),
        aufgaben=daten.get("aufgaben", []),
        beschluesse=daten.get("beschluesse", []),
        stimmung=daten.get("stimmung", ""),
        ki_modell=f"ollama/{config.OLLAMA_MODEL}",
        roh_antwort=roh,
    )


def analysiere_mit_claude(transkript: str, vorlage: str = "meeting") -> AnalysisResult:
    """Analyse mit Claude Haiku (Fallback, ~€0.001/Aufnahme)."""
    import anthropic

    logger.warning("Nutze Claude Haiku als Fallback – Kosten entstehen!")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = _analyse_prompt(transkript, vorlage)

    msg = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT_DE,
        messages=[{"role": "user", "content": prompt}],
    )
    roh = msg.content[0].text
    daten = _parse_antwort(roh)

    return AnalysisResult(
        zusammenfassung=daten.get("zusammenfassung", ""),
        kernpunkte=daten.get("kernpunkte", []),
        aufgaben=daten.get("aufgaben", []),
        beschluesse=daten.get("beschluesse", []),
        stimmung=daten.get("stimmung", ""),
        ki_modell=config.CLAUDE_MODEL,
        roh_antwort=roh,
    )


def analysiere(transkript: str, vorlage: str = "meeting") -> AnalysisResult:
    """
    Haupt-Einstiegspunkt:
    1. Ollama lokal (kostenlos, bevorzugt)
    2. Claude Haiku (Fallback, nur wenn ANTHROPIC_API_KEY gesetzt)
    """
    if not transkript.strip():
        return AnalysisResult(zusammenfassung="Kein Transkript vorhanden.", ki_modell="keine")

    # Versuch 1: Ollama
    try:
        return analysiere_mit_ollama(transkript, vorlage)
    except Exception as exc:
        logger.warning("Ollama nicht verfügbar (%s) – versuche Claude.", exc)

    # Versuch 2: Claude
    if not config.ANTHROPIC_API_KEY:
        logger.error("Weder Ollama noch ANTHROPIC_API_KEY verfügbar.")
        return AnalysisResult(
            zusammenfassung="KI-Analyse nicht verfügbar (Ollama offline, kein API-Key).",
            ki_modell="keine",
        )

    try:
        return analysiere_mit_claude(transkript, vorlage)
    except Exception as exc:
        logger.error("Claude-Analyse fehlgeschlagen: %s", exc)
        return AnalysisResult(
            zusammenfassung=f"Analyse fehlgeschlagen: {exc}",
            ki_modell="fehler",
        )
