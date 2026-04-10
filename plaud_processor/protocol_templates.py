"""6 Protokollvorlagen – erzeugen HTML-Ausgabe aus AnalysisResult + Transkript."""
from dataclasses import dataclass
from typing import Callable

from analyzer import AnalysisResult


@dataclass
class Vorlage:
    schluessel: str
    name: str
    beschreibung: str
    html_ersteller: Callable[[AnalysisResult, str, str], str]


def _abschnitt(titel: str, inhalt: str) -> str:
    if not inhalt:
        return ""
    return f'<section class="protokoll-abschnitt"><h3>{titel}</h3><div class="inhalt">{inhalt}</div></section>'


def _liste(items: list[str]) -> str:
    if not items:
        return "<p><em>Keine Einträge.</em></p>"
    lis = "".join(f"<li>{item}</li>" for item in items)
    return f"<ul>{lis}</ul>"


def _basis_header(titel: str, datum: str, modell: str) -> str:
    return (
        f'<header class="protokoll-header">'
        f'<h1>{titel}</h1>'
        f'<p class="meta">Erstellt: {datum} &nbsp;|&nbsp; KI-Modell: {modell}</p>'
        f'</header>'
    )


# --- Vorlagen-Implementierungen ---

def _besprechung_html(result: AnalysisResult, transkript: str, datum: str) -> str:
    return f"""
{_basis_header('Besprechungsprotokoll', datum, result.ki_modell)}
{_abschnitt('Zusammenfassung', f'<p>{result.zusammenfassung}</p>')}
{_abschnitt('Tagesordnungspunkte / Kernpunkte', _liste(result.kernpunkte))}
{_abschnitt('Beschlüsse', _liste(result.beschluesse))}
{_abschnitt('Aufgaben / To-Dos', _liste(result.aufgaben))}
{_abschnitt('Stimmung', f'<p>{result.stimmung}</p>')}
{_abschnitt('Vollständiges Transkript', f'<pre class="transkript">{transkript}</pre>')}
"""


def _therapie_html(result: AnalysisResult, transkript: str, datum: str) -> str:
    return f"""
{_basis_header('Therapieprotokoll', datum, result.ki_modell)}
<div class="hinweis datenschutz">Vertraulich – nur zur internen Verwendung.</div>
{_abschnitt('Sitzungszusammenfassung', f'<p>{result.zusammenfassung}</p>')}
{_abschnitt('Besprochene Themen', _liste(result.kernpunkte))}
{_abschnitt('Interventionen / Maßnahmen', _liste(result.beschluesse))}
{_abschnitt('Hausaufgaben / Aufgaben', _liste(result.aufgaben))}
{_abschnitt('Transkript', f'<pre class="transkript">{transkript}</pre>')}
"""


def _arzt_html(result: AnalysisResult, transkript: str, datum: str) -> str:
    return f"""
{_basis_header('Arztgespräch – Dokumentation', datum, result.ki_modell)}
<div class="hinweis datenschutz">Vertrauliche Patientendokumentation.</div>
{_abschnitt('Gesprächszusammenfassung', f'<p>{result.zusammenfassung}</p>')}
{_abschnitt('Befunde / Symptome', _liste(result.kernpunkte))}
{_abschnitt('Diagnose / Einschätzung', _liste(result.beschluesse))}
{_abschnitt('Therapieplan / Nächste Schritte', _liste(result.aufgaben))}
{_abschnitt('Transkript', f'<pre class="transkript">{transkript}</pre>')}
"""


def _interview_html(result: AnalysisResult, transkript: str, datum: str) -> str:
    return f"""
{_basis_header('Interview-Protokoll', datum, result.ki_modell)}
{_abschnitt('Überblick', f'<p>{result.zusammenfassung}</p>')}
{_abschnitt('Kernaussagen', _liste(result.kernpunkte))}
{_abschnitt('Wichtige Zitate / Erkenntnisse', _liste(result.beschluesse))}
{_abschnitt('Offene Punkte / Follow-up', _liste(result.aufgaben))}
{_abschnitt('Vollständiges Transkript', f'<pre class="transkript">{transkript}</pre>')}
"""


def _notiz_html(result: AnalysisResult, transkript: str, datum: str) -> str:
    return f"""
{_basis_header('Gesprächsnotiz', datum, result.ki_modell)}
{_abschnitt('Zusammenfassung', f'<p>{result.zusammenfassung}</p>')}
{_abschnitt('Kernpunkte', _liste(result.kernpunkte))}
{_abschnitt('Aufgaben', _liste(result.aufgaben))}
"""


def _transkript_html(result: AnalysisResult, transkript: str, datum: str) -> str:
    return f"""
{_basis_header('Reines Transkript', datum, result.ki_modell)}
{_abschnitt('Transkript', f'<pre class="transkript">{transkript}</pre>')}
"""


# --- Vorlagen-Registry ---

VORLAGEN: dict[str, Vorlage] = {
    "meeting": Vorlage(
        schluessel="meeting",
        name="Besprechung",
        beschreibung="Standardbesprechungsprotokoll mit TOP, Beschlüssen und Aufgaben",
        html_ersteller=_besprechung_html,
    ),
    "therapy": Vorlage(
        schluessel="therapy",
        name="Therapie",
        beschreibung="Therapieprotokoll: Themen, Interventionen, Hausaufgaben",
        html_ersteller=_therapie_html,
    ),
    "medical": Vorlage(
        schluessel="medical",
        name="Arztgespräch",
        beschreibung="Arztgespräch: Befund, Diagnose, Therapieplan",
        html_ersteller=_arzt_html,
    ),
    "interview": Vorlage(
        schluessel="interview",
        name="Interview",
        beschreibung="Interview: Fragen, Antworten, Zitate",
        html_ersteller=_interview_html,
    ),
    "note": Vorlage(
        schluessel="note",
        name="Gesprächsnotiz",
        beschreibung="Kurze Gesprächsnotiz mit Zusammenfassung",
        html_ersteller=_notiz_html,
    ),
    "transcript": Vorlage(
        schluessel="transcript",
        name="Reines Transkript",
        beschreibung="Nur das Transkript, keine KI-Analyse",
        html_ersteller=_transkript_html,
    ),
}


def protokoll_html_erstellen(
    vorlage_key: str,
    result: AnalysisResult,
    transkript: str,
    datum: str,
) -> str:
    vorlage = VORLAGEN.get(vorlage_key, VORLAGEN["meeting"])
    return vorlage.html_ersteller(result, transkript, datum)
