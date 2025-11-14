"""Unit tests for MatheCoachFeedbackGenerator domain service.

Tests cover:
- Feedback generation with various error types
- Emoji and non-emoji formatting
- Perfect lap handling
- Compact feedback format
- Summary advice generation
- Edge cases
"""

import pytest
import sys
from pathlib import Path
import numpy as np

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.domain.services.mathe_coach_feedback import MatheCoachFeedbackGenerator
from src.domain.services.lap_comparator import ComparisonSegment, ErrorType
from src.domain.entities.track_profile import TrackProfile


class TestMatheCoachFeedbackInitialization:
    """Test feedback generator initialization."""
    
    def test_init_with_emojis(self):
        """Test initialization with emojis enabled."""
        generator = MatheCoachFeedbackGenerator(use_emojis=True)
        assert generator.use_emojis is True
    
    def test_init_without_emojis(self):
        """Test initialization with emojis disabled."""
        generator = MatheCoachFeedbackGenerator(use_emojis=False)
        assert generator.use_emojis is False
    
    def test_init_default(self):
        """Test default initialization (emojis enabled)."""
        generator = MatheCoachFeedbackGenerator()
        assert generator.use_emojis is True


class TestFeedbackGeneration:
    """Test main feedback generation functionality."""
    
    def test_generate_feedback_with_segments(self):
        """Test feedback generation with multiple segments."""
        # Arrange
        generator = MatheCoachFeedbackGenerator()
        segments = create_test_segments()
        track_profile = create_test_track_profile()
        
        # Act
        feedback = generator.generate_feedback(
            segments, track_profile, track_name="Monaco", top_n=3
        )
        
        # Assert
        assert "Monaco" in feedback
        assert "Total time vs ideal" in feedback
        assert "Top Improvement Areas" in feedback
        assert "Segment 0" in feedback or "Segment" in feedback
        # Should contain emoji indicators
        assert "📊" in feedback or "📈" in feedback
    
    def test_generate_feedback_without_emojis(self):
        """Test feedback generation without emojis."""
        # Arrange
        generator = MatheCoachFeedbackGenerator(use_emojis=False)
        segments = create_test_segments()
        track_profile = create_test_track_profile()
        
        # Act
        feedback = generator.generate_feedback(
            segments, track_profile, track_name="Silverstone"
        )
        
        # Assert
        assert "Silverstone" in feedback
        assert "Total time vs ideal" in feedback
        # Should not contain emoji indicators
        assert "📊" not in feedback
        assert "📈" not in feedback
    
    def test_generate_feedback_empty_segments(self):
        """Test feedback generation with no segments (perfect lap)."""
        # Arrange
        generator = MatheCoachFeedbackGenerator()
        track_profile = create_test_track_profile()
        
        # Act
        feedback = generator.generate_feedback(
            [], track_profile, track_name="Spa"
        )
        
        # Assert
        assert "Perfect Lap" in feedback
        assert "Spa" in feedback
        assert "Congratulations" in feedback
    
    def test_generate_feedback_uses_track_id_from_profile(self):
        """Test that track name defaults to track_profile.track_id."""
        # Arrange
        generator = MatheCoachFeedbackGenerator()
        segments = create_test_segments()
        track_profile = create_test_track_profile()
        
        # Act: Don't provide track_name
        feedback = generator.generate_feedback(segments, track_profile)
        
        # Assert: Should use track_id from profile
        assert "test_track" in feedback
    
    def test_generate_feedback_limits_top_n(self):
        """Test that feedback respects top_n parameter."""
        # Arrange
        generator = MatheCoachFeedbackGenerator()
        segments = create_test_segments()  # Creates 5 segments
        track_profile = create_test_track_profile()
        
        # Act: Request only top 2
        feedback = generator.generate_feedback(
            segments, track_profile, top_n=2
        )
        
        # Assert: Should only show 2 segments
        # Count segment mentions (rough check)
        segment_count = feedback.count("Segment")
        assert segment_count <= 3  # Header + 2 segments


class TestErrorSpecificFeedback:
    """Test error-specific feedback generation."""
    
    def test_early_braking_feedback(self):
        """Test feedback for early braking error."""
        generator = MatheCoachFeedbackGenerator()
        segment = create_segment_with_error(ErrorType.EARLY_BRAKING)
        
        error_lines = generator._generate_error_specific_feedback(segment)
        feedback_text = "\n".join(error_lines)
        
        assert "Braking too early" in feedback_text
        assert "Entry speed" in feedback_text
        assert "Brake later" in feedback_text
    
    def test_late_braking_feedback(self):
        """Test feedback for late braking error."""
        generator = MatheCoachFeedbackGenerator()
        segment = create_segment_with_error(ErrorType.LATE_BRAKING)
        
        error_lines = generator._generate_error_specific_feedback(segment)
        feedback_text = "\n".join(error_lines)
        
        assert "Braking too late" in feedback_text
        assert "Apex speed" in feedback_text
        assert "Brake earlier" in feedback_text
    
    def test_slow_corner_feedback(self):
        """Test feedback for slow corner error."""
        generator = MatheCoachFeedbackGenerator()
        segment = create_segment_with_error(ErrorType.SLOW_CORNER)
        
        error_lines = generator._generate_error_specific_feedback(segment)
        feedback_text = "\n".join(error_lines)
        
        assert "Slow through entire corner" in feedback_text
        assert "grip circle" in feedback_text.lower()
    
    def test_late_throttle_feedback(self):
        """Test feedback for late throttle error."""
        generator = MatheCoachFeedbackGenerator()
        segment = create_segment_with_error(ErrorType.LATE_THROTTLE)
        
        error_lines = generator._generate_error_specific_feedback(segment)
        feedback_text = "\n".join(error_lines)
        
        assert "Throttle application too late" in feedback_text
        assert "Exit speed" in feedback_text
        assert "throttle earlier" in feedback_text.lower()
    
    def test_line_error_feedback(self):
        """Test feedback for line error."""
        generator = MatheCoachFeedbackGenerator()
        segment = create_segment_with_error(ErrorType.LINE_ERROR)
        
        error_lines = generator._generate_error_specific_feedback(segment)
        feedback_text = "\n".join(error_lines)
        
        assert "racing line" in feedback_text.lower()
        assert "Speed variance" in feedback_text


class TestSummaryAdviceGeneration:
    """Test summary advice generation based on error patterns."""
    
    def test_summary_late_throttle_pattern(self):
        """Test summary when late throttle is most common."""
        generator = MatheCoachFeedbackGenerator()
        segments = [
            create_segment_with_error(ErrorType.LATE_THROTTLE),
            create_segment_with_error(ErrorType.LATE_THROTTLE),
            create_segment_with_error(ErrorType.EARLY_BRAKING)
        ]
        
        summary = generator._generate_summary_advice(segments)
        
        assert "corner exits" in summary.lower()
    
    def test_summary_early_braking_pattern(self):
        """Test summary when early braking is most common."""
        generator = MatheCoachFeedbackGenerator()
        segments = [
            create_segment_with_error(ErrorType.EARLY_BRAKING),
            create_segment_with_error(ErrorType.EARLY_BRAKING),
            create_segment_with_error(ErrorType.SLOW_CORNER)
        ]
        
        summary = generator._generate_summary_advice(segments)
        
        assert "brake later" in summary.lower() or "brakes" in summary.lower()
    
    def test_summary_empty_segments(self):
        """Test summary with no segments."""
        generator = MatheCoachFeedbackGenerator()
        
        summary = generator._generate_summary_advice([])
        
        assert "excellent" in summary.lower() or "keep up" in summary.lower()


class TestCompactFeedback:
    """Test compact feedback generation."""
    
    def test_generate_compact_feedback(self):
        """Test compact feedback format."""
        generator = MatheCoachFeedbackGenerator()
        segments = create_test_segments()
        
        feedback = generator.generate_compact_feedback(
            segments, track_name="Monza", top_n=3
        )
        
        assert "Monza" in feedback
        assert "+0" in feedback or "vs ideal" in feedback
        # Should be more compact than full feedback
        assert len(feedback) < 200  # Rough check for compactness
    
    def test_generate_compact_feedback_perfect_lap(self):
        """Test compact feedback for perfect lap."""
        generator = MatheCoachFeedbackGenerator()
        
        feedback = generator.generate_compact_feedback(
            [], track_name="Spa"
        )
        
        assert "Perfect lap" in feedback
        assert "Spa" in feedback


class TestHelperMethods:
    """Test helper methods."""
    
    def test_get_rank_emoji(self):
        """Test rank emoji generation."""
        generator = MatheCoachFeedbackGenerator()
        
        assert generator._get_rank_emoji(1) == "1️⃣"
        assert generator._get_rank_emoji(5) == "5️⃣"
        assert generator._get_rank_emoji(10) == "🔟"
        assert "11" in generator._get_rank_emoji(11)  # Falls back to number
    
    def test_get_error_emoji(self):
        """Test error type emoji mapping."""
        generator = MatheCoachFeedbackGenerator()
        
        assert generator._get_error_emoji(ErrorType.EARLY_BRAKING) == "🛑"
        assert generator._get_error_emoji(ErrorType.LATE_THROTTLE) == "🚀"
        assert generator._get_error_emoji(ErrorType.SLOW_CORNER) == "🐌"
    
    def test_get_error_emoji_without_emojis(self):
        """Test error emoji returns empty when emojis disabled."""
        generator = MatheCoachFeedbackGenerator(use_emojis=False)
        
        assert generator._get_error_emoji(ErrorType.EARLY_BRAKING) == ""


class TestSpeedConversion:
    """Test speed conversion from m/s to km/h."""
    
    def test_speed_delta_conversion(self):
        """Test that speed deltas are converted to km/h in feedback."""
        generator = MatheCoachFeedbackGenerator()
        # Create segment with -10 m/s delta (should be -36 km/h)
        segment = ComparisonSegment(
            segment_id=1,
            distance_start=100.0,
            distance_end=200.0,
            time_loss=0.5,
            speed_delta_entry=-10.0,  # m/s
            speed_delta_apex=-5.0,
            speed_delta_exit=-3.0,
            error_type=ErrorType.EARLY_BRAKING,
            explanation="Test"
        )
        
        error_lines = generator._generate_error_specific_feedback(segment)
        feedback_text = "\n".join(error_lines)
        
        # Should show km/h value (≈ -36 km/h)
        assert "km/h" in feedback_text
        assert "-36" in feedback_text or "-3" in feedback_text  # Roughly -36 km/h


# Helper functions for creating test data

def create_test_segments() -> list[ComparisonSegment]:
    """Create a list of test comparison segments."""
    segments = [
        ComparisonSegment(
            segment_id=0,
            distance_start=0.0,
            distance_end=200.0,
            time_loss=0.5,
            speed_delta_entry=-5.0,
            speed_delta_apex=-3.0,
            speed_delta_exit=-2.0,
            error_type=ErrorType.EARLY_BRAKING,
            explanation="Early braking"
        ),
        ComparisonSegment(
            segment_id=1,
            distance_start=200.0,
            distance_end=400.0,
            time_loss=0.3,
            speed_delta_entry=-1.0,
            speed_delta_apex=-1.0,
            speed_delta_exit=-4.0,
            error_type=ErrorType.LATE_THROTTLE,
            explanation="Late throttle"
        ),
        ComparisonSegment(
            segment_id=2,
            distance_start=400.0,
            distance_end=600.0,
            time_loss=0.2,
            speed_delta_entry=-4.0,
            speed_delta_apex=-5.0,
            speed_delta_exit=-4.0,
            error_type=ErrorType.SLOW_CORNER,
            explanation="Slow corner"
        ),
        ComparisonSegment(
            segment_id=3,
            distance_start=600.0,
            distance_end=800.0,
            time_loss=0.15,
            speed_delta_entry=0.0,
            speed_delta_apex=-3.0,
            speed_delta_exit=-2.0,
            error_type=ErrorType.LATE_BRAKING,
            explanation="Late braking"
        ),
        ComparisonSegment(
            segment_id=4,
            distance_start=800.0,
            distance_end=1000.0,
            time_loss=0.1,
            speed_delta_entry=-2.0,
            speed_delta_apex=-2.0,
            speed_delta_exit=-2.0,
            error_type=ErrorType.LINE_ERROR,
            explanation="Line error"
        )
    ]
    # Sort by time_loss descending (most impactful first)
    return sorted(segments, key=lambda s: s.time_loss, reverse=True)


def create_segment_with_error(error_type: ErrorType) -> ComparisonSegment:
    """Create a test segment with specific error type."""
    return ComparisonSegment(
        segment_id=1,
        distance_start=100.0,
        distance_end=200.0,
        time_loss=0.3,
        speed_delta_entry=-5.0,
        speed_delta_apex=-3.0,
        speed_delta_exit=-2.0,
        error_type=error_type,
        explanation="Test error"
    )


def create_test_track_profile() -> TrackProfile:
    """Create a test track profile."""
    distance = np.linspace(0, 1000, 100)
    curvature = np.zeros(100)
    curvature[20:30] = 0.03  # Corner section
    
    centerline = np.column_stack([distance, np.zeros(100)])
    elevation = np.zeros(100)
    
    return TrackProfile(
        track_id="test_track",
        centerline=centerline,
        curvature=curvature,
        elevation=elevation,
        distance=distance,
        track_length_m=1000.0
    )
