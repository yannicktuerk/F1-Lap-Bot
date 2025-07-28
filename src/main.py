"""Main entry point for the F1 Lap Time Discord Bot."""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.presentation.bot.f1_bot import F1LapBot


def validate_environment() -> bool:
    """Validate all required environment variables."""
    required_vars = {
        'DISCORD_TOKEN': 'Discord bot token',
        'GUILD_ID': 'Discord guild (server) ID for command syncing',
    }
    
    optional_vars = {
        'LEADERBOARD_CHANNEL_ID': 'Channel ID for leaderboard (optional)',
        'HISTORY_CHANNEL_ID': 'Channel ID for history logs (optional)', 
        'RESET_PASSWORD': 'Password for database reset command (optional)'
    }
    
    missing_required = []
    missing_optional = []
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_required.append(f"  • {var}: {description}")
        elif var == 'GUILD_ID':
            try:
                int(value)
            except ValueError:
                missing_required.append(f"  • {var}: Must be a valid Discord guild ID (numbers only)")
    
    # Check optional variables (just warn if missing)
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value:
            missing_optional.append(f"  • {var}: {description}")
        elif var in ['LEADERBOARD_CHANNEL_ID', 'HISTORY_CHANNEL_ID'] and value != '0':
            try:
                int(value)
            except ValueError:
                missing_required.append(f"  • {var}: Must be a valid Discord channel ID (numbers only)")
    
    # Report results
    if missing_required:
        print("❌ MISSING REQUIRED ENVIRONMENT VARIABLES:")
        for var in missing_required:
            print(var)
        print("\n📝 Please copy .env.example to .env and configure the required variables.")
        return False
    
    if missing_optional:
        print("⚠️  Optional environment variables not set:")
        for var in missing_optional:
            print(var)
        print("   These features will be disabled but the bot will still work.\n")
    
    print("✅ Environment validation passed!")
    return True


async def main():
    """Main function to run the Discord bot."""
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    if not validate_environment():
        return
    
    # Get Discord token (we know it exists from validation)
    token = os.getenv('DISCORD_TOKEN')
    
    # Create and run the bot
    bot = F1LapBot()
    
    try:
        print("🚀 Starting F1 Lap Time Bot...")
        await bot.start(token)
    except KeyboardInterrupt:
        print("\\n⏹️ Bot shutdown requested...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()
        print("👋 Bot stopped.")


if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)
