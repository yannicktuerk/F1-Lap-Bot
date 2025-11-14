"""Domain service for generating human-readable coaching feedback.

This module implements MatheCoachFeedbackGenerator which translates technical
lap comparison data into actionable driving advice for human drivers. Uses
racing terminology and physics principles to explain where and why time is lost.
"""

from typing import List
from .lap_comparator import ComparisonSegment, ErrorType
from ..entities.track_profile import TrackProfile


class MatheCoachFeedbackGenerator:
    """Domain service for generating coaching feedback from lap analysis.
    
    Transforms technical comparison data (speed deltas, time losses) into
    human-readable coaching messages with actionable advice. Uses racing
    terminology and physics explanations to help drivers understand their
    mistakes and improve lap times.
    """
    
    def __init__(self, use_emojis: bool = True):
        """Initialize feedback generator.
        
        Args:
            use_emojis: Whether to include emojis in feedback (default: True).
                Useful for Discord formatting.
        """
        self.use_emojis = use_emojis
    
    def generate_feedback(
        self,
        comparison_segments: List[ComparisonSegment],
        track_profile: TrackProfile,
        track_name: str = None,
        top_n: int = 5
    ) -> str:
        """Generate Markdown-formatted coaching feedback.
        
        Creates a structured feedback message highlighting the most impactful
        areas for improvement. Includes:
        - Total time loss summary
        - Top N segments ranked by time loss
        - Specific advice for each segment
        - Physics-based explanations
        
        Args:
            comparison_segments: List of ComparisonSegment objects (sorted by time_loss).
            track_profile: Track geometry for context.
            track_name: Human-readable track name (default: from track_profile).
            top_n: Number of segments to include in feedback (default: 5).
        
        Returns:
            Markdown-formatted string with coaching feedback.
        """
        if not comparison_segments:
            return self._generate_perfect_lap_feedback(track_name or "Unknown Track")
        
        # Use track name from profile if not provided
        if track_name is None:
            track_name = track_profile.track_id or "Unknown Track"
        
        # Calculate total time loss
        total_loss = sum(seg.time_loss for seg in comparison_segments)
        
        # Build feedback message
        lines = []
        
        # Header
        if self.use_emojis:
            lines.append(f"📊 **Lap Analysis: {track_name}**")
        else:
            lines.append(f"**Lap Analysis: {track_name}**")
        lines.append("")
        
        # Total time loss
        if self.use_emojis:
            lines.append(f"⏱️ Total time vs ideal: **+{total_loss:.2f}s**")
        else:
            lines.append(f"Total time vs ideal: **+{total_loss:.2f}s**")
        lines.append("")
        
        # Top improvement areas
        if self.use_emojis:
            lines.append("🎯 **Top Improvement Areas:**")
        else:
            lines.append("**Top Improvement Areas:**")
        lines.append("")
        
        # Add feedback for top N segments
        segments_to_show = comparison_segments[:top_n]
        for i, segment in enumerate(segments_to_show, 1):
            segment_feedback = self._format_segment_feedback(
                segment, i, track_profile
            )
            lines.extend(segment_feedback)
            lines.append("")  # Blank line between segments
        
        # Overall summary advice
        summary = self._generate_summary_advice(segments_to_show)
        if self.use_emojis:
            lines.append(f"📈 **Overall advice:** {summary}")
        else:
            lines.append(f"**Overall advice:** {summary}")
        
        return "\n".join(lines)
    
    def _generate_perfect_lap_feedback(self, track_name: str) -> str:
        """Generate feedback when no time loss detected (perfect lap)."""
        if self.use_emojis:
            return (
                f"🏆 **Perfect Lap: {track_name}**\n\n"
                "✨ Congratulations! Your lap matches the ideal line.\n"
                "No significant time losses detected. Excellent driving!"
            )
        else:
            return (
                f"**Perfect Lap: {track_name}**\n\n"
                "Congratulations! Your lap matches the ideal line.\n"
                "No significant time losses detected. Excellent driving!"
            )
    
    def _format_segment_feedback(
        self,
        segment: ComparisonSegment,
        rank: int,
        track_profile: TrackProfile
    ) -> List[str]:
        """Format feedback for a single segment.
        
        Args:
            segment: ComparisonSegment with analysis data.
            rank: Ranking number (1-based).
            track_profile: Track geometry for context.
        
        Returns:
            List of strings (lines) for this segment.
        """
        lines = []
        
        # Segment header with rank
        if self.use_emojis:
            rank_emoji = self._get_rank_emoji(rank)
            lines.append(f"{rank_emoji} **Segment {segment.segment_id}** ({segment.time_loss:.2f}s loss)")
        else:
            lines.append(f"**{rank}. Segment {segment.segment_id}** ({segment.time_loss:.2f}s loss)")
        
        # Distance range
        lines.append(f"   📍 Distance: {segment.distance_start:.0f}m - {segment.distance_end:.0f}m")
        
        # Error-specific details and advice
        error_lines = self._generate_error_specific_feedback(segment)
        lines.extend(error_lines)
        
        return lines
    
    def _generate_error_specific_feedback(
        self,
        segment: ComparisonSegment
    ) -> List[str]:
        """Generate error-specific feedback based on error type.
        
        Args:
            segment: ComparisonSegment with error classification.
        
        Returns:
            List of feedback lines specific to this error type.
        """
        lines = []
        
        # Convert speed deltas from m/s to km/h for human readability
        entry_kmh = segment.speed_delta_entry * 3.6
        apex_kmh = segment.speed_delta_apex * 3.6
        exit_kmh = segment.speed_delta_exit * 3.6
        
        if segment.error_type == ErrorType.EARLY_BRAKING:
            lines.append(f"   • ⚠️ Braking too early")
            lines.append(f"   • Entry speed: {entry_kmh:+.1f} km/h vs ideal")
            if self.use_emojis:
                lines.append(f"   • 💡 **Tip:** Brake later! Physics allows more grip here.")
            else:
                lines.append(f"   • **Tip:** Brake later! Physics allows more grip here.")
        
        elif segment.error_type == ErrorType.LATE_BRAKING:
            lines.append(f"   • ⚠️ Braking too late")
            lines.append(f"   • Apex speed: {apex_kmh:+.1f} km/h vs ideal")
            if self.use_emojis:
                lines.append(f"   • 💡 **Tip:** Brake earlier to hit the correct apex speed.")
            else:
                lines.append(f"   • **Tip:** Brake earlier to hit the correct apex speed.")
        
        elif segment.error_type == ErrorType.SLOW_CORNER:
            lines.append(f"   • ⚠️ Slow through entire corner")
            lines.append(f"   • Apex speed: {apex_kmh:+.1f} km/h vs ideal")
            if self.use_emojis:
                lines.append(f"   • 💡 **Tip:** Carry more mid-corner speed. The grip circle allows it.")
            else:
                lines.append(f"   • **Tip:** Carry more mid-corner speed. The grip circle allows it.")
        
        elif segment.error_type == ErrorType.LATE_THROTTLE:
            lines.append(f"   • ⚠️ Throttle application too late")
            lines.append(f"   • Exit speed: {exit_kmh:+.1f} km/h vs ideal")
            if self.use_emojis:
                lines.append(f"   • 💡 **Tip:** Get on throttle earlier on corner exit.")
            else:
                lines.append(f"   • **Tip:** Get on throttle earlier on corner exit.")
        
        elif segment.error_type == ErrorType.LINE_ERROR:
            lines.append(f"   • ⚠️ Suboptimal racing line")
            lines.append(f"   • Speed variance: entry {entry_kmh:+.1f}, apex {apex_kmh:+.1f}, exit {exit_kmh:+.1f} km/h")
            if self.use_emojis:
                lines.append(f"   • 💡 **Tip:** Review the racing line for this section.")
            else:
                lines.append(f"   • **Tip:** Review the racing line for this section.")
        
        return lines
    
    def _generate_summary_advice(
        self,
        segments: List[ComparisonSegment]
    ) -> str:
        """Generate overall summary advice based on error patterns.
        
        Analyzes the top segments to identify common patterns and provide
        overarching advice.
        
        Args:
            segments: List of top ComparisonSegment objects.
        
        Returns:
            Summary advice string.
        """
        if not segments:
            return "Keep up the excellent driving!"
        
        # Count error types
        error_counts = {}
        for segment in segments:
            error_type = segment.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Find most common error
        most_common_error = max(error_counts, key=error_counts.get)
        
        # Generate advice based on patterns
        if most_common_error == ErrorType.LATE_THROTTLE:
            return "Focus on corner exits for maximum time gains!"
        elif most_common_error == ErrorType.EARLY_BRAKING:
            return "Trust the brakes! You can brake later in most corners."
        elif most_common_error == ErrorType.LATE_BRAKING:
            return "Brake earlier to maintain control through corner apexes."
        elif most_common_error == ErrorType.SLOW_CORNER:
            return "Build confidence to carry more mid-corner speed."
        else:  # LINE_ERROR
            return "Review the racing line to find the optimal path."
    
    def _get_rank_emoji(self, rank: int) -> str:
        """Get emoji for ranking number.
        
        Args:
            rank: Ranking number (1-based).
        
        Returns:
            Emoji string for the rank.
        """
        emoji_map = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟"
        }
        return emoji_map.get(rank, f"{rank}.")
    
    def generate_compact_feedback(
        self,
        comparison_segments: List[ComparisonSegment],
        track_name: str = None,
        top_n: int = 3
    ) -> str:
        """Generate compact feedback for limited space (e.g., mobile).
        
        Args:
            comparison_segments: List of ComparisonSegment objects.
            track_name: Track name.
            top_n: Number of segments to include (default: 3).
        
        Returns:
            Compact feedback string.
        """
        if not comparison_segments:
            return f"Perfect lap on {track_name or 'track'}!"
        
        total_loss = sum(seg.time_loss for seg in comparison_segments)
        lines = [f"**{track_name or 'Track'}:** +{total_loss:.2f}s vs ideal"]
        
        for i, seg in enumerate(comparison_segments[:top_n], 1):
            error_emoji = self._get_error_emoji(seg.error_type)
            lines.append(f"{i}. {error_emoji} Seg {seg.segment_id}: -{seg.time_loss:.2f}s")
        
        return "\n".join(lines)
    
    def _get_error_emoji(self, error_type: ErrorType) -> str:
        """Get emoji for error type."""
        if not self.use_emojis:
            return ""
        
        emoji_map = {
            ErrorType.EARLY_BRAKING: "🛑",
            ErrorType.LATE_BRAKING: "⚡",
            ErrorType.SLOW_CORNER: "🐌",
            ErrorType.LATE_THROTTLE: "🚀",
            ErrorType.LINE_ERROR: "〰️"
        }
        return emoji_map.get(error_type, "⚠️")
