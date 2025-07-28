# 🏁 F1 UDP Telemetrie - Quick Reference

> **⚡ Schnelle Übersicht für erfahrene User**

## 🚀 **Setup in 5 Minuten:**

### 1. **Prerequisites:**
```bash
# Python 3.10+ installieren
python --version

# Repository klonen
git clone https://github.com/yannicktuerk/F1-Lap-Bot.git
cd F1-Lap-Bot
git checkout develop-v2-udp-telemetry

# Dependencies
pip install -r requirements.txt
```

### 2. **Config erstellen:**
```bash
cp config_example.json config.json
```

**config.json:**
```json
{
    "discord_user_id": "YOUR_18_DIGIT_DISCORD_ID",
    "bot_api_url": "http://159.69.90.26:5000/api/telemetry/submit",
    "port": 20777,
    "bot_integration": true,
    "player_name": "YourName"
}
```

### 3. **F1 2025 Settings:**
```
UDP Telemetrie: ON
UDP IP: 127.0.0.1
UDP Port: 20777
Format: 2025
All Data: ON
```

### 4. **Start:**
```bash
python udp_listener.py
```

### 5. **Test:**
- F1 2025 → Time Trial → Drive valid lap
- ✅ Automatic submission to Discord bot

---

## 🛠️ **Commands:**

| Command | Description |
|---------|-------------|
| `python udp_listener.py` | Start UDP listener |
| `python api_server_standalone.py` | Start API server only |
| `curl http://159.69.90.26:5000/api/health` | Test server health |

---

## 🎯 **Discord User ID:**
1. Discord → Settings → Advanced → Developer Mode ✅
2. Right-click your name → "Copy User ID"

---

## 📡 **Server Endpoints:**
- **Health**: http://159.69.90.26:5000/api/health
- **Status**: http://159.69.90.26:5000/api/status  
- **Submit**: http://159.69.90.26:5000/api/telemetry/submit

---

## 🚨 **Common Issues:**

| Problem | Solution |
|---------|----------|
| `python not found` | Add Python to PATH |
| `No telemetry data` | Check F1 2025 UDP settings |
| `Invalid laps` | Use Time Trial mode, no corner cuts |
| `Server error` | Check internet + config.json |

---

## ✅ **Optimal Settings:**

**F1 2025:**
- Mode: Time Trial (not Practice!)
- UDP IP: 127.0.0.1 
- UDP Port: 20777

**Best Test Track:** Monaco (short laps)

---

**🏎️ Happy Racing!**
