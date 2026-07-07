# Angebots-Suche auf dem Hetzner-Server einrichten

Schritt-für-Schritt-Anleitung (Ubuntu/Debian). Alles per SSH auf dem Server
ausführen. Zeilen, die mit `#` beginnen, sind nur Erklärungen.

## 1. Vorbereitung (einmalig)

```bash
sudo apt update
sudo apt install -y python3-venv git
```

## 2. Projekt holen

```bash
cd ~
git clone https://github.com/Atlas-KuK/mein-erstes-projekt.git
cd mein-erstes-projekt
```

## 3. Python-Umgebung anlegen

```bash
python3 -m venv venv
venv/bin/pip install requests flask gunicorn
```

## 4. Schlüssel-Datei anlegen

```bash
nano marktguru_keys.txt
```

Inhalt (deine echten Werte aus dem Browser, F12 → Netzwerk → Suche auf
marktguru.de → Request-Header `x-apikey` / `x-clientkey`):

```
apikey=HIER_DEIN_X_APIKEY
clientkey=HIER_DEIN_X_CLIENTKEY
```

Speichern: `Strg+O`, `Enter`, dann `Strg+X`.

## 5. Einmal testen

```bash
venv/bin/python collect.py
```

Es sollten Zeilen wie `58675 / 'krombacher': 3 Treffer, 3 neu` durchlaufen.
Danach existiert die Datenbank `angebote.db`.

## 6. Web-Oberfläche als Dienst einrichten (läuft dauerhaft)

```bash
sudo nano /etc/systemd/system/angebote.service
```

Inhalt (Benutzername ggf. anpassen – `whoami` zeigt ihn dir):

```ini
[Unit]
Description=Angebots-Suche (marktguru)
After=network.target

[Service]
User=DEIN_BENUTZER
WorkingDirectory=/home/DEIN_BENUTZER/mein-erstes-projekt
ExecStart=/home/DEIN_BENUTZER/mein-erstes-projekt/venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now angebote
sudo systemctl status angebote     # muss "active (running)" zeigen
```

## 7. Von deinem PC aus aufrufen

Der Dienst lauscht absichtlich nur auf dem Server selbst (127.0.0.1),
damit nicht das ganze Internet darauf zugreifen kann. Zwei Möglichkeiten:

**A) SSH-Tunnel (einfach & sicher, keine weitere Einrichtung):**

Auf deinem Windows-PC in PowerShell:

```
ssh -L 8080:localhost:8080 DEIN_BENUTZER@DEINE_SERVER_IP
```

Dann im Browser öffnen: <http://localhost:8080>

**B) Öffentlich mit Passwortschutz:** dafür einen Reverse-Proxy
(z. B. Caddy oder nginx mit Basic-Auth) davorschalten. Wenn du das willst,
sag Bescheid – das richten wir dann gemeinsam ein.

## 8. Tägliche Preis-Sammlung per Cron (für die Historie)

```bash
crontab -e
```

Diese Zeile ans Ende (sammelt jeden Morgen um 7 Uhr; Pfade anpassen):

```
0 7 * * * cd /home/DEIN_BENUTZER/mein-erstes-projekt && venv/bin/python collect.py >> collect.log 2>&1
```

Mehrere PLZ? Einfach anhängen: `... collect.py 58675 58636 ...`

## 9. Später aktualisieren

```bash
cd ~/mein-erstes-projekt
git pull
sudo systemctl restart angebote
```

## Dateien-Überblick

| Datei | Zweck |
|---|---|
| `app.py` | Web-Oberfläche (Suche + Historie) |
| `collect.py` | täglicher Sammler für die Preis-Historie |
| `marktguru_client.py` | Anbindung an die marktguru-API |
| `storage.py` | Datenbank (SQLite, Datei `angebote.db`) |
| `produkte.txt` | deine Produktliste – frei editierbar |
| `marktguru_keys.txt` | deine zwei Schlüssel (nur auf dem Server, nicht in Git) |
| `marktguru_test.py` | das ursprüngliche Test-Skript (bleibt als Einzeltest) |
