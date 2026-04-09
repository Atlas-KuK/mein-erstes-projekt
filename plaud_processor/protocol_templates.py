"""6 Protokollvorlagen fuer die KI-Analyse."""

TEMPLATES = {
    "meeting": {
        "name": "Besprechung",
        "description": "Standardbesprechung: TOP, Beschluesse, Aufgaben",
        "prompt": """Erstelle ein strukturiertes Besprechungsprotokoll aus folgendem Transkript.

Gliederung:
1. **Teilnehmer** (soweit erkennbar)
2. **Tagesordnungspunkte (TOP)** – nummeriert
3. **Diskussion** – Zusammenfassung je TOP
4. **Beschluesse** – klar formuliert
5. **Aufgaben** – Wer macht was bis wann?
6. **Naechste Schritte**

Schreibe auf Deutsch. Sei praezise und sachlich.

Transkript:
{transcript}""",
    },
    "therapy": {
        "name": "Therapieprotokoll",
        "description": "Therapiegespraech: Themen, Interventionen, Hausaufgaben",
        "prompt": """Erstelle ein Therapieprotokoll aus folgendem Gespraechstranskript.

Gliederung:
1. **Sitzungsuebersicht** – Datum, Dauer, Stimmung des Klienten
2. **Besprochene Themen** – Hauptthemen der Sitzung
3. **Interventionen** – Angewandte therapeutische Methoden
4. **Fortschritte** – Beobachtete Veraenderungen
5. **Hausaufgaben** – Vereinbarte Uebungen bis zur naechsten Sitzung
6. **Naechste Sitzung** – Geplante Schwerpunkte

WICHTIG: Behandle alle Inhalte vertraulich. Schreibe auf Deutsch.

Transkript:
{transcript}""",
    },
    "medical": {
        "name": "Arztgespraech",
        "description": "Arztgespraech: Befund, Diagnose, Therapieplan",
        "prompt": """Erstelle ein Arztgespraechsprotokoll aus folgendem Transkript.

Gliederung:
1. **Anamnese** – Beschwerden, Symptome, Vorgeschichte
2. **Befund** – Untersuchungsergebnisse
3. **Diagnose** – Festgestellte Diagnosen
4. **Therapieplan** – Empfohlene Behandlung, Medikamente
5. **Weitere Schritte** – Ueberweisungen, Kontrolltermine
6. **Hinweise fuer den Patienten** – Wichtige Anweisungen

WICHTIG: Medizinische Daten vertraulich behandeln. Schreibe auf Deutsch.

Transkript:
{transcript}""",
    },
    "interview": {
        "name": "Interview",
        "description": "Interview: Fragen, Antworten, Zitate",
        "prompt": """Erstelle ein Interviewprotokoll aus folgendem Transkript.

Gliederung:
1. **Interviewuebersicht** – Teilnehmer, Thema, Dauer
2. **Kernaussagen** – Die wichtigsten Aussagen zusammengefasst
3. **Fragen und Antworten** – Strukturierte Darstellung
4. **Woertliche Zitate** – Besonders praegnante Aussagen
5. **Zusammenfassung** – Fazit und Haupterkenntnisse

Schreibe auf Deutsch. Kennzeichne woertliche Zitate mit Anfuehrungszeichen.

Transkript:
{transcript}""",
    },
    "note": {
        "name": "Gespraechsnotiz",
        "description": "Kurze Gespraechsnotiz: Zusammenfassung",
        "prompt": """Erstelle eine kurze Gespraechsnotiz aus folgendem Transkript.

Gliederung:
1. **Zusammenfassung** – 3-5 Saetze, worum ging es?
2. **Wichtige Punkte** – Stichpunkte
3. **Offene Fragen** – Falls vorhanden
4. **Naechste Schritte** – Falls vereinbart

Schreibe auf Deutsch. Halte es kurz und praegnant.

Transkript:
{transcript}""",
    },
    "transcript": {
        "name": "Reines Transkript",
        "description": "Nur Transkription, keine KI-Analyse",
        "prompt": None,  # Keine KI-Analyse
    },
}


def get_template(name: str) -> dict:
    return TEMPLATES.get(name, TEMPLATES["meeting"])


def get_template_names() -> list[dict]:
    return [
        {"key": k, "name": v["name"], "description": v["description"]}
        for k, v in TEMPLATES.items()
    ]
