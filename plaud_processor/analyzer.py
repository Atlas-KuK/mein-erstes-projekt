"""KI-Analyse: Ollama lokal (kostenlos) mit Claude Haiku als Fallback."""

import json
import logging
from dataclasses import dataclass, field

import httpx

import config
from protocol_templates import get_template

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Ergebnis der KI-Analyse."""
    content_html: str = ""
    content_text: str = ""
    engine: str = ""
    template: str = ""
    success: bool = False
    error: str = ""


def analyze(transcript: str, template_name: str = "meeting") -> AnalysisResult:
    """Transkript analysieren und Protokoll erstellen.

    Prioritaet: 1. Ollama (kostenlos) → 2. Claude Haiku (Fallback)
    """
    template = get_template(template_name)

    # Keine Analyse bei reinem Transkript
    if template["prompt"] is None:
        return AnalysisResult(
            content_html=f"<pre>{transcript}</pre>",
            content_text=transcript,
            engine="none",
            template=template_name,
            success=True,
        )

    prompt = template["prompt"].format(transcript=transcript)

    # 1. Versuch: Ollama (lokal, kostenlos)
    try:
        result = _analyze_ollama(prompt, template_name)
        if result.success:
            logger.info("Analyse erfolgreich (Ollama): Vorlage=%s", template_name)
            return result
    except Exception as e:
        logger.warning("Ollama-Analyse fehlgeschlagen: %s", e)

    # 2. Fallback: Claude Haiku
    if config.ANTHROPIC_API_KEY:
        try:
            result = _analyze_claude(prompt, template_name)
            if result.success:
                logger.info("Analyse erfolgreich (Claude): Vorlage=%s", template_name)
                return result
        except Exception as e:
            logger.error("Claude-Analyse fehlgeschlagen: %s", e)

    return AnalysisResult(
        error="Analyse fehlgeschlagen: Weder Ollama noch Claude verfuegbar.",
        template=template_name,
    )


def _analyze_ollama(prompt: str, template_name: str) -> AnalysisResult:
    """Analyse via Ollama (lokal, kostenlos)."""
    url = f"{config.OLLAMA_URL}/api/generate"

    system_prompt = (
        "Du bist ein professioneller Protokollassistent. "
        "Erstelle strukturierte, gut formatierte Protokolle auf Deutsch. "
        "Verwende Markdown-Formatierung."
    )

    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 4096,
        },
    }

    response = httpx.post(url, json=payload, timeout=300)
    response.raise_for_status()
    data = response.json()

    text = data.get("response", "").strip()
    if not text:
        raise ValueError("Leere Antwort von Ollama")

    html = _markdown_to_html(text)

    return AnalysisResult(
        content_html=html,
        content_text=text,
        engine="ollama",
        template=template_name,
        success=True,
    )


def _analyze_claude(prompt: str, template_name: str) -> AnalysisResult:
    """Analyse via Claude Haiku (Fallback)."""
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=(
            "Du bist ein professioneller Protokollassistent. "
            "Erstelle strukturierte, gut formatierte Protokolle auf Deutsch. "
            "Verwende Markdown-Formatierung."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    html = _markdown_to_html(text)

    return AnalysisResult(
        content_html=html,
        content_text=text,
        engine="claude",
        template=template_name,
        success=True,
    )


def check_ollama_available() -> bool:
    """Pruefen ob Ollama erreichbar ist."""
    try:
        response = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def _markdown_to_html(text: str) -> str:
    """Einfache Markdown-zu-HTML-Konvertierung."""
    import re

    lines = text.split("\n")
    html_lines = []

    in_list = False
    for line in lines:
        stripped = line.strip()

        # Ueberschriften
        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        # Listen
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = stripped[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            html_lines.append(f"<li>{content}</li>")
        # Nummerierte Listen
        elif re.match(r"^\d+\.\s", stripped):
            if not in_list:
                html_lines.append("<ol>")
                in_list = True
            content = re.sub(r"^\d+\.\s", "", stripped)
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            html_lines.append(f"<li>{content}</li>")
        # Leerzeilen
        elif not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br>")
        # Normaler Text
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            html_lines.append(f"<p>{content}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)
