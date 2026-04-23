// Cashflow-Seite: laedt Daten aus Supabase, schreibt zurueck

const db = window.auth.client;
const formatter = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' });

let aktuelleUntId = null;

async function init() {
    const user = await window.auth.requireLogin();
    if (!user) return;

    document.getElementById('user-email').textContent = user.email;
    document.getElementById('logout-link').addEventListener('click', e => {
        e.preventDefault();
        window.auth.logout();
    });

    document.getElementById('datum').valueAsDate = new Date();

    document.getElementById('unt-neu').addEventListener('click', neueUnternehmung);
    document.getElementById('unt-select').addEventListener('change', e => {
        aktuelleUntId = e.target.value;
        ladeEintraege();
    });
    document.getElementById('eintrag-form').addEventListener('submit', neuerEintrag);

    await ladeUnternehmungen();
}

async function ladeUnternehmungen() {
    const { data, error } = await db
        .from('unternehmungen')
        .select('*')
        .order('name');

    if (error) {
        alert('Fehler beim Laden der Unternehmungen: ' + error.message);
        return;
    }

    const select = document.getElementById('unt-select');
    select.innerHTML = '';

    if (data.length === 0) {
        select.innerHTML = '<option>Noch keine Unternehmung</option>';
        aktuelleUntId = null;
        zeichneEintraege([]);
        return;
    }

    data.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = u.name;
        select.appendChild(opt);
    });

    aktuelleUntId = data[0].id;
    select.value = aktuelleUntId;
    await ladeEintraege();
}

async function neueUnternehmung() {
    const name = prompt('Name der neuen Unternehmung:');
    if (!name || !name.trim()) return;

    const { error } = await db
        .from('unternehmungen')
        .insert({ name: name.trim() });

    if (error) {
        alert('Fehler: ' + error.message);
        return;
    }
    await ladeUnternehmungen();
}

async function neuerEintrag(e) {
    e.preventDefault();
    if (!aktuelleUntId) {
        alert('Bitte erst eine Unternehmung anlegen.');
        return;
    }

    const eintrag = {
        unternehmung_id: aktuelleUntId,
        datum: document.getElementById('datum').value,
        typ: document.getElementById('typ').value,
        betrag: parseFloat(document.getElementById('betrag').value),
        beschreibung: document.getElementById('beschreibung').value || null
    };

    const { error } = await db.from('cashflow').insert(eintrag);
    if (error) {
        alert('Fehler: ' + error.message);
        return;
    }

    document.getElementById('betrag').value = '';
    document.getElementById('beschreibung').value = '';
    await ladeEintraege();
}

async function ladeEintraege() {
    if (!aktuelleUntId) return zeichneEintraege([]);

    const { data, error } = await db
        .from('cashflow')
        .select('*')
        .eq('unternehmung_id', aktuelleUntId)
        .order('datum', { ascending: false });

    if (error) {
        alert('Fehler beim Laden: ' + error.message);
        return;
    }
    zeichneEintraege(data);
}

function zeichneEintraege(eintraege) {
    const tbody = document.getElementById('eintrag-body');
    const leer = document.getElementById('leer-hinweis');
    tbody.innerHTML = '';

    let einnahmen = 0, ausgaben = 0;

    eintraege.forEach(e => {
        if (e.typ === 'einnahme') einnahmen += Number(e.betrag);
        else ausgaben += Number(e.betrag);

        const tr = document.createElement('tr');
        const vorzeichen = e.typ === 'einnahme' ? '+' : '-';
        const cls = e.typ === 'einnahme' ? 'betrag-einnahme' : 'betrag-ausgabe';
        tr.innerHTML = `
            <td>${formatDatum(e.datum)}</td>
            <td>${e.typ === 'einnahme' ? 'Einnahme' : 'Ausgabe'}</td>
            <td>${escapeHtml(e.beschreibung || '')}</td>
            <td class="${cls}" style="text-align:right;">${vorzeichen} ${formatter.format(e.betrag)}</td>
            <td style="text-align:right;"><button class="loesch-btn" data-id="${e.id}" title="Loeschen">×</button></td>
        `;
        tbody.appendChild(tr);
    });

    leer.style.display = eintraege.length === 0 ? 'block' : 'none';

    document.getElementById('summe-einnahmen').textContent = formatter.format(einnahmen);
    document.getElementById('summe-ausgaben').textContent = formatter.format(ausgaben);
    document.getElementById('summe-saldo').textContent = formatter.format(einnahmen - ausgaben);

    tbody.querySelectorAll('.loesch-btn').forEach(btn => {
        btn.addEventListener('click', () => loescheEintrag(btn.dataset.id));
    });
}

async function loescheEintrag(id) {
    if (!confirm('Eintrag wirklich loeschen?')) return;
    const { error } = await db.from('cashflow').delete().eq('id', id);
    if (error) {
        alert('Fehler: ' + error.message);
        return;
    }
    await ladeEintraege();
}

function formatDatum(iso) {
    const [y, m, d] = iso.split('-');
    return `${d}.${m}.${y}`;
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

init();
