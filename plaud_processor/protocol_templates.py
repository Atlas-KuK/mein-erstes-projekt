"""Protokollvorlagen fuer die KI-Analyse -- adaptiv, mit Kurzuebersicht und Plaud-Stil."""

SYSTEM_PROMPT = """Du bist ein professioneller Protokoll- und Zusammenfassungsassistent.

Regeln:
- Schreibe IMMER auf Deutsch.
- Beginne IMMER mit einer Kurzuebersicht (2-3 Saetze).
- Verwende Markdown-Formatierung (## fuer Ueberschriften, **fett**, - fuer Listen).
- Extrahiere woertliche Zitate wenn sie praegnant sind (in Anfuehrungszeichen).
- Sei praezise, aber bewahre den Ton und die Stimmung des Gespraechs.
- Wenn Sprecher erkennbar sind, kennzeichne sie (z.B. Sprecher 1, Sprecher 2).
- Ignoriere Fuellwoerter, Wiederholungen und Versprecher im Transkript.
- Fasse NICHT zusammen was nicht gesagt wurde -- bleibe beim Inhalt.
"""

TEMPLATES = {
    "meeting": {
        "name": "Besprechung",
        "description": "Standardbesprechung: TOP, Beschluesse, Aufgaben",
        "prompt": """Analysiere das folgende Gespraechstranskript und erstelle ein strukturiertes Besprechungsprotokoll.

## Gliederung:

### Kurzuebersicht
2-3 Saetze: Wer hat worueber gesprochen? Was ist das Kernergebnis?

### Stimmung & Kontext
Eine Zeile: Wie war der Ton? (sachlich/locker/angespannt/konstruktiv/emotional)

### Schluesselbegriffe
5-10 Tags/Stichwoerter fuer schnelle Orientierung, kommagetrennt.

### Teilnehmer
Soweit erkennbar, mit Rolle oder Beziehung zueinander.

### Tagesordnungspunkte (TOP)
Nummeriert. Fuer jeden TOP:
- **Thema**: Was wurde besprochen?
- **Kernpunkte**: Die wichtigsten Aussagen (2-5 Stichpunkte)
- **Ergebnis/Beschluss**: Was wurde entschieden?

### Aufgaben & Zustaendigkeiten
Wer macht was? Als Checkliste:
- [ ] Aufgabe -- Zustaendig -- Bis wann (falls genannt)

### Wichtige Zitate
Praegnante woertliche Aussagen, die den Kern treffen.

### Offene Punkte
Was ist ungeklaert geblieben? Worauf muss man zurueckkommen?

Transkript:
{transcript}""",
    },
    "therapy": {
        "name": "Therapieprotokoll",
        "description": "Therapiegespraech: Themen, Interventionen, Hausaufgaben",
        "prompt": """Analysiere das folgende Gespraechstranskript und erstelle ein vertrauliches Therapieprotokoll.

## Gliederung:

### Kurzuebersicht
2-3 Saetze: Hauptthema der Sitzung und emotionaler Grundton.

### Stimmung & emotionaler Verlauf
Wie hat sich die Stimmung waehrend des Gespraechs entwickelt? (Anfang → Mitte → Ende)

### Schluesselbegriffe
5-10 Tags fuer schnelle Orientierung.

### Sitzungsuebersicht
- Geschaetzte Dauer
- Allgemeine Verfassung des Klienten

### Besprochene Themen
Nummeriert, mit kurzer Zusammenfassung je Thema (3-5 Saetze).

### Interventionen & Methoden
Welche therapeutischen Ansaetze wurden angewandt oder angedeutet?

### Fortschritte & Beobachtungen
Was hat sich veraendert? Welche Muster sind erkennbar?

### Vereinbarte Hausaufgaben / Uebungen
Konkrete Aufgaben bis zur naechsten Sitzung.

### Wichtige Zitate
Praegnante Aussagen des Klienten (woertlich).

### Ausblick naechste Sitzung
Geplante Schwerpunkte oder offene Themen.

WICHTIG: Alle Inhalte sind streng vertraulich. Nur lokale Verarbeitung.

Transkript:
{transcript}""",
    },
    "medical": {
        "name": "Arztgespraech",
        "description": "Arztgespraech: Befund, Diagnose, Therapieplan",
        "prompt": """Analysiere das folgende Gespraechstranskript und erstelle ein Arztgespraechsprotokoll.

## Gliederung:

### Kurzuebersicht
2-3 Saetze: Um welche Beschwerden/Diagnose geht es? Was wurde beschlossen?

### Schluesselbegriffe
5-10 medizinische und allgemeine Tags.

### Anamnese
- Aktuelle Beschwerden und Symptome
- Relevante Vorgeschichte
- Medikamente (falls erwaehnt)

### Befund / Untersuchung
Was wurde festgestellt? Ergebnisse.

### Diagnose
Festgestellte oder vermutete Diagnosen.

### Therapieplan
- Empfohlene Behandlung
- Medikamente (Name, Dosis, Dauer falls genannt)
- Verhaltensempfehlungen

### Naechste Schritte
- Kontrolltermine
- Ueberweisungen
- Weitere Untersuchungen

### Wichtige Hinweise fuer den Patienten
Was muss beachtet werden? Warnzeichen?

### Wichtige Zitate
Praegnante Aussagen des Arztes oder Patienten.

WICHTIG: Medizinische Daten streng vertraulich. Nur lokale Verarbeitung.

Transkript:
{transcript}""",
    },
    "interview": {
        "name": "Interview",
        "description": "Interview: Fragen, Antworten, Zitate",
        "prompt": """Analysiere das folgende Gespraechstranskript und erstelle ein Interviewprotokoll.

## Gliederung:

### Kurzuebersicht
2-3 Saetze: Wer wurde wozu interviewt? Kernaussage?

### Stimmung & Dynamik
Ton des Gespraechs, Interaktion zwischen Interviewer und Befragtem.

### Schluesselbegriffe
5-10 Tags.

### Teilnehmer & Kontext
Wer interviewt wen? Zu welchem Anlass?

### Kernaussagen (Top 5)
Die fuenf wichtigsten Aussagen, jeweils in 1-2 Saetzen.

### Fragen und Antworten
Strukturierte Darstellung der Hauptfragen mit zusammengefassten Antworten.

### Woertliche Zitate
Die praegnantesten Aussagen als woertliche Zitate mit Kontext.

### Zusammenfassung & Fazit
Was nimmt man aus diesem Interview mit?

### Offene Fragen
Was wurde nicht angesprochen oder blieb unklar?

Transkript:
{transcript}""",
    },
    "note": {
        "name": "Gespraechsnotiz",
        "description": "Kurze Gespraechsnotiz: Zusammenfassung",
        "prompt": """Analysiere das folgende Gespraechstranskript und erstelle eine kompakte Gespraechsnotiz.

## Gliederung:

### Kurzuebersicht
2-3 Saetze: Wer, was, worueber, Ergebnis?

### Stimmung
Eine Zeile: Ton und Atmosphaere.

### Schluesselbegriffe
5-8 Tags, kommagetrennt.

### Zusammenfassung
Die wichtigsten Punkte als Stichpunkte (max. 10).

### Entscheidungen / Ergebnisse
Was wurde konkret beschlossen oder vereinbart?

### Wichtige Zitate
1-3 praegnante woertliche Aussagen.

### Offene Punkte / Naechste Schritte
Was muss noch geklaert oder erledigt werden?

Halte alles kurz und praegnant. Maximal 1 Seite.

Transkript:
{transcript}""",
    },
    "family": {
        "name": "Familiengespraech",
        "description": "Alltagsgespraech in der Familie: Planung, Absprachen, Wuensche",
        "prompt": """Analysiere das folgende Familiengespraech und erstelle eine uebersichtliche Zusammenfassung.

## Gliederung:

### Kurzuebersicht
2-3 Saetze: Worum ging es im Kern? Wer war beteiligt?

### Stimmung & Atmosphaere
Eine Zeile: Wie war der Ton? (entspannt/lustig/angespannt/sachlich/chaotisch)

### Schluesselbegriffe
5-10 Tags fuer schnelle Orientierung.

### Beteiligte Personen
Wer kam im Gespraech vor? (Sprecher + erwaehnte Personen, z.B. Kinder)

### Themen-Uebersicht
Nummeriert, jedes Thema mit:
- **Worum ging es?** (2-3 Saetze)
- **Was kam dabei raus?** (Ergebnis/Absprache/offener Punkt)

### Konkrete Absprachen & To-Dos
Was wurde vereinbart? Als Checkliste:
- [ ] Was -- Wer -- Wann

### Vorlieben & Infos (falls relevant)
Listen, Praeferenzen, Fakten die festgehalten wurden.

### Lustige / praegenante Zitate
Woertliche Aussagen, die den Charakter des Gespraechs einfangen.

### Offene Punkte
Was blieb ungeklaert? Worauf muss man zurueckkommen?

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


def get_system_prompt() -> str:
    return SYSTEM_PROMPT


def get_template_names() -> list[dict]:
    return [
        {"key": k, "name": v["name"], "description": v["description"]}
        for k, v in TEMPLATES.items()
    ]
