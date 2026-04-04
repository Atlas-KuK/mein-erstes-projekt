/* ── Sprecher-Zuweisung ──────────────────────────────────────── */

function onSpeakerChange(selectEl, index) {
  if (selectEl.value === '__new__') {
    const name = prompt('Name des neuen Sprechers:');
    if (name && name.trim()) {
      const trimmed = name.trim();
      // Option hinzufügen
      const opt = new Option(trimmed, trimmed, true, true);
      selectEl.insertBefore(opt, selectEl.querySelector('[value="__new__"]'));
      selectEl.value = trimmed;
      segments[index] = { ...segments[index], speaker: trimmed };
      addSpeakerToList(trimmed);
    } else {
      // Zurücksetzen
      selectEl.value = segments[index]?.speaker || '';
    }
  } else {
    segments[index] = { ...segments[index], speaker: selectEl.value };
  }
}

async function saveSegments() {
  const btn = document.querySelector('button[onclick="saveSegments()"]');
  if (btn) { btn.textContent = 'Speichert…'; btn.disabled = true; }

  try {
    const resp = await fetch(`/api/recording/${RECORDING_ID}/speakers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ segments }),
    });
    if (resp.ok) {
      if (btn) { btn.textContent = '✓ Gespeichert'; }
      setTimeout(() => {
        if (btn) { btn.textContent = 'Sprecher speichern'; btn.disabled = false; }
      }, 2000);
    }
  } catch (e) {
    if (btn) { btn.textContent = 'Fehler'; btn.disabled = false; }
  }
}

/* ── Protokoll generieren ───────────────────────────────────── */

async function generateProtocol() {
  const selected = document.querySelector('input[name="template"]:checked');
  if (!selected) return;

  const btn = document.querySelector('button[onclick="generateProtocol()"]');
  const label = document.getElementById('gen-label');
  const status = document.getElementById('gen-status');

  btn.disabled = true;
  label.textContent = '⏳ Generiert…';
  status.className = 'gen-status';
  status.textContent = 'Claude analysiert das Transkript…';

  try {
    // Sprecher erst speichern
    await fetch(`/api/recording/${RECORDING_ID}/speakers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ segments }),
    });

    const resp = await fetch(`/api/recording/${RECORDING_ID}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template: selected.value }),
    });

    const data = await resp.json();

    if (resp.ok) {
      status.className = 'gen-status success';
      status.textContent = '✓ Protokoll erstellt!';
      label.textContent = 'Protokoll generieren';
      btn.disabled = false;

      // Link zum Protokoll anzeigen
      const link = document.createElement('a');
      link.href = `/recording/${RECORDING_ID}/protocol/${data.template}`;
      link.className = 'btn btn-primary btn-block';
      link.style.marginTop = '10px';
      link.textContent = '→ Protokoll ansehen';
      link.target = '_blank';
      status.after(link);

      // Nach 1s neu laden damit Protokoll-Liste aktualisiert
      setTimeout(() => location.reload(), 1200);
    } else {
      throw new Error(data.detail || 'Unbekannter Fehler');
    }
  } catch (e) {
    status.className = 'gen-status error';
    status.textContent = '✗ Fehler: ' + e.message;
    label.textContent = 'Protokoll generieren';
    btn.disabled = false;
  }
}

/* ── Sprecher hinzufügen ────────────────────────────────────── */

async function addSpeaker() {
  const input = document.getElementById('new-speaker-input');
  const name = input.value.trim();
  if (!name) return;

  try {
    const resp = await fetch('/api/speakers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });

    if (resp.ok) {
      addSpeakerToList(name);
      // Alle Dropdowns aktualisieren
      document.querySelectorAll('.speaker-select').forEach(sel => {
        if (![...sel.options].some(o => o.value === name)) {
          const opt = new Option(name, name);
          sel.insertBefore(opt, sel.querySelector('[value="__new__"]'));
        }
      });
      input.value = '';
    }
  } catch (e) {
    console.error('Sprecher hinzufügen fehlgeschlagen:', e);
  }
}

function addSpeakerToList(name) {
  const list = document.getElementById('speaker-list');
  if (!list) return;
  if ([...list.querySelectorAll('.speaker-chip')].some(c => c.textContent === name)) return;
  const chip = document.createElement('div');
  chip.className = 'speaker-chip';
  chip.textContent = name;
  list.appendChild(chip);
}

/* ── Enter-Taste für Sprecher-Input ─────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('new-speaker-input');
  if (input) {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') addSpeaker();
    });
  }
});
