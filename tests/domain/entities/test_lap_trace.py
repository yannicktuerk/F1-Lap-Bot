"""Unit tests for LapTrace entity.

Tests cover:
- Lap trace instantiation and metadata
- Sample management (add, get, ordering)
- Invariant enforcement
- Lap completion tracking
- Business logic methods (speed calculations, distance queries)
"""

import pytest
from src.domain.entities.lap_trace import LapTrace
from src.domain.value_objects.telemetry_sample import TelemetrySample
from src.domain.entities.car_setup_snapshot import CarSetupSnapshot


@pytest.fixture
def sample_telemetry():
    """Fixture providing telemetry samples for lap 1."""
    return [
        TelemetrySample(
            timestamp_ms=1000, lap_number=1, lap_distance=100.0,
            world_position_x=0.0, world_position_y=0.0, world_position_z=0.0,
            world_velocity_x=0.0, world_velocity_y=0.0, world_velocity_z=0.0,
            g_force_lateral=0.0, g_force_longitudinal=0.0, yaw=0.0,
            speed=150.0, throttle=0.8, steer=0.0, brake=0.0,
            gear=5, engine_rpm=8000, drs=0
        ),
        TelemetrySample(
            timestamp_ms=2000, lap_number=1, lap_distance=200.0,
            world_position_x=0.0, world_position_y=0.0, world_position_z=0.0,
            world_velocity_x=0.0, world_velocity_y=0.0, world_velocity_z=0.0,
            g_force_lateral=0.0, g_force_longitudinal=0.0, yaw=0.0,
            speed=200.0, throttle=1.0, steer=0.0, brake=0.0,
            gear=6, engine_rpm=9000, drs=1
        ),
        TelemetrySample(
            timestamp_ms=3000, lap_number=1, lap_distance=300.0,
            world_position_x=0.0, world_position_y=0.0, world_position_z=0.0,
            world_velocity_x=0.0, world_velocity_y=0.0, world_velocity_z=0.0,
            g_force_lateral=0.0, g_force_longitudinal=0.0, yaw=0.0,
            speed=180.0, throttle=0.5, steer=0.1, brake=0.3,
            gear=5, engine_rpm=7500, drs=0
        ),
    ]


@pytest.fixture
def valid_setup_data():
    """Fixture providing valid car setup data."""
    return {
        "session_uid": 123456,
        "timestamp_ms": 50000,
        "front_wing": 10, "rear_wing": 15,
        "on_throttle": 60, "off_throttle": 40,
        "front_camber": -3.5, "rear_camber": -1.5,
        "front_toe": 0.1, "rear_toe": 0.2,
        "front_suspension": 5, "rear_suspension": 6,
        "front_anti_roll_bar": 7, "rear_anti_roll_bar": 8,
        "front_suspension_height": 3, "rear_suspension_height": 4,
        "brake_pressure": 100, "brake_bias": 60, "engine_braking": 50,
        "front_left_tyre_pressure": 23.5, "front_right_tyre_pressure": 23.5,
        "rear_left_tyre_pressure": 22.0, "rear_right_tyre_pressure": 22.0,
        "ballast": 10, "fuel_load": 50.0,
    }


class TestLapTraceInstantiation:
    """Test lap trace creation and metadata."""

    def test_create_with_valid_data(self):
        """Valid lap trace should be created successfully."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.session_uid == 12345
        assert trace.lap_number == 1
        assert trace.car_index == 0
        assert trace.is_valid is True
        assert trace.trace_id is not None

    def test_trace_id_auto_generated(self):
        """Trace ID should be auto-generated if not provided."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.trace_id is not None
        assert len(trace.trace_id) == 36  # UUID format

    def test_custom_trace_id(self):
        """Custom trace ID should be used if provided."""
        custom_id = "test-trace-123"
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0, trace_id=custom_id)
        assert trace.trace_id == custom_id

    def test_lap_number_below_1_raises_error(self):
        """Lap number below 1 should raise ValueError."""
        with pytest.raises(ValueError, match="lap_number must be at least 1"):
            LapTrace(session_uid=12345, lap_number=0, car_index=0)

    def test_negative_lap_time_raises_error(self):
        """Negative lap time should raise ValueError."""
        with pytest.raises(ValueError, match="lap_time_ms must be non-negative"):
            LapTrace(session_uid=12345, lap_number=1, car_index=0, lap_time_ms=-100)

    def test_incomplete_lap_by_default(self):
        """Lap should be incomplete if lap_time_ms not provided."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.is_complete() is False
        assert trace.lap_time_ms is None

    def test_complete_lap_with_time(self):
        """Lap should be complete if lap_time_ms provided."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0, lap_time_ms=85000)
        assert trace.is_complete() is True
        assert trace.lap_time_ms == 85000


class TestLapTraceSampleManagement:
    """Test adding and retrieving telemetry samples."""

    def test_add_sample(self, sample_telemetry):
        """Adding sample should increase sample count."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        trace.add_sample(sample_telemetry[0])
        assert trace.sample_count == 1

    def test_add_multiple_samples(self, sample_telemetry):
        """Adding multiple samples should maintain all."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        for sample in sample_telemetry:
            trace.add_sample(sample)
        assert trace.sample_count == 3

    def test_get_samples_returns_copy(self, sample_telemetry):
        """get_samples should return copy, not internal list."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        trace.add_sample(sample_telemetry[0])
        samples = trace.get_samples()
        samples.append(sample_telemetry[1])
        assert trace.sample_count == 1  # Original unchanged

    def test_get_samples_maintains_order(self, sample_telemetry):
        """Samples should be returned in chronological order."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        for sample in sample_telemetry:
            trace.add_sample(sample)
        samples = trace.get_samples()
        assert samples[0].timestamp_ms == 1000
        assert samples[1].timestamp_ms == 2000
        assert samples[2].timestamp_ms == 3000


class TestLapTraceInvariants:
    """Test invariant enforcement."""

    def test_cannot_add_sample_after_complete(self, sample_telemetry):
        """Cannot add samples after lap is marked complete."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0, lap_time_ms=85000)
        with pytest.raises(ValueError, match="Cannot add sample to completed lap"):
            trace.add_sample(sample_telemetry[0])

    def test_sample_must_match_lap_number(self, sample_telemetry):
        """Sample lap_number must match trace lap_number."""
        trace = LapTrace(session_uid=12345, lap_number=2, car_index=0)
        with pytest.raises(ValueError, match="Sample lap_number.*does not match"):
            trace.add_sample(sample_telemetry[0])  # Sample is lap 1

    def test_samples_must_be_chronological(self, sample_telemetry):
        """Samples must be added in chronological order."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        trace.add_sample(sample_telemetry[1])  # timestamp 2000
        with pytest.raises(ValueError, match="Sample timestamp.*is before last sample"):
            trace.add_sample(sample_telemetry[0])  # timestamp 1000


class TestLapTraceCompletion:
    """Test lap completion tracking."""

    def test_mark_complete(self):
        """mark_complete should set lap time and mark as complete."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.is_complete() is False
        trace.mark_complete(85000)
        assert trace.is_complete() is True
        assert trace.lap_time_ms == 85000

    def test_cannot_mark_complete_twice(self):
        """Cannot mark already complete lap as complete again."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0, lap_time_ms=85000)
        with pytest.raises(ValueError, match="already complete"):
            trace.mark_complete(86000)

    def test_mark_complete_with_negative_time(self):
        """Cannot mark complete with negative lap time."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        with pytest.raises(ValueError, match="lap_time_ms must be non-negative"):
            trace.mark_complete(-100)

    def test_mark_invalid(self):
        """mark_invalid should set is_valid to False."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.is_valid is True
        trace.mark_invalid()
        assert trace.is_valid is False


class TestLapTraceBusinessLogic:
    """Test business logic methods."""

    def test_get_average_speed(self, sample_telemetry):
        """get_average_speed should calculate correct average."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        for sample in sample_telemetry:
            trace.add_sample(sample)
        avg = trace.get_average_speed()
        assert avg == pytest.approx((150.0 + 200.0 + 180.0) / 3)

    def test_get_average_speed_empty(self):
        """get_average_speed should return None for empty trace."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.get_average_speed() is None

    def test_get_max_speed(self, sample_telemetry):
        """get_max_speed should return maximum speed."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        for sample in sample_telemetry:
            trace.add_sample(sample)
        assert trace.get_max_speed() == 200.0

    def test_get_max_speed_empty(self):
        """get_max_speed should return None for empty trace."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.get_max_speed() is None

    def test_get_sample_at_distance(self, sample_telemetry):
        """get_sample_at_distance should return closest sample."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        for sample in sample_telemetry:
            trace.add_sample(sample)
        closest = trace.get_sample_at_distance(190.0)
        assert closest.lap_distance == 200.0  # Closest to 190

    def test_get_sample_at_distance_empty(self):
        """get_sample_at_distance should return None for empty trace."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace.get_sample_at_distance(100.0) is None

    def test_get_samples_in_distance_range(self, sample_telemetry):
        """get_samples_in_distance_range should return samples in range."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        for sample in sample_telemetry:
            trace.add_sample(sample)
        samples = trace.get_samples_in_distance_range(150.0, 250.0)
        assert len(samples) == 1
        assert samples[0].lap_distance == 200.0


class TestLapTraceCarSetup:
    """Test car setup association."""

    def test_set_car_setup(self, valid_setup_data):
        """set_car_setup should associate setup with lap."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        setup = CarSetupSnapshot(**valid_setup_data)
        trace.set_car_setup(setup)
        assert trace.car_setup == setup

    def test_car_setup_in_constructor(self, valid_setup_data):
        """Car setup can be provided in constructor."""
        setup = CarSetupSnapshot(**valid_setup_data)
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0, car_setup=setup)
        assert trace.car_setup == setup


class TestLapTraceEquality:
    """Test entity identity semantics."""

    def test_same_id_equal(self):
        """Traces with same ID should be equal."""
        trace_id = "test-123"
        trace1 = LapTrace(session_uid=12345, lap_number=1, car_index=0, trace_id=trace_id)
        trace2 = LapTrace(session_uid=12345, lap_number=1, car_index=0, trace_id=trace_id)
        assert trace1 == trace2

    def test_different_id_not_equal(self):
        """Traces with different IDs should not be equal."""
        trace1 = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        trace2 = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        assert trace1 != trace2

    def test_same_id_same_hash(self):
        """Traces with same ID should have same hash."""
        trace_id = "test-123"
        trace1 = LapTrace(session_uid=12345, lap_number=1, car_index=0, trace_id=trace_id)
        trace2 = LapTrace(session_uid=12345, lap_number=1, car_index=0, trace_id=trace_id)
        assert hash(trace1) == hash(trace2)

    def test_can_use_in_set(self):
        """LapTrace should be usable in sets."""
        trace = LapTrace(session_uid=12345, lap_number=1, car_index=0)
        trace_set = {trace}
        assert trace in trace_set
        assert len(trace_set) == 1
