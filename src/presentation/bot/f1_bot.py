"""Main Discord bot client for F1 lap time tracking."""
import discord
from discord.ext import commands
import os
from typing import Optional
from ...infrastructure.persistence.sqlite_lap_time_repository import SQLiteLapTimeRepository
from ...application.use_cases.submit_lap_time import SubmitLapTimeUseCase


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
        self.submit_lap_time_use_case = SubmitLapTimeUseCase(self.lap_time_repository)
        
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
        """Update the pinned leaderboard for a track."""
        channel = self.get_leaderboard_channel()
        if not channel:
            return
        
        try:
            from ...domain.value_objects.track_name import TrackName
            track = TrackName(track_name)
            
            # Get top 5 times for the track
            top_times = await self.lap_time_repository.find_top_by_track(track, 5)
            
            # Create beautiful embed with track data
            embed = discord.Embed(
                title=f"🏁 {track.display_name}",
                color=discord.Color.red(),
                description=f"🌍 **{track.country}** • Top 5 fastest lap times"
            )
            
            # Add track layout image and country flag
            embed.set_image(url=track.image_url)
            embed.set_thumbnail(url=track.flag_url)
            
            if not top_times:
                embed.add_field(
                    name="No times yet",
                    value="Be the first to submit a lap time with `/lap submit`!",
                    inline=False
                )
            else:
                medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                leaderboard_text = ""
                
                for i, lap_time in enumerate(top_times):
                    medal = medals[i] if i < len(medals) else f"{i+1}️⃣"
                    leaderboard_text += f"{medal} **{lap_time.username}** - `{lap_time.time_format}`\\n"
                
                embed.add_field(
                    name="🏆 Current Leaders",
                    value=leaderboard_text,
                    inline=False
                )
            
            embed.set_footer(text="Use /lap submit <time> <track> to add your time!")
            
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
            print(f"❌ Error updating leaderboard: {e}")
    
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
