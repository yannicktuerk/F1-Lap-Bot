@echo off
title F1 2025 UDP Telemetry Listener
color 0A

echo.
echo 🏎️  F1 2025 UDP Telemetry Listener
echo ==========================================
echo.

if not exist config.json (
    echo ❌ ERROR: config.json not found!
    echo 📝 Please run setup.bat first to configure the listener.
    echo.
    pause
    exit /b 1
)

echo 🔍 Suche nach Python Installation...
echo.

REM Try different Python paths (most common installation locations)
set PYTHON_FOUND=0

REM Microsoft Store Python (Windows 10/11)
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    echo ✅ Python gefunden: Microsoft Store Version
    set PYTHON_CMD="%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
    set PYTHON_FOUND=1
    goto :run_listener
)

REM Standard Python Installation (python.org) - User
for %%v in (312 311 310 309) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        echo ✅ Python gefunden: Python 3.%%v (User Installation)
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
        set PYTHON_FOUND=1
        goto :run_listener
    )
)

REM System-wide Python Installation
for %%v in (312 311 310 309) do (
    if exist "C:\Python%%v\python.exe" (
        echo ✅ Python gefunden: Python 3.%%v (System Installation)
        set PYTHON_CMD="C:\Python%%v\python.exe"
        set PYTHON_FOUND=1
        goto :run_listener
    )
)

REM Program Files Python
for %%v in (312 311 310) do (
    if exist "%PROGRAMFILES%\Python%%v\python.exe" (
        echo ✅ Python gefunden: Python 3.%%v (Program Files)
        set PYTHON_CMD="%PROGRAMFILES%\Python%%v\python.exe"
        set PYTHON_FOUND=1
        goto :run_listener
    )
)

REM Try 'python' command (if in PATH)
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python gefunden: Im System PATH
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    goto :run_listener
)

REM Try 'py' launcher (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python gefunden: Python Launcher
    set PYTHON_CMD=py
    set PYTHON_FOUND=1
    goto :run_listener
)

REM No Python installation found
echo.
echo ❌ FEHLER: Python nicht gefunden!
echo.
echo 🔧 Lösungsvorschläge:
echo.
echo 1️⃣  Python über Microsoft Store installieren:
echo    - Windows-Taste + "Store" öffnen
echo    - Nach "Python" suchen und installieren
echo.
echo 2️⃣  Python von python.org installieren:
echo    - Besuche: https://www.python.org/downloads/
echo    - ⚠️  WICHTIG: "Add Python to PATH" anhaken!
echo.
echo 3️⃣  Siehe detaillierte Anleitung:
echo    - Öffne: docs\python-setup-windows.md
echo.
echo 📝 Drücke eine beliebige Taste zum Beenden...
pause >nul
exit /b 1

:run_listener
echo 🚀 Starte UDP Listener...
echo.
echo 📋 Anweisungen:
echo 1. F1 2025 UDP Telemetry aktivieren (Port 20777)
echo 2. F1 2025 starten und Time Trial Mode wählen
echo 3. Runden fahren - gültige Zeiten werden automatisch übertragen!
echo.
echo 🛑 Drücke Ctrl+C zum Stoppen
echo.

%PYTHON_CMD% udp_listener.py

echo.
echo 🛑 UDP Listener gestoppt.
echo 📝 Drücke eine beliebige Taste zum Schließen...
pause >nul
