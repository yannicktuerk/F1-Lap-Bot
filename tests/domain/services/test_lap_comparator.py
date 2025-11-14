"""Unit tests for LapComparator domain service.

Tests cover:
- Lap comparison and segment analysis
- Time loss calculation
- Error classification
- Speed delta calculations
- Edge cases and validation
"""

import pytest
import numpy as np
from src.domain.services.lap_comparator import (
    LapComparator,
    ComparisonSegment,
    ErrorType
)
from src.domain.entities.lap_trace import LapTrace
from src.domain.entities.ideal_lap import IdealLap
from src.domain.entities.track_profile import TrackProfile
from src.domain.value_objects.telemetry_sample import TelemetrySample


class TestComparisonSegmentValidation:
    """Test ComparisonSegment value object validation."""
    
    def test_create_valid_comparison_segment(self):
        """Test creating valid ComparisonSegment."""
        segment = ComparisonSegment(
            segment_id=1,
            distance_start=100.0,
            distance_end=200.0,
            time_loss=0.5,
            speed_delta_entry=-5.0,
            speed_delta_apex=-3.0,
            speed_delta_exit=-2.0,
            error_type=ErrorType.EARLY_BRAKING,
            explanation="Early braking cost 500ms"
        )
        
        assert segment.segment_id == 1
        assert segment.time_loss == 0.5
        assert segment.error_type == ErrorType.EARLY_BRAKING
    
    def test_invalid_distance_range_raises_error(self):
        """Test that end < start raises ValueError."""
        with pytest.raises(ValueError, match="distance_end .* must be greater than distance_start"):
            ComparisonSegment(
                segment_id=1,
                distance_start=200.0,
                distance_end=100.0,  # Invalid: end < start
                time_loss=0.5,
                speed_delta_entry=-5.0,
                speed_delta_apex=-3.0,
                speed_delta_exit=-2.0,
                error_type=ErrorType.EARLY_BRAKING,
                explanation="Test"
            )


class TestLapComparatorInitialization:
    """Test LapComparator initialization."""
    
    def test_init_with_default_threshold(self):
        """Test initialization with default threshold."""
        comparator = LapComparator()
        assert comparator.min_time_loss_threshold == 0.05
    
    def test_init_with_custom_threshold(self):
        """Test initialization with custom threshold."""
        comparator = LapComparator(min_time_loss_threshold=0.1)
        assert comparator.min_time_loss_threshold == 0.1


class TestLapComparison:
    """Test lap comparison functionality."""
    
    def test_compare_laps_basic(self):
        """Test basic lap comparison."""
        # Arrange
        actual_lap, ideal_lap, track_profile = create_test_laps_with_time_loss()
        comparator = LapComparator(min_time_loss_threshold=0.01)
        
        # Act
        segments = comparator.compare_laps(
            actual_lap=actual_lap,
            ideal_lap=ideal_lap,
            track_profile=track_profile,
            num_segments=5
        )
        
        # Assert
        assert len(segments) > 0
        # Segments should be sorted by time_loss descending
        for i in range(len(segments) - 1):
            assert segments[i].time_loss >= segments[i+1].time_loss
    
    def test_compare_laps_filters_small_losses(self):
        """Test that small time losses are filtered out."""
        actual_lap, ideal_lap, track_profile = create_test_laps_similar()
        comparator = LapComparator(min_time_loss_threshold=0.5)  # High threshold
        
        segments = comparator.compare_laps(
            actual_lap, ideal_lap, track_profile, num_segments=5
        )
        
        # With high threshold, should filter out most/all segments
        for segment in segments:
            assert segment.time_loss >= 0.5
    
    def test_compare_laps_empty_actual_lap_raises_error(self):
        """Test that empty actual lap raises ValueError."""
        # Empty lap (no samples)
        actual_lap = LapTrace(session_uid=1, lap_number=1, car_index=0, track_id="test")
        ideal_lap, track_profile = create_test_ideal_and_profile()
        comparator = LapComparator()
        
        with pytest.raises(ValueError, match="actual_lap has no telemetry samples"):
            comparator.compare_laps(actual_lap, ideal_lap, track_profile)
    
    def test_compare_laps_track_mismatch_raises_error(self):
        """Test that track mismatch raises ValueError."""
        actual_lap, ideal_lap, track_profile = create_test_laps_with_time_loss()
        # Override track IDs to create mismatch
        actual_lap._track_id = "monaco"
        ideal_lap = IdealLap(
            track_id="silverstone",  # Different track
            ideal_speed=ideal_lap.ideal_speed,
            ideal_throttle=ideal_lap.ideal_throttle,
            ideal_brake=ideal_lap.ideal_brake,
            distance=ideal_lap.distance,
            sector_times=ideal_lap.sector_times,
            total_time=ideal_lap.total_time
        )
        comparator = LapComparator()
        
        with pytest.raises(ValueError, match="Track mismatch"):
            comparator.compare_laps(actual_lap, ideal_lap, track_profile)


class TestSegmentCreation:
    """Test segment creation logic."""
    
    def test_create_segments_equal_length(self):
        """Test that segments are equal length."""
        track_profile = create_test_track_profile()
        comparator = LapComparator()
        
        segments = comparator._create_segments(track_profile, num_segments=5)
        
        assert len(segments) == 5
        expected_length = track_profile.track_length_m / 5
        
        for start, end in segments:
            actual_length = end - start
            assert actual_length == pytest.approx(expected_length, rel=0.01)
    
    def test_create_segments_covers_full_track(self):
        """Test that segments cover the entire track."""
        track_profile = create_test_track_profile()
        comparator = LapComparator()
        
        segments = comparator._create_segments(track_profile, num_segments=10)
        
        # First segment starts at 0
        assert segments[0][0] == pytest.approx(0.0, abs=0.01)
        # Last segment ends at track length
        assert segments[-1][1] == pytest.approx(track_profile.track_length_m, rel=0.01)


class TestErrorClassification:
    """Test error type classification logic."""
    
    def test_classify_early_braking(self):
        """Test classification of early braking."""
        comparator = LapComparator()
        track_profile = create_test_track_profile()
        
        # Early braking: slow entry, normal apex/exit
        error_type = comparator._classify_error(
            speed_delta_entry=-5.0,  # Slow entry
            speed_delta_apex=-1.0,   # Recovered at apex
            speed_delta_exit=-0.5,   # Normal exit
            track_profile=track_profile,
            start_dist=200.0,
            end_dist=300.0  # Corner section
        )
        
        assert error_type == ErrorType.EARLY_BRAKING
    
    def test_classify_late_braking(self):
        """Test classification of late braking."""
        comparator = LapComparator()
        track_profile = create_test_track_profile()
        
        # Late braking: fast entry, slow apex
        error_type = comparator._classify_error(
            speed_delta_entry=0.0,   # Normal entry
            speed_delta_apex=-5.0,   # Slow apex
            speed_delta_exit=-3.0,   # Slow exit
            track_profile=track_profile,
            start_dist=200.0,
            end_dist=300.0
        )
        
        assert error_type == ErrorType.LATE_BRAKING
    
    def test_classify_slow_corner(self):
        """Test classification of slow corner."""
        comparator = LapComparator()
        track_profile = create_test_track_profile()
        
        # Slow corner: slow throughout
        error_type = comparator._classify_error(
            speed_delta_entry=-4.0,
            speed_delta_apex=-5.0,
            speed_delta_exit=-4.0,
            track_profile=track_profile,
            start_dist=200.0,
            end_dist=300.0
        )
        
        assert error_type == ErrorType.SLOW_CORNER
    
    def test_classify_late_throttle(self):
        """Test classification of late throttle."""
        comparator = LapComparator()
        track_profile = create_test_track_profile()
        
        # Late throttle: normal entry/apex, slow exit
        error_type = comparator._classify_error(
            speed_delta_entry=-1.0,
            speed_delta_apex=-1.0,
            speed_delta_exit=-5.0,  # Slow exit
            track_profile=track_profile,
            start_dist=200.0,
            end_dist=300.0
        )
        
        assert error_type == ErrorType.LATE_THROTTLE


class TestSpeedDeltaCalculation:
    """Test speed delta calculations."""
    
    def test_calculate_speed_delta_slower(self):
        """Test speed delta when actual is slower than ideal."""
        comparator = LapComparator()
        
        # Create sample and ideal lap
        sample = create_test_sample(lap_distance=500.0, speed_kmh=144.0)  # 40 m/s
        ideal_lap = create_test_ideal_lap()
        
        # Ideal speed at 500m is 50 m/s
        speed_delta = comparator._calculate_speed_delta(sample, ideal_lap)
        
        # 40 - 50 = -10 m/s (slower)
        assert speed_delta == pytest.approx(-10.0, abs=0.1)
    
    def test_calculate_speed_delta_faster(self):
        """Test speed delta when actual is faster than ideal."""
        comparator = LapComparator()
        
        sample = create_test_sample(lap_distance=500.0, speed_kmh=216.0)  # 60 m/s
        ideal_lap = create_test_ideal_lap()
        
        # Ideal speed at 500m is 50 m/s
        speed_delta = comparator._calculate_speed_delta(sample, ideal_lap)
        
        # 60 - 50 = +10 m/s (faster)
        assert speed_delta == pytest.approx(10.0, abs=0.1)


class TestApexFinding:
    """Test apex (curvature peak) finding."""
    
    def test_find_apex_in_corner(self):
        """Test finding apex in a corner segment."""
        comparator = LapComparator()
        track_profile = create_test_track_profile_with_corner()
        
        # Corner is at 200-300m with peak curvature at ~250m
        apex_dist = comparator._find_apex(200.0, 300.0, track_profile)
        
        # Should find apex near middle of corner
        assert 220.0 < apex_dist < 280.0


class TestExplanationGeneration:
    """Test explanation string generation."""
    
    def test_generate_explanation_early_braking(self):
        """Test explanation for early braking."""
        comparator = LapComparator()
        
        explanation = comparator._generate_explanation(
            error_type=ErrorType.EARLY_BRAKING,
            speed_delta_entry=-5.0,
            speed_delta_apex=-1.0,
            speed_delta_exit=-0.5,
            time_loss=0.3
        )
        
        assert "Early braking" in explanation
        assert "300ms" in explanation
        assert "5.0 m/s slower" in explanation
    
    def test_generate_explanation_late_throttle(self):
        """Test explanation for late throttle."""
        comparator = LapComparator()
        
        explanation = comparator._generate_explanation(
            error_type=ErrorType.LATE_THROTTLE,
            speed_delta_entry=-1.0,
            speed_delta_apex=-1.0,
            speed_delta_exit=-4.0,
            time_loss=0.2
        )
        
        assert "Late throttle" in explanation
        assert "200ms" in explanation
        assert "Exit" in explanation


# Helper functions for creating test data

def create_test_sample(lap_distance: float, speed_kmh: float) -> TelemetrySample:
    """Create a test telemetry sample."""
    return TelemetrySample(
        timestamp_ms=1000,
        world_position_x=0.0,
        world_position_y=0.0,
        world_position_z=0.0,
        world_velocity_x=0.0,
        world_velocity_y=0.0,
        world_velocity_z=0.0,
        g_force_lateral=0.0,
        g_force_longitudinal=0.0,
        yaw=0.0,
        speed=speed_kmh,
        throttle=1.0,
        steer=0.0,
        brake=0.0,
        gear=5,
        engine_rpm=10000,
        drs=0,
        lap_distance=lap_distance,
        lap_number=1
    )


def create_test_ideal_lap() -> IdealLap:
    """Create a test ideal lap."""
    distance = np.linspace(0, 1000, 100)
    ideal_speed = np.full(100, 50.0)  # Constant 50 m/s
    
    return IdealLap(
        track_id="test_track",
        ideal_speed=ideal_speed,
        ideal_throttle=np.ones(100, dtype=int),
        ideal_brake=np.zeros(100, dtype=int),
        distance=distance,
        sector_times=[8.0, 10.0, 9.0],
        total_time=27.0
    )


def create_test_track_profile() -> TrackProfile:
    """Create a test track profile with a corner."""
    distance = np.linspace(0, 1000, 100)
    
    # Curvature: straight -> corner at 200-300m -> straight
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


def create_test_track_profile_with_corner() -> TrackProfile:
    """Create track profile with pronounced corner."""
    distance = np.linspace(0, 1000, 100)
    curvature = np.zeros(100)
    # Peak curvature at index 25 (250m)
    for i in range(20, 30):
        curvature[i] = 0.04 * (1 - abs(i - 25) / 5.0)  # Peak at 25
    
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


def create_test_laps_with_time_loss():
    """Create actual and ideal laps with significant time loss."""
    # Create ideal lap
    ideal_lap = create_test_ideal_lap()
    track_profile = create_test_track_profile()
    
    # Create actual lap with slower speeds (time loss)
    actual_lap = LapTrace(
        session_uid=1,
        lap_number=1,
        car_index=0,
        track_id="test_track"
    )
    
    # Add samples with slower speeds than ideal
    for i in range(0, 100, 2):  # Every 10 meters
        distance = i * 10.0
        # Actual speed is 10-20% slower than ideal
        speed_kmh = 144.0  # 40 m/s (vs ideal 50 m/s)
        
        sample = create_test_sample(distance, speed_kmh)
        actual_lap.add_sample(sample)
    
    return actual_lap, ideal_lap, track_profile


def create_test_laps_similar():
    """Create actual and ideal laps that are very similar."""
    ideal_lap = create_test_ideal_lap()
    track_profile = create_test_track_profile()
    
    actual_lap = LapTrace(
        session_uid=1,
        lap_number=1,
        car_index=0,
        track_id="test_track"
    )
    
    # Add samples with speeds very close to ideal
    for i in range(0, 100, 2):
        distance = i * 10.0
        speed_kmh = 178.0  # 49.4 m/s (very close to ideal 50 m/s)
        sample = create_test_sample(distance, speed_kmh)
        actual_lap.add_sample(sample)
    
    return actual_lap, ideal_lap, track_profile


def create_test_ideal_and_profile():
    """Create test ideal lap and track profile."""
    ideal_lap = create_test_ideal_lap()
    track_profile = create_test_track_profile()
    return ideal_lap, track_profile
