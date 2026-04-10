"""PDF-Erstellung aus Protokoll-HTML via ReportLab."""
import logging
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from config import config

logger = logging.getLogger(__name__)

# Farben
BLAU = colors.HexColor("#2563eb")
GRAU = colors.HexColor("#6b7280")
HELL_GRAU = colors.HexColor("#f3f4f6")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Titel", fontSize=18, textColor=BLAU, spaceAfter=6,
                         fontName="Helvetica-Bold", alignment=TA_LEFT))
    s.add(ParagraphStyle("Meta", fontSize=9, textColor=GRAU, spaceAfter=12,
                         fontName="Helvetica"))
    s.add(ParagraphStyle("H3", fontSize=12, textColor=BLAU, spaceBefore=14, spaceAfter=4,
                         fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Text", fontSize=10, spaceAfter=6, leading=14,
                         fontName="Helvetica"))
    s.add(ParagraphStyle("Code", fontSize=8, fontName="Courier", spaceAfter=6,
                         leading=11, textColor=colors.HexColor("#374151")))
    s.add(ParagraphStyle("Hinweis", fontSize=9, textColor=colors.HexColor("#92400e"),
                         backColor=colors.HexColor("#fef3c7"), spaceBefore=4,
                         spaceAfter=8, fontName="Helvetica-Oblique"))
    return s


def _html_zu_text(html: str) -> str:
    """Einfaches HTML-Stripping für Paragraphen."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _html_zu_elemente(html_inhalt: str, styles) -> list:
    """Parst den HTML-String und erstellt ReportLab-Elemente."""
    elemente = []

    # Header
    for m in re.finditer(r'<h1>(.*?)</h1>', html_inhalt, re.DOTALL):
        elemente.append(Paragraph(_html_zu_text(m.group(1)), styles["Titel"]))

    for m in re.finditer(r'class="meta">(.*?)</p>', html_inhalt, re.DOTALL):
        elemente.append(Paragraph(_html_zu_text(m.group(1)), styles["Meta"]))
        elemente.append(HRFlowable(width="100%", thickness=1, color=BLAU, spaceAfter=8))

    # Datenschutz-Hinweis
    for m in re.finditer(r'class="hinweis datenschutz">(.*?)</div>', html_inhalt, re.DOTALL):
        elemente.append(Paragraph(_html_zu_text(m.group(1)), styles["Hinweis"]))

    # Abschnitte
    for m in re.finditer(
        r'<section class="protokoll-abschnitt"><h3>(.*?)</h3><div class="inhalt">(.*?)</div></section>',
        html_inhalt, re.DOTALL
    ):
        titel = _html_zu_text(m.group(1))
        inhalt_html = m.group(2)
        elemente.append(Paragraph(titel, styles["H3"]))

        # Liste
        li_treffer = re.findall(r"<li>(.*?)</li>", inhalt_html, re.DOTALL)
        if li_treffer:
            items = [ListItem(Paragraph(_html_zu_text(li), styles["Text"]), leftIndent=12)
                     for li in li_treffer]
            elemente.append(ListFlowable(items, bulletType="bullet", leftIndent=12))
        elif "<pre" in inhalt_html:
            # Transkript-Block
            pre_text = re.sub(r"<[^>]+>", "", inhalt_html).strip()
            # In kurze Absätze aufteilen (max 800 Zeichen)
            for i in range(0, len(pre_text), 800):
                chunk = pre_text[i:i+800].replace("\n", "<br/>")
                elemente.append(Paragraph(chunk, styles["Code"]))
        else:
            text = _html_zu_text(inhalt_html)
            if text:
                elemente.append(Paragraph(text, styles["Text"]))

        elemente.append(Spacer(1, 0.2 * cm))

    return elemente


def pdf_erstellen(html_inhalt: str, dateiname_ohne_ext: str) -> str:
    """Erstellt PDF aus HTML-Inhalt und speichert in PDF_OUTPUT_FOLDER."""
    ausgabe_ordner = Path(config.PDF_OUTPUT_FOLDER)
    ausgabe_ordner.mkdir(parents=True, exist_ok=True)

    jetzt = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_pfad = str(ausgabe_ordner / f"{dateiname_ohne_ext}_{jetzt}.pdf")

    doc = SimpleDocTemplate(
        pdf_pfad,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    styles = _styles()
    elemente = _html_zu_elemente(html_inhalt, styles)

    if not elemente:
        elemente = [Paragraph("Kein Inhalt verfügbar.", styles["Text"])]

    doc.build(elemente)
    logger.info("PDF erstellt: %s", pdf_pfad)
    return pdf_pfad
