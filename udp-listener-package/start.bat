@echo off
echo.
echo ==========================================
echo  F1 2025 UDP Telemetry Listener
echo ==========================================
echo.

if not exist config.json (
    echo ERROR: config.json not found!
    echo Please run setup.bat first to configure the listener.
    echo.
    pause
    exit /b 1
)

echo Starting UDP Telemetry Listener...
echo.
echo Instructions:
echo 1. Make sure F1 2025 UDP Telemetry is enabled (Port 20777)
echo 2. Start F1 2025 and go to Time Trial mode
echo 3. Drive laps - valid times will be automatically submitted!
echo.
echo Press Ctrl+C to stop the listener
echo.

python udp_listener.py

echo.
echo UDP Listener stopped.
pause
