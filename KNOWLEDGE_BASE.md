# Projekt-Knowledge-Base

> Lebende Dokumentation. Wird nach jeder Session aktualisiert.
> Zweck: Kontext erhalten für Mensch und KI, damit frühere Entscheidungen nicht neu ausgegraben werden müssen.

**Letzte Aktualisierung:** 2026-04-15

---

## 1. Überblick

Der Ordner `mein-erstes-projekt/` ist kein einzelnes Projekt, sondern inzwischen eine Sammlung mehrerer unabhängiger Sub-Projekte plus Claude-Code-Konfiguration. Das ist organisch gewachsen und wird vorerst so beibehalten.

| Sub-Projekt | Pfad | Stack | Status |
|---|---|---|---|
| Mein erstes Webprojekt | `index.html`, `style.css`, `script.js` | Vanilla HTML/CSS/JS | Fertig, statisch |
| Garderobe-Skizze | `garderobe-skizze.html` | Single-File HTML + Inline-CSS/SVG | Fertig |
| Plaud Audio Processor | `plaud_processor/` | Python, FastAPI, Whisper, Ollama/Claude | MVP fertig |
| Claude-Code-Setup | `.claude/`, `.agents/`, `.ccusage/`, `skills-lock.json` | Config & Skills | Aktiv gepflegt |

---

## 2. Kontext hinter den Entscheidungen

### 2.1 Warum Vanilla-Stack für die Webseite?
- Lernprojekt („mein erstes Projekt") — Fokus auf Grundlagen, nicht auf Tooling.
- Kein Build-Step, keine `node_modules`, öffnet direkt im Browser.
- **Regel:** Kein Framework einbauen, bis die Seite wirklich darüber hinauswächst (siehe `CLAUDE.md`).

### 2.2 Warum mehrere Sub-Projekte im selben Repo?
- Wurde bisher nicht bewusst entschieden — entstand durch sukzessive Erweiterung.
- **Offene Frage für später:** Aufteilen in eigene Repos, sobald ein Sub-Projekt ernsthafter wird? Plaud Processor ist der nächste Kandidat für Auslagerung.

### 2.3 Warum Plaud Processor in Python + FastAPI?
- Ökosystem für Audio/Whisper/KI ist in Python am ausgereiftesten.
- FastAPI statt Flask: Async, type hints, automatische OpenAPI-Docs.
- **Ollama bevorzugt vor Claude API** → Kostenlos & lokal. Claude Haiku nur als Fallback (~€0,001/Aufnahme), nicht als Default.
- **Lokales Whisper bevorzugt vor OpenAI-API** → Datenschutz + keine API-Kosten.

### 2.4 Warum `ccusage offline=true`?
- `ccusage` (Claude-Usage-Tool) hat die Session blockiert, weil LiteLLM beim Start Netzwerk-Fetches machte.
- Fix: `.ccusage/ccusage.json` mit `"offline": true` → Netzwerk-Call entfällt, Start ist nicht mehr blockiert.
- Historischer Kontext: PR #8 (`claude/fix-ccusage-blocking-pfh5t`).

### 2.5 Warum `using-superpowers` als Skill?
- Gibt Claude einen einheitlichen Weg, eigene Skills zu finden und zu nutzen, bevor geantwortet wird.
- Eingebunden über `skills-lock.json` → reproduzierbar pinned an Git-Hash.

### 2.6 Warum eigener `plugin`-Skill?
- Lokaler Skill, der Claude erlaubt, installierte Plugins aufzulisten. Hilft beim Debuggen des eigenen Setups.

---

## 3. Codebasis-Struktur

```
mein-erstes-projekt/
├── CLAUDE.md                 # Projekt-Regeln für Claude Code
├── KNOWLEDGE_BASE.md         # ← Diese Datei
│
├── index.html                # Webseite: Landing-Page (DE)
├── style.css                 # Webseite: Styles (Flexbox, Gradients, Media-Queries)
├── script.js                 # Webseite: Smooth-Scroll, CTA, Form-Handler
│
├── garderobe-skizze.html     # Eigenständige Skizze (Einzeldatei, Inline-CSS)
│
├── plaud_processor/          # Python-App: Audio → Transkript → KI-Analyse → PDF → E-Mail
│   ├── main.py               # Orchestrierung (Polling-Loop)
│   ├── web_app.py            # FastAPI-Web-Interface
│   ├── config.py             # Zentrale Config aus .env
│   ├── plaud_client.py       # Watch-Ordner / Plaud-API
│   ├── transcriber.py        # Whisper (lokal oder OpenAI-Fallback)
│   ├── analyzer.py           # Ollama bevorzugt, Claude als Fallback
│   ├── protocol_templates.py # Protokoll-Vorlagen
│   ├── pdf_generator.py      # ReportLab
│   ├── onedrive_client.py    # OneDrive-Upload
│   ├── email_notifier.py     # SMTP mit Rate-Limit
│   ├── storage.py            # SQLite (DB in /data/plaud.db)
│   ├── docker-compose.yml    # Container-Setup
│   ├── Dockerfile
│   ├── start.bat             # Windows-Starter
│   ├── requirements.txt
│   ├── .env.example          # Konfigurationsvorlage
│   ├── static/               # Web-Assets
│   └── templates/            # Jinja2-Templates
│
├── .claude/skills/           # Projekt-lokale Skills für Claude Code
├── .agents/skills/           # Agenten-Skills
├── .ccusage/ccusage.json     # ccusage offline=true (wichtig, siehe 2.4)
└── skills-lock.json          # Pinned Skill-Versionen
```

---

## 4. Relevante Code-Pointer

### Webseite
- **Smooth-Scroll & CTA:** `script.js:2-15`
- **Form-Handler (Alert-Only, noch kein Backend):** `script.js:17-22`
- **Responsive-Breakpoint (768px):** `style.css:184-193`
- **Farbschema:** `#1a1a2e` (dunkel), `#e94560` (Akzent-Pink), `#16213e` (Gradient)

### Plaud Processor
- **Hauptpipeline pro Aufnahme:** `plaud_processor/main.py:26` (`aufnahme_verarbeiten`)
- **Config-Validierung (Warnungen bei fehlenden ENV):** `plaud_processor/config.py:47-57`
- **Default-KI = Ollama llama3.1:8b:** `plaud_processor/config.py:25-26`
- **Fallback-KI = Claude Haiku:** `plaud_processor/config.py:28-30`

### Claude-Setup
- **Skill-Pinning:** `skills-lock.json` (Git-Hash für `using-superpowers`)
- **ccusage-Fix:** `.ccusage/ccusage.json`

---

## 5. Gatekeeping / Regeln

Diese Regeln gelten verbindlich — sie wurden bewusst entschieden.

- **Webseite:** Kein Framework, kein Build-Tool, kein Package-Manager. Nur Vanilla-JS/CSS/HTML.
- **Webseite CSS:** Bestehende Custom-Properties und Namenskonventionen wiederverwenden.
- **JS:** ES6+ (const/let, Arrow-Functions, Template-Literals) — kein ES5.
- **Externe Abhängigkeiten:** Nicht ohne Absprache hinzufügen.
- **Sync-Regel:** Wenn `CLAUDE.md` geändert wird, fragen, ob das auch in die globale Claude-Konfig soll.
- **Knowledge-Base-Regel:** Nach jeder Projekt-Arbeit muss diese Datei aktualisiert werden.
- **Plaud Processor:** Ollama bleibt Default — Claude API nur wenn Ollama nicht reicht.
- **Keine Tests:** Webseite wird manuell im Browser getestet (Dev-Tools für Responsive).
- **Git-Branches:** Entwicklung läuft auf `claude/<feature>`-Branches, nie direkt auf `main`.

---

## 6. Config-Dateien

| Datei | Zweck | Wichtig |
|---|---|---|
| `CLAUDE.md` | Projekt-Regeln, Tech-Stack, Sync-Regel | Wird von Claude bei jeder Session gelesen |
| `.ccusage/ccusage.json` | `offline=true` für ccusage | Verhindert Session-Blocking durch LiteLLM |
| `skills-lock.json` | Pinned Skills (`using-superpowers`, `plugin`) | Reproduzierbare Skill-Versionen |
| `.claude/skills/` | Projekt-lokale Skill-Quellen | Wird von Claude Code geladen |
| `.agents/skills/` | Agenten-spezifische Skills | — |
| `plaud_processor/.env.example` | Vorlage für ENV-Variablen | `.env` selbst ist nicht im Repo |
| `plaud_processor/docker-compose.yml` | Container-Orchestrierung | — |
| `plaud_processor/Dockerfile` | Image für den Processor | — |
| `plaud_processor/requirements.txt` | Python-Abhängigkeiten (gepinnt) | FastAPI 0.111, Whisper, Anthropic 0.29, OpenAI 1.35 |

---

## 7. Aufgetauchte Probleme & Lösungen

### Problem: Session-Start blockiert durch ccusage / LiteLLM
- **Symptom:** Claude Code startet sehr langsam oder hängt.
- **Ursache:** `ccusage` rief beim Start LiteLLM-Pricing-Daten aus dem Netz ab.
- **Lösung:** `.ccusage/ccusage.json` mit `{"defaults":{"offline":true}}` angelegt.
- **Referenz:** Commit `8d0bdfc`, PR #8.

### Problem: Fehlendes CLAUDE.md → Claude hatte keine Projekt-Regeln
- **Symptom:** Claude schlug Frameworks/Build-Tools vor, die wir nicht wollen.
- **Lösung:** `CLAUDE.md` mit Tech-Stack, Code-Rules, Run-Anweisungen angelegt.
- **Referenz:** Commit `f9fb7e6`.

### Problem: Synchronisation Projekt-CLAUDE.md ↔ globale CLAUDE.md
- **Symptom:** Änderungen in einer Datei nicht in der anderen reflektiert.
- **Lösung:** Sync-Regel in `CLAUDE.md` — Claude fragt aktiv nach.
- **Referenz:** Commit `324521d`.

### Problem: Plaud Processor — erste Implementation
- **Kontext:** Vollständige Neuimplementation mit Polling-Architektur.
- **Entscheidung:** Orchestrierung in `main.py` (Loop), FastAPI nur für Web-UI in `web_app.py`. So kann man den Processor auch headless laufen lassen.
- **Referenz:** Commit `9fad540`, PR #6.

---

## 8. Offene Punkte / TODOs

- [ ] Plaud Processor: Echte Tests fehlen, bisher nur manuell getestet.
- [ ] Webseite: Kontaktformular zeigt nur `alert()` — noch kein echter Versand.
- [ ] Entscheidung: Plaud Processor in eigenes Repo auslagern, sobald er ernsthafter genutzt wird?
- [ ] Garderobe-Skizze: Ist ein Einmal-Artefakt — ggf. in eigenen Ordner `skizzen/` verschieben.

---

## 9. Glossar

- **Plaud:** Audio-Recorder-Gerät, dessen Aufnahmen der `plaud_processor` automatisch verarbeitet.
- **Ollama:** Lokaler LLM-Runner (kostenlos, läuft auf eigener Hardware).
- **Whisper:** OpenAI-Speech-to-Text, hier lokal als Library genutzt.
- **ccusage:** Tool zum Tracking der Claude-Code-Nutzung.
