"""
PDF-Berichtsgenerator.

Erstellt einen professionell gestalteten PDF-Bericht aus einem AnalysisResult.
Benötigt: reportlab  (pip install reportlab)
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from analyzer import AnalysisResult
from config import WORK_DIR

log = logging.getLogger(__name__)


def generate_pdf(result: AnalysisResult, recording_title: str,
                 created_at: str = "") -> Path:
    """
    Erzeugt eine PDF-Datei und gibt ihren Pfad zurück.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle,
            HRFlowable, KeepTogether,
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        raise ImportError(
            "reportlab nicht installiert. Bitte: pip install reportlab"
        )

    pdf_dir = WORK_DIR / "pdfs"
    pdf_dir.mkdir(exist_ok=True)

    safe_name = _safe_filename(result.title or recording_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = pdf_dir / f"{timestamp}_{safe_name}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    # --- Stile ---
    base_styles = getSampleStyleSheet()

    DARK_BLUE = colors.HexColor("#1a3a5c")
    ACCENT    = colors.HexColor("#2e86c1")
    LIGHT_BG  = colors.HexColor("#eaf4fb")
    GREY_TEXT = colors.HexColor("#555555")

    styles = {
        "title": ParagraphStyle(
            "ReportTitle", parent=base_styles["Title"],
            textColor=DARK_BLUE, fontSize=22, spaceAfter=6, leading=28,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base_styles["Normal"],
            textColor=GREY_TEXT, fontSize=10, spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "Section", parent=base_styles["Heading2"],
            textColor=ACCENT, fontSize=13, spaceBefore=14, spaceAfter=4,
            borderPad=0,
        ),
        "body": ParagraphStyle(
            "Body", parent=base_styles["Normal"],
            fontSize=10, leading=15, textColor=colors.HexColor("#333333"),
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base_styles["Normal"],
            fontSize=10, leading=15, leftIndent=14,
            textColor=colors.HexColor("#333333"),
        ),
        "transcript": ParagraphStyle(
            "Transcript", parent=base_styles["Normal"],
            fontSize=9, leading=13, textColor=GREY_TEXT,
            leftIndent=0, fontName="Courier",
        ),
    }

    # --- Inhalt aufbauen ---
    story = []

    # Titel-Block
    title_text = result.title or recording_title
    story.append(Paragraph(_esc(title_text), styles["title"]))

    meta_parts = []
    if created_at:
        meta_parts.append(f"Aufnahme: {created_at}")
    meta_parts.append(f"Bericht erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if result.duration_hint:
        meta_parts.append(f"Geschätzte Dauer: {result.duration_hint} Min.")
    if result.language:
        meta_parts.append(f"Sprache: {result.language}")
    if result.sentiment:
        meta_parts.append(f"Stimmung: {result.sentiment}")

    story.append(Paragraph("  |  ".join(meta_parts), styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=10))

    # Tags
    if result.tags:
        tag_str = "  ".join(f"[{t}]" for t in result.tags)
        story.append(Paragraph(tag_str, styles["subtitle"]))
        story.append(Spacer(1, 8))

    # Zusammenfassung
    if result.summary:
        story.append(Paragraph("Zusammenfassung", styles["section"]))
        _add_summary_box(story, result.summary, styles, LIGHT_BG)

    # Schlüsselpunkte
    if result.key_points:
        story.append(Paragraph("Kernaussagen", styles["section"]))
        for point in result.key_points:
            story.append(Paragraph(f"• {_esc(point)}", styles["bullet"]))
        story.append(Spacer(1, 6))

    # Action Items
    if result.action_items:
        story.append(Paragraph("Aufgaben / Action Items", styles["section"]))
        for item in result.action_items:
            story.append(Paragraph(f"☐ {_esc(item)}", styles["bullet"]))
        story.append(Spacer(1, 6))

    # Entscheidungen
    if result.decisions:
        story.append(Paragraph("Getroffene Entscheidungen", styles["section"]))
        for dec in result.decisions:
            story.append(Paragraph(f"✓ {_esc(dec)}", styles["bullet"]))
        story.append(Spacer(1, 6))

    # Vollständiges Transkript
    if result.raw_transcript:
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#cccccc"), spaceBefore=10))
        story.append(Paragraph("Vollständiges Transkript", styles["section"]))
        # Langer Text: in Absätze aufteilen
        for para in result.raw_transcript.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(_esc(para), styles["transcript"]))
                story.append(Spacer(1, 4))

    doc.build(story, onFirstPage=_add_page_decoration,
              onLaterPages=_add_page_decoration)

    log.info("PDF erstellt: %s", pdf_path)
    return pdf_path


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """Escapiert HTML-Sonderzeichen für ReportLab-Paragraphen."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def _safe_filename(name: str) -> str:
    """Wandelt einen Titel in einen sicheren Dateinamen um."""
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    return safe.strip().replace(" ", "_")[:80]


def _add_summary_box(story, summary: str, styles, bg_color):
    """Fügt die Zusammenfassung in einer farbigen Box ein."""
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors

    data = [[Paragraph(_esc(summary), styles["body"])]]
    tbl = Table(data, colWidths=["100%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))


def _add_page_decoration(canvas, doc):
    """Fügt Kopf- und Fußzeile auf jeder Seite hinzu."""
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    canvas.saveState()
    w, h = doc.pagesize

    # Fußzeile
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(doc.leftMargin, 1.2 * cm,
                      "Erstellt mit Plaud Processor · Powered by Claude AI")
    canvas.drawRightString(w - doc.rightMargin, 1.2 * cm,
                           f"Seite {doc.page}")

    # Kopfzeile – dünne Linie
    canvas.setStrokeColor(colors.HexColor("#2e86c1"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, h - 1.8 * cm, w - doc.rightMargin, h - 1.8 * cm)

    canvas.restoreState()
