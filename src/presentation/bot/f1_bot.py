"""Main Discord bot client for F1 lap time tracking."""
import discord
from discord.ext import commands
import os
from typing import Optional
from ...infrastructure.persistence.sqlite_lap_time_repository import SQLiteLapTimeRepository
from ...infrastructure.persistence.sqlite_driver_rating_repository import SQLiteDriverRatingRepository
from ...application.use_cases.submit_lap_time import SubmitLapTimeUseCase
from ...application.use_cases.update_username import UpdateUsernameUseCase


class F1LapBot(commands.Bot):
    """Main Discord bot class for F1 lap time tracking."""
    
    def __init__(self):
        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='F1 Lap Time Tracking Bot'
        )
        
        # Dependencies (Clean Architecture)
        self.lap_time_repository = SQLiteLapTimeRepository()
        self.driver_rating_repository = SQLiteDriverRatingRepository()
        self.submit_lap_time_use_case = SubmitLapTimeUseCase(
            self.lap_time_repository, 
            self.driver_rating_repository
        )
        self.update_username_use_case = UpdateUsernameUseCase(
            self.lap_time_repository,
            self.driver_rating_repository
        )
        
        # Configuration
        self.leaderboard_channel_id: Optional[int] = None
        self.history_channel_id: Optional[int] = None
        self.leaderboard_message_id: Optional[int] = None
    
    async def setup_hook(self):
        """Setup hook called when the bot is ready."""
        print(f"🏁 {self.user} is ready to track lap times!")
        
        # Load configuration from environment
        self.leaderboard_channel_id = int(os.getenv('LEADERBOARD_CHANNEL_ID', 0)) or None
        self.history_channel_id = int(os.getenv('HISTORY_CHANNEL_ID', 0)) or None
        
        # Load cogs (command modules)
        await self.load_extension('src.presentation.commands.lap_commands')
        
        # Sync slash commands
        try:
            guild_id = int(os.getenv('GUILD_ID', 0))
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"✅ Slash commands synced to guild {guild_id}")
            else:
                await self.tree.sync()
                print("✅ Global slash commands synced")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"🚀 Bot logged in as {self.user}")
        print(f"📊 Connected to {len(self.guilds)} guild(s)")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="F1 lap times | /lap submit"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for commands."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}")
            return
        
        print(f"❌ Command error: {error}")
        await ctx.send("❌ An error occurred while processing your command.")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global error handler for application commands (slash commands)."""
        try:
            # Create a user-friendly error embed
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red()
            )
            
            if isinstance(error, discord.app_commands.CommandOnCooldown):
                embed.description = f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
            elif isinstance(error, discord.app_commands.MissingPermissions):
                embed.description = f"You don't have the required permissions: {', '.join(error.missing_permissions)}"
            elif isinstance(error, discord.app_commands.BotMissingPermissions):
                embed.description = f"I don't have the required permissions: {', '.join(error.missing_permissions)}"
            elif isinstance(error, discord.app_commands.NoPrivateMessage):
                embed.description = "This command cannot be used in private messages."
            elif isinstance(error, discord.app_commands.CommandNotFound):
                embed.description = "Unknown command. Use `/lap help` to see available commands."
            else:
                # Generic error message for unexpected errors
                embed.description = "An unexpected error occurred. Please try again later."
                embed.add_field(
                    name="🔧 Help",
                    value="If this error persists, please contact the bot developer.",
                    inline=False
                )
                
                # Log the full error for debugging
                print(f"❌ Unhandled app command error: {type(error).__name__}: {error}")
                print(f"   Command: /{interaction.command.name if interaction.command else 'unknown'}")
                print(f"   User: {interaction.user} ({interaction.user.id})")
                print(f"   Guild: {interaction.guild.name if interaction.guild else 'DM'} ({interaction.guild_id})")
            
            # Send error response
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            # Fallback if even error handling fails
            print(f"❌ Error in error handler: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ A critical error occurred. Please try again.", 
                        ephemeral=True
                    )
            except:
                pass  # Ultimate fallback - just log and continue
    
    def _format_sector_time(self, time_ms: int) -> str:
        """Format sector time in milliseconds to SS.mmm format."""
        return f"{time_ms / 1000.0:.3f}s"
    
    def get_leaderboard_channel(self) -> Optional[discord.TextChannel]:
        """Get the configured leaderboard channel."""
        if not self.leaderboard_channel_id:
            return None
        return self.get_channel(self.leaderboard_channel_id)
    
    def get_history_channel(self) -> Optional[discord.TextChannel]:
        """Get the configured history channel."""
        if not self.history_channel_id:
            return None
        return self.get_channel(self.history_channel_id)
    
    async def update_leaderboard(self, track_name: str):
        """Update the pinned global leaderboard."""
        await self.update_global_leaderboard()
    
    async def update_global_leaderboard(self):
        """Update the pinned global leaderboard with all tracks overview."""
        channel = self.get_leaderboard_channel()
        if not channel:
            return
        
        try:
            from ...domain.value_objects.track_name import TrackName
            
            # Get all available tracks that have lap times
            all_track_keys = list(TrackName.TRACK_DATA.keys())
            tracks_with_times = []
            
            # First, collect all tracks that have lap times
            for track_key in all_track_keys:
                try:
                    track = TrackName(track_key)
                    best_time = await self.lap_time_repository.find_best_by_track(track)
                    if best_time:
                        tracks_with_times.append((track_key, track, best_time))
                except Exception as e:
                    print(f"Error processing track {track_key}: {e}")
                    continue
            
            # Sort tracks alphabetically by display name
            tracks_with_times.sort(key=lambda x: x[1].display_name)
            
            embed = discord.Embed(
                title="🏁 F1 Lap Time Leaderboard",
                description=f"Current track records across {len(tracks_with_times)} circuits",
                color=discord.Color.red()
            )
            
            # Build track overview
            track_overview = ""
            for track_key, track, best_time in tracks_with_times:
                track_overview += f"{track.flag_emoji} **{track.short_name}** - {best_time.username} `{best_time.time_format}`\n"
            
            if track_overview:
                embed.add_field(
                    name="🏆 Track Records",
                    value=track_overview,
                    inline=False
                )
            
            # Add usage information
            embed.add_field(
                name="🎮 Getting Started",
                value="Use `/lap submit <time> <track>` to submit your lap time!\n"
                      "Example: `/lap submit 1:23.456 monaco`",
                inline=False
            )
            
            embed.set_footer(text="🏁 Submit times • View tracks with /lap tracks • Get help with /lap h")
            
            # Update or create leaderboard message
            if self.leaderboard_message_id:
                try:
                    message = await channel.fetch_message(self.leaderboard_message_id)
                    await message.edit(embed=embed)
                    return
                except discord.NotFound:
                    pass
            
            # Create new leaderboard message
            message = await channel.send(embed=embed)
            try:
                await message.pin()
                self.leaderboard_message_id = message.id
            except discord.HTTPException:
                pass  # Couldn't pin, but message was sent
                
        except Exception as e:
            print(f"❌ Error updating global leaderboard: {e}")
    
    async def log_to_history(self, lap_time, is_personal_best: bool, is_overall_best: bool):
        """Log a new lap time to the history channel."""
        channel = self.get_history_channel()
        if not channel:
            return
        
        try:
            # Create embed for history log
            color = discord.Color.gold() if is_overall_best else (
                discord.Color.green() if is_personal_best else discord.Color.blue()
            )
            
            title = "🏆 NEW OVERALL BEST!" if is_overall_best else (
                "🎯 Personal Best!" if is_personal_best else "⏱️ New Lap Time"
            )
            
            embed = discord.Embed(
                title=title,
                color=color,
                timestamp=lap_time.created_at
            )
            
            embed.add_field(
                name="Driver",
                value=lap_time.username,
                inline=True
            )
            
            embed.add_field(
                name="Time",
                value=f"`{lap_time.time_format}`",
                inline=True
            )
            
            embed.add_field(
                name="Track",
                value=f"🌍 **{lap_time.track_name.display_name}**\n({lap_time.track_name.country})",
                inline=True
            )
            
            # Add sector times if available
            if lap_time.sector1_ms or lap_time.sector2_ms or lap_time.sector3_ms:
                sector_text = ""
                if lap_time.sector1_ms and lap_time.sector1_ms > 0:
                    s1_time = self._format_sector_time(lap_time.sector1_ms)
                    sector_text += f"S1: `{s1_time}`\n"
                if lap_time.sector2_ms and lap_time.sector2_ms > 0:
                    s2_time = self._format_sector_time(lap_time.sector2_ms)
                    sector_text += f"S2: `{s2_time}`\n"
                if lap_time.sector3_ms and lap_time.sector3_ms > 0:
                    s3_time = self._format_sector_time(lap_time.sector3_ms)
                    sector_text += f"S3: `{s3_time}`"
                
                if sector_text:
                    embed.add_field(
                        name="🎯 Sectors",
                        value=sector_text,
                        inline=False
                    )
            
            # Add country flag as thumbnail
            embed.set_thumbnail(url=lap_time.track_name.flag_url)
            
            if is_overall_best:
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/799335921350082600.png")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error logging to history: {e}")
            
    async def send_overtake_notification(self, new_leader, previous_leader):
        """Send notification when someone takes the lead."""
        try:
            # Send DM to previous leader
            if previous_leader:
                try:
                    user = self.get_user(int(previous_leader.user_id))
                    if user:
                        embed = discord.Embed(
                            title="🚨 You've been overtaken!",
                            description=f"**{new_leader.username}** just set a faster time on **{new_leader.track_name.short_name}**",
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="Their time", value=f"`{new_leader.time_format}`", inline=True)
                        embed.add_field(name="Your time", value=f"`{previous_leader.time_format}`", inline=True)
                        embed.add_field(name="Difference", value=f"`{new_leader.get_time_difference_to(previous_leader):.3f}s`", inline=True)
                        
                        await user.send(embed=embed)
                except Exception as e:
                    print(f"❌ Couldn't send DM to previous leader: {e}")
            
        except Exception as e:
            print(f"❌ Error sending overtake notification: {e}")
