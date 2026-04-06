@echo off
:: ── Plaud Processor – Windows Starter ────────────────────────────────────────
title Plaud Processor

echo.
echo  ╔══════════════════════════════════════╗
echo  ║        Plaud Processor               ║
echo  ╚══════════════════════════════════════╝
echo.

:: Prüfen ob Docker läuft
docker info >nul 2>&1
if errorlevel 1 (
    echo  [FEHLER] Docker läuft nicht!
    echo  Bitte Docker Desktop starten und dann diese Datei nochmal ausführen.
    pause
    exit /b 1
)

:: Prüfen ob .env existiert
if not exist ".env" (
    echo  [FEHLER] .env Datei fehlt!
    echo  Bitte .env.example kopieren, umbenennen zu .env und ausfüllen.
    pause
    exit /b 1
)

echo  Starte Plaud Processor...
docker compose up -d --build

echo.
echo  ✓ Plaud Processor läuft im Hintergrund!
echo.
echo  Nützliche Befehle:
echo    Logs ansehen:   docker compose logs -f
echo    Stoppen:        docker compose down
echo.
pause
