"""Unit tests for TelemetrySample value object.

Tests cover:
- Valid instantiation with realistic F1 telemetry data
- Validation of all fields (speed, gear, throttle, brake, steer, DRS, RPM, timestamps)
- Value object semantics (equality, hashing, immutability)
- Edge cases for all boundaries
"""

import pytest
from src.domain.value_objects.telemetry_sample import TelemetrySample


@pytest.fixture
def valid_telemetry_sample():
    """Fixture providing a valid telemetry sample with realistic F1 data."""
    return TelemetrySample(
        timestamp_ms=125000,
        world_position_x=1500.5,
        world_position_y=10.2,
        world_position_z=-250.8,
        world_velocity_x=50.0,
        world_velocity_y=0.5,
        world_velocity_z=-30.2,
        g_force_lateral=1.5,
        g_force_longitudinal=-2.3,
        yaw=1.57,
        speed=285.4,
        throttle=0.95,
        steer=0.2,
        brake=0.0,
        gear=7,
        engine_rpm=11500,
        drs=1,
        lap_distance=2450.8,
        lap_number=3,
    )


@pytest.fixture
def minimal_telemetry_sample():
    """Fixture providing minimal valid telemetry sample with zeros and edge values."""
    return TelemetrySample(
        timestamp_ms=0,
        world_position_x=0.0,
        world_position_y=0.0,
        world_position_z=0.0,
        world_velocity_x=0.0,
        world_velocity_y=0.0,
        world_velocity_z=0.0,
        g_force_lateral=0.0,
        g_force_longitudinal=0.0,
        yaw=0.0,
        speed=0.0,
        throttle=0.0,
        steer=0.0,
        brake=0.0,
        gear=0,
        engine_rpm=0,
        drs=0,
        lap_distance=0.0,
        lap_number=1,
    )


class TestTelemetrySampleValidInstantiation:
    """Test valid instantiation scenarios."""

    def test_create_with_valid_realistic_data(self, valid_telemetry_sample):
        """Valid telemetry sample with realistic F1 data should be created successfully."""
        assert valid_telemetry_sample.timestamp_ms == 125000
        assert valid_telemetry_sample.speed == 285.4
        assert valid_telemetry_sample.gear == 7
        assert valid_telemetry_sample.throttle == 0.95
        assert valid_telemetry_sample.drs == 1

    def test_create_with_minimal_values(self, minimal_telemetry_sample):
        """Telemetry sample with minimal/edge values should be created successfully."""
        assert minimal_telemetry_sample.timestamp_ms == 0
        assert minimal_telemetry_sample.speed == 0.0
        assert minimal_telemetry_sample.gear == 0
        assert minimal_telemetry_sample.lap_number == 1

    def test_create_with_max_throttle_brake(self):
        """Telemetry sample with maximum throttle and brake should be valid."""
        sample = TelemetrySample(
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
            speed=100.0,
            throttle=1.0,
            steer=0.0,
            brake=1.0,
            gear=3,
            engine_rpm=8000,
            drs=0,
            lap_distance=500.0,
            lap_number=2,
        )
        assert sample.throttle == 1.0
        assert sample.brake == 1.0

    def test_create_with_max_steer_left(self):
        """Telemetry sample with maximum left steering should be valid."""
        sample = TelemetrySample(
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
            speed=100.0,
            throttle=0.5,
            steer=-1.0,
            brake=0.0,
            gear=4,
            engine_rpm=9000,
            drs=0,
            lap_distance=500.0,
            lap_number=1,
        )
        assert sample.steer == -1.0

    def test_create_with_max_steer_right(self):
        """Telemetry sample with maximum right steering should be valid."""
        sample = TelemetrySample(
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
            speed=100.0,
            throttle=0.5,
            steer=1.0,
            brake=0.0,
            gear=4,
            engine_rpm=9000,
            drs=0,
            lap_distance=500.0,
            lap_number=1,
        )
        assert sample.steer == 1.0

    def test_create_with_reverse_gear(self):
        """Telemetry sample with reverse gear (-1) should be valid."""
        sample = TelemetrySample(
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
            speed=5.0,
            throttle=0.3,
            steer=0.0,
            brake=0.0,
            gear=-1,
            engine_rpm=3000,
            drs=0,
            lap_distance=10.0,
            lap_number=1,
        )
        assert sample.gear == -1

    def test_create_with_eighth_gear(self):
        """Telemetry sample with 8th gear should be valid."""
        sample = TelemetrySample(
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
            speed=350.0,
            throttle=1.0,
            steer=0.0,
            brake=0.0,
            gear=8,
            engine_rpm=12000,
            drs=1,
            lap_distance=3000.0,
            lap_number=5,
        )
        assert sample.gear == 8


class TestTelemetrySampleValidation:
    """Test field validation rules."""

    def test_negative_timestamp_raises_error(self):
        """Negative timestamp_ms should raise ValueError."""
        with pytest.raises(ValueError, match="timestamp_ms must be non-negative"):
            TelemetrySample(
                timestamp_ms=-1,
                world_position_x=0.0,
                world_position_y=0.0,
                world_position_z=0.0,
                world_velocity_x=0.0,
                world_velocity_y=0.0,
                world_velocity_z=0.0,
                g_force_lateral=0.0,
                g_force_longitudinal=0.0,
                yaw=0.0,
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_negative_speed_raises_error(self):
        """Negative speed should raise ValueError."""
        with pytest.raises(ValueError, match="speed must be non-negative"):
            TelemetrySample(
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
                speed=-10.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_throttle_above_1_raises_error(self):
        """Throttle above 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="throttle must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=1.1,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_throttle_below_0_raises_error(self):
        """Throttle below 0.0 should raise ValueError."""
        with pytest.raises(ValueError, match="throttle must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=-0.1,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_brake_above_1_raises_error(self):
        """Brake above 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="brake must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.0,
                steer=0.0,
                brake=1.5,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_brake_below_0_raises_error(self):
        """Brake below 0.0 should raise ValueError."""
        with pytest.raises(ValueError, match="brake must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=-0.1,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_steer_above_1_raises_error(self):
        """Steer above 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="steer must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=1.1,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_steer_below_negative_1_raises_error(self):
        """Steer below -1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="steer must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=-1.1,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_gear_below_negative_1_raises_error(self):
        """Gear below -1 should raise ValueError."""
        with pytest.raises(ValueError, match="gear must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=-2,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_gear_above_8_raises_error(self):
        """Gear above 8 should raise ValueError."""
        with pytest.raises(ValueError, match="gear must be in range"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=9,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_negative_engine_rpm_raises_error(self):
        """Negative engine RPM should raise ValueError."""
        with pytest.raises(ValueError, match="engine_rpm must be non-negative"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=-1000,
                drs=0,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_invalid_drs_value_raises_error(self):
        """DRS value other than 0 or 1 should raise ValueError."""
        with pytest.raises(ValueError, match="drs must be 0.*or 1"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=2,
                lap_distance=500.0,
                lap_number=1,
            )

    def test_negative_lap_distance_raises_error(self):
        """Negative lap distance should raise ValueError."""
        with pytest.raises(ValueError, match="lap_distance must be non-negative"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=-100.0,
                lap_number=1,
            )

    def test_lap_number_below_1_raises_error(self):
        """Lap number below 1 should raise ValueError."""
        with pytest.raises(ValueError, match="lap_number must be at least 1"):
            TelemetrySample(
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
                speed=100.0,
                throttle=0.5,
                steer=0.0,
                brake=0.0,
                gear=3,
                engine_rpm=8000,
                drs=0,
                lap_distance=500.0,
                lap_number=0,
            )


class TestTelemetrySampleEquality:
    """Test value object equality semantics."""

    def test_identical_samples_are_equal(self, valid_telemetry_sample):
        """Two samples with identical data should be equal."""
        sample2 = TelemetrySample(
            timestamp_ms=125000,
            world_position_x=1500.5,
            world_position_y=10.2,
            world_position_z=-250.8,
            world_velocity_x=50.0,
            world_velocity_y=0.5,
            world_velocity_z=-30.2,
            g_force_lateral=1.5,
            g_force_longitudinal=-2.3,
            yaw=1.57,
            speed=285.4,
            throttle=0.95,
            steer=0.2,
            brake=0.0,
            gear=7,
            engine_rpm=11500,
            drs=1,
            lap_distance=2450.8,
            lap_number=3,
        )
        assert valid_telemetry_sample == sample2

    def test_different_timestamp_not_equal(self, valid_telemetry_sample):
        """Samples with different timestamps should not be equal."""
        sample2 = TelemetrySample(
            timestamp_ms=126000,  # Different
            world_position_x=1500.5,
            world_position_y=10.2,
            world_position_z=-250.8,
            world_velocity_x=50.0,
            world_velocity_y=0.5,
            world_velocity_z=-30.2,
            g_force_lateral=1.5,
            g_force_longitudinal=-2.3,
            yaw=1.57,
            speed=285.4,
            throttle=0.95,
            steer=0.2,
            brake=0.0,
            gear=7,
            engine_rpm=11500,
            drs=1,
            lap_distance=2450.8,
            lap_number=3,
        )
        assert valid_telemetry_sample != sample2

    def test_different_speed_not_equal(self, valid_telemetry_sample):
        """Samples with different speeds should not be equal."""
        sample2 = TelemetrySample(
            timestamp_ms=125000,
            world_position_x=1500.5,
            world_position_y=10.2,
            world_position_z=-250.8,
            world_velocity_x=50.0,
            world_velocity_y=0.5,
            world_velocity_z=-30.2,
            g_force_lateral=1.5,
            g_force_longitudinal=-2.3,
            yaw=1.57,
            speed=290.0,  # Different
            throttle=0.95,
            steer=0.2,
            brake=0.0,
            gear=7,
            engine_rpm=11500,
            drs=1,
            lap_distance=2450.8,
            lap_number=3,
        )
        assert valid_telemetry_sample != sample2

    def test_comparison_with_non_sample_returns_false(self, valid_telemetry_sample):
        """Comparing with non-TelemetrySample should return False."""
        assert valid_telemetry_sample != "not a sample"
        assert valid_telemetry_sample != 42
        assert valid_telemetry_sample != None


class TestTelemetrySampleHashing:
    """Test value object hashing behavior."""

    def test_identical_samples_have_same_hash(self, valid_telemetry_sample):
        """Two samples with identical data should have the same hash."""
        sample2 = TelemetrySample(
            timestamp_ms=125000,
            world_position_x=1500.5,
            world_position_y=10.2,
            world_position_z=-250.8,
            world_velocity_x=50.0,
            world_velocity_y=0.5,
            world_velocity_z=-30.2,
            g_force_lateral=1.5,
            g_force_longitudinal=-2.3,
            yaw=1.57,
            speed=285.4,
            throttle=0.95,
            steer=0.2,
            brake=0.0,
            gear=7,
            engine_rpm=11500,
            drs=1,
            lap_distance=2450.8,
            lap_number=3,
        )
        assert hash(valid_telemetry_sample) == hash(sample2)

    def test_different_samples_have_different_hash(
        self, valid_telemetry_sample, minimal_telemetry_sample
    ):
        """Samples with different data should have different hashes."""
        assert hash(valid_telemetry_sample) != hash(minimal_telemetry_sample)

    def test_can_be_used_in_set(self, valid_telemetry_sample, minimal_telemetry_sample):
        """Telemetry samples should be usable in sets."""
        sample_set = {valid_telemetry_sample, minimal_telemetry_sample}
        assert len(sample_set) == 2
        assert valid_telemetry_sample in sample_set
        assert minimal_telemetry_sample in sample_set

    def test_can_be_used_as_dict_key(self, valid_telemetry_sample):
        """Telemetry samples should be usable as dictionary keys."""
        sample_dict = {valid_telemetry_sample: "lap_3_sample"}
        assert sample_dict[valid_telemetry_sample] == "lap_3_sample"


class TestTelemetrySampleImmutability:
    """Test that TelemetrySample is immutable (frozen dataclass)."""

    def test_cannot_modify_timestamp(self, valid_telemetry_sample):
        """Attempting to modify timestamp_ms should raise error."""
        with pytest.raises(AttributeError):
            valid_telemetry_sample.timestamp_ms = 999999

    def test_cannot_modify_speed(self, valid_telemetry_sample):
        """Attempting to modify speed should raise error."""
        with pytest.raises(AttributeError):
            valid_telemetry_sample.speed = 300.0

    def test_cannot_modify_gear(self, valid_telemetry_sample):
        """Attempting to modify gear should raise error."""
        with pytest.raises(AttributeError):
            valid_telemetry_sample.gear = 5

    def test_cannot_modify_throttle(self, valid_telemetry_sample):
        """Attempting to modify throttle should raise error."""
        with pytest.raises(AttributeError):
            valid_telemetry_sample.throttle = 0.5
