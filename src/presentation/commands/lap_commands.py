"""Discord slash commands for lap time management."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from ...domain.value_objects.track_name import TrackName


class LapCommands(commands.Cog):
    """Cog containing all lap time related commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="submit", description="Submit your lap time")
    @app_commands.describe(
        time="Your lap time (format: 1:23.456 or 83.456)",
        track="Track name (e.g., monaco, silverstone, spa)"
    )
    async def submit_lap_time(
        self,
        interaction: discord.Interaction,
        time: str,
        track: str
    ):
        """Submit a new lap time."""
        await interaction.response.defer()
        
        try:
            # Execute use case
            lap_time, is_personal_best, is_overall_best = await self.bot.submit_lap_time_use_case.execute(
                user_id=str(interaction.user.id),
                username=interaction.user.display_name,
                time_string=time,
                track_string=track
            )
            
            # Create response embed
            if is_overall_best:
                embed = discord.Embed(
                    title="🏆 NEW TRACK RECORD!",
                    description=f"Congratulations! You've set a new track record!",
                    color=discord.Color.gold()
                )
            elif is_personal_best:
                embed = discord.Embed(
                    title="🎯 Personal Best!",
                    description="You've improved your personal best time!",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⏱️ Lap Time Recorded",
                    description="Your lap time has been recorded.",
                    color=discord.Color.blue()
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
            
            # Add beautiful track visuals
            embed.set_image(url=lap_time.track_name.image_url)
            embed.set_thumbnail(url=lap_time.track_name.flag_url)
            
            # Add comparison info if not the first time
            if is_overall_best:
                # Check if there was a previous leader
                previous_best = await self.bot.lap_time_repository.find_best_by_track(lap_time.track_name)
                if previous_best and previous_best.user_id != lap_time.user_id:
                    time_diff = previous_best.get_time_difference_to(lap_time)
                    embed.add_field(
                        name="Improvement",
                        value=f"`-{time_diff:.3f}s` faster than previous best",
                        inline=False
                    )
                    
                    # Send overtake notification
                    await self.bot.send_overtake_notification(lap_time, previous_best)
            
            await interaction.followup.send(embed=embed)
            
            # Update leaderboard and log to history
            await self.bot.update_leaderboard(track)
            await self.bot.log_to_history(lap_time, is_personal_best, is_overall_best)
            
        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Input",
                description=str(e),
                color=discord.Color.red()
            )
            
            if "time format" in str(e).lower():
                error_embed.add_field(
                    name="Valid Time Formats",
                    value="• `1:23.456` (1 minute, 23.456 seconds)\\n• `83.456` (83.456 seconds)",
                    inline=False
                )
            
            if "track name" in str(e).lower():
                valid_tracks = TrackName.get_all_valid_tracks()[:20]  # Show first 20
                tracks_text = ", ".join(valid_tracks)
                error_embed.add_field(
                    name="Valid Track Names",
                    value=f"`{tracks_text}`\\n...and more",
                    inline=False
                )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        except Exception as e:
            print(f"❌ Error in submit command: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @app_commands.command(name="leaderboard", description="Show top times for a track")
    @app_commands.describe(track="Track name (e.g., monaco, silverstone, spa)")
    async def show_leaderboard(
        self,
        interaction: discord.Interaction,
        track: str
    ):
        """Show the leaderboard for a specific track."""
        await interaction.response.defer()
        
        try:
            track_obj = TrackName(track)
            top_times = await self.bot.lap_time_repository.find_top_by_track(track_obj, 10)
            
            embed = discord.Embed(
                title=f"🏁 {track_obj.display_name}",
                description=f"🌍 **{track_obj.country}** • Top 10 fastest lap times",
                color=discord.Color.red()
            )
            
            # Add beautiful track visuals
            embed.set_image(url=track_obj.image_url)
            embed.set_thumbnail(url=track_obj.flag_url)
            
            if not top_times:
                embed.add_field(
                    name="No times yet",
                    value="Be the first to submit a lap time with `/lap submit`!",
                    inline=False
                )
            else:
                medals = ["🥇", "🥈", "🥉"]
                leaderboard_text = ""
                
                for i, lap_time in enumerate(top_times):
                    position_icon = medals[i] if i < 3 else f"`{i+1}.`"
                    leaderboard_text += f"{position_icon} **{lap_time.username}** - `{lap_time.time_format}`\\n"
                
                embed.add_field(
                    name="🏆 Leaderboard",
                    value=leaderboard_text,
                    inline=False
                )
            
            # Add track statistics
            stats = await self.bot.lap_time_repository.get_track_statistics(track_obj)
            if stats['total_laps'] > 0:
                embed.add_field(
                    name="📊 Track Stats",
                    value=f"Total laps: {stats['total_laps']}\\n"
                          f"Drivers: {stats['unique_drivers']}\\n"
                          f"Average: `{stats['average_time_seconds']:.3f}s`",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Track",
                description=str(e),
                color=discord.Color.red()
            )
            
            valid_tracks = TrackName.get_all_valid_tracks()[:20]
            tracks_text = ", ".join(valid_tracks)
            error_embed.add_field(
                name="Valid Track Names",
                value=f"`{tracks_text}`\\n...and more",
                inline=False
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        except Exception as e:
            print(f"❌ Error in leaderboard command: {e}")
            await interaction.followup.send("❌ Error retrieving leaderboard.", ephemeral=True)
    
    @app_commands.command(name="stats", description="Show your personal statistics")
    async def show_personal_stats(self, interaction: discord.Interaction):
        """Show personal statistics for the user."""
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            
            # Get user statistics
            stats = await self.bot.lap_time_repository.get_user_statistics(user_id)
            user_laps = await self.bot.lap_time_repository.find_all_by_user(user_id)
            
            embed = discord.Embed(
                title=f"📊 {interaction.user.display_name}'s Statistics",
                color=discord.Color.blue()
            )
            
            if stats['total_laps'] == 0:
                embed.description = "No lap times recorded yet. Use `/lap submit` to get started!"
                await interaction.followup.send(embed=embed)
                return
            
            # General stats
            embed.add_field(
                name="🏁 General",
                value=f"Total laps: {stats['total_laps']}\\n"
                      f"Personal bests: {stats['personal_bests']}\\n"
                      f"Track records: {stats['overall_bests']}",
                inline=True
            )
            
            # Best times by track (top 5)
            best_times_by_track = {}
            for lap in user_laps:
                track_key = lap.track_name.key
                if track_key not in best_times_by_track or lap.is_faster_than(best_times_by_track[track_key]):
                    best_times_by_track[track_key] = lap
            
            if best_times_by_track:
                best_times_text = ""
                for track_key, lap in list(best_times_by_track.items())[:5]:
                    pb_icon = "🏆" if lap.is_overall_best else "🎯"
                    best_times_text += f"{pb_icon} **{lap.track_name.short_name}** - `{lap.time_format}`\\n"
                
                embed.add_field(
                    name="🎯 Personal Bests",
                    value=best_times_text,
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in stats command: {e}")
            await interaction.followup.send("❌ Error retrieving statistics.", ephemeral=True)
    
    @app_commands.command(name="challenge", description="Get a random track challenge")
    async def random_challenge(self, interaction: discord.Interaction):
        """Show a random track for users to compete on."""
        await interaction.response.defer()
        
        try:
            # Get a random track
            random_track = TrackName.get_random_track()
            
            # Get current leaderboard for this track
            top_times = await self.bot.lap_time_repository.find_top_by_track(random_track, 3)
            
            embed = discord.Embed(
                title=f"🏆 Daily Challenge: {random_track.display_name}",
                description=f"🌍 **{random_track.country}** • Can you beat the current leaders?",
                color=discord.Color.gold()
            )
            
            # Add beautiful track visuals
            embed.set_image(url=random_track.image_url)
            embed.set_thumbnail(url=random_track.flag_url)
            
            # Show current top 3 if any
            if top_times:
                medals = ["🥇", "🥈", "🥉"]
                leaderboard_text = ""
                
                for i, lap_time in enumerate(top_times):
                    medal = medals[i] if i < len(medals) else f"`{i+1}.`"
                    leaderboard_text += f"{medal} **{lap_time.username}** - `{lap_time.time_format}`\\n"
                
                embed.add_field(
                    name="🏆 Current Leaders",
                    value=leaderboard_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎆 First to Set a Time!",
                    value="No times set yet - be the first to establish a benchmark!",
                    inline=False
                )
            
            embed.add_field(
                name="🏁 Get Started",
                value=f"Use `/lap submit <time> {random_track.key}` to submit your lap time!",
                inline=False
            )
            
            embed.set_footer(text="✨ Track challenges refresh daily - compete with your friends!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in challenge command: {e}")
            await interaction.followup.send("❌ Error generating challenge.", ephemeral=True)
    
    @app_commands.command(name="tracks", description="List all available tracks")
    async def list_tracks(self, interaction: discord.Interaction):
        """List all available F1 tracks."""
        await interaction.response.defer()
        
        try:
            valid_tracks = TrackName.get_all_valid_tracks()
            
            # Group tracks for better display
            official_tracks = []
            aliases = []
            
            for track in valid_tracks:
                try:
                    track_obj = TrackName(track)
                    if track == track_obj.key:  # This is an official track name
                        official_tracks.append(f"**{track}** - {track_obj.display_name}")
                except:
                    pass
            
            embed = discord.Embed(
                title="🏁 Available F1 Tracks",
                description="All tracks available for lap time submission",
                color=discord.Color.red()
            )
            
            # Split into chunks for Discord field limits
            chunk_size = 10
            for i in range(0, len(official_tracks), chunk_size):
                chunk = official_tracks[i:i+chunk_size]
                field_name = f"🏎️ Tracks {i//chunk_size + 1}" if i > 0 else "🏎️ F1 Tracks"
                embed.add_field(
                    name=field_name,
                    value="\\n".join(chunk),
                    inline=True
                )
            
            embed.set_footer(text="You can also use track aliases like 'cota', 'vegas', 'spa', etc.")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in tracks command: {e}")
            await interaction.followup.send("❌ Error retrieving track list.", ephemeral=True)
    
    @app_commands.command(name="init", description="Initialize leaderboard in this channel (Admin only)")
    @app_commands.describe(channel="Channel to set as leaderboard channel (optional)")
    @commands.has_permissions(administrator=True)
    async def init_leaderboard(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None
    ):
        """Initialize the leaderboard in a channel."""
        await interaction.response.defer()
        
        target_channel = channel or interaction.channel
        
        # Update bot configuration
        self.bot.leaderboard_channel_id = target_channel.id
        
        embed = discord.Embed(
            title="✅ Leaderboard Initialized",
            description=f"Leaderboard has been set up in {target_channel.mention}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Next Steps",
            value="Submit lap times with `/lap submit <time> <track>` to see the leaderboard update!",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
        # Send initial leaderboard message
        welcome_embed = discord.Embed(
            title="🏁 F1 Lap Time Leaderboard",
            description="Welcome to the F1 lap time tracking system!\\n\\n"
                       "Submit your lap times with `/lap submit <time> <track>`",
            color=discord.Color.red()
        )
        
        welcome_embed.add_field(
            name="📝 How to Submit",
            value="Use `/lap submit 1:23.456 monaco` to submit a time",
            inline=False
        )
        
        welcome_embed.add_field(
            name="🏆 Features",
            value="• Live leaderboard updates\\n"
                  "• Personal best tracking\\n"
                  "• Overtake notifications\\n"
                  "• Detailed statistics",
            inline=False
        )
        
        message = await target_channel.send(embed=welcome_embed)
        try:
            await message.pin()
            self.bot.leaderboard_message_id = message.id
        except discord.HTTPException:
            pass


# Create command group for lap commands
lap_group = app_commands.Group(name="lap", description="F1 lap time commands")

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(LapCommands(bot))
    
    # Add commands to the lap group
    cog = bot.get_cog('LapCommands')
    if cog:
        lap_group.add_command(cog.submit_lap_time)
        lap_group.add_command(cog.show_leaderboard)
        lap_group.add_command(cog.show_personal_stats)
        lap_group.add_command(cog.random_challenge)
        lap_group.add_command(cog.list_tracks)
        lap_group.add_command(cog.init_leaderboard)
        
        bot.tree.add_command(lap_group)
