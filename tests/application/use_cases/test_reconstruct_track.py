"""Unit tests for ReconstructTrackUseCase.

Tests cover:
- Successful track reconstruction with valid data
- Error handling for missing sessions
- Error handling for insufficient laps
- Error handling for insufficient samples after filtering
- Sample aggregation logic from multiple laps
- Valid lap filtering (only valid & complete laps)
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, Mock
from src.application.use_cases.reconstruct_track import ReconstructTrackUseCase
from src.application.exceptions import (
    SessionNotFoundError,
    InsufficientDataError,
    InvalidTrackDataError
)
from src.domain.services.track_reconstructor import TrackReconstructor
from src.domain.entities.track_profile import TrackProfile
from src.domain.entities.lap_trace import LapTrace
from src.domain.value_objects.telemetry_sample import TelemetrySample


@pytest.fixture
def mock_telemetry_repository():
    """Fixture providing mocked ITelemetryRepository."""
    return AsyncMock()


@pytest.fixture
def mock_track_reconstructor():
    """Fixture providing mocked TrackReconstructor."""
    reconstructor = Mock(spec=TrackReconstructor)
    reconstructor.MIN_SAMPLES_REQUIRED = 100
    return reconstructor


@pytest.fixture
def use_case(mock_telemetry_repository, mock_track_reconstructor):
    """Fixture providing ReconstructTrackUseCase with mocked dependencies."""
    return ReconstructTrackUseCase(
        telemetry_repository=mock_telemetry_repository,
        track_reconstructor=mock_track_reconstructor
    )


def create_sample_telemetry_sample(lap_distance: float, lap_number: int = 1) -> TelemetrySample:
    """Helper to create a telemetry sample with minimal required fields."""
    return TelemetrySample(
        timestamp_ms=1000,
        world_position_x=10.0,
        world_position_y=0.0,
        world_position_z=10.0,
        world_velocity_x=0.0,
        world_velocity_y=0.0,
        world_velocity_z=0.0,
        g_force_lateral=0.0,
        g_force_longitudinal=0.0,
        yaw=0.0,
        speed=150.0,
        throttle=0.8,
        steer=0.0,
        brake=0.0,
        gear=5,
        engine_rpm=8000,
        drs=0,
        lap_distance=lap_distance,
        lap_number=lap_number
    )


def create_mock_lap_trace(
    lap_number: int,
    sample_count: int = 200,
    is_valid: bool = True,
    is_complete: bool = True
) -> LapTrace:
    """Helper to create a mocked LapTrace with samples."""
    lap_trace = LapTrace(
        session_uid=12345,
        lap_number=lap_number,
        car_index=0,
        is_valid=is_valid,
        lap_time_ms=85000 if is_complete else None
    )
    
    # Add telemetry samples
    for i in range(sample_count):
        lap_distance = (i / sample_count) * 5000  # 5000m track
        sample = create_sample_telemetry_sample(lap_distance, lap_number)
        
        # Manually set internal state since we're mocking
        lap_trace._samples.append(sample)
    
    if is_complete:
        lap_trace._is_complete = True
    
    return lap_trace


# ============================================================================
# Successful Reconstruction Tests
# ============================================================================

@pytest.mark.asyncio
async def test_successful_track_reconstruction(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test successful track reconstruction with valid data."""
    # Setup: Mock session data
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco",
        "session_type": 18,
        "lap_count": 5
    }
    
    # Setup: Mock lap traces (3 valid laps)
    lap_traces = [
        create_mock_lap_trace(lap_number=1, sample_count=200),
        create_mock_lap_trace(lap_number=2, sample_count=200),
        create_mock_lap_trace(lap_number=3, sample_count=200),
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Setup: Mock TrackReconstructor outputs
    mock_centerline = np.array([[0, 0], [100, 100], [200, 0]])
    mock_distances = np.array([0, 141.42, 282.84])
    mock_curvature = np.array([0.01, 0.02, 0.01])
    mock_elevation = np.array([0.0, 5.0, 0.0])
    
    mock_track_reconstructor.compute_centerline.return_value = (mock_centerline, mock_distances)
    mock_track_reconstructor.compute_curvature.return_value = mock_curvature
    mock_track_reconstructor.compute_elevation.return_value = mock_elevation
    
    # Execute
    result = await use_case.execute(session_uid=12345, min_laps=3)
    
    # Verify
    assert isinstance(result, TrackProfile)
    assert result.track_id == "monaco"
    assert len(result.centerline) == 3
    assert len(result.curvature) == 3
    assert len(result.elevation) == 3
    assert len(result.distance) == 3
    
    # Verify repository was called correctly
    mock_telemetry_repository.get_session.assert_called_once_with(12345)
    mock_telemetry_repository.list_lap_traces.assert_called_once_with(
        session_uid=12345,
        limit=100
    )
    
    # Verify reconstructor was called
    assert mock_track_reconstructor.compute_centerline.called
    assert mock_track_reconstructor.compute_curvature.called
    assert mock_track_reconstructor.compute_elevation.called


@pytest.mark.asyncio
async def test_successful_reconstruction_with_more_laps_than_needed(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test reconstruction when more laps available than min_laps."""
    # Setup: Mock session and 5 laps (more than min_laps=3)
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "silverstone"
    }
    
    lap_traces = [
        create_mock_lap_trace(lap_number=i, sample_count=200)
        for i in range(1, 6)  # 5 laps
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Mock reconstructor outputs
    mock_centerline = np.array([[0, 0], [100, 0]])
    mock_distances = np.array([0, 100])
    mock_track_reconstructor.compute_centerline.return_value = (mock_centerline, mock_distances)
    mock_track_reconstructor.compute_curvature.return_value = np.array([0.0, 0.0])
    mock_track_reconstructor.compute_elevation.return_value = np.array([0.0, 0.0])
    
    # Execute with min_laps=3
    result = await use_case.execute(session_uid=12345, min_laps=3)
    
    # Should succeed - have 5 laps, need only 3
    assert isinstance(result, TrackProfile)
    assert result.track_id == "silverstone"


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_session_not_found_error(
    use_case,
    mock_telemetry_repository
):
    """Test SessionNotFoundError when session doesn't exist."""
    # Setup: Repository returns None for session
    mock_telemetry_repository.get_session.return_value = None
    
    # Execute & Verify
    with pytest.raises(SessionNotFoundError) as exc_info:
        await use_case.execute(session_uid=99999)
    
    assert exc_info.value.session_uid == 99999
    assert "99999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_insufficient_laps_error(
    use_case,
    mock_telemetry_repository
):
    """Test InsufficientDataError when too few laps available."""
    # Setup: Session exists but only 1 lap
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    lap_traces = [create_mock_lap_trace(lap_number=1)]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Execute & Verify
    with pytest.raises(InsufficientDataError) as exc_info:
        await use_case.execute(session_uid=12345, min_laps=3)
    
    assert exc_info.value.required == 3
    assert exc_info.value.actual == 1
    assert exc_info.value.data_type == "laps"
    assert "laps" in str(exc_info.value)


@pytest.mark.asyncio
async def test_insufficient_samples_after_filtering(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test InsufficientDataError when samples < MIN_SAMPLES_REQUIRED after filtering."""
    # Setup: Session and laps exist, but very few samples per lap
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    # Create laps with only 30 samples each (3 laps * 30 = 90 samples < 100 required)
    lap_traces = [
        create_mock_lap_trace(lap_number=i, sample_count=30)
        for i in range(1, 4)
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    mock_track_reconstructor.MIN_SAMPLES_REQUIRED = 100
    
    # Execute & Verify
    with pytest.raises(InsufficientDataError) as exc_info:
        await use_case.execute(session_uid=12345, min_laps=3)
    
    assert exc_info.value.required == 100
    assert exc_info.value.actual == 90  # 3 laps * 30 samples
    assert exc_info.value.data_type == "telemetry samples"


@pytest.mark.asyncio
async def test_invalid_track_length_error(
    use_case,
    mock_telemetry_repository
):
    """Test InvalidTrackDataError when computed track_length_m is invalid."""
    # Setup: Session and laps, but all samples have lap_distance=0
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    # Create laps with all samples at lap_distance=0 (invalid)
    lap_traces = []
    for lap_num in range(1, 4):
        lap_trace = LapTrace(
            session_uid=12345,
            lap_number=lap_num,
            car_index=0,
            lap_time_ms=85000
        )
        # Add samples all at distance 0
        for _ in range(200):
            sample = create_sample_telemetry_sample(lap_distance=0.0, lap_number=lap_num)
            lap_trace._samples.append(sample)
        lap_trace._is_complete = True
        lap_traces.append(lap_trace)
    
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Execute & Verify
    with pytest.raises(InvalidTrackDataError) as exc_info:
        await use_case.execute(session_uid=12345)
    
    assert exc_info.value.field == "track_length_m"
    assert exc_info.value.value == 0.0


# ============================================================================
# Lap Filtering Tests
# ============================================================================

@pytest.mark.asyncio
async def test_filters_out_invalid_laps(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test that invalid laps are filtered out during sample aggregation."""
    # Setup: Mix of valid and invalid laps
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    lap_traces = [
        create_mock_lap_trace(lap_number=1, sample_count=200, is_valid=True),
        create_mock_lap_trace(lap_number=2, sample_count=200, is_valid=False),  # Invalid
        create_mock_lap_trace(lap_number=3, sample_count=200, is_valid=True),
        create_mock_lap_trace(lap_number=4, sample_count=200, is_valid=True),
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Mock reconstructor
    mock_centerline = np.array([[0, 0], [100, 0]])
    mock_distances = np.array([0, 100])
    mock_track_reconstructor.compute_centerline.return_value = (mock_centerline, mock_distances)
    mock_track_reconstructor.compute_curvature.return_value = np.array([0.0, 0.0])
    mock_track_reconstructor.compute_elevation.return_value = np.array([0.0, 0.0])
    
    # Execute
    result = await use_case.execute(session_uid=12345, min_laps=3)
    
    # Verify: Should use only 3 valid laps (laps 1, 3, 4), skipping invalid lap 2
    # Total samples = 3 valid laps * 200 samples = 600
    compute_centerline_call = mock_track_reconstructor.compute_centerline.call_args
    samples_passed = compute_centerline_call[1]["samples"]
    assert len(samples_passed) == 600  # Only valid laps


@pytest.mark.asyncio
async def test_filters_out_incomplete_laps(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test that incomplete laps are filtered out during sample aggregation."""
    # Setup: Mix of complete and incomplete laps
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    lap_traces = [
        create_mock_lap_trace(lap_number=1, sample_count=200, is_complete=True),
        create_mock_lap_trace(lap_number=2, sample_count=200, is_complete=False),  # Incomplete
        create_mock_lap_trace(lap_number=3, sample_count=200, is_complete=True),
        create_mock_lap_trace(lap_number=4, sample_count=200, is_complete=True),
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Mock reconstructor
    mock_centerline = np.array([[0, 0], [100, 0]])
    mock_distances = np.array([0, 100])
    mock_track_reconstructor.compute_centerline.return_value = (mock_centerline, mock_distances)
    mock_track_reconstructor.compute_curvature.return_value = np.array([0.0, 0.0])
    mock_track_reconstructor.compute_elevation.return_value = np.array([0.0, 0.0])
    
    # Execute
    result = await use_case.execute(session_uid=12345, min_laps=3)
    
    # Verify: Should use only 3 complete laps, skipping incomplete lap 2
    compute_centerline_call = mock_track_reconstructor.compute_centerline.call_args
    samples_passed = compute_centerline_call[1]["samples"]
    assert len(samples_passed) == 600  # Only complete laps


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_minimum_lap_requirement_exactly_met(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test reconstruction when exactly min_laps are available."""
    # Setup: Exactly 3 laps (min_laps=3)
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    lap_traces = [
        create_mock_lap_trace(lap_number=i, sample_count=200)
        for i in range(1, 4)  # Exactly 3 laps
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Mock reconstructor
    mock_centerline = np.array([[0, 0], [100, 0]])
    mock_distances = np.array([0, 100])
    mock_track_reconstructor.compute_centerline.return_value = (mock_centerline, mock_distances)
    mock_track_reconstructor.compute_curvature.return_value = np.array([0.0, 0.0])
    mock_track_reconstructor.compute_elevation.return_value = np.array([0.0, 0.0])
    
    # Execute
    result = await use_case.execute(session_uid=12345, min_laps=3)
    
    # Should succeed
    assert isinstance(result, TrackProfile)


@pytest.mark.asyncio
async def test_custom_min_laps_parameter(
    use_case,
    mock_telemetry_repository,
    mock_track_reconstructor
):
    """Test reconstruction with custom min_laps parameter."""
    # Setup: 5 laps available
    mock_telemetry_repository.get_session.return_value = {
        "session_uid": 12345,
        "track_id": "monaco"
    }
    
    lap_traces = [
        create_mock_lap_trace(lap_number=i, sample_count=200)
        for i in range(1, 6)  # 5 laps
    ]
    mock_telemetry_repository.list_lap_traces.return_value = lap_traces
    
    # Mock reconstructor
    mock_centerline = np.array([[0, 0], [100, 0]])
    mock_distances = np.array([0, 100])
    mock_track_reconstructor.compute_centerline.return_value = (mock_centerline, mock_distances)
    mock_track_reconstructor.compute_curvature.return_value = np.array([0.0, 0.0])
    mock_track_reconstructor.compute_elevation.return_value = np.array([0.0, 0.0])
    
    # Execute with min_laps=5
    result = await use_case.execute(session_uid=12345, min_laps=5)
    
    # Should succeed
    assert isinstance(result, TrackProfile)
    
    # Execute with min_laps=6 (more than available)
    with pytest.raises(InsufficientDataError):
        await use_case.execute(session_uid=12345, min_laps=6)
