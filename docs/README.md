# F1 2025 UDP Telemetry Listener

## 🏎️ Overview

The F1 2025 UDP Telemetry Listener is an advanced telemetry processing system that captures lap times from F1 2025 Time Trial sessions and automatically submits personal best times to a Discord bot server. This system provides real-time monitoring, validation, and seamless integration with Discord communities for competitive lap time tracking.

## ✨ Features

- **Real-time F1 2025 UDP telemetry processing**
- **Time Trial session detection and monitoring**
- **Comprehensive lap time validation**
- **Personal best tracking per circuit**
- **Automatic Discord bot integration**
- **Complete track mapping for all F1 2025 circuits**
- **Sector time analysis and debugging**
- **Robust error handling and logging**

## 🚀 Quick Start

### Prerequisites

- F1 2025 game with UDP telemetry enabled
- Python 3.8 or higher
- `f1-packets` library for official packet parsing
- Discord bot server (optional, for automatic submissions)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yannicktuerk/F1-Lap-Bot.git
   cd F1-Lap-Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system:**
   ```bash
   cp config_example.json config.json
   # Edit config.json with your settings
   ```

4. **Run the telemetry listener:**
   ```bash
   python udp_listener.py
   ```

## 📖 Documentation Structure

- **[Installation Guide](installation.md)** - Detailed setup instructions
- **[Configuration Guide](configuration.md)** - Complete configuration options
- **[F1 2025 Setup](f1-setup.md)** - F1 2025 game configuration
- **[API Reference](api.md)** - Discord bot API documentation
- **[Track Mapping](tracks.md)** - Complete circuit reference
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Development](development.md)** - Contributing and development setup

## 🎯 How It Works

1. **Session Detection**: Monitors F1 2025 UDP packets for Time Trial sessions
2. **Lap Monitoring**: Processes lap data packets in real-time
3. **Validation**: Validates lap times for legitimacy (no corner cutting, flashbacks, etc.)
4. **Personal Best Tracking**: Compares new times against stored personal bests
5. **Discord Integration**: Automatically submits new PB times to Discord bot
6. **Manual Fallback**: Provides manual submission commands if bot is unavailable

## 🏁 Supported Tracks

The system supports all 23 official F1 2025 circuits plus reverse layouts:

| Track | Circuit Name | Track ID |
|-------|-------------|----------|
| Melbourne | Albert Park | 0 |
| Shanghai | Shanghai International | 2 |
| Bahrain | Sakhir | 3 |
| Spain | Catalunya | 4 |
| Monaco | Monaco | 5 |
| Canada | Montreal | 6 |
| Silverstone | Silverstone | 7 |
| Hungary | Hungaroring | 9 |
| Spa | Spa-Francorchamps | 10 |
| Monza | Monza | 11 |
| Singapore | Marina Bay | 12 |
| Japan | Suzuka | 13 |
| Abu Dhabi | Yas Marina | 14 |
| USA | Circuit of the Americas | 15 |
| Brazil | Interlagos | 16 |
| Austria | Red Bull Ring | 17 |
| Mexico | Autódromo Hermanos Rodríguez | 19 |
| Baku | Baku City Circuit | 20 |
| Netherlands | Zandvoort | 26 |
| Imola | Imola | 27 |
| Jeddah | Jeddah Corniche Circuit | 29 |
| Miami | Miami International | 30 |
| Las Vegas | Las Vegas Street Circuit | 31 |
| Qatar | Losail International | 32 |

## 🤖 Discord Bot Integration

The system can automatically submit personal best lap times to a Discord bot server. When enabled:

- ✅ New personal best times are automatically submitted
- ✅ **Sector times included** - S1, S2, S3 breakdown for detailed analysis
- ✅ Server validates and stores the lap time with sectors
- ✅ Discord channel receives notification of the new PB
- ✅ **Enhanced leaderboards** show sector times for competitive comparison
- ✅ Manual fallback available if bot is offline

### 🎯 Sector Times Support

The system now captures and transmits detailed sector breakdown:
- **Sector 1**: First third of the track
- **Sector 2**: Middle third of the track  
- **Sector 3**: Final third of the track
- **Automatic calculation** from F1 2025 telemetry data
- **Discord display** in leaderboards with `/lap leaderboard <track>`

## 🔧 Configuration Options

Key configuration parameters in `config.json`:

```json
{
  "bot_integration": true,
  "discord_user_id": "your_discord_user_id",
  "bot_api_url": "http://localhost:8080/api/telemetry/submit",
  "port": 20777,
  "player_name": "Your Name",
  "debug_mode": false
}
```

## 📊 System Architecture

```
F1 2025 Game ──UDP─→ Telemetry Listener ──HTTP─→ Discord Bot ──→ Discord Channel
                           │
                           ├─→ Session Detection
                           ├─→ Lap Validation  
                           ├─→ Personal Best Tracking
                           └─→ Error Handling
```

## 🛡️ Security & Privacy

- No sensitive game data is transmitted
- Only lap times and track names are shared
- User Discord ID is used for identification
- No personal information is stored permanently
- All communications use standard HTTP/HTTPS protocols

## 🎮 Game Requirements

- **F1 2025** game installed and running
- **UDP Telemetry enabled** in game settings
- **Time Trial mode** active
- **Network permissions** for UDP communication on port 20777

## 🔍 Troubleshooting

Common issues and solutions:

- **No telemetry data received**: Check F1 2025 UDP settings
- **Times not submitted**: Verify Discord bot configuration
- **Track not recognized**: Check track mapping or submit new mapping
- **Invalid lap detection**: Review lap validation criteria

For detailed troubleshooting, see [Troubleshooting Guide](troubleshooting.md).

## 🤝 Contributing

We welcome contributions! See [Development Guide](development.md) for:

- Setting up development environment
- Code style guidelines
- Testing procedures
- Submitting pull requests

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yannicktuerk/F1-Lap-Bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yannicktuerk/F1-Lap-Bot/discussions)
- **Discord**: Join our community Discord server

## 🏆 Acknowledgments

- **Codemasters/EA Sports** for F1 2025 and UDP telemetry support
- **f1-packets community** for the excellent packet parsing library
- **Contributors** who helped improve and test the system
- **Discord communities** using this system for competitive racing

---

**Version**: 2.0  
**Last Updated**: January 2025  
**Compatibility**: F1 2025 (all platforms)
