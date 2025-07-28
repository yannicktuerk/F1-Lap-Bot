@echo off
echo.
echo ========================================
echo  F1 2025 UDP Telemetry Listener Setup
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Setting up configuration...
if not exist config.json (
    echo Creating config.json from template...
    copy config_example.json config.json
    echo.
    echo *** IMPORTANT: Please edit config.json with your settings! ***
    echo - Add your Discord User ID
    echo - Add your bot API URL
    echo - Set your player name
    echo.
) else (
    echo config.json already exists, skipping...
)

echo [3/3] Setup complete!
echo.
echo Next steps:
echo 1. Edit config.json with your Discord settings
echo 2. Enable UDP Telemetry in F1 2025 (Port 20777)
echo 3. Run: python udp_listener.py
echo.
echo Press any key to open config.json for editing...
pause > nul
notepad config.json

echo.
echo Setup finished! 🏁
pause
