#!/bin/bash
# ── Plaud Processor – Mac/Linux Starter ──────────────────────────────────────

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║        Plaud Processor               ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Prüfen ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "  [FEHLER] Docker läuft nicht!"
    echo "  Bitte Docker Desktop starten und dann nochmal ausführen."
    exit 1
fi

# Prüfen ob .env existiert
if [ ! -f ".env" ]; then
    echo "  [FEHLER] .env Datei fehlt!"
    echo "  Bitte ausführen: cp .env.example .env"
    echo "  Danach .env mit Ihren Zugangsdaten befüllen."
    exit 1
fi

echo "  Starte Plaud Processor..."
docker compose up -d --build

echo ""
echo "  ✓ Plaud Processor läuft im Hintergrund!"
echo ""
echo "  Nützliche Befehle:"
echo "    Logs ansehen:   docker compose logs -f"
echo "    Stoppen:        docker compose down"
echo ""
