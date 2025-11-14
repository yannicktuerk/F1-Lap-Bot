"""Unit tests for IdealLap value object.

Tests cover:
- Valid construction with various configurations
- Validation of all invariants
- Immutability enforcement
- Speed interpolation accuracy
- Time loss calculations
- Edge cases and error handling
"""

import pytest
import numpy as np
from src.domain.entities.ideal_lap import IdealLap
from src.domain.value_objects.telemetry_sample import TelemetrySample


class TestIdealLapConstruction:
    """Test valid construction of IdealLap value objects."""
    
    def test_create_valid_ideal_lap(self):
        """Test creating IdealLap with valid data."""
        # Arrange: Create valid test data
        track_id = "monaco"
        distance = np.linspace(0, 3337, 334)  # Monaco lap ~3.3km, 10m spacing
        ideal_speed = np.full(334, 50.0)  # Constant 50 m/s for simplicity
        ideal_throttle = np.ones(334, dtype=int)
        ideal_brake = np.zeros(334, dtype=int)
        sector_times = [25.0, 30.0, 28.0]
        total_time = 83.0
        
        # Act: Create IdealLap
        ideal_lap = IdealLap(
            track_id=track_id,
            ideal_speed=ideal_speed,
            ideal_throttle=ideal_throttle,
            ideal_brake=ideal_brake,
            distance=distance,
            sector_times=sector_times,
            total_time=total_time
        )
        
        # Assert: Verify properties
        assert ideal_lap.track_id == track_id
        assert len(ideal_lap.ideal_speed) == 334
        assert len(ideal_lap.ideal_throttle) == 334
        assert len(ideal_lap.ideal_brake) == 334
        assert len(ideal_lap.distance) == 334
        assert ideal_lap.sector_times == sector_times
        assert ideal_lap.total_time == total_time
    
    def test_create_ideal_lap_with_varying_speed(self):
        """Test creating IdealLap with realistic varying speed profile."""
        # Arrange: Simulate speed variation through corners
        distance = np.linspace(0, 1000, 100)
        # Speed varies from 30-80 m/s
        ideal_speed = 55.0 + 25.0 * np.sin(distance / 100.0)
        ideal_throttle = np.where(ideal_speed > 60, 1, 0)
        ideal_brake = np.where(ideal_speed < 40, 1, 0)
        sector_times = [10.0, 8.5, 9.2]
        total_time = 27.7
        
        # Act
        ideal_lap = IdealLap(
            track_id="test_track",
            ideal_speed=ideal_speed,
            ideal_throttle=ideal_throttle,
            ideal_brake=ideal_brake,
            distance=distance,
            sector_times=sector_times,
            total_time=total_time
        )
        
        # Assert
        assert ideal_lap.get_sample_count() == 100
        assert ideal_lap.get_lap_length() == pytest.approx(1000.0, rel=0.01)
    
    def test_create_ideal_lap_minimal_points(self):
        """Test creating IdealLap with minimum 10 points."""
        # Arrange
        distance = np.linspace(0, 100, 10)
        ideal_speed = np.full(10, 40.0)
        ideal_throttle = np.ones(10, dtype=int)
        ideal_brake = np.zeros(10, dtype=int)
        sector_times = [2.0, 2.5, 2.3]
        total_time = 6.8
        
        # Act
        ideal_lap = IdealLap(
            track_id="short_track",
            ideal_speed=ideal_speed,
            ideal_throttle=ideal_throttle,
            ideal_brake=ideal_brake,
            distance=distance,
            sector_times=sector_times,
            total_time=total_time
        )
        
        # Assert
        assert ideal_lap.get_sample_count() == 10


class TestIdealLapValidation:
    """Test validation of IdealLap invariants."""
    
    def test_empty_track_id_raises_error(self):
        """Test that empty track_id raises ValueError."""
        with pytest.raises(ValueError, match="track_id must be a non-empty string"):
            IdealLap(
                track_id="",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],
                total_time=15.0
            )
    
    def test_mismatched_array_lengths_raises_error(self):
        """Test that mismatched array lengths raise ValueError."""
        with pytest.raises(ValueError, match="ideal_speed length .* must match distance length"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0]),  # Wrong length
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],
                total_time=15.0
            )
    
    def test_too_few_points_raises_error(self):
        """Test that less than 10 points raises ValueError."""
        with pytest.raises(ValueError, match="Arrays must contain at least 10 points"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1]),
                ideal_brake=np.array([0, 0, 0]),
                distance=np.array([0, 50, 100]),
                sector_times=[1.0, 1.5, 1.3],
                total_time=3.8
            )
    
    def test_negative_speed_raises_error(self):
        """Test that negative speed values raise ValueError."""
        with pytest.raises(ValueError, match="ideal_speed must be non-negative"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, -10.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],
                total_time=15.0
            )
    
    def test_non_binary_throttle_raises_error(self):
        """Test that non-binary throttle values raise ValueError."""
        with pytest.raises(ValueError, match="ideal_throttle must contain only 0 or 1 values"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 0.5, 1, 1, 1, 1, 1, 1, 1]),  # 0.5 is invalid
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],
                total_time=15.0
            )
    
    def test_non_binary_brake_raises_error(self):
        """Test that non-binary brake values raise ValueError."""
        with pytest.raises(ValueError, match="ideal_brake must contain only 0 or 1 values"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 2, 0, 0, 0, 0, 0, 0, 0]),  # 2 is invalid
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],
                total_time=15.0
            )
    
    def test_non_monotonic_distance_raises_error(self):
        """Test that non-increasing distance raises ValueError."""
        with pytest.raises(ValueError, match="distance must be monotonically increasing"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 15, 40, 50, 60, 70, 80, 90]),  # 15 < 20
                sector_times=[5.0, 5.0, 5.0],
                total_time=15.0
            )
    
    def test_invalid_sector_times_count_raises_error(self):
        """Test that sector_times with != 3 values raises ValueError."""
        with pytest.raises(ValueError, match="sector_times must contain exactly 3 values"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0],  # Only 2 sectors
                total_time=10.0
            )
    
    def test_negative_sector_time_raises_error(self):
        """Test that negative sector times raise ValueError."""
        with pytest.raises(ValueError, match="sector_times\\[1\\] must be positive"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, -2.0, 5.0],  # Negative sector 2
                total_time=8.0
            )
    
    def test_negative_total_time_raises_error(self):
        """Test that negative total_time raises ValueError."""
        with pytest.raises(ValueError, match="total_time must be positive"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],
                total_time=-15.0
            )
    
    def test_total_time_not_matching_sectors_raises_error(self):
        """Test that total_time not matching sum of sectors raises ValueError."""
        with pytest.raises(ValueError, match="total_time .* must equal sum of sector_times"):
            IdealLap(
                track_id="test",
                ideal_speed=np.array([50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]),
                ideal_throttle=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
                ideal_brake=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                distance=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90]),
                sector_times=[5.0, 5.0, 5.0],  # Sum = 15.0
                total_time=20.0  # Does not match (> 1% tolerance)
            )


class TestIdealLapImmutability:
    """Test that IdealLap is immutable (frozen dataclass)."""
    
    def test_cannot_modify_track_id(self):
        """Test that track_id cannot be modified after creation."""
        ideal_lap = create_test_ideal_lap()
        
        with pytest.raises(AttributeError):
            ideal_lap.track_id = "modified"
    
    def test_cannot_modify_total_time(self):
        """Test that total_time cannot be modified after creation."""
        ideal_lap = create_test_ideal_lap()
        
        with pytest.raises(AttributeError):
            ideal_lap.total_time = 999.0


class TestIdealLapSpeedInterpolation:
    """Test speed interpolation methods."""
    
    def test_get_speed_at_exact_point(self):
        """Test getting speed at exact distance point."""
        # Arrange
        distance = np.array([0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0])
        ideal_speed = np.array([50.0, 60.0, 70.0, 80.0, 70.0, 60.0, 50.0, 40.0, 50.0, 60.0])
        ideal_lap = IdealLap(
            track_id="test",
            ideal_speed=ideal_speed,
            ideal_throttle=np.ones(10, dtype=int),
            ideal_brake=np.zeros(10, dtype=int),
            distance=distance,
            sector_times=[10.0, 9.0, 11.0],
            total_time=30.0
        )
        
        # Act & Assert
        assert ideal_lap.get_speed_at(0.0) == pytest.approx(50.0)
        assert ideal_lap.get_speed_at(200.0) == pytest.approx(70.0)
        assert ideal_lap.get_speed_at(900.0) == pytest.approx(60.0)
    
    def test_get_speed_at_interpolated_point(self):
        """Test getting speed at interpolated distance (between sample points)."""
        # Arrange
        distance = np.array([0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0])
        ideal_speed = np.array([50.0, 60.0, 70.0, 80.0, 70.0, 60.0, 50.0, 40.0, 50.0, 60.0])
        ideal_lap = IdealLap(
            track_id="test",
            ideal_speed=ideal_speed,
            ideal_throttle=np.ones(10, dtype=int),
            ideal_brake=np.zeros(10, dtype=int),
            distance=distance,
            sector_times=[10.0, 9.0, 11.0],
            total_time=30.0
        )
        
        # Act & Assert: Midpoint between 50 and 60 should be 55
        assert ideal_lap.get_speed_at(50.0) == pytest.approx(55.0)
        # Midpoint between 70 and 80 should be 75
        assert ideal_lap.get_speed_at(250.0) == pytest.approx(75.0)
    
    def test_get_speed_at_out_of_range_raises_error(self):
        """Test that distance outside valid range raises ValueError."""
        ideal_lap = create_test_ideal_lap()
        
        with pytest.raises(ValueError, match="distance .* is outside valid range"):
            ideal_lap.get_speed_at(-10.0)
        
        with pytest.raises(ValueError, match="distance .* is outside valid range"):
            ideal_lap.get_speed_at(10000.0)


class TestIdealLapTimeLossCalculations:
    """Test time loss calculation methods."""
    
    def test_get_time_loss_slower_than_ideal(self):
        """Test time loss calculation when actual speed is slower than ideal."""
        # Arrange
        ideal_lap = create_test_ideal_lap()
        distance = 500.0  # meters
        ideal_speed = ideal_lap.get_speed_at(distance)  # ~50 m/s
        actual_speed = 40.0  # m/s (slower)
        
        # Act
        time_loss = ideal_lap.get_time_loss_at(distance, actual_speed)
        
        # Assert: Should be positive (losing time)
        expected_loss = (1.0 / 40.0 - 1.0 / ideal_speed)
        assert time_loss == pytest.approx(expected_loss)
        assert time_loss > 0
    
    def test_get_time_loss_faster_than_ideal(self):
        """Test time loss calculation when actual speed is faster than ideal."""
        # Arrange
        ideal_lap = create_test_ideal_lap()
        distance = 500.0
        ideal_speed = ideal_lap.get_speed_at(distance)  # ~50 m/s
        actual_speed = 60.0  # m/s (faster)
        
        # Act
        time_loss = ideal_lap.get_time_loss_at(distance, actual_speed)
        
        # Assert: Should be negative (gaining time)
        expected_loss = (1.0 / 60.0 - 1.0 / ideal_speed)
        assert time_loss == pytest.approx(expected_loss)
        assert time_loss < 0
    
    def test_get_time_loss_equal_to_ideal(self):
        """Test time loss is zero when speed equals ideal."""
        # Arrange
        ideal_lap = create_test_ideal_lap()
        distance = 500.0
        ideal_speed = ideal_lap.get_speed_at(distance)
        
        # Act
        time_loss = ideal_lap.get_time_loss_at(distance, ideal_speed)
        
        # Assert
        assert time_loss == pytest.approx(0.0, abs=1e-10)
    
    def test_get_time_loss_with_zero_actual_speed(self):
        """Test time loss returns 0 when actual speed is zero."""
        ideal_lap = create_test_ideal_lap()
        
        time_loss = ideal_lap.get_time_loss_at(500.0, 0.0)
        
        assert time_loss == 0.0
    
    def test_get_time_loss_with_negative_speed_raises_error(self):
        """Test that negative actual speed raises ValueError."""
        ideal_lap = create_test_ideal_lap()
        
        with pytest.raises(ValueError, match="actual_speed must be non-negative"):
            ideal_lap.get_time_loss_at(500.0, -10.0)
    
    def test_compute_total_time_loss_with_real_samples(self):
        """Test computing total time loss across multiple telemetry samples."""
        # Arrange
        ideal_lap = create_test_ideal_lap()
        
        # Create actual lap samples (slower than ideal)
        actual_samples = [
            create_test_telemetry_sample(lap_distance=100.0, speed_kmh=144.0),  # 40 m/s
            create_test_telemetry_sample(lap_distance=200.0, speed_kmh=144.0),
            create_test_telemetry_sample(lap_distance=300.0, speed_kmh=144.0),
            create_test_telemetry_sample(lap_distance=400.0, speed_kmh=144.0),
            create_test_telemetry_sample(lap_distance=500.0, speed_kmh=144.0),
        ]
        
        # Act
        total_loss = ideal_lap.compute_total_time_loss(actual_samples)
        
        # Assert: Should be positive (losing time)
        assert total_loss > 0
    
    def test_compute_total_time_loss_with_empty_samples_raises_error(self):
        """Test that empty samples list raises ValueError."""
        ideal_lap = create_test_ideal_lap()
        
        with pytest.raises(ValueError, match="actual_lap_samples cannot be empty"):
            ideal_lap.compute_total_time_loss([])


class TestIdealLapHelperMethods:
    """Test helper methods for querying IdealLap properties."""
    
    def test_get_sample_count(self):
        """Test getting number of distance points."""
        distance = np.linspace(0, 5000, 500)
        ideal_lap = IdealLap(
            track_id="spa",
            ideal_speed=np.full(500, 60.0),
            ideal_throttle=np.ones(500, dtype=int),
            ideal_brake=np.zeros(500, dtype=int),
            distance=distance,
            sector_times=[30.0, 35.0, 32.0],
            total_time=97.0
        )
        
        assert ideal_lap.get_sample_count() == 500
    
    def test_get_lap_length(self):
        """Test getting total lap length."""
        distance = np.linspace(0, 4500, 450)
        ideal_lap = IdealLap(
            track_id="silverstone",
            ideal_speed=np.full(450, 65.0),
            ideal_throttle=np.ones(450, dtype=int),
            ideal_brake=np.zeros(450, dtype=int),
            distance=distance,
            sector_times=[28.0, 31.0, 29.0],
            total_time=88.0
        )
        
        assert ideal_lap.get_lap_length() == pytest.approx(4500.0, rel=0.01)


# Helper functions for creating test objects

def create_test_ideal_lap() -> IdealLap:
    """Create a standard test IdealLap for reuse in tests."""
    distance = np.linspace(0, 1000, 100)
    ideal_speed = np.full(100, 50.0)  # Constant 50 m/s
    ideal_throttle = np.ones(100, dtype=int)
    ideal_brake = np.zeros(100, dtype=int)
    sector_times = [8.0, 10.0, 9.0]
    total_time = 27.0
    
    return IdealLap(
        track_id="test_track",
        ideal_speed=ideal_speed,
        ideal_throttle=ideal_throttle,
        ideal_brake=ideal_brake,
        distance=distance,
        sector_times=sector_times,
        total_time=total_time
    )


def create_test_telemetry_sample(lap_distance: float, speed_kmh: float) -> TelemetrySample:
    """Create a minimal TelemetrySample for testing."""
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
