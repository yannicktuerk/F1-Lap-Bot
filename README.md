# 🏎️ F1 Lap Bot

Track F1 2025 lap times with automatic telemetry integration, Discord leaderboards, ELO ratings, and physics-based coaching powered by Clean Architecture.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.0%2B-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

### 🏁 Core Functionality
- **Automatic Telemetry** - Real-time lap capture from F1 2025 via UDP
- **Leaderboards** - Track-specific rankings with personal bests
- **ELO Rating System** - AI-powered skill assessment (800-2200+ ELO)
- **Advanced Analytics** - Hall of Fame, Track Heatmap, Driver Rivalries
- **Physics-Based Coaching** - Mathe-Coach analyzes laps and provides actionable feedback

### 🎮 Discord Commands
```
/lap submit <time> <track>      # Submit lap time
/lap leaderboard <track>         # View rankings
/lap rating                      # Your ELO rating
/lap analytics                   # Advanced stats
/lap coach <session_uid>         # Get physics-based coaching
```

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yannicktuerk/F1-Lap-Bot.git
cd f1-lap-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your Discord bot token
```

### 4. Run Bot
```bash
python src/main.py
```

## 🎮 F1 2025 Telemetry Setup

### In-Game Configuration
1. **F1 2025** → **Settings** → **Telemetry Settings**
2. Enable **UDP Telemetry**:
   - Port: `20777`
   - Format: `2025`
   - IP: `127.0.0.1`

### UDP Listener Setup
1. Download [UDP Listener](https://github.com/yannicktuerk/F1-Lap-Bot/raw/main/f1-udp-listener-v1.2.zip)
2. Extract and edit `config.json`:
```json
{
    "discord_user_id": "YOUR_DISCORD_USER_ID",
    "bot_api_url": "ASK_BOT_ADMIN_FOR_URL",
    "port": 20777,
    "bot_integration": true
}
```
3. Run `python udp_listener.py`

**Supported:** Time Trial mode only  
**Validation:** No corner cuts, flashbacks, or penalties

## 🏆 ELO Rating System

The bot uses intelligent ELO ratings (800-2200+) with 7 skill tiers:

| ELO Range | Rank | Description |
|-----------|------|-------------|
| 2200+ | 👑 Legendary | Absolute elite |
| 2000-2199 | 🔥 Master | Consistently fast |
| 1800-1999 | ⚡ Expert | Advanced skills |
| 1600-1799 | 🎯 Advanced | Experienced driver |
| 1400-1599 | 📈 Intermediate | Solid fundamentals |
| 1200-1399 | 🌱 Novice | Learning phase |
| 800-1199 | 🏁 Beginner | First steps |

ELO updates with every lap submission through virtual time-trial matches against other drivers.

## 🧠 Mathe-Coach - Physics-Based Coaching

**New in Phase 3:** Get AI-powered lap analysis based on real physics!

```bash
/lap coach 12345         # Analyze latest lap from session
/lap coach 12345 5       # Analyze specific lap number
```

### How It Works
1. **Track Reconstruction** - Builds 3D track geometry from telemetry
2. **Ideal Lap Construction** - Physics simulation calculates theoretical best lap
3. **Lap Comparison** - Identifies errors (early braking, late throttle, etc.)
4. **Coaching Feedback** - Provides actionable tips with physics principles

### Error Types Detected
- 🛑 **Early Braking** - Braking too soon before corners
- ⚡ **Late Braking** - Braking too late, losing apex speed
- 🐌 **Slow Corner** - Not using full grip through corner
- 🚀 **Late Throttle** - Throttle application too late on exit
- 〰️ **Line Error** - Suboptimal racing line

### Requirements
- At least **3 complete laps** in Time Trial session
- Telemetry recording enabled in F1 2025
- Session ID from telemetry system

## 📊 Command Reference

### Lap Time Commands
| Command | Description |
|---------|-------------|
| `/lap submit <time> <track>` | Submit lap time (e.g., `1:23.456 monaco`) |
| `/lap leaderboard <track>` | View track leaderboard |
| `/lap global` | All track records |
| `/lap stats` | Your personal statistics |
| `/lap personal` | Your personal bests |
| `/lap delete <track> <time>` | Delete specific lap time |
| `/lap deletelast` | Delete last submitted lap |

### Analytics Commands
| Command | Description |
|---------|-------------|
| `/lap analytics` | Advanced analytics dashboard |
| `/lap heatmap` | Track popularity heatmap |
| `/lap rivalries` | Driver head-to-head stats |
| `/lap rating` | Your ELO rating & analysis |
| `/lap elo-leaderboard` | Global ELO rankings |

### Coaching Commands
| Command | Description |
|---------|-------------|
| `/lap coach <session_uid>` | Analyze latest lap |
| `/lap coach <session_uid> <lap#>` | Analyze specific lap |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/lap init` | Initialize leaderboard (Admin) |
| `/lap reset <password>` | Reset database (Admin) |
| `/lap username <name>` | Change display name |

## 🏗️ Architecture

This project follows **Clean Architecture** principles with strict layer separation:

```
src/
├── domain/              # Business logic (inner layer)
│   ├── entities/       # Core business objects
│   ├── services/       # Domain services (physics, comparison)
│   └── interfaces/     # Abstract repository interfaces
├── application/        # Use cases & orchestration
│   ├── use_cases/     # Application workflows
│   └── exceptions/    # Application errors
├── infrastructure/     # External integrations
│   └── persistence/   # Database implementations
└── presentation/       # User interface
    ├── bot/           # Discord bot
    └── commands/      # Slash commands
```

### Key Principles
- **Dependency Rule** - Inner layers never depend on outer layers
- **Testability** - 90%+ domain coverage, 80%+ application coverage
- **SOLID** - Single responsibility, dependency inversion
- **Domain-Driven Design** - Rich domain models, ubiquitous language

## 🗄️ Database Schema

### lap_times
Stores all submitted lap times with validation flags:
```sql
lap_id, user_id, username, track_key, total_milliseconds,
sector1_ms, sector2_ms, sector3_ms, is_personal_best,
is_overall_best, source, created_at
```

### driver_ratings
ELO rating system for competitive rankings:
```sql
user_id, username, current_elo, peak_elo, matches_played,
wins, losses, last_updated
```

### telemetry_sessions
F1 2025 telemetry sessions with lap traces:
```sql
session_uid, track_id, session_type, track_length_m, created_at
```

### lap_traces
Individual lap telemetry data with samples:
```sql
trace_id, session_uid, lap_number, car_index, lap_time_ms,
is_valid, sector_times, created_at
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# With coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Domain layer tests (target: ≥90%)
pytest tests/domain/ --cov=src.domain

# Application layer tests (target: ≥80%)
pytest tests/application/ --cov=src.application
```

### Testing Philosophy
- **70% Unit Tests** - Fast, isolated tests
- **20% Integration Tests** - Layer interaction tests
- **10% E2E Tests** - Full workflow tests

## 🔧 Configuration

### Required Environment Variables
```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here
LEADERBOARD_CHANNEL_ID=channel_for_leaderboards
HISTORY_CHANNEL_ID=channel_for_history_logs
RESET_PASSWORD=secure_password_for_reset
```

### Optional Environment Variables
```env
API_HOST=0.0.0.0              # Telemetry API host
API_PORT=8080                 # Telemetry API port
LOG_LEVEL=INFO                # Logging level
```

## 🏎️ Supported Tracks

All 24 F1 2025 tracks with city/country aliases:
- **Bahrain** (bahrain)
- **Saudi Arabia** (saudi, jeddah)
- **Australia** (australia, albert-park)
- **Monaco** (monaco)
- **Silverstone** (silverstone, uk, britain)
- **Spa** (spa, spa-francorchamps, belgium)
- **Monza** (monza, italy)
- **Singapore** (singapore, marina-bay)
- **Abu Dhabi** (abu-dhabi, yas-marina)
- ... and 15 more

**Pro-Tip:** Use city names like `houston`, `vegas`, or `baku`!

## 🐛 Troubleshooting

### Bot Not Responding
```bash
# Check bot token and permissions
echo $DISCORD_TOKEN
# Bot needs: Send Messages, Use Slash Commands, Embed Links

# View logs
tail -f f1_lap_bot.log
```

### Telemetry Not Working
- Verify F1 2025 UDP settings (port 20777, format 2025)
- Run `python udp_listener.py --debug`
- Check Windows Firewall allows Python
- Ensure Time Trial mode (not Practice/Race)

### Mathe-Coach Errors
- Need at least **3 complete laps** for track reconstruction
- Verify `session_uid` is correct
- Check telemetry recording is enabled

## 📝 Development

### Contributing
1. Fork repository
2. Create feature branch: `git checkout -b feature/awesome-feature`
3. Follow Clean Architecture principles
4. Write tests (≥80% coverage)
5. Submit pull request

### Code Style
- **Black** for formatting (88 char line length)
- **isort** for import sorting
- **mypy** for type checking
- **pytest** for testing
- **Google-style** docstrings

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **F1 Community** - Inspiration and feedback
- **Discord.py** - Amazing Discord library
- **Clean Architecture** - Uncle Bob's principles
- **Contributors** - Everyone who made this better

---

<div align="center">

**Made with ❤️ for the F1 gaming community**

[⭐ Star this repo](https://github.com/yannicktuerk/F1-Lap-Bot) • [🐛 Report Bug](https://github.com/yannicktuerk/F1-Lap-Bot/issues) • [💡 Request Feature](https://github.com/yannicktuerk/F1-Lap-Bot/issues/new)

</div>
