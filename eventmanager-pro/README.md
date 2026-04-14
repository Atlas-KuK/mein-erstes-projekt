# EventManager Pro

Event- und Catering-Management für **Lucky Event**, **Mettgenpin 1877** und **Schänke 1998**.

**Tech-Stack:** Next.js 14 (App Router) · TypeScript · Prisma · PostgreSQL · Tailwind CSS · JWT-Auth · PWA-fähig

---

## Stand: Phase 1 (Fundament) – fertig

| Baustein | Status |
|---|---|
| Projekt-Setup (Next.js, TypeScript, Tailwind) | ✓ |
| Prisma-Schema (9 Tabellen) | ✓ |
| Docker-Compose mit PostgreSQL 16 | ✓ |
| Auth-System (Login, Logout, Passwort vergessen, JWT, Rollen) | ✓ |
| Passwort ändern (eingeloggt) | ✓ |
| Benutzerverwaltung (CRUD, Rollen, Admin-Passwort-Reset) | ✓ |
| DSGVO: Datenexport + Löschung | ✓ |
| Audit-Log | ✓ |
| Seed mit ~88 Events 2026 + 4 Detail-Eventblättern | ✓ |
| Minimales Dashboard + Login-UI | ✓ |

**Phase 2** (Event-CRUD, Jahresübersicht, Detail-Tabs, Dashboard-Kennzahlen) startet danach.

---

## Setup (von Null, ca. 5 Minuten)

### Voraussetzungen
- Node.js 20+
- Docker & docker-compose (für Postgres)

### Schritte

```bash
cd eventmanager-pro

# 1) Abhängigkeiten installieren
npm install

# 2) Postgres starten
docker compose up -d

# 3) Umgebungsvariablen
cp .env.example .env
# -> JWT_ACCESS_SECRET und JWT_REFRESH_SECRET durch starke Werte ersetzen:
#    node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"

# 4) Datenbank-Schema anlegen
npx prisma migrate dev --name init

# 5) Seed-Daten einspielen (Admin + ~88 Events + 4 Detail-Eventblätter)
npm run db:seed
# ⚠️  In der Konsole wird das initiale Admin-Passwort ausgegeben.
#    Sofort notieren – es wird nie wieder angezeigt.

# 6) App starten
npm run dev
```

Die App läuft auf **http://localhost:3000**.

**Login:** `polikarpos@luckyevent.de` + das im Seed ausgegebene Passwort.

---

## Wichtige Befehle

```bash
npm run dev            # Dev-Server
npm run build          # Produktions-Build
npm run start          # Produktions-Server

npm run db:migrate     # Neue Migration erzeugen & anwenden
npm run db:push        # Schema ohne Migration pushen (nur dev)
npm run db:studio      # Prisma Studio (DB-Browser)
npm run db:seed        # Seed-Daten (idempotent)
npm run db:reset       # Komplett-Reset + Seed
```

---

## Projektstruktur

```
eventmanager-pro/
├── prisma/
│   ├── schema.prisma        # Datenbank-Schema (9 Modelle)
│   ├── seed.ts              # Seed-Script
│   └── seed-events.ts       # Event-Daten 2026
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx          # /  →  Login oder Dashboard
│   │   ├── login/
│   │   ├── passwort-vergessen/
│   │   ├── passwort-zuruecksetzen/
│   │   ├── dashboard/
│   │   ├── benutzer/         # Admin: User-Verwaltung
│   │   ├── datenschutz/
│   │   └── api/
│   │       ├── auth/         # login, logout, me, forgot, reset, change-password
│   │       └── users/        # CRUD, reset-password, export, data (DSGVO)
│   └── lib/
│       ├── prisma.ts         # Prisma-Client-Singleton
│       ├── auth.ts           # bcrypt + JWT + Token-Generierung
│       └── session.ts        # Cookie-Sessions, Rollen-Guard
├── middleware.ts             # Edge-Middleware: Redirect auf /login
├── docker-compose.yml        # PostgreSQL 16 lokal
├── public/
│   ├── manifest.webmanifest  # PWA-Manifest
│   └── icons/                # (Platzhalter bis Phase 4)
├── .env.example
└── package.json
```

---

## Rollen & Berechtigungen (Phase 1)

| Rolle | Bereich Phase 1 |
|---|---|
| **Admin** | Alles: Dashboard, Benutzerverwaltung, Seed-Zugriff |
| **Teamleitung** | Dashboard (Events-Verwaltung folgt in Phase 2) |
| **Mitarbeiter** | Dashboard (Arbeitsanweisungen folgen in Phase 3) |
| **Kunde** | Dashboard (Kunden-Portal folgt in Phase 3) |
| **Partner** | Dashboard (Partner-Portal folgt in Phase 3) |

Rollen werden beim User-Anlegen vergeben und sind serverseitig in jedem API-Endpoint durchgesetzt.

---

## Sicherheit

- Passwörter via **bcrypt** (12 Rounds, konfigurierbar in `.env`)
- **JWT** Access-Token (15 Min) + Refresh-Token (7 Tage, DB-gehasht → serverseitig invalidierbar)
- **HttpOnly Cookies**, `SameSite=Lax`, in Produktion `Secure`
- **Audit-Log** für alle sicherheitsrelevanten Aktionen (Login, Logout, Passwort, Benutzer-Änderungen, DSGVO-Aktionen)
- **Rollen-Guard** auf jedem geschützten Endpoint
- **Prisma** verhindert SQL-Injection
- Einheitliche Fehlermeldungen bei Login (keine User-Enumeration)
- `forgot-password` gibt nie preis, ob eine E-Mail existiert

---

## DSGVO

- Datenschutzerklärung als Seite (`/datenschutz`)
- Admin kann pro User:
  - Datenexport als JSON (`GET /api/users/:id/export`)
  - Komplettlöschung (`DELETE /api/users/:id/data`)
- Kein externes Tracking, keine Analytics
- HTTPS-Pflicht in Produktion (Cookie `Secure` flag)

---

## E-Mail-Versand (noch nicht konfiguriert)

Passwort-Reset-Links werden aktuell **in die Server-Konsole** geloggt.
In Phase 2 kommt ein SMTP-Adapter (Nodemailer + eigener Mailserver oder Postmark o.ä.).

---

## Hosting-Empfehlung

Läuft auf jedem Linux-VPS (Hetzner, Netcup etc.). Empfohlenes Setup:

- Docker + Postgres
- `next build` + `next start` hinter **Caddy** oder **nginx** (TLS)
- Backups: `pg_dump` via Cron

**Kein Vendor-Lock-in, keine externen Abhängigkeiten.**
