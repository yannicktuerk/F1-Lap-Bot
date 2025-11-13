# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

F1 Lap Bot is a Discord bot that tracks F1 2025 lap times with real-time UDP telemetry integration. The bot features:
- Discord slash commands for lap time submission and leaderboards
- HTTP API server for receiving telemetry data from F1 2025 UDP listeners
- ELO-based driver rating system
- SQLite persistence layer
- Analytics and rivalry tracking

**Key Architectural Decision**: The bot runs **two services simultaneously**:
1. Discord bot client (slash commands, embeds, DM notifications)
2. HTTP API server (receives telemetry from UDP listeners running on players' machines)

Both services share the same repository instances and run in a single Python process via `asyncio`.

## Architecture

This project strictly follows **Clean Architecture** principles with clear layer boundaries:

```
src/
├── domain/                 # Core business logic (NO external dependencies)
│   ├── entities/          # LapTime, DriverRating (rich models with behavior)
│   ├── value_objects/     # TimeFormat, TrackName (immutable, validated)
│   ├── interfaces/        # Repository contracts (ports)
│   └── services/          # TimeTrialEloService
├── application/           # Use cases orchestrating domain logic
│   └── use_cases/         # SubmitLapTimeUseCase, UpdateEloRatingsUseCase, UpdateUsernameUseCase
├── infrastructure/        # External concerns (adapters)
│   └── persistence/       # SQLiteLapTimeRepository, SQLiteDriverRatingRepository
└── presentation/          # User-facing interfaces
    ├── bot/              # F1LapBot (discord.py client)
    ├── commands/         # LapCommands (slash command handlers)
    └── api/              # TelemetryAPI (aiohttp HTTP server)
```

### Critical Architectural Patterns

**Dependency Rule**: Inner layers NEVER depend on outer layers
- Domain entities know nothing about Discord, HTTP, or SQLite
- Application use cases depend on repository **interfaces** (in domain layer)
- Infrastructure implements those interfaces
- Presentation layer orchestrates use cases

**Repository Pattern**:
- Interfaces defined in `src/domain/interfaces/`
- SQLite implementations in `src/infrastructure/persistence/`
- All database operations go through repositories
- Use cases receive repository instances via dependency injection

**Value Objects for Validation**:
- `TimeFormat`: Parses and validates lap times (e.g., "1:23.456"), immutable
- `TrackName`: Validates track names, handles aliases (e.g., "cota" → "usa"), contains track metadata
- Both enforce business rules at construction time

**Rich Domain Entities**:
- `LapTime`: Not anemic - contains methods like `is_faster_than()`, `get_time_difference_to()`
- `DriverRating`: ELO calculation logic lives in domain service, not database layer

## Key Implementation Details

### Dual-Service Architecture

The bot is unique in that it runs **two async services concurrently** in `src/main.py`:

```python
# Start HTTP API server first
await api_server.start()

# Start Discord bot (blocks until shutdown)
bot_task = asyncio.create_task(bot.start(token))
await bot_task
```

**Why?** UDP telemetry listeners run on players' machines and POST lap times to the bot's HTTP API. The Discord bot then updates leaderboards and sends DM notifications.

### Database Layer

**Current State**:
- **Single SQLite database** (`f1_lap_bot.db` in project root)
- **Two main repositories**:
  - `SQLiteLapTimeRepository`: Stores lap times with sector splits
  - `SQLiteDriverRatingRepository`: Stores ELO ratings
- **Async operations** using `aiosqlite`
- **Schema migrations** are in `src/infrastructure/persistence/` (`.pyc` files suggest auto-applied)

**Planned Architecture** (for future telemetry/AI features):
- **Application Database** (current): Fast live queries for lap times, ELO, leaderboards - operational data for Discord bot
- **Telemetry Database** (future): Separate storage for complete lap traces, detailed telemetry samples, AI training data
  - Clean separation at persistence layer
  - Allows independent scaling and optimization
  - Analytics/KI modules access telemetry DB without impacting bot performance
  - Preserves Clean Architecture: domain/application layers unchanged, only infrastructure adapters differ

### ELO Rating System

The `TimeTrialEloService` (domain service) implements a virtual match system:
- Each lap time submission triggers ELO recalculation
- Driver "races" against all other drivers' best times on that track
- Wins increase ELO, losses decrease it
- 7 skill tiers: Beginner → Novice → Intermediate → Advanced → Expert → Master → Legendary

### Discord Command Structure

All commands are in `src/presentation/commands/lap_commands.py`:
- Prefix: `/lap <subcommand>`
- Uses `discord.app_commands` (slash commands, NOT prefix commands)
- Command groups: submission, leaderboards, analytics, ELO ratings, admin

**Recent Refactoring** (see `REFACTORING_SUMMARY.md`):
- `EmbedBuilder` class centralizes Discord embed creation
- `AnalyticsService` extracts calculation logic from command handlers
- List comprehensions replace string concatenation loops for efficiency

### Telemetry Integration

Players run a **separate UDP listener script** on their local machine:
- Listens on UDP port 20777 for F1 2025 telemetry packets
- Validates lap times (Time Trial mode only, no penalties, realistic times)
- POSTs valid laps to bot's HTTP API endpoint
- API endpoint: `POST /api/telemetry/submit`

**Critical Design Decision**: The UDP listener is intentionally NOT part of the main bot process. Each player runs their own listener that sends data to the centralized bot via a stable HTTP API.

**Why external listeners?**
- **Bot stays lightweight** - No telemetry processing burden on central bot
- **Easy updates** - Telemetry validation logic can change without redeploying bot or distributing new binaries
- **Simple deployment** - Players run a simple Python script, no complex setup
- **Stable interface** - HTTP API contract remains consistent even as telemetry logic evolves

## Common Development Commands

### Setup & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (REQUIRED before first run)
# Create .env file with:
# - DISCORD_TOKEN (required)
# - GUILD_ID (required for command syncing)
# - LEADERBOARD_CHANNEL_ID (optional)
# - HISTORY_CHANNEL_ID (optional)
# - RESET_PASSWORD (optional, for database reset)
# - API_HOST (default: 0.0.0.0)
# - API_PORT (default: 8080)

# Start the bot (runs both Discord bot + HTTP API server)
python src/main.py
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/

# Run specific test file
pytest tests/test_packet_decoder.py

# Run with verbose output
pytest -v
```

**Testing Strategy** (from Clean Architecture guidelines):
- **Domain Layer**: 90% branch coverage target, pure unit tests (no mocks)
- **Use Case Layer**: 80% coverage, mock repositories
- **Infrastructure Layer**: Integration tests with real SQLite
- **Pyramid**: ~70% Unit, ~20% Integration, ~10% E2E

### Database Operations

```bash
# Database file location (auto-created on first run)
# f1_lap_bot.db in project root

# Backup database
cp f1_lap_bot.db backups/f1_lap_bot_$(date +%Y%m%d).db

# Reset database (requires RESET_PASSWORD in .env)
# Use Discord command: /lap reset <password>
```

### Code Quality

```bash
# Format code (project uses auto-formatting on commit)
black src/ tests/

# Type checking (if mypy is added)
mypy src/

# Run syntax check on all Python files
python -m py_compile src/**/*.py
```

## Discord Slash Commands

### Primary Commands

- `/lap submit <time> <track>` - Submit lap time (e.g., `/lap submit 1:23.456 monaco`)
- `/lap leaderboard <track>` - View track leaderboard
- `/lap global` - Global leaderboard (all tracks)
- `/lap personal [track]` - Personal best times
- `/lap stats` - Personal statistics
- `/lap analytics` - Advanced analytics dashboard
- `/lap heatmap` - Track popularity heatmap
- `/lap rivalries` - Head-to-head driver comparisons
- `/lap rating` - View your ELO skill rating
- `/lap elo-leaderboard` - Global ELO rankings
- `/lap username <name>` - Change display name

### Admin Commands

- `/lap init [channel]` - Initialize leaderboard (admin only)
- `/lap reset <password>` - Reset database with password protection (admin only)

### Track Names

All F1 2025 tracks supported. Use canonical names or aliases:
- Canonical: `monaco`, `silverstone`, `spa`, `monza`, `austria`, `bahrain`, etc.
- Aliases: `cota` (→ usa), `vegas` (→ las-vegas), `barcelona` (→ spain), `hungaroring` (→ hungary)
- Full list in `src/domain/value_objects/track_name.py` (TRACK_DATA and ALIASES dicts)

## Configuration

### Environment Variables

Required:
- `DISCORD_TOKEN`: Discord bot token from Developer Portal
- `GUILD_ID`: Discord server ID (for slash command syncing)

Optional:
- `LEADERBOARD_CHANNEL_ID`: Channel for pinned leaderboard (0 to disable)
- `HISTORY_CHANNEL_ID`: Channel for lap history logs (0 to disable)
- `RESET_PASSWORD`: Secure password for database reset command
- `API_HOST`: HTTP API bind address (default: `0.0.0.0`)
- `API_PORT`: HTTP API port (default: `8080`)

### Bot Setup Requirements

Discord bot needs these permissions:
- Send Messages
- Use Slash Commands
- Embed Links
- Manage Messages (for pinned leaderboards)

## Critical Code Patterns

### Creating New Use Cases

1. Define use case class in `src/application/use_cases/`
2. Inject repository **interfaces** (from `src/domain/interfaces/`)
3. Create domain entities, call domain methods
4. Save via repository
5. Return results to presentation layer

Example:
```python
class SubmitLapTimeUseCase:
    def __init__(self, lap_time_repository: LapTimeRepository):
        self._repository = lap_time_repository
    
    async def execute(self, user_id, username, time_string, track_string):
        # Create value objects (validates at construction)
        time_format = TimeFormat(time_string)
        track_name = TrackName(track_string)
        
        # Create entity
        lap_time = LapTime(user_id, username, time_format, track_name)
        
        # Business logic via entity methods
        user_best = await self._repository.find_user_best_by_track(user_id, track_name)
        if user_best and not lap_time.is_faster_than(user_best):
            raise ValueError("Time is slower than your best")
        
        # Save
        await self._repository.save(lap_time)
        return lap_time
```

### Adding New Discord Commands

1. Add method to `LapCommands` class in `src/presentation/commands/lap_commands.py`
2. Use `@app_commands.command()` decorator
3. Call use case via `self.bot.submit_lap_time_use_case.execute()`
4. Use `EmbedBuilder` for consistent embed formatting
5. Handle errors with user-friendly messages

### Repository Implementation Pattern

```python
class SQLiteExampleRepository(ExampleRepository):  # Inherit from domain interface
    def __init__(self, db_path: str = "f1_lap_bot.db"):
        self.db_path = db_path
    
    async def save(self, entity: DomainEntity) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO ...", (...))
            await db.commit()
    
    async def find_by_id(self, entity_id: str) -> Optional[DomainEntity]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT ... WHERE id = ?", (entity_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            # Map database row to domain entity
            return DomainEntity(...)
```

### String Building Best Practice

**Do NOT** use string concatenation in loops (inefficient):
```python
# BAD
result = ""
for item in items:
    result += f"{item}\n"
```

**DO** use list comprehensions with join (efficient):
```python
# GOOD
result = "\n".join(f"{item}" for item in items)
```

This pattern is used throughout after recent refactoring (see `REFACTORING_SUMMARY.md`).

## Troubleshooting

### Bot Won't Start

1. Check `.env` file exists with required variables
2. Verify `DISCORD_TOKEN` is valid
3. Verify `GUILD_ID` is a valid integer
4. Check port 8080 (or custom `API_PORT`) is not in use

### Slash Commands Not Appearing

1. Ensure `GUILD_ID` in `.env` matches your Discord server
2. Bot needs "applications.commands" scope when invited
3. Check console for "✅ Slash commands synced" message
4. Wait ~5 minutes for Discord to propagate commands

### Database Errors

- Database file must be writable
- Check file permissions on `f1_lap_bot.db`
- If corrupted, restore from backup or delete and restart bot

### Telemetry Not Working

- UDP listener must run **on the same PC as F1 2025**
- F1 2025 settings: UDP Telemetry ON, Port 20777, Format 2025
- Check `bot_api_url` in listener's `config.json` matches bot's HTTP endpoint
- Verify firewall allows UDP port 20777
- Only works in **Time Trial mode** (not Practice/Race)

## Key Files Reference

- `src/main.py` - Entry point, starts both services
- `src/presentation/bot/f1_bot.py` - Discord bot client
- `src/presentation/commands/lap_commands.py` - All slash commands (~2300 lines)
- `src/presentation/commands/embed_builder.py` - Reusable Discord embed creation
- `src/presentation/commands/analytics_service.py` - Analytics calculations
- `src/presentation/api/telemetry_api.py` - HTTP API server
- `src/domain/entities/lap_time.py` - Core lap time entity
- `src/domain/value_objects/track_name.py` - Track validation + metadata (TRACK_DATA dict)
- `src/application/use_cases/submit_lap_time.py` - Lap submission orchestration
- `REFACTORING_SUMMARY.md` - Recent efficiency improvements

## Dependencies

Core:
- `discord.py==2.3.2` - Discord bot framework
- `aiohttp==3.9.1` - HTTP server for telemetry API
- `aiosqlite==0.19.0` - Async SQLite operations
- `f1-packets==2025.1.1` - F1 2025 telemetry packet parsing

Testing:
- `pytest==7.4.3`
- `pytest-asyncio==0.21.1`

Utilities:
- `python-dotenv==1.0.0` - Environment variable loading
- `pytz==2023.3` - Timezone handling
- `aiohttp-cors==0.7.0` - CORS for HTTP API

## Notes for AI Assistants

- **Always respect layer boundaries** - Domain code must not import from infrastructure/presentation
- **Use dependency injection** - Pass repositories to use cases, not hardcoded instantiation
- **Value objects validate** - Let `TimeFormat` and `TrackName` constructors raise `ValueError`
- **Entities have behavior** - Add business logic methods to entities, not in repositories
- **Async all the way** - All repository methods are `async def`, all use cases are `async def`
- **Database migrations** - Schema changes require updates in repository `_ensure_tables()` methods
- **Recent refactoring** - Use `EmbedBuilder` for embeds, `AnalyticsService` for calculations
- **Two services, one process** - Bot handles Discord interactions AND HTTP API requests
- **UDP listeners are external BY DESIGN** - Do not suggest integrating them into bot process. The external architecture is intentional for maintainability
- **Future telemetry features** - When adding telemetry/AI features, plan for separate telemetry database. Keep operational data (lap times, ELO) in application DB
- **HTTP API is stable** - Listener-to-bot interface should remain backwards-compatible. Changes to telemetry validation happen in listener, not bot
