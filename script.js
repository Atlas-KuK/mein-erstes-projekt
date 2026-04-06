// ── Konfiguration ──────────────────────────────────────────────
// Google Sheet als CSV veröffentlichen und URL hier eintragen.
// Datei → Im Web veröffentlichen → CSV → URL kopieren
const CONFIG_KEY = 'catering_sheet_url';

// Demo-Daten (werden durch echte Sheet-Daten ersetzt sobald URL konfiguriert ist)
const DEMO_EVENTS = [
  {
    datum:     '2026-04-19',
    titel:     'Catering Firma Müller AG',
    typ:       'catering',
    pax:       60,
    ort:       'Kongresszentrum München',
    personal_einkauf:  'Max Mustermann',
    personal_kochen:   'Lisa Schmidt',
    personal_lieferung:'Tom Wagner',
    status:    'bestaetigt',
    notizen:   '3-Gang Menü, vegetarische Option nötig'
  },
  {
    datum:     '2026-04-25',
    titel:     'Firmenfeier TechCorp',
    typ:       'event',
    pax:       120,
    ort:       'Rooftop Bar, Hamburg',
    personal_einkauf:  'Anna Bauer',
    personal_kochen:   '',
    personal_lieferung:'Max Mustermann',
    status:    'geplant',
    notizen:   'Fingerfood, Getränkeservice'
  },
  {
    datum:     '2026-05-03',
    titel:     'Privates Dinner',
    typ:       'catering',
    pax:       12,
    ort:       'Kundenadresse',
    personal_einkauf:  '',
    personal_kochen:   'Lisa Schmidt',
    personal_lieferung:'Lisa Schmidt',
    status:    'geplant',
    notizen:   ''
  }
];

// ── Hilfsfunktionen ────────────────────────────────────────────
function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
}

function daysUntil(dateStr) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(dateStr + 'T00:00:00');
  return Math.ceil((d - today) / 86400000);
}

function isThisWeek(dateStr) {
  const days = daysUntil(dateStr);
  return days >= 0 && days <= 7;
}

function typLabel(typ) {
  return { catering: 'Catering', event: 'Event', other: 'Sonstiges' }[typ] || typ;
}

function statusLabel(status) {
  return { geplant: 'Geplant', bestaetigt: 'Bestätigt', abgeschlossen: 'Erledigt' }[status] || status;
}

// ── Event Card rendern ─────────────────────────────────────────
function renderCard(ev) {
  const days = daysUntil(ev.datum);
  const isUpcoming = days >= 0 && days <= 7;
  const isPast = days < 0;

  function slotRow(icon, label, person) {
    const personHtml = person
      ? `<span class="slot-person">${person}</span>`
      : `<span class="slot-person slot-empty">nicht besetzt</span>`;
    return `<div class="slot-item">
      <span class="slot-icon">${icon}</span>
      <span class="slot-name">${label}</span>
      ${personHtml}
    </div>`;
  }

  return `
    <div class="event-card ${ev.typ}" data-type="${ev.typ}" data-date="${ev.datum}">
      <div class="card-header">
        <span class="card-date">${formatDate(ev.datum)}${isUpcoming ? ' 🔔' : ''}</span>
        <span class="card-badge badge-${ev.typ}">${typLabel(ev.typ)}</span>
      </div>
      <div class="card-title">${ev.titel}</div>
      <div class="card-meta">📍 ${ev.ort || '–'}${ev.notizen ? '<br>💬 ' + ev.notizen : ''}</div>
      <div class="card-slots">
        ${slotRow('🛒', 'Einkauf', ev.personal_einkauf)}
        ${slotRow('🍳', 'Kochen', ev.personal_kochen)}
        ${slotRow('🚚', 'Lieferung', ev.personal_lieferung)}
      </div>
      <div class="card-status">
        <span class="status-pill pill-${ev.status}">${statusLabel(ev.status)}</span>
        <span class="card-pax">${ev.pax ? ev.pax + ' Pax' : ''}</span>
      </div>
    </div>`;
}

// ── Timeline Item rendern ──────────────────────────────────────
function renderTimelineItem(ev) {
  const days = daysUntil(ev.datum);
  const daysLabel = days === 0 ? 'Heute' : days === 1 ? 'Morgen' : `in ${days} Tagen`;
  return `
    <div class="timeline-item">
      <span class="tl-date">${formatDate(ev.datum)}</span>
      <span class="tl-dot ${ev.typ}"></span>
      <span class="tl-title">${ev.titel}</span>
      <span class="tl-meta">${ev.pax ? ev.pax + ' Pax · ' : ''}${daysLabel}</span>
    </div>`;
}

// ── Dashboard befüllen ─────────────────────────────────────────
function renderDashboard(events) {
  const future = events
    .filter(e => daysUntil(e.datum) >= 0)
    .sort((a, b) => a.datum.localeCompare(b.datum));

  // Statistiken
  document.getElementById('count-total').textContent    = events.length;
  document.getElementById('count-upcoming').textContent = events.filter(e => isThisWeek(e.datum)).length;
  document.getElementById('count-done').textContent     = events.filter(e => e.status === 'abgeschlossen').length;

  // Event Cards
  const grid = document.getElementById('events-grid');
  if (future.length === 0) {
    grid.innerHTML = '<p class="empty-state">Keine anstehenden Ereignisse.</p>';
  } else {
    grid.innerHTML = future.map(renderCard).join('');
  }

  // Timeline (nächste 30 Tage)
  const tl = document.getElementById('timeline-container');
  const next30 = future.filter(e => daysUntil(e.datum) <= 30);
  tl.innerHTML = next30.length
    ? next30.map(renderTimelineItem).join('')
    : '<p class="empty-state">Keine Ereignisse in den nächsten 30 Tagen.</p>';
}

// ── Filter ─────────────────────────────────────────────────────
let allEvents = [];

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.event-card').forEach(card => {
      card.style.display = (filter === 'all' || card.dataset.type === filter) ? '' : 'none';
    });
  });
});

// ── Google Sheets CSV laden ─────────────────────────────────────
function parseCSV(text) {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/ /g, '_'));
  return lines.slice(1).map(line => {
    // Einfaches CSV-Parsing (keine Kommas in Feldern)
    const values = line.split(',');
    const obj = {};
    headers.forEach((h, i) => { obj[h] = (values[i] || '').trim(); });
    return obj;
  }).filter(e => e.datum);
}

async function loadFromSheet(url) {
  try {
    // CORS-Proxy für Google Sheets CSV (kein API-Key nötig)
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    return parseCSV(text);
  } catch (err) {
    console.warn('Sheet konnte nicht geladen werden:', err.message);
    return null;
  }
}

// ── Konfiguration speichern/laden ──────────────────────────────
function saveConfig() {
  const url = document.getElementById('sheet-url').value.trim();
  if (!url) return;
  localStorage.setItem(CONFIG_KEY, url);
  init();
}

async function init() {
  const savedUrl = localStorage.getItem(CONFIG_KEY);

  if (savedUrl) {
    document.getElementById('sheet-url').value = savedUrl;
    const events = await loadFromSheet(savedUrl);
    if (events && events.length > 0) {
      allEvents = events;
      renderDashboard(allEvents);
      return;
    }
  }

  // Demo-Daten anzeigen wenn kein Sheet konfiguriert
  allEvents = DEMO_EVENTS;
  renderDashboard(allEvents);
}

// ── Start ──────────────────────────────────────────────────────
init();
