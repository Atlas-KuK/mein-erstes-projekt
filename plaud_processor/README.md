# Plaud Processor

Automatische Verarbeitung von [Plaud.ai](https://www.plaud.ai) Audioaufnahmen:

1. **Abrufen** – Plaud.ai API oder lokaler Ordner-Watch
2. **Transkription** – OpenAI Whisper
3. **KI-Analyse** – Claude (Anthropic): Zusammenfassung, Kernaussagen, Action Items, Entscheidungen
4. **PDF-Bericht** – professionell gestaltetes Dokument
5. **OneDrive** – automatischer Upload in konfigurierten Ordner
6. **E-Mail** – kurze Benachrichtigung (max. 1x pro Stunde)

---

## Schnellstart

### 1. Voraussetzungen

- Python 3.10+
- `ffmpeg` (optional, für Aufnahmen > 25 MB): `brew install ffmpeg` / `apt install ffmpeg`

### 2. Installation

```bash
cd plaud_processor
pip install -r requirements.txt
```

### 3. Konfiguration

```bash
cp .env.example .env
# .env mit Editor öffnen und Werte eintragen
```

Mindestens erforderlich:
- `PLAUD_API_TOKEN` **oder** `PLAUD_WATCH_FOLDER`
- `OPENAI_API_KEY` (Transkription)
- `ANTHROPIC_API_KEY` (KI-Analyse)
- OneDrive-Zugangsdaten
- SMTP-Zugangsdaten

### 4. Ausführen

```bash
# Einmaliger Lauf
python main.py

# Dauerhafter Polling-Betrieb (alle 5 Minuten)
python main.py --loop
```

---

## Plaud.ai Anbindung

### Option A: API-Token
Das API-Token finden Sie in der Plaud-App unter **Einstellungen → Konto → API**.

### Option B: Ordner-Watch
1. Plaud-App öffnen
2. Aufnahme auswählen → **Exportieren → Audiodatei**
3. In den konfigurierten `PLAUD_WATCH_FOLDER` speichern

Der Prozessor erkennt alle neuen Dateien im Ordner automatisch.

---

## OneDrive-Einrichtung (Azure App-Registrierung)

1. [Azure Portal](https://portal.azure.com) → **Azure Active Directory → App-Registrierungen → Neue Registrierung**
2. Name: z. B. `Plaud Processor`
3. **Zertifikate & Geheimnisse → Neuer geheimer Clientschlüssel** → Wert notieren
4. **API-Berechtigungen → Hinzufügen → Microsoft Graph → Anwendungsberechtigungen → `Files.ReadWrite.All`**
5. **Administratoreinwilligung erteilen**
6. **Übersicht**: `Anwendungs-ID` = `ONEDRIVE_CLIENT_ID`, `Verzeichnis-ID` = `ONEDRIVE_TENANT_ID`

---

## Automatisch als Systemdienst einrichten

### macOS (launchd)

```xml
<!-- ~/Library/LaunchAgents/com.plaud.processor.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>             <string>com.plaud.processor</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/pfad/zu/plaud_processor/main.py</string>
    <string>--loop</string>
  </array>
  <key>RunAtLoad</key>         <true/>
  <key>KeepAlive</key>         <true/>
  <key>StandardOutPath</key>   <string>/tmp/plaud_processor/stdout.log</string>
  <key>StandardErrorPath</key> <string>/tmp/plaud_processor/stderr.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.plaud.processor.plist
```

### Linux (systemd)

```ini
# /etc/systemd/system/plaud-processor.service
[Unit]
Description=Plaud Processor
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /pfad/zu/plaud_processor/main.py --loop
WorkingDirectory=/pfad/zu/plaud_processor
Restart=on-failure
User=IhrBenutzer

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now plaud-processor
```

### Windows (Aufgabenplanung)
Verwenden Sie den Windows Aufgabenplaner mit dem Trigger "Bei Systemstart"
und dem Programm `python` mit dem Argument `C:\Pfad\plaud_processor\main.py --loop`.

---

## Logs

Logs werden gespeichert in: `WORK_DIR/plaud_processor.log` (Standard: `/tmp/plaud_processor/`)

---

## Dateistruktur

```
plaud_processor/
├── main.py              # Hauptprogramm / Scheduler
├── config.py            # Konfiguration aus .env
├── plaud_client.py      # Plaud.ai API & Ordner-Watch
├── transcriber.py       # Whisper-Transkription
├── analyzer.py          # Claude KI-Analyse
├── pdf_generator.py     # PDF-Bericht erstellen
├── onedrive_client.py   # OneDrive Upload
├── email_notifier.py    # E-Mail mit Rate-Limiting
├── requirements.txt
└── .env.example
```
