@AGENTS.md

# Project: Hypnose Coaching Website

## Kontext
Webseite für ein Hypnose-Coaching-Angebot in 58675 Hemer und deutschlandweit per Zoom.
- Zielgruppe: Klienten für Einzel- und Gruppensitzungen sowie Online-Sitzungen
- Inspiriert von www.mryasin.com (HypnoX Akademie) — Premium Dark Theme mit Gold-Akzenten
- Ausführliche Konkurrenzanalyse: siehe Git-Historie und Chat-Verlauf

## Tech Stack
- Next.js 16 (App Router) — **Beachte: Breaking Changes ggü. älteren Next-Versionen,
  Docs sind in `node_modules/next/dist/docs/` hinterlegt**
- React 19
- TypeScript
- Tailwind CSS v4 (CSS-first config via `@theme` in `app/globals.css`)
- Turbopack dev-Server
- Keine zusätzlichen Dependencies ohne Rücksprache

## Struktur
- `app/layout.tsx` — Root-Layout mit Metadaten (lang="de")
- `app/page.tsx` — Landing-Page (Hero, Angebote, Über mich, Kontakt, Footer)
- `app/globals.css` — Tailwind-Import + CSS-Variablen (Farb-Theme)
- `public/` — statische Assets (Bilder, Favicon später)

## Running
```bash
cd hypnose-website
npm run dev     # Dev-Server auf http://localhost:3000
npm run build   # Production-Build (inkl. Type-Check)
npm run lint    # ESLint
```

## Farbpalette (Platzhalter, in `app/globals.css`)
- `--background`: #0a0a0a (fast schwarz)
- `--foreground`: #f5f5f4 (off-white)
- `--surface`: #18181b (Karten/Sections)
- `--border`: #27272a
- `--accent`: #c8a24b (Gold)
- `--muted`: #a1a1aa

→ **Finale Marken-Farben mit Kunden klären, bevor groß ausgerollt wird.**

## Offene Entscheidungen
- [ ] Marken-/Geschäftsname
- [ ] Logo
- [ ] Finale Farbpalette (Hex-Werte)
- [ ] Tonalität (du/Sie, Duktus)
- [ ] Finale Preise
- [ ] Kontaktformular-Backend (z. B. Resend + API-Route, Formspree, o. Ä.)
- [ ] Deployment-Ziel (Vercel empfohlen)
- [ ] Domain
- [ ] Impressum / Datenschutz / AGB — rechtlich prüfen lassen!

## Roadmap
- **Phase 1 (MVP):** Landing Page, Über mich, Angebote, Kontakt, Rechtliches → jetzt
- **Phase 2:** Online-Buchung (Calendly-Integration), Newsletter + Lead-Magnet, Blog (SEO)
- **Phase 3:** Mitgliederbereich, Online-Programme, ggf. eigene Akademie

## Code-Regeln
- Komponenten in `app/` (App Router). Wiederverwendbare UI-Bausteine in `app/_components/`
  oder `components/` platzieren, sobald mehrere Seiten entstehen
- Server Components als Default, `"use client"` nur wenn nötig
- Deutsche Texte im Code, englische Variablen-/Funktionsnamen
- Keine Tracking-Skripte ohne DSGVO-konforme Lösung (Consent Banner)

## Git / Branch
- Entwicklung auf Branch `claude/hypnosis-coaching-website-k5p5t`
- `main` gehört zum parallelen Lernprojekt und bleibt unberührt
