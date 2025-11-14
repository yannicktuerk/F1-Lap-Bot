"""Unit tests for MatheCoachAnalysisUseCase.

Tests cover:
- Successful analysis with latest lap
- Successful analysis with specific lap number
- Error handling for missing sessions
- Error handling for missing laps
- Error handling for missing specific lap number
- Integration of all domain services
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, Mock
from src.application.use_cases.mathe_coach_analysis import MatheCoachAnalysisUseCase
from src.application.exceptions import (
    SessionNotFoundError,
    LapNotFoundError
)
from src.domain.entities.track_profile import TrackProfile
from src.domain.entities.lap_trace import LapTrace
from src.domain.entities.ideal_lap import IdealLap
from src.domain.services.lap_comparator import ComparisonSegment, ErrorType
from src.domain.value_objects.telemetry_sample import TelemetrySample


@pytest.fixture
def mock_telemetry_repository():
    """Fixture providing mocked ITelemetryRepository."""
    return AsyncMock()


@pytest.fixture
def mock_reconstruct_track():
    """Fixture providing mocked ReconstructTrackUseCase."""
    return AsyncMock()


@pytest.fixture
def mock_ideal_lap_constructor():
    """Fixture providing mocked IdealLapConstructor."""
    return Mock()


@pytest.fixture
def mock_lap_comparator():
    """Fixture providing mocked LapComparator."""
    return Mock()


@pytest.fixture
def mock_feedback_generator():
    """Fixture providing mocked MatheCoachFeedbackGenerator."""
    return Mock()


@pytest.fixture
def use_case(
    mock_telemetry_repository,
    mock_reconstruct_track,
    mock_ideal_lap_constructor,
    mock_lap_comparator,
    mock_feedback_generator
):
    """Fixture providing MatheCoachAnalysisUseCase with mocked dependencies."""
    return MatheCoachAnalysisUseCase(
        telemetry_repository=mock_telemetry_repository,
        reconstruct_track=mock_reconstruct_track,
        ideal_lap_constructor=mock_ideal_lap_constructor,
        lap_comparator=mock_lap_comparator,
        feedback_generator=mock_feedback_generator
    )


def create_mock_track_profile() -> TrackProfile:
    """Helper to create a mock TrackProfile."""
    distance = np.linspace(0, 5000, 100)
    centerline = np.column_stack([distance, np.zeros(100)])
    curvature = np.zeros(100)
    curvature[30:40] = 0.02  # Corner section
    elevation = np.zeros(100)
    
    return TrackProfile(
        track_id="monaco",
        centerline=centerline,
        curvature=curvature,
        elevation=elevation,
        distance=distance,
        track_length_m=5000.0
    )


def create_mock_lap_trace(lap_number: int = 1) -> LapTrace:
    """Helper to create a mock LapTrace."""
    lap_trace = LapTrace(
        session_uid=12345,
        lap_number=lap_number,
        car_index=0,
        is_valid=True,
        lap_time_ms=85000
    )
    
    # Add minimal samples
    for i in range(50):
        lap_distance = i * 100.0
        sample = TelemetrySample(
            timestamp_ms=1000 + i * 100,
            world_position_x=lap_distance,
            world_position_y=0.0,
            world_position_z=0.0,
            world_velocity_x=50.0,
            world_velocity_y=0.0,
            world_velocity_z=0.0,
            g_force_lateral=0.0,
            g_force_longitudinal=0.0,
            yaw=0.0,
            speed=180.0,
            throttle=0.8,
            steer=0.0,
            brake=0.0,
            gear=6,
            engine_rpm=9000,
            drs=0,
            lap_distance=lap_distance,
            lap_number=lap_number
        )
        lap_trace._samples.append(sample)
    
    lap_trace._is_complete = True
    return lap_trace


def create_mock_ideal_lap() -> IdealLap:
    """Helper to create a mock IdealLap."""
    distance = np.linspace(0, 5000, 100)
    ideal_speed = np.full(100, 55.56)  # ~200 km/h = 55.56 m/s
    ideal_throttle = np.ones(100, dtype=int)  # Full throttle
    ideal_brake = np.zeros(100, dtype=int)  # No braking
    sector_times = [30.0, 30.0, 30.0]  # 3 sectors
    total_time = 90.0
    
    return IdealLap(
        track_id="monaco",
        ideal_speed=ideal_speed,
        ideal_throttle=ideal_throttle,
        ideal_brake=ideal_brake,
        distance=distance,
        sector_times=sector_times,
        total_time=total_time
    )


def create_mock_comparison_segments() -> list[ComparisonSegment]:
    """Helper to create mock comparison segments."""
    return [
        ComparisonSegment(
            segment_id=0,
            distance_start=0.0,
            distance_end=1000.0,
            time_loss=0.3,
            speed_delta_entry=-5.0,
            speed_delta_apex=-3.0,
            speed_delta_exit=-2.0,
            error_type=ErrorType.EARLY_BRAKING,
            explanation="Early braking"
        ),
        ComparisonSegment(
            segment_id=1,
            distance_start=1000.0,
            distance_end=2000.0,
            time_loss=0.2,
            speed_delta_entry=-1.0,
            speed_delta_apex=-1.0,
            speed_delta_exit=-3.0,
            error_type=ErrorType.LATE_THROTTLE,
            explanation="Late throttle"
        )
    ]


# ============================================================================
# Successful Analysis Tests
# ============================================================================

@pytest.mark.asyncio
async def test_successful_analysis_latest_lap(
    use_case,
    mock_telemetry_repository,
    mock_reconstruct_track,
    mock_ideal_lap_constructor,
    mock_lap_comparator,
    mock_feedback_generator
):
    """Test successful analysis with latest lap."""
    # Setup: Mock track profile
    track_profile = create_mock_track_profile()
    mock_reconstruct_track.execute.return_value = track_profile
    
    # Setup: Mock latest lap
    lap_trace = create_mock_lap_trace(lap_number=5)
    mock_telemetry_repository.get_latest_lap_trace.return_value = lap_trace
    
    # Setup: Mock ideal lap
    ideal_lap = create_mock_ideal_lap()
    mock_ideal_lap_constructor.construct_ideal_lap.return_value = ideal_lap
    
    # Setup: Mock comparison segments
    comparison_segments = create_mock_comparison_segments()
    mock_lap_comparator.compare_laps.return_value = comparison_segments
    
    # Setup: Mock feedback
    mock_feedback = "# Monaco Lap Analysis\n\n+0.5s vs ideal lap"
    mock_feedback_generator.generate_feedback.return_value = mock_feedback
    
    # Execute
    result = await use_case.execute(session_uid=12345)
    
    # Verify result is feedback string
    assert result == mock_feedback
    assert "Monaco" in result
    
    # Verify workflow called correctly
    mock_reconstruct_track.execute.assert_called_once_with(12345)
    mock_telemetry_repository.get_latest_lap_trace.assert_called_once_with(12345)
    mock_ideal_lap_constructor.construct_ideal_lap.assert_called_once_with(track_profile)
    mock_lap_comparator.compare_laps.assert_called_once()
    mock_feedback_generator.generate_feedback.assert_called_once()


@pytest.mark.asyncio
async def test_successful_analysis_specific_lap_number(
    use_case,
    mock_telemetry_repository,
    mock_reconstruct_track,
    mock_ideal_lap_constructor,
    mock_lap_comparator,
    mock_feedback_generator
):
    """Test successful analysis with specific lap number."""
    # Setup: Mock track profile
    track_profile = create_mock_track_profile()
    mock_reconstruct_track.execute.return_value = track_profile
    
    # Setup: Mock lap list with specific lap number
    all_laps = [
        create_mock_lap_trace(lap_number=3),
        create_mock_lap_trace(lap_number=4),
        create_mock_lap_trace(lap_number=5),
    ]
    mock_telemetry_repository.list_lap_traces.return_value = all_laps
    
    # Setup: Mock ideal lap
    ideal_lap = create_mock_ideal_lap()
    mock_ideal_lap_constructor.construct_ideal_lap.return_value = ideal_lap
    
    # Setup: Mock comparison segments
    comparison_segments = create_mock_comparison_segments()
    mock_lap_comparator.compare_laps.return_value = comparison_segments
    
    # Setup: Mock feedback
    mock_feedback = "# Monaco Lap 4 Analysis\n\n+0.4s vs ideal lap"
    mock_feedback_generator.generate_feedback.return_value = mock_feedback
    
    # Execute with specific lap_number=4
    result = await use_case.execute(session_uid=12345, lap_number=4)
    
    # Verify result
    assert result == mock_feedback
    
    # Verify lap number filtering
    mock_telemetry_repository.list_lap_traces.assert_called_once_with(
        session_uid=12345,
        limit=1000
    )
    
    # Verify correct lap was used (lap_number=4)
    call_args = mock_lap_comparator.compare_laps.call_args
    driver_lap = call_args.kwargs["driver_lap"]
    assert driver_lap.lap_number == 4


@pytest.mark.asyncio
async def test_domain_services_called_with_correct_parameters(
    use_case,
    mock_telemetry_repository,
    mock_reconstruct_track,
    mock_ideal_lap_constructor,
    mock_lap_comparator,
    mock_feedback_generator
):
    """Test that all domain services receive correct parameters."""
    # Setup mocks
    track_profile = create_mock_track_profile()
    mock_reconstruct_track.execute.return_value = track_profile
    
    lap_trace = create_mock_lap_trace()
    mock_telemetry_repository.get_latest_lap_trace.return_value = lap_trace
    
    ideal_lap = create_mock_ideal_lap()
    mock_ideal_lap_constructor.construct_ideal_lap.return_value = ideal_lap
    
    comparison_segments = create_mock_comparison_segments()
    mock_lap_comparator.compare_laps.return_value = comparison_segments
    
    mock_feedback_generator.generate_feedback.return_value = "Feedback"
    
    # Execute
    await use_case.execute(session_uid=12345)
    
    # Verify LapComparator called with correct parameters
    comparator_call = mock_lap_comparator.compare_laps.call_args
    assert comparator_call.kwargs["driver_lap"] == lap_trace
    assert comparator_call.kwargs["ideal_lap"] == ideal_lap
    assert comparator_call.kwargs["track_profile"] == track_profile
    assert "segments" in comparator_call.kwargs
    
    # Verify FeedbackGenerator called with correct parameters
    feedback_call = mock_feedback_generator.generate_feedback.call_args
    assert feedback_call.kwargs["comparison_segments"] == comparison_segments
    assert feedback_call.kwargs["track_profile"] == track_profile
    assert feedback_call.kwargs["track_name"] == "monaco"  # From track_profile
    assert feedback_call.kwargs["top_n"] == 5


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_session_not_found_error(
    use_case,
    mock_reconstruct_track
):
    """Test SessionNotFoundError propagation from track reconstruction."""
    # Setup: ReconstructTrackUseCase raises SessionNotFoundError
    mock_reconstruct_track.execute.side_effect = SessionNotFoundError(12345)
    
    # Execute and verify error
    with pytest.raises(SessionNotFoundError) as exc_info:
        await use_case.execute(session_uid=12345)
    
    assert exc_info.value.session_uid == 12345


@pytest.mark.asyncio
async def test_no_laps_found_for_session(
    use_case,
    mock_telemetry_repository,
    mock_reconstruct_track
):
    """Test LapNotFoundError when no laps exist in session."""
    # Setup: Track reconstruction succeeds
    track_profile = create_mock_track_profile()
    mock_reconstruct_track.execute.return_value = track_profile
    
    # Setup: No laps found
    mock_telemetry_repository.get_latest_lap_trace.return_value = None
    
    # Execute and verify error
    with pytest.raises(LapNotFoundError) as exc_info:
        await use_case.execute(session_uid=12345)
    
    assert "No lap found for session 12345" in str(exc_info.value)


@pytest.mark.asyncio
async def test_specific_lap_number_not_found(
    use_case,
    mock_telemetry_repository,
    mock_reconstruct_track
):
    """Test LapNotFoundError when specific lap_number does not exist."""
    # Setup: Track reconstruction succeeds
    track_profile = create_mock_track_profile()
    mock_reconstruct_track.execute.return_value = track_profile
    
    # Setup: Laps exist but not lap_number=10
    all_laps = [
        create_mock_lap_trace(lap_number=1),
        create_mock_lap_trace(lap_number=2),
        create_mock_lap_trace(lap_number=3),
    ]
    mock_telemetry_repository.list_lap_traces.return_value = all_laps
    
    # Execute and verify error
    with pytest.raises(LapNotFoundError) as exc_info:
        await use_case.execute(session_uid=12345, lap_number=10)
    
    assert "Lap number 10 not found" in str(exc_info.value)


# ============================================================================
# Track Configuration Tests
# ============================================================================

def test_get_track_segments_default(use_case):
    """Test _get_track_segments returns default for unknown track."""
    segments = use_case._get_track_segments("unknown_track")
    
    # Should return default 3-sector split
    assert len(segments) == 3
    assert segments[0]["name"] == "Sector 1"
    assert segments[1]["name"] == "Sector 2"
    assert segments[2]["name"] == "Sector 3"


def test_get_track_name_fallback(use_case):
    """Test _get_track_name falls back to track_id if not configured."""
    track_name = use_case._get_track_name("unknown_track")
    
    # Should return track_id as fallback
    assert track_name == "unknown_track"


def test_get_track_name_for_monaco(use_case):
    """Test _get_track_name returns track_id when not in mapping."""
    # Note: Current implementation only has "default" in _TRACK_NAMES
    # So "monaco" falls back to track_id
    track_name = use_case._get_track_name("monaco")
    assert track_name == "monaco"
