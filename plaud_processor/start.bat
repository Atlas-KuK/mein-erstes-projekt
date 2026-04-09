@echo off
echo ============================================
echo   Plaud Audio Processor - Starten
echo ============================================
echo.

REM Pruefen ob Docker laeuft
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Docker Desktop ist nicht gestartet!
    echo Bitte Docker Desktop starten und warten bis es bereit ist.
    echo.
    pause
    exit /b 1
)

REM Pruefen ob .env existiert
if not exist .env (
    echo HINWEIS: Keine .env Datei gefunden.
    echo Kopiere .env.example nach .env...
    copy .env.example .env
    echo.
    echo WICHTIG: Bitte .env Datei bearbeiten und anpassen!
    echo   - Windows-Benutzernamen setzen (echo %%USERNAME%%)
    echo   - E-Mail-Einstellungen konfigurieren
    echo.
    notepad .env
    pause
)

echo Starte Ollama (falls nicht bereits gestartet)...
start /B ollama serve >nul 2>&1

echo.
echo Starte Docker Container...
docker compose up -d --build

echo.
echo ============================================
echo   System gestartet!
echo   Web-UI: http://localhost:8080
echo ============================================
echo.
echo Druecke eine Taste um die Logs anzuzeigen...
pause >nul
docker compose logs -f
