"""Helper module for building Discord embeds efficiently."""
import discord
from typing import Optional, List, Tuple, Dict
from ...domain.entities.lap_time import LapTime
from ...domain.value_objects.track_name import TrackName


# Constants for medals and emojis
MEDALS = ["🥇", "🥈", "🥉"]
SKILL_EMOJIS = {
    "Legendary": "👑",
    "Master": "🔥",
    "Expert": "⚡",
    "Advanced": "🎯",
    "Intermediate": "📈",
    "Novice": "🌱",
    "Beginner": "🏁"
}

SKILL_COLORS = {
    "Legendary": discord.Color.from_rgb(255, 215, 0),  # Gold
    "Master": discord.Color.from_rgb(192, 192, 192),   # Silver
    "Expert": discord.Color.from_rgb(205, 127, 50),    # Bronze
    "Advanced": discord.Color.purple(),
    "Intermediate": discord.Color.blue(),
    "Novice": discord.Color.green(),
    "Beginner": discord.Color.light_grey()
}


class EmbedBuilder:
    """Helper class for building Discord embeds with common patterns."""
    
    @staticmethod
    def format_time_seconds(total_seconds: float) -> str:
        """Format seconds to MM:SS.mmm or SS.mmm format."""
        if total_seconds >= 60:
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
        return f"{total_seconds:.3f}s"
    
    @staticmethod
    def create_error_embed(title: str, description: str, add_examples: bool = False) -> discord.Embed:
        """Create a standard error embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )
        
        if add_examples and "track" in description.lower():
            examples = ["monaco", "silverstone", "spa", "monza", "cota"]
            embed.add_field(
                name="Example Tracks",
                value=f"`{', '.join(examples)}`\n\nUse `/lap tracks` to see all available tracks.",
                inline=False
            )
        
        return embed
    
    @staticmethod
    def add_track_visuals(embed: discord.Embed, track: TrackName) -> None:
        """Add track image and flag to embed."""
        embed.set_image(url=track.image_url)
        embed.set_thumbnail(url=track.flag_url)
    
    @staticmethod
    def format_position_icon(index: int) -> str:
        """Get position icon (medal or number)."""
        return MEDALS[index] if index < len(MEDALS) else f"`{index+1}.`"
    
    @staticmethod
    def get_skill_emoji(skill_level: str) -> str:
        """Get emoji for skill level."""
        return SKILL_EMOJIS.get(skill_level, "🏁")
    
    @staticmethod
    def get_skill_color(skill_level: str) -> discord.Color:
        """Get color based on skill level."""
        return SKILL_COLORS.get(skill_level, discord.Color.blue())
    
    @staticmethod
    def create_lap_submission_embed(
        lap_time: LapTime, 
        is_personal_best: bool, 
        is_overall_best: bool,
        format_time_func
    ) -> discord.Embed:
        """Create embed for lap submission result."""
        if is_overall_best:
            embed = discord.Embed(
                title="🏆 NEW TRACK RECORD!",
                description="Congratulations! You've set a new track record!",
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
        
        embed.add_field(name="Driver", value=lap_time.username, inline=True)
        embed.add_field(name="Time", value=f"`{lap_time.time_format}`", inline=True)
        embed.add_field(
            name="Track",
            value=f"🌍 **{lap_time.track_name.display_name}**\n({lap_time.track_name.country})",
            inline=True
        )
        
        # Add sector times if available
        if lap_time.sector1_ms or lap_time.sector2_ms or lap_time.sector3_ms:
            sector_text = ""
            if lap_time.sector1_ms and lap_time.sector1_ms > 0:
                sector_text += f"S1: `{format_time_func(lap_time.sector1_ms / 1000.0)}`\n"
            if lap_time.sector2_ms and lap_time.sector2_ms > 0:
                sector_text += f"S2: `{format_time_func(lap_time.sector2_ms / 1000.0)}`\n"
            if lap_time.sector3_ms and lap_time.sector3_ms > 0:
                sector_text += f"S3: `{format_time_func(lap_time.sector3_ms / 1000.0)}`"
            
            if sector_text:
                embed.add_field(name="🎯 Sectors", value=sector_text, inline=False)
        
        EmbedBuilder.add_track_visuals(embed, lap_time.track_name)
        return embed
    
    @staticmethod
    def create_leaderboard_embed(
        track: TrackName,
        top_times: List[LapTime],
        format_time_func
    ) -> discord.Embed:
        """Create embed for track leaderboard."""
        embed = discord.Embed(
            title=f"🏁 {track.display_name}",
            description=f"🌍 **{track.country}** • Top 10 fastest lap times",
            color=discord.Color.red()
        )
        
        EmbedBuilder.add_track_visuals(embed, track)
        
        if not top_times:
            embed.add_field(
                name="No times yet",
                value="Be the first to submit a lap time with `/lap submit`!",
                inline=False
            )
        else:
            leaderboard_text = ""
            for i, lap_time in enumerate(top_times):
                position_icon = EmbedBuilder.format_position_icon(i)
                gap_text = " 🏆" if i == 0 else ""
                
                if i > 0:
                    previous_time = top_times[i-1]
                    gap_seconds = lap_time.time_format.total_seconds - previous_time.time_format.total_seconds
                    gap_text = f" `(+{gap_seconds:.3f}s)`"
                
                leaderboard_text += f"{position_icon} **{lap_time.username}** - `{lap_time.time_format}`{gap_text}\n"
            
            embed.add_field(name="🏆 Leaderboard", value=leaderboard_text, inline=False)
        
        return embed
