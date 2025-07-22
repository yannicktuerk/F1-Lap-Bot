"""Discord slash commands for lap time management."""
import discord
import random
from discord.ext import commands
from discord import app_commands
from typing import Optional
from ...domain.value_objects.track_name import TrackName
from ...domain.value_objects.time_format import TimeFormat


class LapCommands(commands.Cog):
    """Cog containing all lap time related commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    def _format_time_seconds(self, total_seconds: float) -> str:
        """Format seconds to MM:SS.mmm or SS.mmm format."""
        if total_seconds >= 60:
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
        else:
            return f"{total_seconds:.3f}s"
    
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
                    value="• `1:23.456` (1 minute, 23.456 seconds)\n• `83.456` (83.456 seconds)",
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
                    
                    # Calculate gap to next position (or to leader if first position)
                    gap_text = ""
                    if i == 0:
                        gap_text = " 🏆"  # Leader indicator
                    elif i < len(top_times):
                        # Calculate gap to the position above (faster time)
                        previous_time = top_times[i-1]
                        gap_seconds = lap_time.time_format.total_seconds - previous_time.time_format.total_seconds
                        gap_text = f" `(+{gap_seconds:.3f}s)`"
                    
                    leaderboard_text += f"{position_icon} **{lap_time.username}** - `{lap_time.time_format}`{gap_text}\n"
                
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
                    value=f"Total laps: {stats['total_laps']}\n"
                          f"Drivers: {stats['unique_drivers']}\n"
                          f"Average: `{self._format_time_seconds(stats['average_time_seconds'])}`",
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
                value=f"`{tracks_text}`\n...and more",
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
                value=f"Total laps: {stats['total_laps']}\n"
                      f"Personal bests: {stats['personal_bests']}\n"
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
                    best_times_text += f"{pb_icon} **{lap.track_name.short_name}** - `{lap.time_format}`\n"
                
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
                    leaderboard_text += f"{medal} **{lap_time.username}** - `{lap_time.time_format}`\n"
                
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
    
    @app_commands.command(name="info", description="Show detailed information about a specific track")
    @app_commands.describe(track="Track name to get information about")
    async def track_info(self, interaction: discord.Interaction, track: str):
        """Show detailed information about a specific F1 track."""
        await interaction.response.defer()
        
        try:
            track_obj = TrackName(track)
            
            # Get track statistics
            stats = await self.bot.lap_time_repository.get_track_statistics(track_obj)
            
            embed = discord.Embed(
                title=f"🏁 {track_obj.display_name}",
                description=f"🌍 **{track_obj.country}** • Track Information & Statistics",
                color=discord.Color.purple()
            )
            
            # Add the track layout as main image
            embed.set_image(url=track_obj.image_url)
            # Add country flag as thumbnail
            embed.set_thumbnail(url=track_obj.flag_url)
            
            # Track details
            embed.add_field(
                name="🏎️ Track Details",
                value=f"**Official Name:** {track_obj.display_name}\n"
                      f"**Location:** {track_obj.country}",
                inline=True
            )
            
            
            # Statistics (if available)
            if stats and stats.get('total_laps', 0) > 0:
                embed.add_field(
                    name="📊 Track Statistics",
                    value=f"Total Laps: **{stats['total_laps']}**\n"
                          f"Drivers: **{stats['unique_drivers']}**\n"
                          f"Average Time: `{self._format_time_seconds(stats['average_time_seconds'])}`",
                    inline=True
                )
                
                # Get current record holder
                best_time = await self.bot.lap_time_repository.find_best_by_track(track_obj)
                if best_time:
                    embed.add_field(
                        name="🏆 Current Record",
                        value=f"🎆 **{best_time.username}**\n"
                              f"⏱️ `{best_time.time_format}`\n"
                              f"📅 {best_time.created_at.strftime('%Y-%m-%d')}",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="🎆 No Times Yet!",
                    value="Be the first to set a lap time on this track!\n"
                          "Your time will become the first track record! 🏆",
                    inline=False
                )
            
            
            
            await interaction.followup.send(embed=embed)
            
        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Track",
                description=str(e),
                color=discord.Color.red()
            )
            
            # Show some example tracks
            examples = ["monaco", "silverstone", "spa", "monza", "cota"]
            error_embed.add_field(
                name="Example Tracks",
                value=f"`{', '.join(examples)}`\n\nUse `/lap tracks` to see all available tracks.",
                inline=False
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Error in track info command: {e}")
            await interaction.followup.send("❌ Error retrieving track information.", ephemeral=True)
    
    @app_commands.command(name="delete", description="Delete a specific lap time for a track")
    @app_commands.describe(
        track="Track name to delete time from",
        time="Exact lap time to delete (format: 1:23.456 or 83.456)"
    )
    async def delete_lap_time(self, interaction: discord.Interaction, track: str, time: str):
        """Delete user's personal best time for a specific track."""
        await interaction.response.defer()
        
        try:
            track_obj = TrackName(track)
            user_id = str(interaction.user.id)
            
            # Convert time string to total milliseconds for exact matching
            time_format = TimeFormat(time)
            total_milliseconds = time_format.total_milliseconds

            # Find the specific lap time the user wants to delete
            lap_time = await self.bot.lap_time_repository.find_specific_lap_time(user_id, track_obj, total_milliseconds)
            
            if not lap_time:
                embed = discord.Embed(
                    title="❌ No Time Found",
                    description=f"No recorded time of `{time}` found for you on **{track_obj.display_name}**.",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=track_obj.flag_url)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Delete the time from repository
            success = await self.bot.lap_time_repository.delete_lap_time(lap_time.lap_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Time Deleted Successfully",
                    description=f"The time `{lap_time.time_format}` has been removed from **{track_obj.display_name}**.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="Deleted Time",
                    value=f"`{lap_time.time_format}`",
                    inline=True
                )
                
                embed.add_field(
                    name="Track",
                    value=f"🌍 **{track_obj.display_name}**\n({track_obj.country})",
                    inline=True
                )
                
                embed.set_image(url=track_obj.image_url)
                embed.set_thumbnail(url=track_obj.flag_url)
                
                await interaction.followup.send(embed=embed)
                
                # Update leaderboard after deletion
                await self.bot.update_leaderboard(track)
                
            else:
                embed = discord.Embed(
                    title="❌ Delete Failed",
                    description="Failed to delete the specified time. Please try again later.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Track",
                description=str(e),
                color=discord.Color.red()
            )
            
            examples = ["monaco", "silverstone", "spa", "monza", "cota"]
            error_embed.add_field(
                name="Example Tracks",
                value=f"`{', '.join(examples)}`\n\nUse `/lap tracks` to see all available tracks.",
                inline=False
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Error in delete command: {e}")
            await interaction.followup.send("❌ Error deleting time.", ephemeral=True)
    
    @app_commands.command(name="deleteall", description="Delete ALL your lap times for a specific track")
    @app_commands.describe(track="Track name to delete all times from")
    async def delete_all_lap_times(self, interaction: discord.Interaction, track: str):
        """Delete all lap times for a user on a specific track."""
        await interaction.response.defer()
        
        try:
            track_obj = TrackName(track)
            user_id = str(interaction.user.id)
            
            # Get user's current times on this track for confirmation
            user_times = await self.bot.lap_time_repository.find_user_times_by_track(user_id, track_obj)
            
            if not user_times:
                embed = discord.Embed(
                    title="❌ No Times Found",
                    description=f"You have no recorded times on **{track_obj.display_name}**.",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=track_obj.flag_url)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Show confirmation with times to be deleted
            times_list = "\n".join([f"• `{time.time_format}` ({time.created_at.strftime('%Y-%m-%d')})" for time in user_times[:10]])
            if len(user_times) > 10:
                times_list += f"\n... and {len(user_times) - 10} more times"
            
            # Create confirmation embed
            embed = discord.Embed(
                title="⚠️ Confirm Deletion",
                description=f"**Are you sure you want to delete ALL {len(user_times)} lap times on {track_obj.display_name}?**\n\n"
                           f"This action cannot be undone!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="Times to be deleted:",
                value=times_list,
                inline=False
            )
            
            embed.add_field(
                name="Track",
                value=f"🌍 **{track_obj.display_name}**\n({track_obj.country})",
                inline=True
            )
            
            embed.set_image(url=track_obj.image_url)
            embed.set_thumbnail(url=track_obj.flag_url)
            
            # Add confirmation buttons
            class ConfirmView(discord.ui.View):
                def __init__(self, timeout=60):
                    super().__init__(timeout=timeout)
                    self.confirmed = None
                
                @discord.ui.button(label="✅ Yes, Delete All", style=discord.ButtonStyle.danger)
                async def confirm_delete(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("❌ Only the original user can confirm this action.", ephemeral=True)
                        return
                    
                    self.confirmed = True
                    self.stop()
                    await button_interaction.response.defer()
                
                @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
                async def cancel_delete(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("❌ Only the original user can confirm this action.", ephemeral=True)
                        return
                    
                    self.confirmed = False
                    self.stop()
                    await button_interaction.response.defer()
            
            view = ConfirmView()
            message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
            # Wait for user confirmation
            await view.wait()
            
            if view.confirmed is None:  # Timeout
                embed.title = "⏰ Confirmation Timeout"
                embed.description = "Deletion cancelled due to timeout."
                embed.color = discord.Color.light_grey()
                await message.edit(embed=embed, view=None)
                return
            
            if not view.confirmed:  # User cancelled
                embed.title = "❌ Deletion Cancelled"
                embed.description = "Your lap times remain safe!"
                embed.color = discord.Color.green()
                await message.edit(embed=embed, view=None)
                return
            
            # User confirmed - proceed with deletion
            deleted_count = await self.bot.lap_time_repository.delete_all_user_times_by_track(user_id, track_obj)
            
            if deleted_count > 0:
                embed = discord.Embed(
                    title="🗑️ All Times Deleted Successfully",
                    description=f"**{deleted_count} lap times** have been removed from **{track_obj.display_name}**.",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="Deleted Times",
                    value=f"**{deleted_count}** lap times",
                    inline=True
                )
                
                embed.add_field(
                    name="Track",
                    value=f"🌍 **{track_obj.display_name}**\n({track_obj.country})",
                    inline=True
                )
                
                embed.set_image(url=track_obj.image_url)
                embed.set_thumbnail(url=track_obj.flag_url)
                embed.set_footer(text="You can start fresh with new lap times!")
                
                await message.edit(embed=embed, view=None)
                
                # Update leaderboard after deletion
                await self.bot.update_leaderboard(track)
                
            else:
                embed = discord.Embed(
                    title="❌ Delete Failed",
                    description="Failed to delete lap times. Please try again later.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed, view=None)
                
        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Track",
                description=str(e),
                color=discord.Color.red()
            )
            
            examples = ["monaco", "silverstone", "spa", "monza", "cota"]
            error_embed.add_field(
                name="Example Tracks",
                value=f"`{', '.join(examples)}`\n\nUse `/lap tracks` to see all available tracks.",
                inline=False
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Error in deleteall command: {e}")
            await interaction.followup.send("❌ Error deleting times.", ephemeral=True)
    
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
                    value="\n".join(chunk),
                    inline=True
                )
            
            embed.set_footer(text="You can also use track aliases like 'cota', 'vegas', 'spa', etc.")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in tracks command: {e}")
            await interaction.followup.send("❌ Error retrieving track list.", ephemeral=True)
    
    @app_commands.command(name="global", description="Show global leaderboard with all track records")
    async def show_global_leaderboard(self, interaction: discord.Interaction):
        """Show the global leaderboard with all track records."""
        await interaction.response.defer()
        
        try:
            from ...domain.value_objects.track_name import TrackName
            
            # Get all track keys
            all_track_keys = list(TrackName.TRACK_DATA.keys())
            
            embed = discord.Embed(
                title="🏆 Global F1 Leaderboard",
                description="Track record holders across all circuits",
                color=discord.Color.gold()
            )
            
            # Split tracks into chunks for multiple fields (Discord has field limits)
            chunk_size = 12
            track_chunks = [all_track_keys[i:i + chunk_size] for i in range(0, len(all_track_keys), chunk_size)]
            
            # Color scheme for different users - smaller symbols for compact display
            colors = ['⬤', '🟢', '🔵', '🟡', '🟠', '🟣', '🟤', '•', '●', '🔶']
            color_names = ['RED', 'GRN', 'BLU', 'YLW', 'ORG', 'PUR', 'BRN', 'BLK', 'DOT', 'DMD']
            user_colors = {}
            user_times = {}  # To store best times for legend
            
            for chunk_index, track_chunk in enumerate(track_chunks):
                leaderboard_text = ""
                
                for track_key in track_chunk:
                    try:
                        track = TrackName(track_key)
                        best_time = await self.bot.lap_time_repository.find_best_by_track(track)
                        
                        if best_time:
                            # Assign color if user doesn't have one
                            if best_time.username not in user_colors:
                                user_colors[best_time.username] = colors[len(user_colors) % len(colors)]
                                user_times[best_time.username] = []
                            
                            user_color = user_colors[best_time.username]
                            user_times[best_time.username].append((track.short_name, best_time.time_format))
                            
                            leaderboard_text += f"🏁 **{track.short_name}** - {user_color} `{best_time.time_format}`\n"
                        else:
                            leaderboard_text += f"🏁 **{track.short_name}** - `-`\n"
                    except Exception as e:
                        print(f"Error processing track {track_key}: {e}")
                        continue
                
                if leaderboard_text:
                    field_name = "🏆 Track Records" if chunk_index == 0 else f"🏆 Track Records ({chunk_index + 1})"
                    embed.add_field(
                        name=field_name,
                        value=leaderboard_text,
                        inline=True
                    )
            
            # Add compact color legend
            if user_colors:
                legend_items = []
                for username, color in list(user_colors.items())[:10]:  # Show more users
                    track_count = len(user_times.get(username, []))
                    # Abbreviate long usernames
                    short_name = username[:8] + ".." if len(username) > 8 else username
                    legend_items.append(f"{color}**{short_name}**({track_count})")
                
                if legend_items:
                    # Display in a compact grid format
                    legend_text = " • ".join(legend_items)
                    embed.add_field(
                        name="🎨 Drivers",
                        value=legend_text,
                        inline=False
                    )
            
            # Add overall statistics
            all_times = []
            total_drivers = set()
            for track_key in all_track_keys:
                try:
                    track = TrackName(track_key)
                    track_times = await self.bot.lap_time_repository.find_top_by_track(track, 100)  # Get all times
                    all_times.extend(track_times)
                    for time in track_times:
                        total_drivers.add(time.user_id)
                except:
                    continue
            
            if all_times:
                embed.add_field(
                    name="📊 Global Stats",
                    value=f"Total laps: {len(all_times)}\n"
                          f"Active drivers: {len(total_drivers)}\n"
                          f"Tracks with times: {len([k for k in all_track_keys if any(t.track_name.key == k for t in all_times)])}",
                    inline=True
                )
            
            embed.set_footer(text="🏁 Use /lap leaderboard <track> to see detailed track leaderboards")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in global leaderboard command: {e}")
            await interaction.followup.send("❌ Error retrieving global leaderboard.", ephemeral=True)
    
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
        
        # Send initial global leaderboard overview
        await self.bot.update_global_leaderboard()
    
    @app_commands.command(name="analytics", description="🔥 Advanced analytics and performance insights!")
    async def show_analytics(self, interaction: discord.Interaction):
        """Show advanced analytics dashboard."""
        await interaction.response.defer()
        
        try:
            from ...domain.value_objects.track_name import TrackName
            import statistics
            
            # Get all data for analysis
            all_track_keys = list(TrackName.TRACK_DATA.keys())
            all_times = []
            track_data = {}
            user_performance = {}
            
            for track_key in all_track_keys:
                try:
                    track = TrackName(track_key)
                    times = await self.bot.lap_time_repository.find_top_by_track(track, 100)
                    if times:
                        all_times.extend(times)
                        track_data[track_key] = {
                            'times': times,
                            'best': min(times, key=lambda x: x.time_format.total_seconds),
                            'worst': max(times, key=lambda x: x.time_format.total_seconds),
                            'avg': statistics.mean([t.time_format.total_seconds for t in times]),
                            'count': len(times)
                        }
                        
                        # Collect user performance data
                        for time in times:
                            if time.username not in user_performance:
                                user_performance[time.username] = []
                            user_performance[time.username].append(time.time_format.total_seconds)
                except:
                    continue
            
            if not all_times:
                embed = discord.Embed(
                    title="📊 Analytics Dashboard",
                    description="No data available yet. Submit some lap times to see analytics!",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📊 F1 Lap Bot Analytics Dashboard",
                description="🔥 **Performance insights and statistics across all tracks**",
                color=discord.Color.from_rgb(255, 20, 147)  # Hot pink for analytics
            )
            
            # 🏆 Hall of Fame - Most dominant drivers
            track_leaders = {}
            for track_key, data in track_data.items():
                leader = data['best'].username
                track_leaders[leader] = track_leaders.get(leader, 0) + 1
            
            if track_leaders:
                sorted_leaders = sorted(track_leaders.items(), key=lambda x: x[1], reverse=True)[:5]
                hall_of_fame = ""
                medals = ["👑", "🥇", "🥈", "🥉", "🏅"]
                for i, (driver, count) in enumerate(sorted_leaders):
                    medal = medals[i] if i < len(medals) else "🎖️"
                    hall_of_fame += f"{medal} **{driver}** - {count} track records\n"
                
                embed.add_field(
                    name="👑 Hall of Fame",
                    value=hall_of_fame,
                    inline=True
                )
            
            # 🚀 Speed Demons - Fastest overall times
            fastest_times = sorted(all_times, key=lambda x: x.time_format.total_seconds)[:5]
            speed_demons = ""
            for i, time in enumerate(fastest_times):
                speed_demons += f"🚀 **{time.track_name.short_name}** - {time.username} `{time.time_format}`\n"
            
            embed.add_field(
                name="🚀 Speed Demons",
                value=speed_demons,
                inline=True
            )
            
            # 📈 Track Difficulty Analysis
            if len(track_data) > 0:
                # Calculate track difficulty based on average times and spread
                track_difficulty = []
                for track_key, data in track_data.items():
                    if data['count'] >= 3:  # Need at least 3 times for meaningful stats
                        times = [t.time_format.total_seconds for t in data['times']]
                        std_dev = statistics.stdev(times) if len(times) > 1 else 0
                        difficulty_score = data['avg'] + (std_dev * 2)  # Higher = more difficult/inconsistent
                        track_difficulty.append((track_key, difficulty_score, data['avg']))
                
                if track_difficulty:
                    track_difficulty.sort(key=lambda x: x[1], reverse=True)
                    hardest_tracks = ""
                    difficulty_icons = ["💀", "🔥", "⚡", "🌪️", "💥"]
                    for i, (track_key, score, avg) in enumerate(track_difficulty[:5]):
                        track = TrackName(track_key)
                        icon = difficulty_icons[i] if i < len(difficulty_icons) else "🎯"
                        hardest_tracks += f"{icon} **{track.short_name}** - Avg: `{self._format_time_seconds(avg)}`\n"
                    
                    embed.add_field(
                        name="💀 Hardest Tracks",
                        value=hardest_tracks,
                        inline=True
                    )
            
            # 🎯 Consistency Kings - Most consistent drivers
            consistency_data = []
            for username, times in user_performance.items():
                if len(times) >= 5:  # Need at least 5 times
                    std_dev = statistics.stdev(times)
                    avg_time = statistics.mean(times)
                    consistency_score = 100 - (std_dev / avg_time * 100)  # Higher = more consistent
                    consistency_data.append((username, consistency_score, len(times)))
            
            if consistency_data:
                consistency_data.sort(key=lambda x: x[1], reverse=True)
                consistency_kings = ""
                for i, (driver, score, count) in enumerate(consistency_data[:5]):
                    consistency_kings += f"🎯 **{driver}** - {score:.1f}% ({count} laps)\n"
                
                embed.add_field(
                    name="🎯 Consistency Kings",
                    value=consistency_kings,
                    inline=True
                )
            
            # 🏃‍♂️ Most Active Drivers
            activity_data = [(username, len(times)) for username, times in user_performance.items()]
            activity_data.sort(key=lambda x: x[1], reverse=True)
            most_active = ""
            activity_icons = ["🏃‍♂️", "🚴‍♂️", "🏋️‍♂️", "🤾‍♂️", "🏊‍♂️"]
            for i, (driver, count) in enumerate(activity_data[:5]):
                icon = activity_icons[i] if i < len(activity_icons) else "🏃"
                most_active += f"{icon} **{driver}** - {count} total laps\n"
            
            embed.add_field(
                name="🏃‍♂️ Most Active",
                value=most_active,
                inline=True
            )
            
            # 📊 Global Statistics Summary
            total_unique_drivers = len(user_performance)
            total_laps = len(all_times)
            tracks_with_times = len([k for k in all_track_keys if k in track_data])
            overall_avg = statistics.mean([t.time_format.total_seconds for t in all_times])
            
            embed.add_field(
                name="📊 Global Summary",
                value=f"🏁 **{total_laps}** total laps\n"
                      f"🏎️ **{total_unique_drivers}** active drivers\n"
                      f"🏃‍♂️ **{tracks_with_times}**/{len(all_track_keys)} tracks with times\n"
                      f"⏱️ Avg lap time: `{self._format_time_seconds(overall_avg)}`",
                inline=True
            )
            
            embed.set_footer(text="🔥 Analytics update every time new lap times are submitted!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in analytics command: {e}")
            await interaction.followup.send("❌ Error generating analytics.", ephemeral=True)
    
    @app_commands.command(name="heatmap", description="🗺️ Show track popularity and performance heatmap")
    async def show_heatmap(self, interaction: discord.Interaction):
        """Show track popularity and performance heatmap."""
        await interaction.response.defer()
        
        try:
            from ...domain.value_objects.track_name import TrackName
            import statistics
            
            all_track_keys = list(TrackName.TRACK_DATA.keys())
            track_stats = {}
            
            # Collect data for each track
            for track_key in all_track_keys:
                try:
                    track = TrackName(track_key)
                    times = await self.bot.lap_time_repository.find_top_by_track(track, 100)
                    
                    if times:
                        track_stats[track_key] = {
                            'name': track.short_name,
                            'country': track.country,
                            'count': len(times),
                            'best_time': min(times, key=lambda x: x.time_format.total_seconds),
                            'avg_time': statistics.mean([t.time_format.total_seconds for t in times]),
                            'unique_drivers': len(set(t.username for t in times))
                        }
                    else:
                        track_stats[track_key] = {
                            'name': track.short_name,
                            'country': track.country,
                            'count': 0,
                            'best_time': None,
                            'avg_time': 0,
                            'unique_drivers': 0
                        }
                except:
                    continue
            
            embed = discord.Embed(
                title="🗺️ Track Heatmap & Popularity",
                description="🔥 **Track activity levels and performance overview**",
                color=discord.Color.from_rgb(255, 69, 0)  # Orange red for heatmap
            )
            
            # 🔥 Hottest Tracks (Most Popular)
            popular_tracks = sorted(
                [(k, v) for k, v in track_stats.items() if v['count'] > 0],
                key=lambda x: x[1]['count'],
                reverse=True
            )[:8]
            
            if popular_tracks:
                hottest_tracks = ""
                heat_levels = ["🔥🔥🔥", "🔥🔥", "🔥", "🌡️", "🌡️", "🌶️", "🌶️", "❄️"]
                for i, (track_key, data) in enumerate(popular_tracks):
                    heat = heat_levels[i] if i < len(heat_levels) else "❄️"
                    hottest_tracks += f"{heat} **{data['name']}** - {data['count']} laps ({data['unique_drivers']} drivers)\n"
                
                embed.add_field(
                    name="🔥 Hottest Tracks",
                    value=hottest_tracks,
                    inline=False
                )
            
            # 🏜️ Cold Tracks (Least Popular)
            cold_tracks = []
            for track_key, data in track_stats.items():
                if data['count'] == 0:
                    cold_tracks.append(data['name'])
                elif data['count'] <= 2:
                    cold_tracks.append(f"{data['name']} ({data['count']} laps)")
            
            if cold_tracks:
                cold_tracks_text = "❄️ " + ", ".join(cold_tracks[:10])
                if len(cold_tracks) > 10:
                    cold_tracks_text += f" and {len(cold_tracks) - 10} more..."
                
                embed.add_field(
                    name="❄️ Tracks Needing Love",
                    value=cold_tracks_text,
                    inline=False
                )
            
            # 🏎️ Speed Zones (Fastest Average Times)
            speed_zones = sorted(
                [(k, v) for k, v in track_stats.items() if v['count'] >= 3],
                key=lambda x: x[1]['avg_time']
            )[:5]
            
            if speed_zones:
                speed_zones_text = ""
                for track_key, data in speed_zones:
                    best_driver = data['best_time'].username if data['best_time'] else "N/A"
                    speed_zones_text += f"💨 **{data['name']}** - Avg: `{self._format_time_seconds(data['avg_time'])}` (Best: {best_driver})\n"
                
                embed.add_field(
                    name="💨 Speed Zones",
                    value=speed_zones_text,
                    inline=True
                )
            
            # 📊 Activity Overview
            total_active_tracks = len([t for t in track_stats.values() if t['count'] > 0])
            total_inactive_tracks = len([t for t in track_stats.values() if t['count'] == 0])
            total_laps = sum(t['count'] for t in track_stats.values())
            
            embed.add_field(
                name="📊 Track Overview",
                value=f"🏁 **{total_active_tracks}** active tracks\n"
                      f"❄️ **{total_inactive_tracks}** inactive tracks\n"
                      f"🏎️ **{total_laps}** total laps recorded\n"
                      f"🎯 Avg: **{total_laps / max(total_active_tracks, 1):.1f}** laps per active track",
                inline=True
            )
            
            embed.set_footer(text="🗺️ Set times on cold tracks to heat them up!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in heatmap command: {e}")
            await interaction.followup.send("❌ Error generating heatmap.", ephemeral=True)
    
    @app_commands.command(name="rivalries", description="⚔️ Show the most epic driver rivalries!")
    async def show_rivalries(self, interaction: discord.Interaction):
        """Show driver rivalries and head-to-head comparisons."""
        await interaction.response.defer()
        
        try:
            from ...domain.value_objects.track_name import TrackName
            
            all_track_keys = list(TrackName.TRACK_DATA.keys())
            user_track_times = {}  # {username: {track: best_time}}
            rivalries = {}  # {(user1, user2): {'battles': int, 'user1_wins': int, 'user2_wins': int}}
            
            # Collect each user's best time per track
            for track_key in all_track_keys:
                try:
                    track = TrackName(track_key)
                    times = await self.bot.lap_time_repository.find_top_by_track(track, 100)
                    
                    track_user_best = {}
                    for time in times:
                        if time.username not in track_user_best or time.is_faster_than(track_user_best[time.username]):
                            track_user_best[time.username] = time
                    
                    # Store each user's best time for this track
                    for username, best_time in track_user_best.items():
                        if username not in user_track_times:
                            user_track_times[username] = {}
                        user_track_times[username][track_key] = best_time
                except:
                    continue
            
            # Calculate rivalries
            usernames = list(user_track_times.keys())
            for i, user1 in enumerate(usernames):
                for j, user2 in enumerate(usernames[i+1:], i+1):
                    battles = 0
                    user1_wins = 0
                    user2_wins = 0
                    
                    # Check each track where both have times
                    for track_key in all_track_keys:
                        if track_key in user_track_times[user1] and track_key in user_track_times[user2]:
                            battles += 1
                            time1 = user_track_times[user1][track_key]
                            time2 = user_track_times[user2][track_key]
                            
                            if time1.is_faster_than(time2):
                                user1_wins += 1
                            else:
                                user2_wins += 1
                    
                    if battles >= 3:  # Only consider rivalries with at least 3 battles
                        rivalry_key = tuple(sorted([user1, user2]))
                        rivalries[rivalry_key] = {
                            'battles': battles,
                            'user1': user1 if user1 == rivalry_key[0] else user2,
                            'user2': user2 if user1 == rivalry_key[0] else user1,
                            'user1_wins': user1_wins if user1 == rivalry_key[0] else user2_wins,
                            'user2_wins': user2_wins if user1 == rivalry_key[0] else user1_wins
                        }
            
            embed = discord.Embed(
                title="⚔️ Epic Driver Rivalries",
                description="🔥 **Head-to-head battles across the circuit!**",
                color=discord.Color.from_rgb(220, 20, 60)  # Crimson for rivalries
            )
            
            if not rivalries:
                embed.add_field(
                    name="🤷‍♂️ No Rivalries Yet",
                    value="Need at least 2 drivers with 3+ head-to-head battles to show rivalries.\nGet racing!",
                    inline=False
                )
            else:
                # Sort by total battles and competitiveness
                sorted_rivalries = sorted(
                    rivalries.items(),
                    key=lambda x: (x[1]['battles'], abs(x[1]['user1_wins'] - x[1]['user2_wins'])),
                    reverse=True
                )
                
                rivalries_text = ""
                for i, ((user1, user2), data) in enumerate(sorted_rivalries[:6]):
                    battles = data['battles']
                    u1_wins = data['user1_wins']
                    u2_wins = data['user2_wins']
                    
                    # Determine rivalry intensity
                    if abs(u1_wins - u2_wins) <= 1:
                        intensity = "🔥🔥🔥"  # Super close
                    elif abs(u1_wins - u2_wins) <= 2:
                        intensity = "🔥🔥"    # Close
                    else:
                        intensity = "🔥"      # One-sided but still a rivalry
                    
                    rivalries_text += f"{intensity} **{data['user1']}** vs **{data['user2']}**\n"
                    rivalries_text += f"     `{u1_wins}-{u2_wins}` ({battles} battles)\n\n"
                
                embed.add_field(
                    name="🏆 Top Rivalries",
                    value=rivalries_text,
                    inline=False
                )
                
                # Most Dominant Driver
                driver_dominance = {}
                for (user1, user2), data in rivalries.items():
                    u1 = data['user1']
                    u2 = data['user2']
                    u1_wins = data['user1_wins']
                    u2_wins = data['user2_wins']
                    
                    if u1 not in driver_dominance:
                        driver_dominance[u1] = {'wins': 0, 'battles': 0}
                    if u2 not in driver_dominance:
                        driver_dominance[u2] = {'wins': 0, 'battles': 0}
                    
                    driver_dominance[u1]['wins'] += u1_wins
                    driver_dominance[u1]['battles'] += data['battles']
                    driver_dominance[u2]['wins'] += u2_wins
                    driver_dominance[u2]['battles'] += data['battles']
                
                # Calculate win rates
                dominant_drivers = []
                for driver, stats in driver_dominance.items():
                    if stats['battles'] >= 5:  # Minimum battles for consideration
                        win_rate = (stats['wins'] / stats['battles']) * 100
                        dominant_drivers.append((driver, win_rate, stats['wins'], stats['battles']))
                
                if dominant_drivers:
                    dominant_drivers.sort(key=lambda x: x[1], reverse=True)
                    dominance_text = ""
                    for i, (driver, win_rate, wins, battles) in enumerate(dominant_drivers[:5]):
                        crown = "👑" if i == 0 else "🏆" if i < 3 else "🥇"
                        dominance_text += f"{crown} **{driver}** - {win_rate:.1f}% ({wins}/{battles})\n"
                    
                    embed.add_field(
                        name="👑 Most Dominant",
                        value=dominance_text,
                        inline=True
                    )
            
            embed.set_footer(text="⚔️ Rivalries are based on head-to-head best times per track!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in rivalries command: {e}")
            await interaction.followup.send("❌ Error generating rivalries.", ephemeral=True)
    
    @app_commands.command(name="rating", description="🧠 Show your AI-powered ELO skill rating")
    async def show_driver_rating(self, interaction: discord.Interaction):
        """Show driver's ELO rating and skill assessment."""
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            
            # Get driver rating
            driver_rating = await self.bot.driver_rating_repository.find_by_user_id(user_id)
            
            if not driver_rating:
                embed = discord.Embed(
                    title="🏁 No Rating Yet",
                    description="Submit some lap times to get your ELO rating!\nUse `/lap submit <time> <track>` to start.",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Get user rank
            user_rank = await self.bot.driver_rating_repository.get_user_rank(user_id)
            
            embed = discord.Embed(
                title=f"🧠 {interaction.user.display_name}'s ELO Rating",
                description=f"**{driver_rating.skill_level}** Driver",
                color=self._get_skill_color(driver_rating.skill_level)
            )
            
            # Current ELO and Peak
            embed.add_field(
                name="⚡ Current Rating",
                value=f"`{driver_rating.current_elo}` ELO\n🏆 Peak: `{driver_rating.peak_elo}`",
                inline=True
            )
            
            # Rank and Performance
            rank_text = f"#{user_rank}" if user_rank else "Unranked"
            embed.add_field(
                name="🏁 Performance",
                value=f"Rank: **{rank_text}**\nMatches: **{driver_rating.matches_played}**\nWin Rate: **{driver_rating.win_rate:.1f}%**",
                inline=True
            )
            
            # Skill breakdown
            elo_trend = driver_rating.get_elo_trend()
            trend_emoji = "📈" if elo_trend > 0 else "📉" if elo_trend < 0 else "📊"
            
            embed.add_field(
                name="📊 Analysis",
                value=f"{trend_emoji} 7-day trend: `{elo_trend:+d}`\n🎯 Wins: **{driver_rating.wins}** | Losses: **{driver_rating.losses}**",
                inline=False
            )
            
            # Set user avatar as thumbnail
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            embed.set_footer(text=f"🏁 Last updated: {driver_rating.last_updated.strftime('%Y-%m-%d %H:%M')} UTC")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in rating command: {e}")
            await interaction.followup.send("❌ Error retrieving rating information.", ephemeral=True)
    
    def _get_skill_color(self, skill_level: str) -> discord.Color:
        """Get color based on skill level."""
        colors = {
            "Legendary": discord.Color.from_rgb(255, 215, 0),  # Gold
            "Master": discord.Color.from_rgb(192, 192, 192),   # Silver
            "Expert": discord.Color.from_rgb(205, 127, 50),    # Bronze
            "Advanced": discord.Color.purple(),
            "Intermediate": discord.Color.blue(),
            "Novice": discord.Color.green(),
            "Beginner": discord.Color.light_grey()
        }
        return colors.get(skill_level, discord.Color.blue())
    
    @app_commands.command(name="elo-leaderboard", description="🏆 Show the ELO rating leaderboard")
    async def show_elo_leaderboard(self, interaction: discord.Interaction):
        """Show the ELO rating leaderboard."""
        await interaction.response.defer()
        
        try:
            # Get top ratings
            top_ratings = await self.bot.driver_rating_repository.find_top_ratings(15)
            
            if not top_ratings:
                embed = discord.Embed(
                    title="🏁 ELO Leaderboard",
                    description="No ratings yet! Submit lap times to start earning ELO points.",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🏆 ELO Rating Leaderboard",
                description="**Top drivers ranked by skill rating**",
                color=discord.Color.gold()
            )
            
            # Build leaderboard text
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, rating in enumerate(top_ratings):
                position_icon = medals[i] if i < 3 else f"`{i+1}.`"
                skill_emoji = self._get_skill_emoji(rating.skill_level)
                
                leaderboard_text += (
                    f"{position_icon} **{rating.username}** {skill_emoji}\n"
                    f"     `{rating.current_elo}` ELO • {rating.win_rate:.1f}% WR ({rating.matches_played} matches)\n\n"
                )
            
            embed.add_field(
                name="🏁 Top Drivers",
                value=leaderboard_text,
                inline=False
            )
            
            # Add statistics
            all_ratings = await self.bot.driver_rating_repository.find_all_ratings()
            if all_ratings:
                avg_elo = sum(r.current_elo for r in all_ratings) / len(all_ratings)
                embed.add_field(
                    name="📊 League Stats",
                    value=f"Active drivers: **{len(all_ratings)}**\nAverage ELO: **{avg_elo:.0f}**",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in elo leaderboard command: {e}")
            await interaction.followup.send("❌ Error retrieving ELO leaderboard.", ephemeral=True)
    
    def _get_skill_emoji(self, skill_level: str) -> str:
        """Get emoji for skill level."""
        emojis = {
            "Legendary": "👑",
            "Master": "🔥",
            "Expert": "⚡",
            "Advanced": "🎯",
            "Intermediate": "📈",
            "Novice": "🌱",
            "Beginner": "🏁"
        }
        return emojis.get(skill_level, "🏁")
    
    @app_commands.command(name="reset", description="🗑️ Reset all lap times and data (Admin only)")
    @commands.has_permissions(administrator=True)
    async def reset_database(self, interaction: discord.Interaction):
        """Reset all lap times and data - ADMIN ONLY."""
        await interaction.response.defer(ephemeral=True)  # Make this ephemeral for security
        
        try:
            # Create confirmation embed
            embed = discord.Embed(
                title="⚠️ DANGER ZONE - DATABASE RESET",
                description="**🚨 This will permanently delete ALL data:**\n\n"
                           "• All lap times\n"
                           "• All ELO ratings\n"
                           "• All user statistics\n"
                           "• All leaderboard data\n\n"
                           "**⚠️ THIS CANNOT BE UNDONE!**",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🔒 Admin Action",
                value=f"Requested by: {interaction.user.mention}",
                inline=False
            )
            
            # Add confirmation buttons
            class ResetConfirmView(discord.ui.View):
                def __init__(self, timeout=120):  # 2 minute timeout for safety
                    super().__init__(timeout=timeout)
                    self.confirmed = None
                
                @discord.ui.button(
                    label="🗑️ YES, RESET EVERYTHING", 
                    style=discord.ButtonStyle.danger,
                    emoji="⚠️"
                )
                async def confirm_reset(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message(
                            "❌ Only the administrator who initiated this can confirm.", 
                            ephemeral=True
                        )
                        return
                    
                    self.confirmed = True
                    self.stop()
                    await button_interaction.response.defer()
                
                @discord.ui.button(
                    label="❌ Cancel - Keep Data Safe", 
                    style=discord.ButtonStyle.secondary,
                    emoji="🛡️"
                )
                async def cancel_reset(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message(
                            "❌ Only the administrator who initiated this can confirm.", 
                            ephemeral=True
                        )
                        return
                    
                    self.confirmed = False
                    self.stop()
                    await button_interaction.response.defer()
            
            view = ResetConfirmView()
            message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
            # Wait for confirmation
            await view.wait()
            
            if view.confirmed is None:  # Timeout
                embed.title = "⏰ Reset Timeout"
                embed.description = "Database reset cancelled due to timeout. All data remains safe."
                embed.color = discord.Color.light_grey()
                await message.edit(embed=embed, view=None)
                return
            
            if not view.confirmed:  # User cancelled
                embed.title = "✅ Reset Cancelled"
                embed.description = "Database reset cancelled. All data remains safe!"
                embed.color = discord.Color.green()
                await message.edit(embed=embed, view=None)
                return
            
            # User confirmed - proceed with reset
            embed = discord.Embed(
                title="🔄 Resetting Database...",
                description="Please wait while all data is being cleared...",
                color=discord.Color.orange()
            )
            await message.edit(embed=embed, view=None)
            
            # Perform the actual reset
            try:
                # Reset all repositories
                await self.bot.lap_time_repository.reset_all_data()
                await self.bot.driver_rating_repository.reset_all_data()
                
                # Success embed
                embed = discord.Embed(
                    title="✅ Database Reset Complete",
                    description="**All data has been successfully cleared:**\n\n"
                               "• All lap times deleted\n"
                               "• All ELO ratings reset\n"
                               "• All statistics cleared\n"
                               "• Leaderboards emptied\n\n"
                               "🚀 **Ready for fresh data!** Users can start submitting new lap times.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🔄 Next Steps",
                    value="Users can now start fresh with `/lap submit <time> <track>`",
                    inline=False
                )
                
                embed.set_footer(
                    text=f"Reset completed by {interaction.user.display_name} at {interaction.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                )
                
                await message.edit(embed=embed)
                
                # Also send a public notification (optional - remove if you want it to be completely silent)
                public_embed = discord.Embed(
                    title="🔄 Database Reset",
                    description="The F1 Lap Bot database has been reset by an administrator.\n\n"
                               "🚀 **Ready to race again!** Submit your lap times with `/lap submit <time> <track>`",
                    color=discord.Color.blue()
                )
                
                # Send to the same channel (you can modify this to send to a specific channel)
                await interaction.followup.send(embed=public_embed, ephemeral=False)
                
            except Exception as reset_error:
                embed = discord.Embed(
                    title="❌ Reset Failed",
                    description=f"An error occurred during database reset:\n`{str(reset_error)}`\n\nPlease check logs and try again.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
                print(f"❌ Database reset error: {reset_error}")
        
        except Exception as e:
            print(f"❌ Error in reset command: {e}")
            error_embed = discord.Embed(
                title="❌ Reset Command Error",
                description="An error occurred while processing the reset command.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @app_commands.command(name="help", description="📚 Show all available F1 Lap Bot commands and features")
    async def show_help(self, interaction: discord.Interaction):
        """Show comprehensive help with all available commands and features."""
        await interaction.response.defer()
        
        try:
            embed = discord.Embed(
                title="🏁 F1 Lap Bot - Command Overview",
                description="**🚀 Your ultimate F1 lap time tracking companion!**\n\nTrack lap times, compete with friends, and analyze performance across all F1 circuits.",
                color=discord.Color.from_rgb(229, 43, 80)  # F1 Red
            )
            
            # Basic Commands
            basic_commands = (
                "`/lap submit <time> <track>` - Submit your lap time\n"
                "`/lap leaderboard <track>` - Track-specific leaderboard\n"
                "`/lap global` - Global leaderboard (all tracks)\n"
                "`/lap stats` - Your personal statistics\n"
                "`/lap tracks` - List all available tracks\n"
                "`/lap info <track>` - Detailed track information\n"
                "`/lap challenge` - Get a random track challenge\n"
                "`/lap delete <track> <time>` - Delete specific lap time\n"
                "`/lap deleteall <track>` - Delete ALL your times for a track"
            )
            
            embed.add_field(
                name="🏁 Basic Commands",
                value=basic_commands,
                inline=False
            )
            
            # Analytics Commands
            analytics_commands = (
                "`/lap analytics` - 📊 Advanced performance dashboard\n"
                "`/lap heatmap` - 🗺️ Track popularity & performance heatmap\n"
                "`/lap rivalries` - ⚔️ Epic driver rivalries & head-to-head stats"
            )
            
            # ELO Rating Commands
            elo_commands = (
                "`/lap rating` - 🧠 Your AI-powered ELO skill rating\n"
                "`/lap elo-leaderboard` - 🏆 ELO rating leaderboard"
            )
            
            embed.add_field(
                name="📊 Analytics Commands",
                value=analytics_commands,
                inline=False
            )
            
            embed.add_field(
                name="🧠 ELO Rating Commands",
                value=elo_commands,
                inline=False
            )
            
            # Time Format Examples
            time_formats = (
                "• `1:23.456` - 1 minute, 23.456 seconds\n"
                "• `83.456` - 83.456 seconds\n\n"
                "**⚡ Valid Range:** 30 seconds - 5 minutes"
            )
            
            embed.add_field(
                name="⏱️ Time Formats",
                value=time_formats,
                inline=True
            )
            
            # Track Examples
            track_examples = (
                "• `monaco` - Monaco Grand Prix\n"
                "• `silverstone` - British GP\n"
                "• `spa` - Belgian GP\n"
                "• `houston` or `usa` - US GP\n"
                "• `baku` or `azerbaijan` - Azerbaijan GP\n\n"
                "**💡 Pro-Tip:** Use city names too!"
            )
            
            embed.add_field(
                name="🏎️ Track Examples",
                value=track_examples,
                inline=True
            )
            
            # Analytics Features
            analytics_features = (
                "🏆 **Hall of Fame** - Most dominant drivers\n"
                "🚀 **Speed Demons** - Fastest overall times\n"
                "💀 **Track Difficulty** - Consistency analysis\n"
                "🎯 **Consistency Kings** - Most consistent drivers\n"
                "🔥 **Track Heatmap** - Popularity visualization\n"
                "⚔️ **Driver Rivalries** - Head-to-head battles"
            )
            
            embed.add_field(
                name="🔥 Analytics Features",
                value=analytics_features,
                inline=False
            )
            
            # Quick Start
            quick_start = (
                "**1.** `/lap submit 1:23.456 monaco` - Submit your first time\n"
                "**2.** `/lap leaderboard monaco` - See the competition\n"
                "**3.** `/lap global` - Check all track records\n"
                "**4.** `/lap analytics` - Dive into advanced stats!\n\n"
                "**🎯 Ready to race?** Start with any track and climb the leaderboards!"
            )
            
            embed.add_field(
                name="🚀 Quick Start Guide",
                value=quick_start,
                inline=False
            )
            
            embed.set_footer(
                text="🏁 F1 Lap Bot v1.3.0 • Built for speed and analytics • Ready to race?"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in help command: {e}")
            await interaction.followup.send("❌ Error displaying help.", ephemeral=True)


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
        lap_group.add_command(cog.track_info)
        lap_group.add_command(cog.delete_lap_time)
        lap_group.add_command(cog.delete_all_lap_times)
        lap_group.add_command(cog.list_tracks)
        lap_group.add_command(cog.show_global_leaderboard)
        lap_group.add_command(cog.show_analytics)
        lap_group.add_command(cog.show_heatmap)
        lap_group.add_command(cog.show_rivalries)
        lap_group.add_command(cog.show_driver_rating)
        lap_group.add_command(cog.show_elo_leaderboard)
        lap_group.add_command(cog.show_help)
        lap_group.add_command(cog.init_leaderboard)
        lap_group.add_command(cog.reset_database)
        
        bot.tree.add_command(lap_group)
