# TEMPLATE FÜR ALLE PROJEKTE

**Kopiere dieses Template für jedes neue Projekt.**

Einmalig erstellen, 50x verwenden. 15 Minuten Anpassung pro Projekt.

---

## Was gehört in jedes neue Projekt?

```
mein-neues-projekt/
├── CLAUDE.md                    # ← Kopiere aus diesem Projekt
├── SECURITY-SYSTEM-PROMPT.md    # ← Kopiere aus diesem Projekt
├── CHECKLISTEN-SICHERHEIT.md    # ← Kopiere aus diesem Projekt
├── .gitignore                   # ← Standard Template
├── .git/hooks/pre-commit        # ← Git Hook (optionale Automation)
├── README.md                    # ← Projekt-spezifisch
└── [dein Code]
```

---

## Schritt 1: CLAUDE.md vorbereiten (5 min)

**Kopiere `CLAUDE.md` aus diesem Projekt und passe an:**

### Was bleibt gleich:
- Sicherheit & Datenschutz: Verbindliche Regeln
- Anforderungs-Workflow: Phase 1-3
- Development & Testing: Allgemein

### Was musst du anpassen:
```markdown
## Projekt-Kontext

**Typ:** [Dein Projekt-Typ: API, Web App, CLI, etc.]
**Fokus:** [Kurz: Was macht das Projekt?]
**Verarbeitete Daten:** [Welche Personendaten? Oder "keine"]

---

## Projekt-Struktur

[Deine tatsächliche Struktur]
```

**Beispiel für Backend-API:**
```markdown
## Projekt-Kontext

**Typ:** Python FastAPI Backend  
**Fokus:** User Management + Dokumentation API  
**Verarbeitete Daten:** User ID, Email, Hashed Password, API Keys

---

## Projekt-Struktur

```
api/
├── main.py                  # FastAPI App
├── models.py                # Pydantic Models
├── routes/
│   ├── auth.py             # Login, Register
│   ├── users.py            # User Management
│   └── docs.py             # Document API
├── db/
│   ├── database.py          # DB Connection
│   └── models.py            # SQLAlchemy Models
├── config.py               # Settings
├── requirements.txt        # Dependencies
└── tests/
    ├── test_auth.py
    ├── test_users.py
    └── test_security.py
```
```

---

## Schritt 2: System-Prompt verwenden (0 min)

**`SECURITY-SYSTEM-PROMPT.md` kopieren - KEINE Änderungen nötig!**

Dieser Text gilt für ALLE Projekte.

**Nutze ihn so:**

Jedes Mal wenn du Claude Code eine Feature-Anfrage stellst:

```
[Kopiere den kompletten System-Prompt]

Jetzt meine Feature-Anfrage:
Feature: User Registration

Kontext:
- Neue User können sich mit Email + Passwort registrieren
- Passwörter werden gehasht gespeichert
- Email muss validiert werden (Confirmation Link)

Anforderungen:
1. Funktional: Registration Form, Validation, Email-Confirm
2. Sicherheit: Passwort-Hashing, Rate Limiting, CSRF
3. DSGVO: Datensparsamkeit (nur Email + Passwort), 90-Tage-Auto-Delete
```

---

## Schritt 3: Checklisten verwenden (0 min)

**`CHECKLISTEN-SICHERHEIT.md` kopieren - KEINE Änderungen nötig!**

Diese Checklisten gelten für ALLE Projekte.

**Nutze sie so:**

1. **Vor Commit:** Pre-Commit Checklist durchgehen
2. **Vor Merge:** Code Review Checklist durchgehen
3. **Vor Deploy:** Deploy Checklist durchgehen

---

## Schritt 4: Git Hook einrichten (10 min, optional)

**Automatisiere Pre-Commit Checks mit einem Git Hook.**

Erstelle `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Pre-Commit Security Hook
# Blockiert Commits mit Secrets/APIs/Passwörtern

set -e

echo "🔍 Running pre-commit security checks..."

# 1. Secrets Scan
echo "  → Checking for secrets..."
if git diff --cached | grep -iE "(password|api.?key|token|secret|credential|aws_|private_key)" > /dev/null; then
    echo "  ❌ FAIL: Secrets found in staged changes!"
    echo "     (Don't commit passwords, API keys, or tokens)"
    exit 1
fi
echo "  ✅ No secrets found"

# 2. Check for large files
echo "  → Checking file sizes..."
if git diff --cached --name-only --diff-filter=A -z | xargs -0 du -h | grep -E "[0-9]M" > /dev/null; then
    echo "  ⚠️  WARNING: Large files detected (>1MB)"
    echo "     Consider using git-lfs for binary files"
fi

# 3. Check for debug statements (optional)
echo "  → Checking for debug statements..."
if git diff --cached | grep -E "^\\+.*console\\.log|^\\+.*debugger|^\\+.*pdb\\.set_trace" > /dev/null; then
    echo "  ⚠️  WARNING: Debug statements found"
    echo "     (Remove console.log, debugger, pdb.set_trace before commit)"
fi

echo "✅ Pre-commit checks passed!"
exit 0
```

**Installiere den Hook:**
```bash
chmod +x .git/hooks/pre-commit
```

**Teste ihn:**
```bash
# Versuche ein Passwort zu committen (sollte blockiert werden)
echo "password: secret123" > test.txt
git add test.txt
git commit -m "test"  # ← sollte fehlschlagen
git reset HEAD test.txt
rm test.txt
```

---

## Schritt 5: README.md schreiben (10 min)

**Projekt-spezifisches README (nicht copy-paste).**

**Template:**

```markdown
# [Projekt-Name]

[Kurze Beschreibung: Was macht das Projekt?]

## Features

- Feature 1
- Feature 2
- Feature 3

## Tech Stack

- Language: [Python, JavaScript, etc.]
- Framework: [FastAPI, Express, etc.]
- DB: [PostgreSQL, MongoDB, etc.]
- Deploy: [Docker, Vercel, etc.]

## Setup

```bash
# Installation
pip install -r requirements.txt

# Run Lokal
python main.py

# Tests
pytest
```

## Security & Privacy

- Siehe `CLAUDE.md` für Security Policy
- Siehe `CHECKLISTEN-SICHERHEIT.md` für Review-Standards
- DSGVO-konform (Datenminimierung, Auto-Delete, Export)

## License

[Your License]
```

---

## Schritt 6: .gitignore (2 min)

**Standard `.gitignore` für dein Projekt-Type.**

**Python:**
```
__pycache__/
*.py[cod]
*$py.class
*.so
.env
.env.local
venv/
.vscode/
.idea/
*.egg-info/
dist/
build/
```

**JavaScript/Node.js:**
```
node_modules/
.env
.env.local
dist/
build/
.vscode/
.idea/
*.log
.DS_Store
```

**Allgemein:**
```
.DS_Store
*.swp
*.swo
*~
.vscode/
.idea/
```

---

## Schritt 7: Erstes Feature mit Claude Code (15 min prep)

**Wenn alles vorbereitet ist:**

1. Kopiere `SECURITY-SYSTEM-PROMPT.md` in die Anfrage
2. Schreibe deine Feature-Anfrage
3. Stelle sicher, dass Claude Code:
   - Phase 1 (Verstehen) macht
   - Bedrohungsanalyse liefert
   - Architektur-Vorschlag macht
   - DSGVO-Einschätzung gibt
4. Erst dann akzeptierst du Code

**Beispiel-Anfrage:**

```
[Kopiere den kompletten SECURITY-SYSTEM-PROMPT.md]

---

## Feature: User Authentication

Kontext:
- Users sollen sich mit Email + Passwort anmelden
- Passwörter werden gehashed mit Argon2 gespeichert
- Session-Token wird nach erfolgreichem Login zurückgegeben

Anforderungen:
1. Funktional: Login-Formular, Validierung, Token-Generierung
2. Sicherheit: Passwort-Hashing, Rate Limiting (5 Versuche/Stunde/IP), CSRF-Token
3. DSGVO: Email + Passwort speichern, 90 Tage Auto-Delete, Export-Funktion
4. Logging: Login-Versuche loggen (ohne Passwort), Errors ohne Stack Trace

Bevor du Implementierst:
1. Bedrohungsanalyse (Wer greift an, wie?)
2. DSGVO-Risiken (Datenspeicherung, Nutzerrechte)
3. Architektur-Diagramm (Wer spricht mit wem?)
4. Dann erst Code

Rote Linien:
- Passwörter NICHT im Klartext speichern
- KEINE Passwörter in Logs
- Keine direkten User-IDs in URLs ohne Auth-Check
```

---

## Checkliste: Template-Vorbereitung

```
Für jedes neue Projekt:

□ CLAUDE.md angepasst (Typ, Fokus, Daten)
□ SECURITY-SYSTEM-PROMPT.md kopiert (keine Änderung)
□ CHECKLISTEN-SICHERHEIT.md kopiert (keine Änderung)
□ .gitignore erstellt
□ README.md geschrieben
□ Git Hook installiert (optional aber empfohlen)
□ Erstes Feature mit System-Prompt geplant

= Total: ~45 Minuten Setup, dann produktionsreif
```

---

## Langzeit-Wiederverwertung

Nach 3-5 Projekten mit diesem Template wirst du merken:

✅ **Was ist gleich:**
- Security System Prompt (100%)
- Checklisten (100%)
- CLAUDE.md Struktur (80%)
- .gitignore (80%)

⚠️ **Was ändert sich:**
- Projekt-Kontext (Typ, Tech Stack)
- Konkrete Anforderungen (Features)
- Daten-Klassifikation (Welche Personendaten?)

**Optimierung nach 5 Projekten:**
Erstelle ein **Master-Repository** mit:
```
master-template/
├── CLAUDE-TEMPLATE.md
├── SECURITY-SYSTEM-PROMPT.md (fix)
├── CHECKLISTEN-SICHERHEIT.md (fix)
├── .gitignore-PYTHON
├── .gitignore-NODEJS
├── .git-hooks/
└── README-TEMPLATE.md
```

Dann für jedes Projekt:
```bash
git clone master-template.git mein-neues-projekt
# 5 Minuten anpassen
# Fertig
```

---

**Stand:** 2026-04-20  
**Für:** Alle Projekte (Web, API, CLI, etc.)  
**Wartung:** Jährlich überprüfen (neue OWASP Top 10, neue DSGVO Urteile)
