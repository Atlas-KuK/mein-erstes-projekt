"""
Protokoll-Vorlagen: Definition und Claude-Prompts für verschiedene Protokolltypen.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, WORK_DIR

log = logging.getLogger(__name__)


@dataclass
class Template:
    key: str
    label: str
    icon: str
    description: str
    prompt: str
    sections: List[str]


TEMPLATES: dict[str, Template] = {
    "besprechung": Template(
        key="besprechung",
        label="Besprechungsprotokoll",
        icon="📋",
        description="Formelles Protokoll für Meetings und Besprechungen",
        sections=["Teilnehmer", "Tagesordnung", "Ergebnisse", "Beschlüsse", "Aufgaben", "Nächster Termin"],
        prompt="""Erstelle ein formelles Besprechungsprotokoll aus diesem Transkript.
Antworte mit einem HTML-Dokument (nur der <body>-Inhalt, kein <html>/<head>).
Verwende diese Struktur:

<h2>Besprechungsdetails</h2>
<table> Datum, Ort/Format, Dauer, Protokollführer </table>

<h2>Teilnehmer</h2>
<ul> alle erkennbaren Teilnehmer </ul>

<h2>Tagesordnung</h2>
<ol> erkennbare Tagesordnungspunkte </ol>

<h2>Ergebnisse und Diskussion</h2>
<p> je TOP: Zusammenfassung </p>

<h2>Beschlüsse</h2>
<ul class="decisions"> konkrete Beschlüsse </ul>

<h2>Aufgaben</h2>
<table> Was | Wer | Bis wann </table>

<h2>Nächster Termin</h2>
<p> falls erwähnt </p>

Halte es sachlich und präzise. Falls etwas im Transkript nicht erwähnt wurde, lasse den Abschnitt leer aber behalte die Überschrift."""
    ),

    "therapie": Template(
        key="therapie",
        label="Therapieprotokoll",
        icon="🧠",
        description="Strukturierte Dokumentation für Therapiesitzungen",
        sections=["Sitzungsdetails", "Hauptthemen", "Beobachtungen", "Interventionen", "Hausaufgaben", "Planung"],
        prompt="""Erstelle ein professionelles Therapiesitzungsprotokoll aus diesem Transkript.
Antworte mit einem HTML-Dokument (nur der <body>-Inhalt).
Behandle alle Informationen vertraulich und professionell.

<h2>Sitzungsdetails</h2>
<table> Datum, Sitzungsnummer (falls erkennbar), Dauer, Therapeut, Patient </table>

<h2>Hauptthemen der Sitzung</h2>
<ul> Welche Themen wurden besprochen? </ul>

<h2>Beobachtungen</h2>
<p> Emotionaler Zustand, Stimmung, auffällige Verhaltensweisen </p>

<h2>Interventionen und Techniken</h2>
<ul> Welche therapeutischen Ansätze wurden eingesetzt? </ul>

<h2>Fortschritt</h2>
<p> Fortschritt bezüglich der Therapieziele </p>

<h2>Hausaufgaben / Übungen</h2>
<ul> Vereinbarte Aufgaben bis zur nächsten Sitzung </ul>

<h2>Planung nächste Sitzung</h2>
<p> Themen, Termine, Besonderheiten </p>

Formuliere einfühlsam und professionell."""
    ),

    "arzt": Template(
        key="arzt",
        label="Arztgespräch",
        icon="🏥",
        description="Dokumentation eines medizinischen Gesprächs",
        sections=["Gesprächsdetails", "Anamnese", "Befunde", "Diagnose", "Behandlung", "Nächste Schritte"],
        prompt="""Erstelle eine strukturierte Dokumentation eines Arztgesprächs aus diesem Transkript.
Antworte mit einem HTML-Dokument (nur der <body>-Inhalt).

<h2>Gesprächsdetails</h2>
<table> Datum, Arzt/Fachrichtung, Patient </table>

<h2>Anlass / Symptome</h2>
<ul> Beschwerden und Anlass des Gesprächs </ul>

<h2>Anamnese</h2>
<p> Relevante Vorgeschichte, Medikamente, Allergien </p>

<h2>Befunde / Untersuchung</h2>
<p> Ergebnisse von Untersuchungen </p>

<h2>Diagnose</h2>
<p> Diagnose oder Verdachtsdiagnose </p>

<h2>Behandlungsplan</h2>
<ul> Empfohlene Maßnahmen, Medikamente, Therapien </ul>

<h2>Nächste Schritte</h2>
<ul> Folgeuntersuchungen, Termine, Überweisungen </ul>

<h2>Offene Fragen</h2>
<ul> Vom Patienten gestellte Fragen und Antworten </ul>"""
    ),

    "interview": Template(
        key="interview",
        label="Interviewprotokoll",
        icon="🎤",
        description="Strukturierte Aufbereitung eines Interviews",
        sections=["Details", "Hauptaussagen", "Zitate", "Zusammenfassung"],
        prompt="""Erstelle ein Interviewprotokoll aus diesem Transkript.
Antworte mit einem HTML-Dokument (nur der <body>-Inhalt).

<h2>Interviewdetails</h2>
<table> Datum, Interviewer, Interviewpartner, Thema/Anlass </table>

<h2>Thematischer Überblick</h2>
<p> Kurze Einführung in das Thema des Interviews </p>

<h2>Fragen und Antworten</h2>
(Für jede wichtige Frage:)
<div class="qa-block">
  <p class="question"><strong>F:</strong> Frage...</p>
  <p class="answer"><strong>A:</strong> Zusammenfassung der Antwort</p>
</div>

<h2>Markante Zitate</h2>
<blockquote> Direkte Zitate mit Quellenangabe </blockquote>

<h2>Zusammenfassung</h2>
<p> Die wichtigsten Erkenntnisse des Interviews </p>"""
    ),

    "notiz": Template(
        key="notiz",
        label="Gesprächsnotiz",
        icon="📝",
        description="Kompakte informelle Gesprächsnotiz",
        sections=["Kurzinfo", "Kernpunkte", "Aufgaben"],
        prompt="""Erstelle eine kompakte Gesprächsnotiz aus diesem Transkript.
Antworte mit einem HTML-Dokument (nur der <body>-Inhalt).
Halte es kurz und auf das Wesentliche reduziert.

<h2>Kurzinfo</h2>
<table> Datum, Gesprächspartner, Thema </table>

<h2>Kernpunkte</h2>
<ul> Die 3–7 wichtigsten Punkte aus dem Gespräch </ul>

<h2>Aufgaben</h2>
<ul> Falls Aufgaben oder Vereinbarungen erwähnt wurden </ul>

<h2>Notizen</h2>
<p> Sonstige relevante Informationen </p>"""
    ),

    "transkript": Template(
        key="transkript",
        label="Reines Transkript",
        icon="📄",
        description="Vollständiges Transkript mit Sprechern, ohne Zusammenfassung",
        sections=["Transkript"],
        prompt=""  # Kein Claude-Aufruf nötig – wird direkt aus Segmenten gebaut
    ),
}


def get_template(key: str) -> Optional[Template]:
    return TEMPLATES.get(key)


def list_templates() -> List[dict]:
    return [
        {"key": t.key, "label": t.label, "icon": t.icon, "description": t.description}
        for t in TEMPLATES.values()
    ]


# ---------------------------------------------------------------------------
# Protokoll generieren
# ---------------------------------------------------------------------------

def generate_protocol_html(template_key: str, transcript_text: str,
                            segments: list, recording_title: str = "") -> str:
    """
    Generiert den HTML-Inhalt eines Protokolls.
    Für 'transkript': direkte Aufbereitung ohne Claude.
    Für alle anderen: Claude-basierte Generierung.
    """
    template = get_template(template_key)
    if not template:
        raise ValueError(f"Unbekannte Vorlage: {template_key}")

    if template_key == "transkript":
        return _build_transcript_html(segments, transcript_text)

    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY fehlt – Protokoll kann nicht generiert werden")
        return f"<p>Fehler: ANTHROPIC_API_KEY nicht konfiguriert.</p>"

    try:
        import anthropic
    except ImportError:
        return "<p>Fehler: anthropic-Paket nicht installiert.</p>"

    # Transkript mit Sprechern aufbereiten
    if segments:
        formatted = _format_segments_for_prompt(segments)
    else:
        formatted = transcript_text

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    log.info("Generiere %s für '%s'…", template.label, recording_title)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=f"Du bist ein professioneller Assistent für Protokollerstellung. "
               f"Erstelle strukturierte, gut lesbare Protokolle auf Deutsch.",
        messages=[{
            "role": "user",
            "content": f"Titel der Aufnahme: {recording_title}\n\n"
                       f"Transkript:\n{formatted}\n\n---\n\n{template.prompt}"
        }],
    )

    html = message.content[0].text.strip()
    # Markdown-Code-Blöcke entfernen falls vorhanden
    html = re.sub(r"^```[a-z]*\n?", "", html)
    html = re.sub(r"\n?```$", "", html)
    return html


def _format_segments_for_prompt(segments: list) -> str:
    """Formatiert Segmente als lesbaren Text mit Sprechern."""
    lines = []
    current_speaker = None
    for seg in segments:
        speaker = seg.get("speaker", "Unbekannt")
        text = seg.get("text", "").strip()
        if not text:
            continue
        if speaker != current_speaker:
            lines.append(f"\n**{speaker}:** {text}")
            current_speaker = speaker
        else:
            lines.append(text)
    return "\n".join(lines)


def _build_transcript_html(segments: list, fallback_text: str) -> str:
    """Baut ein reines Transkript-HTML aus Segmenten."""
    if not segments:
        return f"<div class='transcript-raw'>{fallback_text}</div>"

    html_parts = []
    current_speaker = None
    current_texts = []

    def flush():
        if current_texts and current_speaker:
            color = _speaker_color(current_speaker)
            html_parts.append(
                f'<div class="transcript-block">'
                f'<span class="speaker-badge" style="background:{color}">{current_speaker}</span>'
                f'<p>{" ".join(current_texts)}</p>'
                f'</div>'
            )

    for seg in segments:
        speaker = seg.get("speaker", "Unbekannt")
        text = seg.get("text", "").strip()
        if not text:
            continue
        if speaker != current_speaker:
            flush()
            current_speaker = speaker
            current_texts = [text]
        else:
            current_texts.append(text)

    flush()
    return "\n".join(html_parts)


def _speaker_color(name: str) -> str:
    colors = ["#2e86c1", "#27ae60", "#8e44ad", "#e67e22", "#c0392b", "#16a085"]
    return colors[hash(name) % len(colors)]


# ---------------------------------------------------------------------------
# PDF aus Protokoll-HTML
# ---------------------------------------------------------------------------

def protocol_to_pdf(html_content: str, title: str,
                    template_label: str, recording_id: int) -> Path:
    """Konvertiert HTML-Protokoll in eine PDF-Datei."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT
    except ImportError:
        raise ImportError("reportlab nicht installiert")

    from html.parser import HTMLParser

    pdf_dir = WORK_DIR / "pdfs"
    pdf_dir.mkdir(exist_ok=True)

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:60]
    pdf_path = pdf_dir / f"{ts}_{safe}_{template_label}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
    )

    DARK = colors.HexColor("#1a3a5c")
    ACCENT = colors.HexColor("#2e86c1")
    LIGHT = colors.HexColor("#eaf4fb")

    base = getSampleStyleSheet()
    styles = {
        "h1": ParagraphStyle("H1", parent=base["Heading1"], textColor=DARK, fontSize=18, spaceAfter=6),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], textColor=ACCENT, fontSize=13, spaceBefore=12, spaceAfter=4),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], textColor=DARK, fontSize=11, spaceBefore=8, spaceAfter=3),
        "p":  ParagraphStyle("P",  parent=base["Normal"], fontSize=10, leading=15),
        "li": ParagraphStyle("LI", parent=base["Normal"], fontSize=10, leading=15, leftIndent=14),
        "blockquote": ParagraphStyle("BQ", parent=base["Normal"], fontSize=10, leading=15,
                                     leftIndent=20, textColor=colors.HexColor("#555555"),
                                     borderPad=5),
    }

    def esc(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Einfacher HTML→Platypus Parser
    story = []
    story.append(Paragraph(esc(title), styles["h1"]))
    story.append(Paragraph(f"{template_label} · {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["p"]))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=12))

    # HTML parsen (vereinfacht)
    _parse_html_to_story(html_content, story, styles, LIGHT)

    def footer(canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(doc.leftMargin, 1.2*cm, "Erstellt mit Plaud Processor")
        canvas.drawRightString(w - doc.rightMargin, 1.2*cm, f"Seite {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return pdf_path


def _parse_html_to_story(html: str, story: list, styles: dict, light_color) -> None:
    """Wandelt einfaches HTML in ReportLab-Flowables um."""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    import re

    def esc(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Tags entfernen und Abschnitte extrahieren
    # h2
    for match in re.finditer(r"<h2>(.*?)</h2>", html, re.DOTALL | re.IGNORECASE):
        idx = html.find(match.group(0))
        # Text vor h2
        before = html[:idx]
        _add_text_block(before, story, styles, esc)
        story.append(Paragraph(esc(re.sub(r"<[^>]+>", "", match.group(1))), styles["h2"]))
        html = html[idx + len(match.group(0)):]

    _add_text_block(html, story, styles, esc)


def _add_text_block(html: str, story: list, styles: dict, esc) -> None:
    import re
    from reportlab.platypus import Paragraph, Spacer

    if not html.strip():
        return

    # <p> Tags
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", html, re.DOTALL | re.IGNORECASE):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if text:
            story.append(Paragraph(esc(text), styles["p"]))
            story.append(Spacer(1, 4))

    # <li> Tags
    for m in re.finditer(r"<li[^>]*>(.*?)</li>", html, re.DOTALL | re.IGNORECASE):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if text:
            story.append(Paragraph(f"• {esc(text)}", styles["li"]))

    # <blockquote>
    for m in re.finditer(r"<blockquote[^>]*>(.*?)</blockquote>", html, re.DOTALL | re.IGNORECASE):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if text:
            story.append(Paragraph(f'„{esc(text)}"', styles["blockquote"]))
            story.append(Spacer(1, 4))

    # Reiner Text (kein Tag) – als Paragraph
    clean = re.sub(r"<[^>]+>", " ", html).strip()
    # Nur wenn nach Tag-Entfernung noch sinnvoller Inhalt
    if clean and not re.search(r"<[pli]", html, re.IGNORECASE):
        for para in clean.split("\n\n"):
            para = para.strip()
            if len(para) > 10:
                story.append(Paragraph(esc(para), styles["p"]))
