# 🏎️ F1 2025 UDP Telemetry Listener - Standalone Package

This package contains everything you need to capture F1 2025 lap times and automatically submit them to your Discord bot.

## 📦 Package Contents

- `udp_listener.py` - Main telemetry listener script
- `config_example.json` - Configuration template
- `requirements.txt` - Python dependencies
- `README.md` - This file

## 🚀 Quick Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Listener

1. **Rename configuration file:**
   ```bash
   mv config_example.json config.json
   ```

2. **Edit config.json with your settings:**
   ```json
   {
       "bot_integration": true,
       "discord_user_id": "YOUR_DISCORD_USER_ID",
       "bot_api_url": "YOUR_BOT_SERVER_URL/api/telemetry/submit",
       "port": 20777,
       "player_name": "YourPlayerName",
       "debug_mode": false
   }
   ```

### 3. Setup F1 2025 Game

1. **Start F1 2025**
2. **Go to Settings → Telemetry**
3. **Enable UDP Telemetry:** `ON`
4. **Set UDP Port:** `20777`
5. **Set UDP IP:** `127.0.0.1`
6. **Save settings**

### 4. Run the Listener

```bash
python udp_listener.py
```

## ⚙️ Configuration Options

### Required Settings (for Discord integration):

- **`discord_user_id`**: Your Discord User ID (18 digits)
  - Enable Developer Mode in Discord
  - Right-click your name → "Copy User ID"

- **`bot_api_url`**: Discord bot server URL
  - Get this from your bot administrator
  - Must end with `/api/telemetry/submit`
  - Example: `https://your-bot.herokuapp.com/api/telemetry/submit`

### Optional Settings:

- **`player_name`**: Display name for logs (optional)
- **`debug_mode`**: Enable verbose logging (`true`/`false`)
- **`port`**: UDP port (default: `20777`)

### Standalone Mode (No Discord):

```json
{
    "bot_integration": false,
    "port": 20777,
    "player_name": "YourPlayerName",
    "debug_mode": true
}
```

## 🎮 Usage

1. **Start the UDP listener BEFORE starting F1 2025**
2. **Launch F1 2025 and go to Time Trial mode**
3. **Select any track and start driving**
4. **Valid lap times will be automatically detected and submitted**

## ✅ What Gets Captured

- ✅ Time Trial sessions only
- ✅ Valid laps (no corner cutting, penalties, etc.)
- ✅ Lap times between 30 seconds and 5 minutes
- ✅ Complete sector times (S1, S2, S3)
- ✅ Track identification

## ❌ What Gets Ignored

- ❌ Race/Practice sessions
- ❌ Invalid laps with penalties
- ❌ Flashback usage during lap
- ❌ Unrealistic lap times

## 🔧 Troubleshooting

### No Telemetry Data Received
- ✅ Check F1 2025 UDP settings are enabled
- ✅ Verify port 20777 is available
- ✅ Ensure you're in Time Trial mode
- ✅ Start UDP listener before F1 2025

### Lap Times Not Submitted to Discord
- ✅ Check `discord_user_id` is correct
- ✅ Verify `bot_api_url` is correct
- ✅ Ensure bot server is running
- ✅ Check internet connection

### Permission Errors
- ✅ Run Command Prompt as Administrator (Windows)
- ✅ Use `sudo` if needed (macOS/Linux)

## 📞 Support

For support and detailed documentation:
- **GitHub**: https://github.com/yannicktuerk/F1-Lap-Bot
- **Installation Guide**: https://github.com/yannicktuerk/F1-Lap-Bot/blob/main/docs/installation.md
- **Configuration Guide**: https://github.com/yannicktuerk/F1-Lap-Bot/blob/main/docs/configuration.md

---

**🏁 Ready to race? Start your engines and track those lap times!**
