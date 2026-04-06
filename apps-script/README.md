# Apps Script – Einrichtung

## Schritt-für-Schritt

### 1. Google Sheet erstellen

Neues Sheet mit diesen Spalten (Zeile 1 = Header):

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Datum | Titel | Typ | Pax | Ort | Einkauf-Personal | Koch-Personal | Liefer-Personal | Status | Notizen |

**Typ-Werte:** `catering`, `event`, `other`

### 2. Google Form verknüpfen

- Im Sheet: **Einfügen → Formular**
- Felder anlegen (entsprechen den Sheet-Spalten)
- Form mit Sheet verknüpfen → Antworten landen direkt im Sheet

### 3. Apps Script einfügen

- Im Sheet: **Erweiterungen → Apps Script**
- Inhalt von `automation.gs` einfügen
- `DEINE_EMAIL` ersetzen
- **Speichern**

### 4. Trigger einrichten

- In Apps Script: **Trigger** (Uhr-Symbol links)
- **Trigger hinzufügen:**
  - Funktion: `onFormSubmit`
  - Event-Typ: `Beim Absenden des Formulars`
- Berechtigungen bestätigen

### 5. Testen

- In Apps Script: Funktion `testMitDemoAuftrag` auswählen → **Ausführen**
- Prüfe deine E-Mail und Google Drive (Ordner "Catering Aufträge")

---

## Ordio – Workaround

Da Ordio keine öffentliche API hat, bekommst du pro neuem Auftrag eine E-Mail mit:

- **Tagesnotiz** (fertig zum kopieren)
- **3 Personalslots** mit Person, Datum und Bezeichnung

Das Eintragen dauert ~2 Minuten. Wenn Ordio später eine API veröffentlicht, kann dieser Schritt vollautomatisiert werden.
