# Configuration Guide

## ⚙️ F1 2025 UDP Telemetry Listener Configuration

This guide covers all configuration options for the F1 2025 UDP Telemetry Listener.

## Configuration File Overview

The main configuration file is `config.json` in the project root directory.

### Default Configuration Structure

```json
{
    "discord_user_id": "your_discord_user_id_here",
    "bot_api_url": "http://localhost:8080/api/telemetry/submit",
    "port": 20777,
    "player_name": "Your Racing Name",
    "debug_mode": false,
    "default_track": "spain",
    "min_lap_time_seconds": 30,
    "max_lap_time_seconds": 300
}
```

## Configuration Options

### Core Settings

#### Bot Integration
- **Status**: Always enabled
- **Description**: Discord bot integration is always active when a valid Discord User ID is provided
- **Behavior**: Automatically submits personal bests to Discord bot server
- **Fallback**: If Discord User ID is missing, shows manual submission instructions

#### `discord_user_id` (string)
- **Default**: `"your_discord_user_id_here"`
- **Description**: Your Discord user ID for lap time attribution
- **Required**: Yes (if bot_integration is enabled)
- **Format**: 18-digit Discord snowflake ID

**How to get your Discord User ID:**
1. Enable Developer Mode in Discord (User Settings → Appearance → Advanced)
2. Right-click your username → "Copy User ID"

**Example:**
```json
{
    "discord_user_id": "123456789012345678"
}
```

#### `player_name` (string)
- **Default**: `"Your Racing Name"`
- **Description**: Display name for lap time submissions
- **Required**: Recommended
- **Format**: Any string (max 50 characters)

**Example:**
```json
{
    "player_name": "YannickF1Pro"
}
```

### Network Settings

#### `port` (integer)
- **Default**: `20777`
- **Description**: UDP port for F1 2025 telemetry reception
- **Range**: `1024-65535`
- **Note**: Must match F1 2025 game settings

**Example:**
```json
{
    "port": 20777
}
```

#### `bot_api_url` (string)
- **Default**: `"http://localhost:8080/api/telemetry/submit"`
- **Description**: Discord bot API endpoint for lap time submission
- **Format**: Full HTTP/HTTPS URL
- **Note**: Must match your Discord bot server configuration

**Examples:**
```json
{
    "bot_api_url": "http://localhost:8080/api/telemetry/submit"
}
// or for remote server:
{
    "bot_api_url": "https://your-bot-server.com/api/telemetry/submit"
}
```

### Advanced Settings

#### `debug_mode` (boolean)
- **Default**: `false`
- **Description**: Enable detailed debugging output
- **Options**:
  - `true`: Show all packet data and detailed logs
  - `false`: Standard operation with minimal output

**Example:**
```json
{
    "debug_mode": true
}
```

#### `default_track` (string)
- **Default**: `"spain"`
- **Description**: Fallback track when game doesn't provide track info
- **Options**: Any valid track name from the track mapping
- **Note**: Only used in rare cases where track detection fails

**Valid track names:**
- `monaco`, `silverstone`, `spa`, `monza`, `austria`, `bahrain`, etc.

**Example:**
```json
{
    "default_track": "monaco"
}
```

#### `min_lap_time_seconds` (integer)
- **Default**: `30`
- **Description**: Minimum valid lap time in seconds
- **Range**: `10-120`
- **Purpose**: Filter out invalid/unrealistic lap times

**Example:**
```json
{
    "min_lap_time_seconds": 45
}
```

#### `max_lap_time_seconds` (integer)
- **Default**: `300`
- **Description**: Maximum valid lap time in seconds (5 minutes)
- **Range**: `60-600`
- **Purpose**: Filter out incomplete/invalid laps

**Example:**
```json
{
    "max_lap_time_seconds": 240
}
```

## Environment-Specific Configurations

### Development Configuration

```json
{
    "bot_integration": false,
    "discord_user_id": "dev_user_id",
    "bot_api_url": "http://localhost:3000/api/test",
    "port": 20777,
    "player_name": "Dev Testing",
    "debug_mode": true,
    "default_track": "spain",
    "min_lap_time_seconds": 10,
    "max_lap_time_seconds": 600
}
```

### Production Configuration

```json
{
    "bot_integration": true,
    "discord_user_id": "123456789012345678",
    "bot_api_url": "https://f1-bot-server.herokuapp.com/api/telemetry/submit",
    "port": 20777,
    "player_name": "RacingProGamer",
    "debug_mode": false,
    "default_track": "silverstone",
    "min_lap_time_seconds": 30,
    "max_lap_time_seconds": 300
}
```

### Community Server Configuration

```json
{
    "bot_integration": true,
    "discord_user_id": "987654321098765432",
    "bot_api_url": "https://community-f1-bot.com/api/submit",
    "port": 20777,
    "player_name": "CommunityRacer",
    "debug_mode": false,
    "default_track": "monaco",
    "min_lap_time_seconds": 35,
    "max_lap_time_seconds": 180
}
```

## Track Configuration

### Track Mapping Override

You can override the default track mapping by adding a `track_overrides` section:

```json
{
    "track_overrides": {
        "99": "custom_track_1",
        "100": "custom_track_2"
    }
}
```

### Track-Specific Settings

Configure different validation rules per track:

```json
{
    "track_settings": {
        "monaco": {
            "min_lap_time_seconds": 60,
            "max_lap_time_seconds": 120
        },
        "spa": {
            "min_lap_time_seconds": 90,
            "max_lap_time_seconds": 180
        }
    }
}
```

## Security Configuration

### API Authentication

For secure Discord bot communication:

```json
{
    "bot_api_url": "https://secure-bot-server.com/api/telemetry/submit",
    "api_key": "your_secure_api_key_here",
    "use_ssl_verification": true
}
```

### Rate Limiting

Prevent spam submissions:

```json
{
    "rate_limiting": {
        "max_submissions_per_minute": 10,
        "cooldown_between_submissions": 5
    }
}
```

## Validation Rules

### Custom Lap Validation

```json
{
    "validation": {
        "allow_flashback_laps": false,
        "allow_corner_cutting": false,
        "allow_wall_riding": false,
        "require_clean_sectors": true,
        "max_penalties": 0
    }
}
```

### Sector Time Validation

```json
{
    "sector_validation": {
        "require_all_sectors": true,
        "max_sector_time_seconds": 60,
        "validate_sector_progression": true
    }
}
```

## Performance Settings

### Resource Optimization

```json
{
    "performance": {
        "packet_buffer_size": 2048,
        "max_packets_per_second": 60,
        "memory_cleanup_interval": 300
    }
}
```

### Logging Configuration

```json
{
    "logging": {
        "log_level": "INFO",
        "log_to_file": true,
        "log_file_path": "f1_telemetry.log",
        "max_log_file_size_mb": 10,
        "log_rotation_count": 5
    }
}
```

## Configuration Validation

### Automatic Validation

The system automatically validates your configuration on startup:

- ✅ **Required fields** are present
- ✅ **Data types** are correct
- ✅ **Value ranges** are valid
- ✅ **Network connectivity** is testable

### Manual Validation

Test your configuration:

```bash
# Validate configuration file
python -c "import json; json.load(open('config.json')); print('✅ Valid JSON')"

# Test Discord bot connectivity
python test_config.py
```

## Configuration Templates

### Quick Start Template

```json
{
    "bot_integration": false,
    "discord_user_id": "",
    "port": 20777,
    "player_name": "F1 Racer",
    "debug_mode": true
}
```

### Competitive Racing Template

```json
{
    "bot_integration": true,
    "discord_user_id": "YOUR_DISCORD_ID",
    "bot_api_url": "https://your-league-bot.com/api/submit",
    "port": 20777,
    "player_name": "YourRacingName",
    "debug_mode": false,
    "min_lap_time_seconds": 40,
    "max_lap_time_seconds": 200,
    "validation": {
        "allow_flashback_laps": false,
        "max_penalties": 0
    }
}
```

## Troubleshooting Configuration

### Common Configuration Errors

#### Invalid JSON Format
```bash
# Check JSON syntax
python -m json.tool config.json
```

#### Missing Required Fields
- Ensure `discord_user_id` is set if `bot_integration` is true
- Verify `port` is a valid integer
- Check `bot_api_url` is a valid URL

#### Network Issues
- Test if port 20777 is available
- Verify Discord bot server is reachable
- Check firewall settings

### Configuration Backup

```bash
# Create backup before changes
cp config.json config_backup_$(date +%Y%m%d).json

# Restore from backup if needed
cp config_backup_YYYYMMDD.json config.json
```

## Environment Variables

Override configuration with environment variables:

```bash
# Set environment variables
export F1_DISCORD_USER_ID="123456789012345678"
export F1_BOT_API_URL="https://production-bot.com/api/submit"
export F1_DEBUG_MODE="false"

# Run with environment overrides
python udp_listener.py
```

## Configuration Updates

### Automatic Updates

The system can automatically update configuration:

```json
{
    "auto_update": {
        "enabled": true,
        "check_interval_hours": 24,
        "backup_before_update": true
    }
}
```

### Manual Updates

```bash
# Pull latest configuration templates
git pull origin main

# Merge new configuration options
python merge_config.py
```

---

**Configuration complete!** ⚙️ Your F1 2025 UDP Telemetry Listener is now optimally configured!
