# F1 2025 UDP Telemetry Listener v3.0

**New in v3.0:** Full telemetry capture for Mathe-Coach physics-based coaching!

## What's New?

### v3.0 Features
- ✅ **Full Telemetry Capture**: Records Position, Velocity, G-Forces, Inputs (300-500 samples per lap)
- ✅ **Session Tracking**: Automatically links sessions to your Discord user ID
- ✅ **Mathe-Coach Ready**: Telemetry traces enable physics-based coaching analysis
- ✅ **Backward Compatible**: Still submits lap times to leaderboards

### What It Captures
- **Motion Data**: World position (X,Y,Z), velocity (X,Y,Z), g-forces, yaw
- **Car Telemetry**: Speed, throttle, brake, steering, gear, RPM, DRS
- **Lap Data**: Lap distance, lap number, sector times

## Installation

### Requirements
```bash
pip install f1-packets requests
```

### Configuration

Create/Update `config.json`:
```json
{
    "discord_user_id": "YOUR_DISCORD_USER_ID",
    "bot_api_url": "http://localhost:8080",
    "port": 20777,
    "bot_integration": true
}
```

**How to get your Discord User ID:**
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your username → Copy User ID

## Usage

### Start Listener
```bash
python telemetry_listener_v3.py
```

### In F1 2025
1. **Settings** → **Telemetry Settings**
2. Enable **UDP Telemetry**
3. Set **Port**: `20777`
4. Set **Format**: `2025`
5. Set **IP**: `127.0.0.1` (localhost)

### Play Time Trial
- Drive laps in **Time Trial mode** only
- Listener captures telemetry automatically
- Personal bests are submitted to Discord bot

## How It Works

### Workflow
1. **Session Start**: Detects Time Trial session → Registers with bot (session_uid + user_id)
2. **During Lap**: Captures telemetry from F1 25 UDP packets every frame
3. **Lap Complete**: Validates lap → Submits to bot:
   - Lap time → Leaderboard (if personal best)
   - Telemetry trace → Database (for Mathe-Coach)

### Packet Types Captured
- **Packet ID 0**: Motion Data (Position, Velocity, G-Forces)
- **Packet ID 1**: Session Data (Track, Session Type)
- **Packet ID 2**: Lap Data (Lap Number, Distance, Sectors)
- **Packet ID 6**: Car Telemetry (Speed, Inputs, RPM)

### Lap Validation
Only valid laps are submitted:
- ✅ No corner cutting
- ✅ No penalties
- ✅ No flashbacks
- ✅ Time range: 30s - 5min

## API Endpoints

### Leaderboard Submission
```http
POST /api/telemetry/submit
{
  "time": "1:23.456",
  "track": "monaco",
  "user_id": "123456789",
  "sector_times": { "sector1_ms": 25000, ... }
}
```

### Session Registration
```http
POST /api/telemetry/session/register
{
  "session_uid": 12345,
  "track_id": "monaco",
  "session_type": 18,
  "user_id": "123456789"
}
```

### Telemetry Trace Submission
```http
POST /api/telemetry/trace
{
  "session_uid": 12345,
  "track_id": "monaco",
  "lap_number": 5,
  "lap_time_ms": 83456,
  "user_id": "123456789",
  "telemetry_samples": [
    {
      "timestamp_ms": 1000,
      "world_position_x": 123.4,
      "speed": 280.5,
      "throttle": 1.0,
      ...
    },
    // 300-500 more samples
  ]
}
```

## Troubleshooting

### No telemetry data captured
- Check F1 2025 UDP settings (port 20777, format 2025)
- Ensure listener is running BEFORE starting Time Trial
- Verify Windows Firewall allows Python

### Lap not submitted
- Only **personal bests** are submitted to leaderboard
- Only **valid laps** are submitted (no penalties/corner cutting)
- Check listener console output for validation messages

### Mathe-Coach shows "No sessions found"
- Verify `user_id` in config.json matches your Discord user ID
- Check bot API is running (`http://localhost:8080/api/health`)
- Ensure you've completed at least 3 valid laps

## Migration from v2.0

### Differences
| Feature | v2.0 | v3.0 |
|---------|------|------|
| Lap Times | ✅ | ✅ |
| Leaderboards | ✅ | ✅ |
| Telemetry Traces | ❌ | ✅ |
| Mathe-Coach Support | ❌ | ✅ |
| Session Tracking | ❌ | ✅ |

### Upgrade Steps
1. Install new dependencies: `pip install f1-packets`
2. Update `config.json` (add `user_id` if not present)
3. Run `python telemetry_listener_v3.py`
4. Old listener still works for lap times only

## Performance

### Telemetry Capture Rate
- **~60 Hz** (every F1 25 UDP packet)
- **300-500 samples** per lap (depends on track length)
- **~50-100 KB** per lap trace (compressed JSON)

### Network Usage
- Lap time: ~500 bytes
- Telemetry trace: ~50-100 KB
- Minimal bandwidth required

## Support

### Logs
Check console output for:
- Session detection
- Lap completion
- Submission success/failure
- Sample count per lap

### Common Issues
- **"f1-packets not found"**: Run `pip install f1-packets`
- **"Cannot connect to bot server"**: Check `bot_api_url` in config.json
- **"Session registered but no traces"**: Ensure 3+ valid laps driven

---

**Made with ❤️ for the F1 gaming community**

[⭐ Star the repo](https://github.com/yannicktuerk/F1-Lap-Bot) • [🐛 Report Issues](https://github.com/yannicktuerk/F1-Lap-Bot/issues)
