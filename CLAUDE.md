# Projekt: mp1877.de / Lucky Event – Personalplanung

## Kontext
Dieser Repo gehört zu **mp1877.de** (Mettgenpin 1877) und **Lucky Event** (Catering & Eventservice).
Inhaber/Nutzer: pkarafulidis@gmail.com
GitHub: Atlas-KuK/mein-erstes-projekt
GitHub Pages: über `main`-Branch

## Projektstruktur
- `index.html` – Hauptwebsite (mp1877.de, unverändert lassen)
- `style.css`, `script.js` – Haupt-Stylesheets (unverändert lassen)
- `personalplanung.html` – WhatsApp-Vorlagen + Schichtplanung für alle Events Apr/Mai 2026
- `hartwig-schwibbe-2026-05-01.html` – Eigenständige Seite für Firmenjubiläum Hartwig & Schwibbe

## Design-System (Lucky Event / mp1877.de)

### Farben
- Grün (Schänke 1998): `#1b7a3e`
- Blau (Mettgenpin 1877): `#1a4fa0`
- Orange (Firmenjubiläum): `#b84e00`
- Lila (Mettgenpin Schichtplan): `#4a235a`
- Navy (Lucky Event Template): `#0d5c8a`
- Gold (Hartwig & Schwibbe): `#c4922a`, Hero-Gradient: `#1a2a4a → #2d4a7a`

### Wiederkehrende CSS-Patterns
```css
/* Event-Karte */
.event-card { background:#fff; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08); }

/* Input-Felder für Personalslots */
.slot-input { display:block; width:100%; padding:5px 8px; margin-bottom:5px; border:1px solid #ddd; border-radius:6px; font-size:0.84rem; }

/* Positions-Grid */
display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:10px;

/* WhatsApp-Block */
.wa-block { background:#e8f5e9; border:1px solid #a5d6a7; border-radius:10px; cursor:pointer; }
```

### Wiederkehrende JS-Patterns
```js
// Clipboard-Copy mit Fallback
function copyText(el) {
  const text = el.querySelector('.wa-text').innerText;
  navigator.clipboard.writeText(text).catch(() => {
    const range = document.createRange();
    range.selectNodeContents(el.querySelector('.wa-text'));
    window.getSelection().addRange(range);
    document.execCommand('copy');
  });
}

// Person-Slot hinzufügen
function addSlot(btn) {
  const container = btn.previousElementSibling;
  const inp = document.createElement('input');
  inp.type = 'text';
  inp.placeholder = 'Person ' + (container.children.length + 1);
  inp.className = 'slot-input';
  container.appendChild(inp);
}
```

## Events / Aufträge

### Event 1 – Schänke 1998 (Apr 2026)
- Janni: Einlass, Laki: Backup
- Service: Sonja Brockhoff, Marlies (ggf.)
- Farbe: Grün `#1b7a3e`

### Event 2 – Mettgenpin 1877 (Apr/Mai 2026)
- Security: Marvin Brösecke (kompletter Bedarf, beide Venues)
- Roll-Up Banner Hinweis: Mitarbeiter dürfen Roll-Up aufstellen (Lucky Event Werbung)
- Schänke + Mettgenpin sollen sich gegenseitig unterstützen
- Schichtplanung-Sektion: Geländeübersicht als CSS-Grid (5 Zonen)
  - Gastraum 1 (Ausschank) · Gastraum 2 · Gastraum 3 · Küche · Biergarten 200 Pax · Lounge · Parkplatz
- Positionen: Innenbereich Theke · Außenbereich Theke · Läufer · Cocktailtheke · Springer · Security

### Event 3 – Firmenjubiläum Hartwig & Schwibbe (01.05.2026)
- Auftragsnummer: AB0013
- Location: Solingen, Firmengelände, 150 Gäste
- Uhrzeit: 12:00–20:00 Uhr
- Aufbau: Di. 28.04. + Mi. 29.04. (5 Pers.)
- Abbau: So. 02.05. + Mo. 03.05. (5 Pers.)
- LKW-Fahrer: Uwe Delke
- Catering: Deutsche Imbissstation + Griechischer Grillstand + Vegan + Getränke
- Essenrunden: 2–4x pro Gast
- Positionen: Koordination · Imbiss · Grill · Vegan · Zapfer · Läufer · Springer · Aufbauteam · Schlepper · LKW

### Getränkeangebot (Standard Lucky Event)
Afri Cola · Bluna · Wasser · Säfte · Grand Sud Merlot & Chardonnay · Prosecco
Brinkhoff · Starnberger · Krombacher (Weizen, 0,0%) · Lillet Wild Berry · Aperol Spritz

## Eigenständige Event-Seiten (Vorlage: hartwig-schwibbe-2026-05-01.html)
Jede eigenständige Event-Seite enthält:
1. **Hero-Banner** (Eventname, Datum, Gäste, Badges)
2. **Nav** (Personalplanung · Projektübersicht · Zeitplan · WhatsApp-Vorlagen)
3. **Personalplanung** – Interaktive Positionskarten nach Tag/Phase (Aufbau / Event / Abbau)
4. **Projektübersicht** – Auftraggeber, Angebotsnummer, Kalkulation, Cateringangebot
5. **Zeitplan** – Timeline-View aller Tage
6. **WhatsApp-Vorlagen** – Kopierbare Anfragetexte pro Rolle

## GitHub / Deployment
- Repo: `Atlas-KuK/mein-erstes-projekt`
- Branch für Entwicklung: `claude/event-staffing-planning-cUcrk`
- Branch für GitHub Pages: `main` (wurde angelegt via `git checkout -b main && git push -u origin main`)
- GitHub Pages URL: https://atlas-kuk.github.io/mein-erstes-projekt/
- Kein Backend, kein Framework – rein statisches HTML/CSS/JS

## Häufige Aufgaben
- **Neue Event-Seite erstellen**: Vorlage aus `hartwig-schwibbe-2026-05-01.html` kopieren, Farben/Inhalte anpassen
- **Mitarbeiter hinzufügen**: Slot-Inputs in der jeweiligen Positionskarte befüllen
- **WhatsApp-Text anpassen**: `.wa-text` Div in `wa-block` editieren
- **Schichtplan exportieren**: `exportHSPlan()` / `exportPlan()` / `exportLuckyEvent()` – gibt Text in Clipboard

## Wichtige Mitarbeiter (bekannte Namen)
- Janni – Einlass/Kasse
- Laki – Backup/Flex
- Sonja Brockhoff – Service
- Marlies – Service
- Marvin Brösecke – Security (SFP, beide Venues)
- Uwe Delke – LKW-Fahrer
