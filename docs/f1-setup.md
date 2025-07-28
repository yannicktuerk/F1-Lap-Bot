# F1 2025 Game Setup Guide

## 🎮 F1 2025 UDP Telemetry Configuration

This guide covers how to properly configure F1 2025 for UDP telemetry integration with the lap time tracking system.

## Game Settings Overview

The F1 2025 UDP Telemetry Listener requires specific game settings to function correctly. Follow these steps to enable telemetry data transmission.

## Step-by-Step Setup

### 1. Launch F1 2025

- Start F1 2025 game
- Wait for the main menu to load completely
- Ensure the game is running in stable mode (not crashed/frozen)

### 2. Access Game Settings

1. **Navigate to Settings**:
   - From the main menu, select **"Settings"**
   - Or press the settings button (gear icon)

2. **Find Telemetry Settings**:
   - Look for **"Telemetry"** or **"Online"** section
   - May be under **"Advanced Settings"** or **"Data"**
   - Settings location can vary by platform

### 3. Configure UDP Telemetry

#### Essential Settings

**UDP Telemetry**: `ON` ✅
- **Description**: Enables real-time data transmission
- **Required**: Must be enabled
- **Impact**: Without this, no data will be sent

**UDP Port**: `20777`
- **Description**: Network port for data transmission
- **Default**: Usually 20777
- **Note**: Must match your config.json port setting

**UDP IP Address**: `127.0.0.1`
- **Description**: Destination IP for telemetry data
- **Local Setup**: Use `127.0.0.1` (localhost)
- **Network Setup**: Use your computer's IP address

**UDP Format**: `F1 2025` or `Latest`
- **Description**: Data packet format version
- **Required**: Must be F1 2025 format
- **Note**: Older formats (F1 2024, etc.) are not supported

#### Advanced Settings

**Telemetry Frequency**: `60Hz` (Recommended)
- **Options**: 10Hz, 20Hz, 60Hz
- **Recommended**: 60Hz for real-time tracking
- **Performance**: Higher frequency = more CPU usage

**Send Data Rate**: `Maximum` or `High`
- **Description**: How often packets are sent
- **Recommended**: Maximum for best accuracy
- **Note**: May impact game performance on older systems

### 4. Platform-Specific Instructions

#### PC (Windows/Steam)

1. **Steam Version**:
   - Launch through Steam
   - Settings → Telemetry
   - Enable all UDP options

2. **EA App Version**:
   - Launch through EA App
   - Same telemetry settings apply
   - May require EA account login

3. **Game Pass Version**:
   - Settings identical to other PC versions
   - Ensure Windows firewall allows UDP traffic

#### PlayStation 5

1. **Access Settings**:
   - Main menu → Settings → Telemetry
   - Enable UDP Telemetry

2. **Network Configuration**:
   - Use PlayStation's IP address as destination
   - Configure port forwarding if needed
   - Check PlayStation network settings

#### Xbox Series X/S

1. **Game Settings**:
   - Settings → Online → Telemetry
   - Enable UDP output

2. **Network Setup**:
   - Use Xbox IP address
   - Configure network sharing if needed
   - Check Xbox network configuration

### 5. Verify Settings

After configuration, verify your settings:

**In-Game Verification**:
- Settings should show UDP Telemetry as `ON`
- Port should be `20777`
- IP should be correct for your setup

**Test Connection**:
- Start a Time Trial session
- Run the UDP listener
- Check for "Session detected" messages

## Network Configuration

### Local Setup (Same Computer)

**IP Address**: `127.0.0.1`
- **Usage**: Game and listener on same computer
- **Advantages**: No network configuration needed
- **Disadvantages**: Limited to single machine

### Network Setup (Different Computers)

**Find Your Computer's IP**:

**Windows**:
```cmd
ipconfig
# Look for IPv4 Address under your active connection
```

**macOS/Linux**:
```bash
ifconfig
# Look for inet address
```

**Router Configuration**:
- May need to configure firewall rules
- Ensure UDP port 20777 is open
- Check router security settings

### Firewall Configuration

#### Windows Firewall

1. **Open Windows Security**
2. **Firewall & Network Protection**
3. **Allow an app through firewall**
4. **Add F1 2025** to allowed programs
5. **Enable for both Private and Public networks**

#### Router Firewall

1. **Access router admin panel**
2. **Find Port Forwarding or Firewall settings**
3. **Allow UDP traffic on port 20777**
4. **Set destination to your computer's IP**

## Game Mode Requirements

### Time Trial Mode

**Required for lap tracking**:
- Only Time Trial sessions are monitored
- Other modes (Race, Practice, etc.) are ignored
- Ensure you're in actual Time Trial, not Quick Race

**Session Setup**:
1. **Select Time Trial** from main menu
2. **Choose any track** (all supported)
3. **Select any car** (telemetry works with all)
4. **Start session** and begin driving

### Supported Game Modes

**✅ Supported**:
- Time Trial (Primary)
- Grand Prix Time Trial
- Custom Time Trial sessions

**❌ Not Supported**:
- Race weekends
- Career mode
- Multiplayer sessions
- Practice sessions (by design)

## Telemetry Data Types

### What Data is Captured

**Lap Information**:
- Complete lap times
- Sector 1, 2, 3 times
- Lap validity status
- Current lap progress

**Session Information**:
- Track identification
- Session type detection
- Weather conditions
- Track temperature

**Car Status**:
- Speed and position
- Penalties applied
- Pit status
- Driver status

### What Data is NOT Captured

**Personal Information**:
- No personal data
- No account information
- No voice/chat data

**Sensitive Game Data**:
- No save game modification
- No game file access
- No anti-cheat interference

## Troubleshooting Game Setup

### Common Issues

#### "No Telemetry Data Received"

**Check Game Settings**:
- Verify UDP Telemetry is `ON`
- Confirm port is `20777`
- Check IP address is correct

**Test Network**:
```bash
# Test if port is open (Windows)
netstat -an | findstr :20777

# Test if port is open (macOS/Linux)
lsof -i :20777
```

#### "Session Not Detected"

**Verify Session Type**:
- Must be in Time Trial mode
- Not Practice or Race mode
- Session must be actively running

**Check Track Support**:
- All official F1 2025 tracks are supported
- Custom tracks may not be recognized
- DLC tracks should work if mapped

#### "Invalid Lap Times"

**Game-side Issues**:
- Check for game updates
- Verify telemetry format is F1 2025
- Restart game to reset telemetry

**Validation Issues**:
- Times must be realistic (30s - 5min)
- No corner cutting penalties
- No flashback usage during lap

### Performance Issues

#### Game Stuttering with Telemetry

**Reduce Telemetry Frequency**:
- Change from 60Hz to 20Hz
- Monitor system performance
- Adjust based on hardware

**System Resources**:
- Close unnecessary programs
- Ensure adequate RAM
- Check CPU usage

#### Network Lag

**Local Network**:
- Use wired connection if possible
- Check WiFi signal strength
- Restart router if needed

**Internet Connection**:
- Not required for local setup
- Only needed for Discord bot integration
- Check bandwidth if using remote bot

## Advanced Configuration

### Multiple Computers Setup

**Game Computer** (F1 2025):
- Configure UDP to send to listener computer IP
- Ensure firewall allows outbound UDP

**Listener Computer** (UDP Listener):
- Configure to receive from game computer
- Set appropriate IP in configuration
- Test network connectivity

### Professional Racing Setup

**Dedicated Racing Rig**:
- Game on primary gaming computer
- Telemetry processing on secondary computer
- Network setup for real-time data

**Streaming Setup**:
- Game with OBS/Streamlabs
- Telemetry data for overlay information
- Discord integration for community

## Verification Checklist

Before starting, verify:

- ✅ **F1 2025 installed** and updated
- ✅ **UDP Telemetry enabled** in game settings
- ✅ **Port 20777 configured** correctly
- ✅ **IP address set** appropriately
- ✅ **Time Trial mode** accessible
- ✅ **Network connectivity** working
- ✅ **Firewall configured** for UDP traffic
- ✅ **UDP Listener ready** to receive data

## Getting Help

### Game-Specific Issues

- **F1 2025 Forums**: Official EA/Codemasters support
- **Steam Community**: Steam-specific issues
- **Platform Support**: PlayStation/Xbox network issues

### Telemetry Integration Issues

- **GitHub Issues**: Technical problems with UDP listener
- **Discord Community**: Real-time help and support
- **Documentation**: Check troubleshooting guides

---

**F1 2025 setup complete!** 🏁 Your game is now ready to transmit telemetry data for lap time tracking!
