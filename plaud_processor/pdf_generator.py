"""PDF-Erstellung mit ReportLab."""

import logging
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

import config

logger = logging.getLogger(__name__)


def _get_styles():
    """Benutzerdefinierte Stile fuer das PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitelStil",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    ))

    styles.add(ParagraphStyle(
        name="Untertitel",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#666666"),
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="Ueberschrift2",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#16213e"),
    ))

    styles.add(ParagraphStyle(
        name="Ueberschrift3",
        parent=styles["Heading3"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#0f3460"),
    ))

    styles.add(ParagraphStyle(
        name="Inhalt",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="ListenPunkt",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=4,
        bulletIndent=10,
    ))

    styles.add(ParagraphStyle(
        name="Fusszeile",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    ))

    return styles


def generate_pdf(
    filename: str,
    title: str,
    content_text: str,
    template_name: str = "meeting",
    output_dir: str | None = None,
) -> str:
    """PDF aus Analysetext erstellen.

    Returns: Pfad zur erstellten PDF-Datei.
    """
    if output_dir is None:
        output_dir = config.PDF_OUTPUT_FOLDER

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Dateiname bereinigen
    safe_name = re.sub(r"[^\w\s\-.]", "", filename)
    safe_name = safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"{safe_name}_{timestamp}.pdf"
    pdf_path = str(Path(output_dir) / pdf_filename)

    styles = _get_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    # Titel
    story.append(Paragraph(title, styles["TitelStil"]))

    # Metadaten
    meta = (
        f"Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
        f"Vorlage: {template_name} | "
        f"Quelle: {filename}"
    )
    story.append(Paragraph(meta, styles["Untertitel"]))
    story.append(Spacer(1, 10))

    # Trennlinie
    line_data = [["" * 80]]
    line_table = Table(line_data, colWidths=[16 * cm])
    line_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#e0e0e0")),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 15))

    # Inhalt parsen und formatieren
    _parse_content(content_text, story, styles)

    # PDF erstellen
    doc.build(story)
    logger.info("PDF erstellt: %s", pdf_path)
    return pdf_path


def _parse_content(text: str, story: list, styles):
    """Markdown-aehnlichen Text in ReportLab-Elemente umwandeln."""
    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 6))
            continue

        # Ueberschriften
        if stripped.startswith("### "):
            content = _clean_markdown(stripped[4:])
            story.append(Paragraph(content, styles["Ueberschrift3"]))
        elif stripped.startswith("## "):
            content = _clean_markdown(stripped[3:])
            story.append(Paragraph(content, styles["Ueberschrift2"]))
        elif stripped.startswith("# "):
            content = _clean_markdown(stripped[2:])
            story.append(Paragraph(content, styles["Ueberschrift2"]))
        # Aufzaehlungen
        elif stripped.startswith("- ") or stripped.startswith("* "):
            content = _clean_markdown(stripped[2:])
            story.append(Paragraph(f"\u2022 {content}", styles["ListenPunkt"]))
        # Nummerierte Listen
        elif re.match(r"^\d+\.\s", stripped):
            content = _clean_markdown(re.sub(r"^\d+\.\s", "", stripped))
            num = re.match(r"^(\d+)\.", stripped).group(1)
            story.append(Paragraph(f"{num}. {content}", styles["ListenPunkt"]))
        # Normaler Text
        else:
            content = _clean_markdown(stripped)
            story.append(Paragraph(content, styles["Inhalt"]))


def _clean_markdown(text: str) -> str:
    """Markdown-Formatierung fuer ReportLab aufbereiten."""
    # Fett → ReportLab Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Kursiv → ReportLab Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Sonderzeichen escapen
    text = text.replace("&", "&amp;")
    # Aber nicht die ReportLab-Tags zerstoeren
    text = text.replace("&amp;amp;", "&amp;")
    text = text.replace("<b>", "<<<B>>>").replace("</b>", "<<<EB>>>")
    text = text.replace("<i>", "<<<I>>>").replace("</i>", "<<<EI>>>")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("<<<B>>>", "<b>").replace("<<<EB>>>", "</b>")
    text = text.replace("<<<I>>>", "<i>").replace("<<<EI>>>", "</i>")
    return text
