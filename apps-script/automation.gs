/**
 * Catering Event Automation – Google Apps Script
 * ------------------------------------------------
 * Einrichtung:
 *   1. Google Sheet mit diesen Spalten anlegen:
 *      Datum | Titel | Typ | Pax | Ort | Einkauf-Personal | Koch-Personal | Liefer-Personal | Status | Notizen
 *   2. Diesen Code unter Erweiterungen → Apps Script einfügen
 *   3. DEINE_EMAIL unten eintragen
 *   4. Trigger setzen: Bei Formularübermittlung → onFormSubmit
 *
 * Was passiert automatisch:
 *   • PDF mit allen Details wird in Google Drive erstellt
 *   • E-Mail mit Ordio-Checkliste wird verschickt
 *   • Status im Sheet wird auf "geplant" gesetzt
 */

// ── Konfiguration ──────────────────────────────────────────────
const CONFIG = {
  email:         'DEINE_EMAIL@example.com',   // ← hier deine E-Mail eintragen
  driveFolder:   'Catering Aufträge',          // Google Drive Ordner Name
  emailBetreff:  '📋 Neuer Auftrag: ',
};

// Spalten-Index (0-basiert) – anpassen wenn dein Sheet anders aufgebaut ist
const COL = {
  datum:             0,
  titel:             1,
  typ:               2,
  pax:               3,
  ort:               4,
  personal_einkauf:  5,
  personal_kochen:   6,
  personal_lieferung:7,
  status:            8,
  notizen:           9,
};

// ── Trigger: wird bei jedem neuen Formular-Eintrag aufgerufen ──
function onFormSubmit(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  const row = sheet.getRange(lastRow, 1, 1, 10).getValues()[0];

  const auftrag = parseRow(row);

  // Status auf "geplant" setzen
  sheet.getRange(lastRow, COL.status + 1).setValue('geplant');

  // PDF erstellen
  const pdfUrl = createPDF(auftrag, lastRow);

  // E-Mail mit Ordio-Checkliste senden
  sendOrdioEmail(auftrag, pdfUrl);
}

// ── Daten aus Sheet-Zeile lesen ────────────────────────────────
function parseRow(row) {
  return {
    datum:              formatDate(row[COL.datum]),
    datumRaw:           row[COL.datum],
    titel:              row[COL.titel]             || '',
    typ:                row[COL.typ]               || 'catering',
    pax:                row[COL.pax]               || '',
    ort:                row[COL.ort]               || '',
    personal_einkauf:   row[COL.personal_einkauf]  || '',
    personal_kochen:    row[COL.personal_kochen]   || '',
    personal_lieferung: row[COL.personal_lieferung]|| '',
    notizen:            row[COL.notizen]            || '',
  };
}

// ── Datum formatieren ──────────────────────────────────────────
function formatDate(d) {
  if (!d) return '–';
  const date = new Date(d);
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'dd.MM.yyyy');
}

function formatDateLong(d) {
  if (!d) return '–';
  const date = new Date(d);
  return Utilities.formatDate(date, Session.getScriptTimeZone(), "EEEE, dd. MMMM yyyy");
}

// Vorbereitungsdatum berechnen (z.B. 2 Tage vorher für Einkauf)
function addDays(d, days) {
  const date = new Date(d);
  date.setDate(date.getDate() + days);
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'dd.MM.yyyy');
}

// ── PDF erstellen ──────────────────────────────────────────────
function createPDF(auftrag, rowNumber) {
  // Ordner in Google Drive finden oder erstellen
  let folder;
  const folders = DriveApp.getFoldersByName(CONFIG.driveFolder);
  folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(CONFIG.driveFolder);

  // Temporäres Google Doc erstellen
  const doc = DocumentApp.create(`Auftrag_${auftrag.datum}_${auftrag.titel}`);
  const body = doc.getBody();

  // PDF-Inhalt aufbauen
  body.appendParagraph('AUFTRAGSDETAILS').setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph('');

  // Basisdaten
  const table = body.appendTable([
    ['Datum',   auftrag.datum],
    ['Auftrag', auftrag.titel],
    ['Typ',     auftrag.typ.charAt(0).toUpperCase() + auftrag.typ.slice(1)],
    ['Pax',     auftrag.pax ? auftrag.pax + ' Personen' : '–'],
    ['Ort',     auftrag.ort || '–'],
  ]);
  table.setBorderWidth(1);
  body.appendParagraph('');

  // Personalplanung
  body.appendParagraph('PERSONALPLANUNG').setHeading(DocumentApp.ParagraphHeading.HEADING2);
  const personalTable = body.appendTable([
    ['Phase',             'Personal',                  'Datum (ca.)'],
    ['🛒 Einkauf/Vorbereitung', auftrag.personal_einkauf  || 'nicht besetzt', addDays(auftrag.datumRaw, -2)],
    ['🍳 Kochen/Zubereitung',  auftrag.personal_kochen    || 'nicht besetzt', auftrag.datum],
    ['🚚 Lieferung/Ausführung', auftrag.personal_lieferung || 'nicht besetzt', auftrag.datum],
  ]);
  personalTable.setBorderWidth(1);
  body.appendParagraph('');

  // Notizen
  if (auftrag.notizen) {
    body.appendParagraph('NOTIZEN').setHeading(DocumentApp.ParagraphHeading.HEADING2);
    body.appendParagraph(auftrag.notizen);
    body.appendParagraph('');
  }

  // Ordio-Tagesnotiz
  body.appendParagraph('ORDIO – TAGESNOTIZ').setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph(buildOrdioTagesnotiz(auftrag));

  doc.saveAndClose();

  // Als PDF speichern
  const docFile = DriveApp.getFileById(doc.getId());
  const pdfBlob = docFile.getAs('application/pdf');
  const pdfFile = folder.createFile(pdfBlob);
  pdfFile.setName(`Auftrag_${auftrag.datum}_${auftrag.titel}.pdf`);

  // Temp-Doc löschen
  docFile.setTrashed(true);

  Logger.log('PDF erstellt: ' + pdfFile.getUrl());
  return pdfFile.getUrl();
}

// ── Ordio Tagesnotiz Text ──────────────────────────────────────
function buildOrdioTagesnotiz(auftrag) {
  const parts = [auftrag.typ.charAt(0).toUpperCase() + auftrag.typ.slice(1)];
  if (auftrag.pax)   parts.push(auftrag.pax + ' Pax');
  if (auftrag.titel) parts.push('– ' + auftrag.titel);
  if (auftrag.ort)   parts.push('@ ' + auftrag.ort);
  return parts.join(' ');
  // Beispiel-Output: "Catering 60 Pax – Firma Müller AG @ Kongresszentrum München"
}

// ── E-Mail mit Ordio-Checkliste ────────────────────────────────
function sendOrdioEmail(auftrag, pdfUrl) {
  const einkaufDatum  = addDays(auftrag.datumRaw, -2);  // 2 Tage vorher
  const kochDatum     = addDays(auftrag.datumRaw, 0);   // Am Event-Tag (morgens)
  const lieferDatum   = auftrag.datum;                   // Am Event-Tag

  const ordioNotiz = buildOrdioTagesnotiz(auftrag);

  const htmlBody = `
<div style="font-family: Arial, sans-serif; max-width: 600px;">
  <h2 style="color: #1a1a2e;">📋 Neuer Auftrag erstellt</h2>

  <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
    <tr><td style="padding: 6px 12px; background: #f5f5f5; font-weight: bold;">Auftrag</td>
        <td style="padding: 6px 12px;">${auftrag.titel}</td></tr>
    <tr><td style="padding: 6px 12px; background: #f5f5f5; font-weight: bold;">Datum</td>
        <td style="padding: 6px 12px;">${auftrag.datum}</td></tr>
    <tr><td style="padding: 6px 12px; background: #f5f5f5; font-weight: bold;">Pax</td>
        <td style="padding: 6px 12px;">${auftrag.pax || '–'}</td></tr>
    <tr><td style="padding: 6px 12px; background: #f5f5f5; font-weight: bold;">Ort</td>
        <td style="padding: 6px 12px;">${auftrag.ort || '–'}</td></tr>
    ${auftrag.notizen ? `<tr><td style="padding: 6px 12px; background: #f5f5f5; font-weight: bold;">Notizen</td>
        <td style="padding: 6px 12px;">${auftrag.notizen}</td></tr>` : ''}
  </table>

  <h3 style="color: #1a1a2e; border-bottom: 2px solid #e94560; padding-bottom: 6px;">
    📌 Ordio – Bitte eintragen (copy-paste)
  </h3>

  <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
    <strong>Tagesnotiz für ${auftrag.datum}:</strong><br>
    <code style="font-size: 1.05em; color: #333;">${ordioNotiz}</code>
  </div>

  <h4>Personalslots anlegen:</h4>
  <table style="border-collapse: collapse; width: 100%;">
    <thead>
      <tr style="background: #1a1a2e; color: white;">
        <th style="padding: 8px 12px; text-align: left;">Phase</th>
        <th style="padding: 8px 12px; text-align: left;">Person</th>
        <th style="padding: 8px 12px; text-align: left;">Datum</th>
        <th style="padding: 8px 12px; text-align: left;">Bezeichnung in Ordio</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background: #fef9e7;">
        <td style="padding: 8px 12px;">🛒 Einkauf</td>
        <td style="padding: 8px 12px;">${auftrag.personal_einkauf || '<em>nicht besetzt</em>'}</td>
        <td style="padding: 8px 12px;">${einkaufDatum}</td>
        <td style="padding: 8px 12px;"><code>Einkauf – ${auftrag.titel}</code></td>
      </tr>
      <tr style="background: #f0faf5;">
        <td style="padding: 8px 12px;">🍳 Kochen</td>
        <td style="padding: 8px 12px;">${auftrag.personal_kochen || '<em>nicht besetzt</em>'}</td>
        <td style="padding: 8px 12px;">${kochDatum}</td>
        <td style="padding: 8px 12px;"><code>Kochen – ${auftrag.titel}</code></td>
      </tr>
      <tr style="background: #fef2f0;">
        <td style="padding: 8px 12px;">🚚 Lieferung</td>
        <td style="padding: 8px 12px;">${auftrag.personal_lieferung || '<em>nicht besetzt</em>'}</td>
        <td style="padding: 8px 12px;">${lieferDatum}</td>
        <td style="padding: 8px 12px;"><code>Lieferung – ${auftrag.titel}</code></td>
      </tr>
    </tbody>
  </table>

  <p style="margin-top: 20px;">
    📄 <a href="${pdfUrl}">Auftragsdetails als PDF öffnen</a>
  </p>

  <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
  <p style="color: #888; font-size: 0.85em;">
    Diese E-Mail wurde automatisch erstellt. Änderungen im
    <a href="https://docs.google.com/spreadsheets">Google Sheet</a> vornehmen.
  </p>
</div>`;

  MailApp.sendEmail({
    to:       CONFIG.email,
    subject:  CONFIG.emailBetreff + auftrag.titel + ' (' + auftrag.datum + ')',
    htmlBody: htmlBody,
  });

  Logger.log('E-Mail gesendet an: ' + CONFIG.email);
}

// ── Manuell testen (einmalig ausführen um zu testen) ───────────
function testMitDemoAuftrag() {
  const demoAuftrag = {
    datum:              '19.04.2026',
    datumRaw:           new Date('2026-04-19'),
    titel:              'Catering Müller AG',
    typ:                'catering',
    pax:                '60',
    ort:                'Kongresszentrum München',
    personal_einkauf:   'Max Mustermann',
    personal_kochen:    'Lisa Schmidt',
    personal_lieferung: 'Tom Wagner',
    notizen:            '3-Gang Menü, vegetarische Option nötig',
  };

  const pdfUrl = createPDF(demoAuftrag, 'test');
  sendOrdioEmail(demoAuftrag, pdfUrl);
  Logger.log('Test abgeschlossen!');
}
