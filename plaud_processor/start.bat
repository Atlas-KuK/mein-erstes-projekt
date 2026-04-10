@echo off
chcp 65001 >nul
echo ============================================================
echo  Plaud Audio Processor – Starter
echo ============================================================
echo.

REM Prüfen ob Docker Desktop läuft
docker info >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Docker Desktop läuft nicht!
    echo Bitte Docker Desktop starten und erneut versuchen.
    pause
    exit /b 1
)

REM Prüfen ob .env vorhanden
if not exist ".env" (
    echo FEHLER: .env Datei nicht gefunden!
    echo Bitte .env.example nach .env kopieren und anpassen:
    echo   copy .env.example .env
    echo   notepad .env
    pause
    exit /b 1
)

echo Starte Plaud Audio Processor...
echo.
docker compose up -d --build

if errorlevel 1 (
    echo.
    echo FEHLER beim Starten. Logs anzeigen:
    docker compose logs --tail=50
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  System gestartet!
echo  Web-UI:  http://localhost:8080
echo  Logs:    docker compose logs -f
echo  Stoppen: docker compose down
echo ============================================================
echo.

REM Web-UI im Browser öffnen
timeout /t 3 /nobreak >nul
start http://localhost:8080

pause
