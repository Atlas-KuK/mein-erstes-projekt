# QUICK START: Sichere Entwicklung

**Schritt-für-Schritt Anleitung zum Start mit Claude Code.**

---

## TL;DR - Für Ungeduldigere

```bash
# 1. Setup (einmalig)
chmod +x .git-hooks-pre-commit.sh
cp .git-hooks-pre-commit.sh .git/hooks/pre-commit

# 2. Vor JEDEM Feature
# Kopiere SECURITY-SYSTEM-PROMPT.md in deine Feature-Anfrage

# 3. Vor JEDEM Commit
# Nutze Pre-Commit Checklist aus CHECKLISTEN-SICHERHEIT.md

# 4. Vor JEDEM Merge
# Nutze Code Review Checklist aus CHECKLISTEN-SICHERHEIT.md

# 5. Vor JEDEM Deployment
# Nutze Deploy Checklist aus CHECKLISTEN-SICHERHEIT.md
```

---

## SCHRITT 1: Git Hook installieren (2 min)

```bash
# Mache das Script ausführbar
chmod +x .git-hooks-pre-commit.sh

# Installiere es als Git Hook
cp .git-hooks-pre-commit.sh .git/hooks/pre-commit

# Test: Versuche mit Passwort zu committen (sollte blockiert werden)
echo "password: secret123" > test.txt
git add test.txt
git commit -m "test"  # ← Sollte FEHLSCHLAGEN

# Cleanup
git reset HEAD test.txt
rm test.txt
```

**Was der Hook macht:**
- ✅ Blockiert Commits mit API Keys, Passwörtern, Tokens
- ✅ Warnt vor großen Dateien (>100MB)
- ✅ Warnt vor Debug-Statements (console.log, debugger, etc.)
- ✅ Erinnert an Security TODOs

---

## SCHRITT 2: Feature mit System-Prompt starten

**Jedes Mal wenn du Claude Code eine neue Feature gibst:**

### A) System-Prompt kopieren

Kopiere den **kompletten Text** aus `SECURITY-SYSTEM-PROMPT.md`

### B) Deine Feature-Anfrage schreiben

```
[HIER SECURITY-SYSTEM-PROMPT.md einfügen]

---

## Feature: [Titel]

Kontext:
- Was soll gebaut werden?
- Welche Daten sind betroffen?
- Wer hat Zugriff?

Anforderungen:
1. Funktional: [Was muss es tun?]
2. Sicherheit: [Welche Angriffe müssen abgewehrt werden?]
3. DSGVO: [Wie werden Daten geschützt?]
4. Performance: [Gibt es Limits?]

Rote Linien:
- [Was darf NICHT passieren?]
```

### C) Erwarte diese Struktur von Claude Code

Claude Code sollte liefern:

```
1. ✓ Zielverständnis (Was genau soll es tun?)
2. ✓ Bedrohungsanalyse (Wer greift an, wie?)
3. ✓ DSGVO-Einschätzung (Personenbezogene Daten?)
4. ✓ Architektur-Vorschlag (Wer spricht mit wem?)
5. ✓ Rollen & Berechtigungen (Wer darf was?)
6. ✓ Validierungsregeln (Input, Output, Auth)
7. ✓ Logging-Konzept (Was wird geloggt, wie lange?)
8. ✓ Code + Tests
9. ✓ Sicherheits-Review (Checklist)
10. ✓ Offene Risiken (Was noch nicht gelöst?)
```

**Wenn Claude Code blind Code schreibt:** STOPPEN und System-Prompt nochmal geben.

---

## SCHRITT 3: Vor jedem Commit - Pre-Commit Checklist

**Öffne `CHECKLISTEN-SICHERHEIT.md` → Sektion "1. PRE-COMMIT CHECKLIST"**

```bash
# Secrets Scanning
git secrets --scan
git diff --cached | grep -iE "(password|api.?key|token|secret)"

# Dependency Check
npm audit          # Wenn JavaScript
pip audit          # Wenn Python

# Linting
npm run lint       # Wenn JavaScript
pylint myfile.py   # Wenn Python
```

**Checkliste durcharbeiten:**
- [ ] Keine Secrets?
- [ ] Keine .env mit echten Werten?
- [ ] Dependencies sauber?
- [ ] Linting ok?
- [ ] Commit Message aussagekräftig?

**Dann commiten:**
```bash
git add [files]
git commit -m "fix: [Was wurde fixed?] [Warum?]"
```

---

## SCHRITT 4: Vor jedem Merge - Code Review Checklist

**Öffne `CHECKLISTEN-SICHERHEIT.md` → Sektion "2. CODE REVIEW CHECKLIST"**

**Durcharbeite:**
1. OWASP Top 10 2025 (A01-A10)
2. DSGVO & Datenschutz
3. Error Handling
4. Input Validation
5. Tests
6. Code Quality

**Wenn alle Checks grün:** Merge ok

**Wenn etwas rot:** Zurück an Claude Code mit:
```
Code Review Checklist Status:
□ FAIL: [Was ist nicht ok?]

Bitte fixen:
1. [konkrete Anforderung]
2. [konkrete Anforderung]
```

---

## SCHRITT 5: Vor jedem Deployment - Deploy Checklist

**Öffne `CHECKLISTEN-SICHERHEIT.md` → Sektion "3. DEPLOY CHECKLIST"**

**Vor Live-Gang überprüfen:**

```bash
# Secrets in Production?
grep -r "password\|api.key\|token" config/production/ || echo "✓ No secrets"

# Backups konfiguriert?
# HTTPS erzwungen?
# Security Headers gesetzt?
# Logging aktiv?
# Monitoring aktiv?
```

**Checklist durcharbeiten:**
- [ ] Secrets secure?
- [ ] HTTPS?
- [ ] Security Headers?
- [ ] Rate Limiting?
- [ ] Database sauber?
- [ ] Logging & Monitoring?
- [ ] Data & Privacy?
- [ ] Rollback Plan?

---

## BEISPIEL: Feature mit diesem Workflow

### Feature: "Kontaktformular mit Email-Versand"

**1. System-Prompt + Feature-Anfrage:**

```
[Kopiere SECURITY-SYSTEM-PROMPT.md]

---

Feature: Kontaktformular mit Email-Versand

Kontext:
- Nutzer füllen Formular mit Name + Email + Nachricht
- Email wird an admin@example.com versendet
- Nutzer erhält Bestätigungs-Email

Anforderungen:
1. Funktional: Formular, Validierung, Email-Versand
2. Sicherheit: Input-Validierung, CSRF-Token, Rate Limiting (5/Stunde)
3. DSGVO: Email-Adressen 90 Tage speichern, dann auto-delete
4. Performance: Email async, nicht blocking

Rote Linien:
- Keine Kundendaten im Log
- Keine Email-Adressen im Error-Message
- Keine SMTP-Passwörter im Code
```

**2. Claude Code liefert:**

✓ Bedrohungsanalyse
✓ Architektur (Frontend → Backend → SMTP)
✓ DSGVO-Plan (Auto-Delete nach 90 Tagen)
✓ Rollen (Owner sieht nur seine Email)
✓ Code + Tests
✓ Sicherheits-Review

**3. Vor Commit:**

```bash
# Pre-Commit Checklist
□ SMTP-Password nicht in Code?
□ CSRF-Token implementiert?
□ Dependencies ok?
```

**4. Vor Merge:**

```bash
# Code Review Checklist
□ Input-Validierung auf Server?
□ Rate Limiting implementiert?
□ DSGVO: Auto-Delete cron job?
□ Tests: Spam-Versuche getestet?
□ Logs: Keine Emails sichtbar?
```

**5. Vor Deployment:**

```bash
# Deploy Checklist
□ SMTP-Passwort in Production-Env gesetzt?
□ Email-Auto-Delete cron job läuft?
□ Monitoring für Fehler aktiv?
```

---

## Best Practices

### DOs ✅

- ✅ **Immer System-Prompt voranstellen** (copy-paste)
- ✅ **Kleine Features** (nicht 1000 Zeilen auf einmal)
- ✅ **Checklisten durcharbeiten** (nicht überspringen)
- ✅ **Fragen stellen** bei Unsicherheit (Claude Code wird es sagen)
- ✅ **Tests schreiben** (Golden Path + Missbrauch)
- ✅ **Logs überprüfen** (keine Kundendaten!)

### DON'Ts ❌

- ❌ Große Features ohne Risikoanalyse
- ❌ "Nur schnell" Code ohne Review
- ❌ Passwords im Code lassen
- ❌ Secrets in Logs
- ❌ Checklisten skippen
- ❌ Deployment ohne Deploy-Checklist

---

## Troubleshooting

### Git Hook blockiert meinen Commit

**Problem:** Hook sagt "Secrets found" aber ich habe keine

**Lösung:**
```bash
# Check was genau blockiert wird
git diff --cached | grep -iE "(password|api|token|secret)"

# Oft sind es False Positives in Comments
# Beispiel: "// TODO: add password validation"

# Behebe es:
git diff --cached  # Überprüfe den Diff
git reset HEAD file.js
# Ändere die Datei
git add file.js
git commit -m "..."
```

### Claude Code liefert keine Bedrohungsanalyse

**Problem:** Claude Code macht einfach Code statt Analyse

**Lösung:**
```
Du hast den System-Prompt nicht gelesen!

Laut SECURITY-SYSTEM-PROMPT.md musst du IMMER so arbeiten:
1. Risikoanalyse
2. Bedrohungsmodell
3. Architektur
4. Erst dann Code

Gib mir bitte:
- [ ] Bedrohungsanalyse (3-5 Angriffsvektoren)
- [ ] DSGVO-Einschätzung
- [ ] Architektur-Diagramm
- [ ] Dann Code
```

### Checklisten sind zu viel

**Problem:** "Das ist ja eine riesige Liste!"

**Lösung:** Das ist normal. Aber:
- Erste 3 Projekte: Volle Checkliste durcharbeiten (Lernen)
- Ab Projekt 4: Routine, dauert nur noch 10 Minuten
- Ab Projekt 10: Ganz normal geworden

**Shortcut (nur für triviale Features):**
```
Feature: Fix Typo in Footer

Keine Personendaten betroffen.
Checklist: Nur Pre-Commit (Secrets, Linting)
```

---

## Zusammenfassung

| Schritt | Was | Wann | Dauer |
|---------|-----|------|-------|
| 1 | Setup Git Hook | Einmalig | 2 min |
| 2 | System-Prompt voranstellen | Jede Feature | 2 min |
| 3 | Pre-Commit Checklist | Vor commit | 5 min |
| 4 | Code Review Checklist | Vor Merge | 10 min |
| 5 | Deploy Checklist | Vor Production | 10 min |
| | **TOTAL pro Feature** | | **30 min** |

**Nach 3 Projekten:** Wird zur Routine, halbiert sich.

**Sicherheitslevel:** 95%+ (OWASP + DSGVO)

---

**Stand:** 2026-04-20  
**Für Anfänger, die sauberen Code bauen wollen**
