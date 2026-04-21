# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Projekt-Kontext

**Typ:** Statische Website mit HTML/CSS/JavaScript  
**Fokus:** Persönliches Lernprojekt (aktuell ohne Backend)  
**Verarbeitete Daten:** Kontaktformular erfasst Name, E-Mail, Nachricht

---

## Sicherheit & Datenschutz: Verbindliche Regeln

Dieses Projekt muss sich an folgende Standards halten, unabhängig vom Umfang:

### 1. NIEMALS - Absolute Verbote

- ❌ **Passwörter im Klartext** speichern oder übertragen
- ❌ **API Keys, Tokens, Secrets** in Code, Tests, Logs oder `.git` schreiben
- ❌ **Personendaten im Frontend verarbeiten** und speichern ohne Backend-Validierung
- ❌ **Logs mit Kundendaten** (E-Mails, Nummern, IP-Adressen, Auth-Token)
- ❌ **Fehlermeldungen mit technischen Details** an Benutzer (Stack Traces, SQL, Pfade)
- ❌ **Produktivdaten in Dev/Test** oder Debug-Kontexten

### 2. Kontaktformular - Sicherheit & DSGVO

**Aktueller Stand:** Nur Frontend mit Alert  
**Problem:** Keine Datenspeicherung, aber Formular-Felder erfassen personenbezogene Daten

**Anforderungen bei Backend-Erweiterung:**

- Serverseitige Input-Validierung (nicht nur HTML `required`)
- HTTPS obligatorisch (keine HTTP)
- Passwort-Hashing mit Argon2 (falls Auth nötig)
- Datenminimierung: Nur Name + E-Mail + Nachricht speichern
- Speicherfrist: max. 90 Tage, dann automatisch löschen
- Keine Weitergabe an Drittanbieter ohne explizite Zustimmung
- Error Handling: Nie Stacktraces oder DB-Fehler an Frontend
- Rate Limiting auf Formular-Submissions (z.B. 5 pro IP pro Stunde)
- CSRF Protection bei POST-Requests
- Content Security Policy Header

### 3. API-Sicherheit (falls Backend kommt)

- Validiere **alle Eingaben** auf dem Server
- Prüfe **Berechtigungen** auf dem Server (nicht nur Frontend)
- Keine direkten IDs in URLs ohne Autorisierungsprüfung
- Sicherer Session-Token (HttpOnly, Secure, SameSite)
- SQL Injection: Prepared Statements oder ORM
- XSS Prevention: Output-Encoding, CSP Header

### 4. Logging & Monitoring

- Logs niemals mit Kundendaten schreiben
- Sicherheitsrelevante Events protokollieren (Login-Versuche, Formular-Fehler)
- Logs mit Timestamps, Log-Level, Kontext
- Keine Passwörter, Tokens, Secrets in Logs
- Logs maximal 30 Tage aufbewahren, dann löschen

---

## Datenschutz: DSGVO-Compliance

Dieses Projekt verarbeitet personenbezogene Daten (über Kontaktformular). Folgende Regeln:

### Privacy by Design & Default
- Nur notwendige Daten erfassen (Name, E-Mail, Nachricht - nicht mehr)
- Kurze Speicherfrist (90 Tage max.)
- Zugriff begrenzen auf notwendige Personen
- Keine Automatisierte Entscheidungsfindung

### Nutzerrechte
- Export-Funktion für Nutzerdaten (falls Backend: JSON-Export)
- Lösch-Funktion für Nutzerdaten (Recht auf Vergessenwerden)
- Transparenz: Datenschutzerklärung erforderlich (falls personenbezogene Daten verarbeitet)

### Drittanbieter
- Derzeit keine 3rd-party Services (Google Analytics, Hotjar, etc.) verwenden
- Falls nötig: DPA (Data Processing Agreement) vor Integration
- Keine Datenübertragung in Drittländer

---

## Anforderungs-Workflow: So arbeitest du mit Claude Code

### Phase 1: Vor der Implementierung
Vor jeder Feature-Anfrage oder jedem Bug-Fix:

1. **Definiere die Anforderung klar** - Was genau soll passieren?
2. **Risikoanalyse** - Welche Sicherheitsrisiken entstehen?
3. **DSGVO-Check** - Werden personenbezogene Daten verarbeitet?
4. **Bedrohungsmodell** - Wer könnte das ausnutzen und wie?
5. **Architekturvorschlag** - Wie wird es technisch gelöst?

Nutze diesen Prompt-Template:

```
Feature: [Titel]

Kontext:
- Was soll gemacht werden?
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

### Phase 2: Implementierung mit Sicherheits-Checkpoints
Claude Code soll liefern:

1. ✅ Bedrohungsanalyse (3-5 realistische Angriffsvektoren)
2. ✅ Architektur-Diagramm (Text reicht)
3. ✅ Code mit Kommentaren bei sicherheitskritischen Stellen
4. ✅ Validierungs-Regeln (Input, Output, Auth)
5. ✅ Test-Cases (inkl. Missbrauch-Szenarien)
6. ✅ Sicherheits-Checklist (OWASP Top 10 2025)

### Phase 3: Review & Abnahme
Vor jedem Merge:

```
Sicherheits-Review Checklist:

□ Keine Secrets im Code / Logs / Git
□ Validierung auf dem Server (nicht nur Frontend)
□ Authentifizierung / Autorisierung korrekt
□ SQL Injection / XSS / CSRF geschützt
□ Fehler zeigen keine technischen Details
□ Passwörter: Argon2, nicht Plaintext
□ DSGVO: Datensparsamkeit, Löschbarkeit, Export
□ Logs: Keine Personendaten, keine Secrets
□ Dependencies: Keine bekannten Vulnerabilities
□ Rate Limiting bei sensiblen Operationen
```

---

## Projekt-Struktur

```
mein-erstes-projekt/
├── index.html              # Haupt-Website (Startseite)
├── personalplanung.html    # Unterseite (falls vorhanden)
├── script.js              # Client-side Logik (Navigation, Formular)
├── style.css              # Styling (responsive Design)
├── README.md              # Projekt-Beschreibung
└── CLAUDE.md              # Diese Datei
```

### Wichtige Dateien im Detail

**index.html**
- Definiert Struktur (Header, Hero, About, Contact, Footer)
- Kontaktformular mit Name, E-Mail, Nachricht
- Verlinkt auf style.css und script.js

**script.js**
- Smooth Scrolling für Navigation
- CTA Button (Call-to-Action) scrollt zu About
- Kontaktformular: Nur Frontend-Verarbeitung (Alert + Reset)
- **⚠️ Problem:** Keine Backend-Validierung, keine Datenverarbeitung

**style.css**
- Modernes Gradient-Design (Dark Blue / Red Accents)
- Responsive Grid für Cards
- Mobile-optimiert (Media Query für <768px)

---

## Development & Testing

### Lokales Testen
```bash
# HTML im Browser öffnen (keine Server nötig für statische Files)
open index.html   # macOS
xdg-open index.html  # Linux

# Oder mit lokalem Server (Python 3)
python3 -m http.server 8000
# Dann: http://localhost:8000
```

### Browser Console Check
Öffne DevTools (F12) und überprüfe:
- Keine Fehler in der Console
- Keine Secrets/Passwörter im Local Storage
- Netzwerk: Alle Requests sind HTTPS (später, wenn Backend)
- Performance: Painting/Rendering < 60ms

### Accessibility Testing
- Keyboard Navigation (Tab, Enter, Escape)
- Screen Reader kompatibel (für A11y)
- Contrast Ratio mind. 4.5:1 (WCAG AA)

---

## Backend-Erweiterung: Wenn es kommt

Falls du ein Backend hinzufügst (Python, Node.js, etc.):

### Sicherheit
1. **Auth:** Passwort mit Argon2 + HTTPS + Sessions
2. **Validierung:** Alle Inputs auf Server prüfen
3. **Rollen:** Admin vs. Nutzer (falls relevant)
4. **Logs:** Sicherheitsrelevante Events, aber ohne Kundendaten

### DSGVO
1. **Datensparsamkeit:** Nur Name + E-Mail + Nachricht
2. **Speicherfrist:** Auto-Löschung nach 90 Tagen
3. **Export:** Nutzerdaten als JSON downloadbar
4. **Löschung:** Delete-Endpoint für DSGVO Recht

### API-Endpoints (Beispiel)
```
POST   /api/contact          # Submit Nachricht (validiert, speichert)
GET    /api/contact/:id      # Get Nachricht (nur Owner/Admin)
DELETE /api/contact/:id      # Delete Nachricht (Owner/Admin)
GET    /api/export-my-data   # DSGVO Export (authenticated)
```

---

## CI/CD & Sicherheit

### Pre-Commit Checks (wenn Backend kommt)
```bash
# Secrets Scanning
git secrets --scan

# Dependency Check
pip audit  # Python
npm audit  # Node.js

# Linting
pylint myfile.py
eslint script.js
```

### Deploy Checklist
- [ ] Keine `.env.example` mit echten Secrets
- [ ] HTTPS erzwungen
- [ ] Security Headers gesetzt (CSP, X-Frame-Options, etc.)
- [ ] Rate Limiting konfiguriert
- [ ] Logs gecheckt (keine Kundendaten)

---

## Häufige Fehler: NICHT machen

1. ❌ **Kontaktformular-Daten im Frontend speichern** (localStorage)
2. ❌ **API Keys im Code** oder in `.env.example`
3. ❌ **Error Messages mit Stack Traces** dem Nutzer zeigen
4. ❌ **Passwörter hashing mit MD5 oder SHA1**
5. ❌ **Daten ohne Konsentmanagement** verarbeiten
6. ❌ **Admin-Funktionen nur im Frontend schützen**
7. ❌ **Logs mit personenbezogenen Daten** speichern

---

## Ressourcen & Standards

- **OWASP Top 10 2025** - Webrisiken: https://owasp.org/Top10/
- **NIST Cybersecurity Framework** - Best Practices
- **BSI (DE)** - Passwort-Sicherheit: Argon2 statt MD5/SHA1
- **DSGVO Artikel 32, 25** - Datenschutz durch Technik
- **MDN Web Docs** - HTML/CSS/JS Standards

---

## Fragen vor Implementation

Bevor Claude Code an einer Feature arbeitet, stelle sicher:

1. **Daten:** Welche personenbezogenen Daten sind betroffen?
2. **Speicherung:** Werden Daten gespeichert? Wie lange?
3. **Zugriff:** Wer darf darauf zugreifen?
4. **Löschung:** Wie werden Daten gelöscht?
5. **Validierung:** Wo geschieht Validierung (Frontend, Server)?
6. **Fehlerbehandlung:** Was wird bei Fehlern ausgegeben?
7. **Logging:** Was wird protokolliert und wie lange aufbewahrt?

Nur wenn diese Fragen geklärt sind, beginnt die Implementierung.

---

**Zuletzt aktualisiert:** 2026-04-20  
**Status:** Sicherheitsorientierte Baseline für Lernprojekt  
**Next Steps:** Backend + DSGVO-Compliance bei Datenspeicherung hinzufügen
