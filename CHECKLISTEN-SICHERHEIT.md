# SICHERHEITS-CHECKLISTEN

Nutze diese 3 Checklisten bei jedem Schritt der Entwicklung.

---

## 1. PRE-COMMIT CHECKLIST

**Vor jedem `git commit`**

### Secrets Scanning
```bash
# Prüfe auf API Keys, Passwörter, Tokens
git secrets --scan

# Oder manuell: Überprüfe geänderte Dateien
git diff --cached | grep -iE "(password|api.?key|token|secret|credential|auth)"
```

**Checkliste:**
- [ ] Keine `.env.local` mit echten Werten committed
- [ ] Keine `config.js` mit API Keys
- [ ] Keine Test-Daten mit echten Passwörtern
- [ ] Keine `.pem` / `.key` Dateien
- [ ] Keine Tokens in Code-Comments
- [ ] Keine DB-Passwörter in Migrations

### Dependency Check
```bash
# Python
pip audit

# JavaScript/Node.js
npm audit
```

**Checkliste:**
- [ ] `npm audit` zeigt keine CRITICAL Vulnerabilities
- [ ] `pip audit` zeigt keine CRITICAL Vulnerabilities
- [ ] Alte Dependencies aktualisiert?

### Code Quality
```bash
# ESLint (falls JavaScript)
npm run lint

# Python (falls Python)
pylint myfile.py
```

**Checkliste:**
- [ ] Keine Linting Errors?
- [ ] Keine `console.log` mit Kundendaten?
- [ ] Keine `print()` mit Passwörtern?

### Commit Message
- [ ] Aussagekräftig (nicht "WIP" oder "aaaaaa")
- [ ] Beschreibt WAS und WARUM
- [ ] Referenziert Issue/Ticket (falls relevant)

---

## 2. CODE REVIEW CHECKLIST

**Vor jedem Merge**

### OWASP Top 10 2025

#### A01 - Broken Access Control
```
□ Server prüft Autorisierung bei jedem Request?
□ Keine direkten IDs in URLs ohne Auth-Check?
□ Nutzer sieht nur seine Daten?
□ Admin-Funktionen geschützt?
□ Keine Privilege Escalation möglich?
```

#### A02 - Cryptographic Failures
```
□ Passwörter gehasht (Argon2, nicht MD5/SHA1)?
□ Daten-in-Transit: HTTPS?
□ Sensitive Data: nicht im Frontend?
□ Session-Tokens: cryptographisch sicher?
```

#### A03 - Injection
```
□ SQL Injection: Prepared Statements oder ORM?
□ Command Injection: Keine Shell-Befehle mit User-Input?
□ LDAP Injection: Escaping?
□ NoSQL Injection: Safe Queries?
□ XSS: Output-Encoding oder DOMPurify?
```

#### A04 - Insecure Design
```
□ Threat Model dokumentiert?
□ Sichere Default-Werte?
□ Rate Limiting implementiert (Login, Formular)?
□ CSRF-Token bei POST/PUT/DELETE?
```

#### A05 - Security Misconfiguration
```
□ Debug-Mode in Production aus?
□ Keine Default-Credentials?
□ Security Headers gesetzt?
  - Content-Security-Policy
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
□ HTTPS erzwungen?
□ Unnötige Features disabled?
```

#### A06 - Vulnerable Components
```
□ Dependencies up-to-date?
□ npm audit / pip audit clean?
□ Keine veralteten Libraries?
```

#### A07 - Authentication Failures
```
□ Passwort-Validierung (Länge, Komplexität)?
□ Rate Limiting bei Login?
□ Session-Management sicher?
□ Logout löscht Session?
□ Password Reset: Token temporal + einmalig?
```

#### A08 - Software/Data Integrity Failures
```
□ Dependencies von vertrauenswürdigen Quellen?
□ Updates signiert/verifiziert?
□ CI/CD sicher konfiguriert?
```

#### A09 - Logging & Monitoring Failures
```
□ Sicherheitsrelevante Events geloggt?
  - Login-Versuche
  - Autorisierungs-Fehler
  - API-Fehler
□ Logs haben Timestamps?
□ Logs haben Log-Level (INFO, WARN, ERROR)?
□ KEINE Kundendaten in Logs?
□ KEINE Tokens/Secrets in Logs?
□ Logs werden nach 30 Tagen gelöscht?
```

#### A10 - SSRF
```
□ Externe URLs validiert?
□ Keine Requests zu internen IPs/localhost?
□ Whitelist für erlaubte Domains?
```

### DSGVO & Datenschutz

```
□ Personenbezogene Daten minimal erfasst?
  - Nur Name, Email, Nachricht (nicht Alter, Adresse, etc.)

□ Speicherfrist definiert und implementiert?
  - Maximum 90 Tage
  - Auto-Delete implementiert

□ Nutzerrechte implementiert?
  - [ ] Export-Funktion (JSON)
  - [ ] Delete-Funktion (Recht auf Vergessenwerden)
  - [ ] Datenschutzerklärung

□ Server-Seitigkeit
  - [ ] Validierung auf Server
  - [ ] Berechtigungsprüfung auf Server
  - [ ] Keine Daten-Speicherung im Frontend (localStorage)

□ Logs DSGVO-konform?
  - [ ] Keine Kundendaten (Emails, etc.)
  - [ ] Keine Tokens/Secrets
  - [ ] Aufbewahrungsfrist (30 Tage max.)

□ Drittanbieter?
  - [ ] Keinen User Tracking (Google Analytics)?
  - [ ] Keinen Cookies ohne Consent?
  - [ ] DPA mit Services?
```

### Error Handling

```
□ Keine Stack Traces dem User gezeigt?
□ Keine DB-Fehler sichtbar?
□ Keine Pfad-Informationen ausgegeben?
□ Generische Messages ("Etwas ist schief gelaufen")?
□ Details in Logs (für Debugging)?
```

### Input Validation

```
□ Alle User-Inputs validiert?
□ Längen-Limits?
□ Format-Validierung (Email, URL, etc.)?
□ Whitelist-Validierung (nur erlaubte Werte)?
□ SQL Injection Schutz?
□ XSS Schutz?
```

### Tests

```
□ Golden Path getestet?
  - [ ] Normaler Ablauf funktioniert?
  - [ ] Erfolg-Nachrichten korrekt?

□ Missbrauchsfälle getestet?
  - [ ] Ungültige Inputs werden abgewiesen?
  - [ ] SQL Injection versuche funktionieren nicht?
  - [ ] XSS Versuche funktionieren nicht?
  - [ ] CSRF ohne Token funktioniert nicht?
  - [ ] Unauthorized Access wird abgewiesen?
  - [ ] Rate Limiting funktioniert?

□ Edge Cases getestet?
  - [ ] Leere Inputs?
  - [ ] Sehr lange Inputs?
  - [ ] Special Characters?
  - [ ] Unicode?
  - [ ] Null/None/undefined?
```

### Code Quality

```
□ Verständlich und wartbar?
□ Keine Duplikationen?
□ Sinnvolle Funktions-/Variablen-Namen?
□ Kommentare bei nicht-offensichtlichem Code?
□ Keine Dead Code (unused Variablen, Funktionen)?
```

---

## 3. DEPLOY CHECKLIST

**Vor jedem Deployment in Production**

### Secrets & Credentials
```
□ Keine `.env.local` mit echten Werten in Repo?
□ Produktions-Secrets in Umgebungsvariablen / Secret Manager?
□ API Keys rotiert?
□ DB-Passwörter stark (>16 Zeichen)?
□ SSH Keys / Zertifikate sicher stored?
```

### HTTPS & Transport Security
```
□ HTTPS erzwungen (HTTP → 301 Redirect)?
□ SSL/TLS Zertifikat gültig?
□ TLS 1.2 oder höher?
□ Keine Mixed Content (HTTP + HTTPS)?
```

### Security Headers
```
□ Content-Security-Policy gesetzt?
□ X-Frame-Options: DENY oder SAMEORIGIN?
□ X-Content-Type-Options: nosniff?
□ X-XSS-Protection: 1; mode=block?
□ Strict-Transport-Security (HSTS)?
□ Referrer-Policy gesetzt?
```

### Rate Limiting
```
□ Login: max. 5 Versuche pro IP pro Stunde?
□ Formular-Submission: max. 10 pro IP pro Stunde?
□ API: Rate Limits pro Endpoint?
□ Slowdown (nicht block) bei Überschreitung?
```

### Database Security
```
□ DB läuft auf localhost / Private Network?
□ DB-Passwort stark?
□ Backups verschlüsselt?
□ Backup-Aufbewahrung dokumentiert?
□ Auto-Backup konfiguriert?
```

### Logging & Monitoring
```
□ Logs werden gesammelt (zentral)?
□ Alerts bei Sicherheits-Events?
  - [ ] Login-Fehler
  - [ ] Autorisierungs-Fehler
  - [ ] API-Fehler
□ Logs-Aufbewahrung: max. 30 Tage?
□ Logs werden nicht öffentlich einsehbar?
□ Fehler-Tracking (Sentry, etc.) konfiguriert?
```

### Data & Privacy
```
□ Auto-Deletion nach Speicherfrist aktiv?
  - [ ] Cron-Job oder Task?
  - [ ] Logs täglich?

□ Daten-Export-Funktion funktioniert?
□ Daten-Löschung-Funktion funktioniert?
□ Datenschutzerklärung veröffentlicht?
□ DSGVO-Verzeichnis der Verarbeitung aktuell?
```

### Monitoring & Incident Response
```
□ Uptime-Monitoring konfiguriert?
□ Error-Rate-Monitoring?
□ Performance-Monitoring?
□ Incident Response Plan vorhanden?
  - [ ] Wer wird bei Sicherheits-Incident benachrichtigt?
  - [ ] Wie werden Betroffene informiert (DSGVO)?
  - [ ] Wie werden Logs analysiert?
```

### Final Check
```
□ Staging → Production getestet?
□ Rollback-Plan vorhanden?
□ Deployment-Logs überprüft?
□ Keine Fehler im Error-Tracking?
□ Performance OK (Load Times, CPU, Memory)?
```

---

## Wie du die Checklisten nutzt

### Für dieses Projekt:
1. Vor jedem **Commit:** Pre-Commit Checklist
2. Vor jedem **Merge:** Code Review Checklist
3. Vor **Deployment:** Deploy Checklist

### Automation (später):
```bash
# Git Hook pre-commit
.git/hooks/pre-commit → ruft Pre-Commit Checklist auf

# CI/CD Pipeline
deploy.yml → führt Deploy Checklist aus
```

### Integration mit Claude Code:
Immer wenn Claude Code fertig ist, sagt er:
"✅ Code Review Checklist: [Status]"
"⚠️ Offene Risiken: [Liste]"

---

**Stand:** 2026-04-20  
**Verwendung:** Verbindlich für alle Commits und Deployments
