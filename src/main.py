"""Main entry point for the F1 Lap Time Discord Bot."""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.presentation.bot.f1_bot import F1LapBot


async def main():
    """Main function to run the Discord bot."""
    # Load environment variables
    load_dotenv()
    
    # Get Discord token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN environment variable is required!")
        print("Please copy .env.example to .env and fill in your bot token.")
        return
    
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
