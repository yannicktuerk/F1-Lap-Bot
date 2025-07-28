# Installation Guide

## 🚀 F1 2025 UDP Telemetry Listener Installation

This guide will walk you through the complete installation process of the F1 2025 UDP Telemetry Listener.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: Version 3.8 or higher
- **F1 2025 Game**: Installed and running
- **Network**: UDP port 20777 available
- **RAM**: Minimum 2GB available
- **Storage**: 500MB free space

### Required Software
- **Git**: For cloning the repository
- **Python pip**: For installing dependencies
- **Text Editor**: For configuration (VS Code, Notepad++, etc.)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/yannicktuerk/F1-Lap-Bot.git

# Navigate to the project directory
cd F1-Lap-Bot
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv f1-telemetry-env

# Activate virtual environment
# Windows:
f1-telemetry-env\Scripts\activate

# macOS/Linux:
source f1-telemetry-env/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- `f1-packets` - Official F1 2025 packet parsing
- `requests` - HTTP client for Discord bot API
- `dataclasses` - Python dataclass support

### 4. Configuration Setup

```bash
# Copy example configuration
cp config_example.json config.json

# Edit configuration file
# Use your preferred text editor
```

**config.json example:**
```json
{
    "bot_integration": true,
    "discord_user_id": "your_discord_user_id_here",
    "bot_api_url": "http://localhost:8080/api/telemetry/submit",
    "port": 20777,
    "player_name": "Your Racing Name",
    "debug_mode": false
}
```

### 5. Discord User ID Setup

**How to get your Discord User ID:**

1. **Enable Developer Mode** in Discord:
   - Go to User Settings (gear icon)
   - Appearance → Advanced → Developer Mode ✅

2. **Get Your User ID**:
   - Right-click on your username
   - Select "Copy User ID"
   - Paste into `config.json`

### 6. F1 2025 Game Configuration

**Enable UDP Telemetry:**
1. Start F1 2025
2. Go to **Settings** → **Telemetry**
3. Set **UDP Telemetry** to **On**
4. Set **UDP Port** to **20777**
5. Set **UDP IP Address** to **127.0.0.1**
6. **Save settings**

### 7. First Run Test

```bash
# Test the installation
python udp_listener.py
```

**Expected output:**
```
🏎️ F1 2025 Telemetry Listener started on port 20777
🎯 Monitoring for Time Trial sessions...
⚠️  Make sure F1 2025 UDP telemetry is enabled in game settings!
📡 Waiting for telemetry data...
```

### 8. Discord Bot Setup (Optional)

If you want automatic Discord integration:

1. **Set up Discord Bot Server** (separate installation)
2. **Configure API endpoint** in `config.json`
3. **Test connectivity** with bot server

---

## 🚀 Alternative Installation: UDP Listener Only

For users who only need the telemetry listener without the full repository:

### Method 1: Direct Download from GitHub

1. **Download `udp_listener.py`**: 
   - [Direct Download Link](https://raw.githubusercontent.com/yannicktuerk/F1-Lap-Bot/main/udp_listener.py)
   - Right-click the link and select "Save link as..."
   - Save to a folder like `C:\F1-Telemetry\` or `~/F1-Telemetry/`

2. **Download configuration template**: 
   - [config_example.json](https://raw.githubusercontent.com/yannicktuerk/F1-Lap-Bot/main/config_example.json)
   - Save in the same folder as `udp_listener.py`
   - Rename to `config.json`

### Method 2: Using Command Line

```bash
# Create project directory
mkdir F1-Telemetry
cd F1-Telemetry

# Download files directly
curl -O https://raw.githubusercontent.com/yannicktuerk/F1-Lap-Bot/main/udp_listener.py
curl -O https://raw.githubusercontent.com/yannicktuerk/F1-Lap-Bot/main/config_example.json

# Rename configuration file
mv config_example.json config.json
```

### Setup Steps for Direct Download:

**1. Create Virtual Environment (Recommended):**
```bash
# Navigate to your F1-Telemetry folder
cd F1-Telemetry

# Create virtual environment
python -m venv f1-telemetry-env

# Activate virtual environment
# Windows:
f1-telemetry-env\Scripts\activate

# macOS/Linux:
source f1-telemetry-env/bin/activate
```

**2. Install Required Dependencies:**
```bash
# Install essential packages
pip install requests f1-packets

# Verify installation
pip list
```

**3. Configure UDP Listener:**
- Edit `config.json` (see Configuration Setup section above)
- Follow F1 2025 Game Configuration steps
- Test with: `python udp_listener.py`

### Configuration for Direct Download

**Essential config.json settings:**
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

**Key Points:**
- Get `discord_user_id` from Discord Developer Mode
- Get `bot_api_url` from your Discord bot administrator
- Must end with `/api/telemetry/submit`
- `player_name` is optional (for local logs only)

### Standalone Usage (No Discord Integration)

To use the UDP listener without Discord bot integration:

```json
{
    "bot_integration": false,
    "port": 20777,
    "player_name": "YourPlayerName",
    "debug_mode": true,
    "default_track": "silverstone"
}
```

**Benefits:**
- ✅ Local lap time monitoring
- ✅ Debug output with detailed timing
- ✅ No external dependencies
- ✅ Works offline

**Limitations:**
- ❌ No automatic Discord submissions
- ❌ No leaderboard integration
- ❌ Manual lap time entry still required

## Troubleshooting Installation

### Common Issues

#### Python Not Found
```bash
# Check Python installation
python --version
# or
python3 --version

# Install Python if missing
# Download from: https://python.org/downloads/
```

#### Port 20777 Already in Use
```bash
# Check what's using the port (Windows)
netstat -an | findstr :20777

# Check what's using the port (macOS/Linux)
lsof -i :20777

# Kill process if needed
# Windows: taskkill /PID [process_id] /F
# macOS/Linux: kill -9 [process_id]
```

#### UDP Packets Not Received
1. **Check F1 2025 UDP settings** are enabled
2. **Verify port 20777** is not blocked by firewall
3. **Ensure F1 2025 is running** in Time Trial mode
4. **Check network interface** (use 0.0.0.0 instead of 127.0.0.1)

#### Dependencies Installation Failed
```bash
# Update pip first
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Install individual packages if needed
pip install f1-packets requests
```

#### Permission Errors
```bash
# Windows: Run Command Prompt as Administrator
# macOS/Linux: Use sudo if needed
sudo pip install -r requirements.txt
```

### Network Firewall Configuration

**Windows Firewall:**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Add Python.exe to allowed programs
4. Enable for both Private and Public networks

**macOS Firewall:**
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Add Python to allowed applications

**Linux (ufw):**
```bash
# Allow UDP traffic on port 20777
sudo ufw allow 20777/udp
```

## Verification

### Test Installation Success

1. **Start F1 2025** in Time Trial mode
2. **Run telemetry listener**: `python udp_listener.py`
3. **Complete a lap** in F1 2025
4. **Check console output** for lap detection

**Success indicators:**
- ✅ Session detection: "TIME TRIAL SESSION DETECTED!"
- ✅ Lap data: "LAP DATA DEBUG" with timing information
- ✅ Valid lap completion: "Valid lap completed!"

### Performance Check

Monitor system resources:
- **CPU Usage**: Should be < 5% during normal operation
- **Memory Usage**: Should be < 100MB
- **Network**: UDP packets every ~16ms during active session

## Post-Installation

### Next Steps

1. **Read Configuration Guide** for advanced settings
2. **Set up Discord Bot** for automatic submissions
3. **Join F1 Community** for competitive racing
4. **Explore Analytics Features** for performance tracking

### Updates

```bash
# Check for updates
git fetch origin main
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
```

### Backup Configuration

```bash
# Backup your settings
cp config.json config_backup.json

# Backup personal bests (if stored locally)
cp personal_bests.json personal_bests_backup.json
```

## Support

If you encounter issues during installation:

- **Check logs** in console output
- **Review troubleshooting** section above
- **Submit GitHub issue** with error details
- **Join Discord community** for live support

---

**Installation complete!** 🏁 You're ready to start tracking F1 2025 lap times!
