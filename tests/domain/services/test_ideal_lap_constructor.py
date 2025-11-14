"""Unit tests for IdealLapConstructor domain service.

Tests cover:
- Ideal lap construction from track profiles
- Physics calculations (cornering speed, acceleration, braking)
- Forward/backward pass algorithm
- Sector time calculation
- Edge cases and validation
"""

import pytest
import numpy as np
from src.domain.services.ideal_lap_constructor import IdealLapConstructor
from src.domain.entities.track_profile import TrackProfile
from src.domain.entities.ideal_lap import IdealLap


class TestIdealLapConstructorInitialization:
    """Test constructor initialization and parameter handling."""
    
    def test_init_with_default_params(self):
        """Test initialization with default vehicle parameters."""
        constructor = IdealLapConstructor()
        
        assert constructor.params['mu'] == 1.5
        assert constructor.params['mass'] == 798.0
        assert constructor.params['a_brake_max'] == pytest.approx(5.0 * 9.81)
        assert constructor.params['a_accel_max'] == pytest.approx(1.2 * 9.81)
        assert constructor.params['downforce_factor'] == 0.002
        assert constructor.params['v_max_cap'] == 95.0
    
    def test_init_with_custom_params(self):
        """Test initialization with custom vehicle parameters."""
        custom_params = {
            'mu': 1.8,
            'a_brake_max': 6.0 * 9.81,
            'v_max_cap': 100.0
        }
        constructor = IdealLapConstructor(params=custom_params)
        
        assert constructor.params['mu'] == 1.8
        assert constructor.params['a_brake_max'] == pytest.approx(6.0 * 9.81)
        assert constructor.params['v_max_cap'] == 100.0
        # Default values still present
        assert constructor.params['mass'] == 798.0


class TestIdealLapConstruction:
    """Test ideal lap construction from track profiles."""
    
    def test_construct_straight_track(self):
        """Test ideal lap on perfectly straight track."""
        # Arrange: Create straight track (zero curvature)
        distance = np.linspace(0, 1000, 100)
        centerline = np.column_stack([distance, np.zeros(100)])
        curvature = np.zeros(100)  # Straight = zero curvature
        elevation = np.zeros(100)  # Flat
        
        track_profile = TrackProfile(
            track_id="straight_test",
            centerline=centerline,
            curvature=curvature,
            elevation=elevation,
            distance=distance,
            track_length_m=1000.0
        )
        
        constructor = IdealLapConstructor()
        
        # Act
        ideal_lap = constructor.construct_ideal_lap(track_profile)
        
        # Assert
        assert isinstance(ideal_lap, IdealLap)
        assert ideal_lap.track_id == "straight_test"
        assert len(ideal_lap.ideal_speed) == 100
        assert len(ideal_lap.ideal_throttle) == 100
        assert len(ideal_lap.ideal_brake) == 100
        assert len(ideal_lap.sector_times) == 3
        assert ideal_lap.total_time > 0
        
        # On straight, speed should reach max cap
        assert np.max(ideal_lap.ideal_speed) == pytest.approx(95.0, abs=0.1)
    
    def test_construct_single_corner_track(self):
        """Test ideal lap with single corner section."""
        # Arrange: Track with one corner in the middle
        distance = np.linspace(0, 1000, 100)
        
        # Curvature: straight -> corner -> straight
        curvature = np.zeros(100)
        curvature[40:60] = 0.05  # Sharp corner (R = 20m) in middle
        
        centerline = np.column_stack([distance, np.zeros(100)])
        elevation = np.zeros(100)
        
        track_profile = TrackProfile(
            track_id="corner_test",
            centerline=centerline,
            curvature=curvature,
            elevation=elevation,
            distance=distance,
            track_length_m=1000.0
        )
        
        constructor = IdealLapConstructor()
        
        # Act
        ideal_lap = constructor.construct_ideal_lap(track_profile)
        
        # Assert
        assert ideal_lap.track_id == "corner_test"
        
        # Speed should be lower in corner section
        speed_in_corner = ideal_lap.ideal_speed[40:60]
        speed_on_straight = ideal_lap.ideal_speed[0:20]
        
        assert np.mean(speed_in_corner) < np.mean(speed_on_straight)
        
        # Should have braking before corner
        assert np.any(ideal_lap.ideal_brake[35:45] == 1)
    
    def test_construct_chicane_track(self):
        """Test ideal lap with chicane (left-right-left corners)."""
        # Arrange: Chicane pattern
        distance = np.linspace(0, 1000, 100)
        
        # Curvature: alternating left/right corners
        curvature = np.zeros(100)
        curvature[30:40] = 0.04   # Left corner
        curvature[40:50] = -0.04  # Right corner
        curvature[50:60] = 0.04   # Left corner
        
        centerline = np.column_stack([distance, np.zeros(100)])
        elevation = np.zeros(100)
        
        track_profile = TrackProfile(
            track_id="chicane_test",
            centerline=centerline,
            curvature=curvature,
            elevation=elevation,
            distance=distance,
            track_length_m=1000.0
        )
        
        constructor = IdealLapConstructor()
        
        # Act
        ideal_lap = constructor.construct_ideal_lap(track_profile)
        
        # Assert
        # Speed should be consistently lower through chicane
        speed_in_chicane = ideal_lap.ideal_speed[30:60]
        speed_before_chicane = ideal_lap.ideal_speed[0:20]
        
        assert np.mean(speed_in_chicane) < np.mean(speed_before_chicane)
    
    def test_construct_with_custom_sector_distances(self):
        """Test ideal lap with custom sector boundaries."""
        # Arrange
        track_profile = create_test_track_profile()
        sector_distances = np.array([300.0, 600.0, 1000.0])
        constructor = IdealLapConstructor()
        
        # Act
        ideal_lap = constructor.construct_ideal_lap(
            track_profile,
            sector_distances=sector_distances
        )
        
        # Assert
        assert len(ideal_lap.sector_times) == 3
        # Each sector time should be positive
        for sector_time in ideal_lap.sector_times:
            assert sector_time > 0
    
    def test_construct_insufficient_points_raises_error(self):
        """Test that track with < 10 points raises ValueError."""
        # Arrange: Track with only 5 points
        distance = np.linspace(0, 100, 5)
        centerline = np.column_stack([distance, np.zeros(5)])
        curvature = np.zeros(5)
        elevation = np.zeros(5)
        
        track_profile = TrackProfile(
            track_id="tiny_track",
            centerline=centerline,
            curvature=curvature,
            elevation=elevation,
            distance=distance,
            track_length_m=100.0
        )
        
        constructor = IdealLapConstructor()
        
        # Act & Assert
        with pytest.raises(ValueError, match="track_profile must have at least 10 points"):
            constructor.construct_ideal_lap(track_profile)


class TestCorneringSpeedCalculation:
    """Test cornering speed physics calculations."""
    
    def test_compute_cornering_speed_straight(self):
        """Test cornering speed on straight (zero curvature)."""
        constructor = IdealLapConstructor()
        curvature = np.zeros(10)
        distance = np.linspace(0, 100, 10)
        
        v_corner = constructor._compute_cornering_speed(curvature, distance)
        
        # On straight, cornering speed should be capped at v_max
        assert np.all(v_corner == constructor.params['v_max_cap'])
    
    def test_compute_cornering_speed_tight_corner(self):
        """Test cornering speed on tight corner (high curvature)."""
        constructor = IdealLapConstructor()
        curvature = np.full(10, 0.1)  # R = 10m tight corner
        distance = np.linspace(0, 100, 10)
        
        v_corner = constructor._compute_cornering_speed(curvature, distance)
        
        # Tight corner should have low speed
        # v = sqrt(μ * g * R) = sqrt(1.5 * 9.81 * 10) ≈ 12.1 m/s
        expected_speed = np.sqrt(1.5 * 9.81 * 10.0)
        assert np.all(v_corner == pytest.approx(expected_speed, rel=0.01))
    
    def test_compute_cornering_speed_medium_corner(self):
        """Test cornering speed on medium corner."""
        constructor = IdealLapConstructor()
        curvature = np.full(10, 0.02)  # R = 50m medium corner
        distance = np.linspace(0, 100, 10)
        
        v_corner = constructor._compute_cornering_speed(curvature, distance)
        
        # v = sqrt(1.5 * 9.81 * 50) ≈ 27.1 m/s
        expected_speed = np.sqrt(1.5 * 9.81 * 50.0)
        assert np.all(v_corner == pytest.approx(expected_speed, rel=0.01))


class TestForwardBackwardPasses:
    """Test forward and backward pass algorithms."""
    
    def test_forward_pass_acceleration(self):
        """Test forward pass applies acceleration correctly."""
        constructor = IdealLapConstructor()
        
        # High cornering speed limit (won't constrain acceleration)
        v_max_corner = np.full(100, 95.0)
        distance = np.linspace(0, 1000, 100)
        
        v_forward = constructor._forward_pass(v_max_corner, distance)
        
        # Speed should increase monotonically (accelerating)
        assert np.all(np.diff(v_forward) >= -0.001)  # Allow tiny numerical errors
        
        # Should reach max speed eventually
        assert v_forward[-1] == pytest.approx(95.0, abs=1.0)
    
    def test_backward_pass_braking(self):
        """Test backward pass applies braking correctly."""
        constructor = IdealLapConstructor()
        
        # Setup: high speed initially, low speed required at end
        distance = np.linspace(0, 1000, 100)
        v_forward = np.full(100, 80.0)
        v_max_corner = np.full(100, 80.0)
        v_max_corner[-20:] = 30.0  # Tight corner at end
        
        v_ideal = constructor._backward_pass(v_forward, v_max_corner, distance)
        
        # Speed should decrease approaching the corner
        assert v_ideal[-1] <= 30.1  # Should respect corner speed
        # Check that speed is being constrained earlier in the lap
        assert v_ideal[-20] < 80.0  # Should be slower before corner
    
    def test_forward_backward_respects_corner_limits(self):
        """Test complete forward-backward pass respects all constraints."""
        constructor = IdealLapConstructor()
        
        # Track with tight corner in middle
        distance = np.linspace(0, 1000, 100)
        v_max_corner = np.full(100, 80.0)
        v_max_corner[45:55] = 30.0  # Tight corner in middle
        
        v_forward = constructor._forward_pass(v_max_corner, distance)
        v_ideal = constructor._backward_pass(v_forward, v_max_corner, distance)
        
        # Speed in corner should not exceed limit
        assert np.all(v_ideal[45:55] <= 30.1)
        
        # Speed should be lower before corner (braking)
        assert v_ideal[40] < v_ideal[30]


class TestInputGeneration:
    """Test throttle and brake input generation."""
    
    def test_compute_inputs_accelerating(self):
        """Test throttle/brake when accelerating."""
        constructor = IdealLapConstructor()
        
        # Increasing speed
        distance = np.linspace(0, 100, 20)
        v_ideal = np.linspace(20, 60, 20)  # Accelerating
        v_max_corner = np.full(20, 80.0)
        
        throttle, brake = constructor._compute_inputs(v_ideal, v_max_corner, distance)
        
        # Should be mostly throttle, no brake
        assert np.sum(throttle) > 15
        assert np.sum(brake) < 5
    
    def test_compute_inputs_braking(self):
        """Test throttle/brake when decelerating."""
        constructor = IdealLapConstructor()
        
        # Decreasing speed with significant deceleration
        distance = np.linspace(0, 100, 20)
        v_ideal = np.linspace(80, 20, 20)  # Strong braking (larger speed change)
        v_max_corner = np.full(20, 90.0)
        
        throttle, brake = constructor._compute_inputs(v_ideal, v_max_corner, distance)
        
        # Should have braking detected
        assert np.sum(brake) > 5  # At least some braking points
        # When braking, throttle should be off
        brake_points = brake == 1
        assert np.all(throttle[brake_points] == 0)


class TestSectorTimeCalculation:
    """Test sector and total time calculations."""
    
    def test_calculate_sector_times_equal_sectors(self):
        """Test sector time calculation with equal sectors."""
        constructor = IdealLapConstructor()
        
        distance = np.linspace(0, 1000, 100)
        v_ideal = np.full(100, 50.0)  # Constant 50 m/s
        sector_distances = np.array([333.33, 666.67, 1000.0])
        
        sector_times = constructor._calculate_sector_times(
            v_ideal, distance, sector_distances
        )
        
        # Each sector ~333m at 50 m/s ≈ 6.67 seconds
        assert len(sector_times) == 3
        for sector_time in sector_times:
            assert sector_time == pytest.approx(6.67, rel=0.05)
    
    def test_calculate_total_time_constant_speed(self):
        """Test total time with constant speed."""
        constructor = IdealLapConstructor()
        
        distance = np.linspace(0, 1000, 100)
        v_ideal = np.full(100, 40.0)  # 40 m/s constant
        
        total_time = constructor._calculate_total_time(v_ideal, distance)
        
        # 1000m at 40 m/s = 25 seconds
        assert total_time == pytest.approx(25.0, rel=0.01)
    
    def test_calculate_total_time_varying_speed(self):
        """Test total time with varying speed."""
        constructor = IdealLapConstructor()
        
        distance = np.linspace(0, 1000, 100)
        # Speed varies: slow -> fast -> slow
        v_ideal = 40.0 + 20.0 * np.sin(distance / 159.15)  # 20-60 m/s range
        
        total_time = constructor._calculate_total_time(v_ideal, distance)
        
        # Should be between 1000/60 and 1000/20 seconds
        assert 16.7 < total_time < 50.0


class TestPhysicsPlausibility:
    """Test that generated ideal laps are physically plausible."""
    
    def test_speed_within_bounds(self):
        """Test that ideal lap speeds are within realistic bounds."""
        track_profile = create_test_track_profile()
        constructor = IdealLapConstructor()
        
        ideal_lap = constructor.construct_ideal_lap(track_profile)
        
        # All speeds should be positive
        assert np.all(ideal_lap.ideal_speed > 0)
        
        # No speed should exceed max cap
        assert np.all(ideal_lap.ideal_speed <= constructor.params['v_max_cap'])
    
    def test_lap_time_reasonable(self):
        """Test that lap times are in reasonable range."""
        track_profile = create_test_track_profile()
        constructor = IdealLapConstructor()
        
        ideal_lap = constructor.construct_ideal_lap(track_profile)
        
        # For 1000m track, lap time should be roughly 20-40 seconds
        # (depending on curvature)
        assert 15.0 < ideal_lap.total_time < 60.0
    
    def test_sector_times_sum_to_total(self):
        """Test that sector times sum to total time (within tolerance)."""
        track_profile = create_test_track_profile()
        constructor = IdealLapConstructor()
        
        ideal_lap = constructor.construct_ideal_lap(track_profile)
        
        sector_sum = sum(ideal_lap.sector_times)
        
        # Should match total time (within 1% tolerance enforced by IdealLap)
        assert abs(sector_sum - ideal_lap.total_time) < 0.01 * ideal_lap.total_time


# Helper functions

def create_test_track_profile() -> TrackProfile:
    """Create a standard test TrackProfile for reuse."""
    distance = np.linspace(0, 1000, 100)
    
    # Mix of straight and corners
    curvature = np.zeros(100)
    curvature[20:30] = 0.03  # Corner 1
    curvature[60:70] = 0.04  # Corner 2
    
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
