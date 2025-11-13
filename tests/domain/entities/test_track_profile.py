"""Unit tests for TrackProfile value object.

Tests validation, interpolation methods, and section extraction
for the TrackProfile domain entity.
"""

import pytest
import numpy as np
from src.domain.entities.track_profile import TrackProfile


@pytest.fixture
def valid_track_data():
    """Fixture providing valid track geometry data for testing.
    
    Returns:
        Dict with centerline, curvature, elevation, distance arrays
        and track_length_m representing a simple 1000m track.
    """
    # Create a simple track with 100 points over 1000m
    n_points = 100
    distance = np.linspace(0, 1000, n_points)
    
    # Simple centerline: circular arc
    theta = np.linspace(0, 2 * np.pi, n_points)
    centerline = np.column_stack([
        100 * np.cos(theta),
        100 * np.sin(theta)
    ])
    
    # Curvature: constant for circular arc (1/radius)
    curvature = np.full(n_points, 0.01)  # 1/100m radius
    
    # Elevation: sinusoidal profile
    elevation = 10 * np.sin(theta) + 50  # Varies between 40m and 60m
    
    return {
        "track_id": "test_track",
        "centerline": centerline,
        "curvature": curvature,
        "elevation": elevation,
        "distance": distance,
        "track_length_m": 1000.0
    }


@pytest.fixture
def valid_track_profile(valid_track_data):
    """Fixture providing a valid TrackProfile instance."""
    return TrackProfile(**valid_track_data)


# ============================================================================
# Validation Tests
# ============================================================================

def test_valid_track_profile_creation(valid_track_data):
    """Test that valid data creates TrackProfile without errors."""
    profile = TrackProfile(**valid_track_data)
    
    assert profile.track_id == "test_track"
    assert len(profile.centerline) == 100
    assert len(profile.curvature) == 100
    assert len(profile.elevation) == 100
    assert len(profile.distance) == 100
    assert profile.track_length_m == 1000.0


def test_array_length_mismatch_centerline(valid_track_data):
    """Test that mismatched centerline length raises ValueError."""
    valid_track_data["centerline"] = valid_track_data["centerline"][:50]  # Half length
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "All arrays must have same length" in str(exc_info.value)
    assert "centerline=50" in str(exc_info.value)


def test_array_length_mismatch_curvature(valid_track_data):
    """Test that mismatched curvature length raises ValueError."""
    valid_track_data["curvature"] = valid_track_data["curvature"][:75]
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "All arrays must have same length" in str(exc_info.value)
    assert "curvature=75" in str(exc_info.value)


def test_array_length_mismatch_elevation(valid_track_data):
    """Test that mismatched elevation length raises ValueError."""
    valid_track_data["elevation"] = valid_track_data["elevation"][:80]
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "All arrays must have same length" in str(exc_info.value)
    assert "elevation=80" in str(exc_info.value)


def test_array_length_mismatch_distance(valid_track_data):
    """Test that mismatched distance length raises ValueError."""
    valid_track_data["distance"] = valid_track_data["distance"][:90]
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "All arrays must have same length" in str(exc_info.value)
    assert "distance=90" in str(exc_info.value)


def test_non_monotonic_distance_decreasing(valid_track_data):
    """Test that non-increasing distance raises ValueError."""
    # Make distance decrease at index 50
    valid_track_data["distance"][50] = valid_track_data["distance"][49] - 1.0
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "distance array must be monotonically increasing" in str(exc_info.value)
    assert "Violation at index 49" in str(exc_info.value)


def test_non_monotonic_distance_equal(valid_track_data):
    """Test that equal consecutive distances raises ValueError."""
    # Make two consecutive distances equal
    valid_track_data["distance"][50] = valid_track_data["distance"][49]
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "distance array must be monotonically increasing" in str(exc_info.value)


def test_negative_track_length():
    """Test that negative track_length_m raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(
            track_id="test",
            centerline=np.array([[0, 0], [1, 1]]),
            curvature=np.array([0.0, 0.0]),
            elevation=np.array([0.0, 0.0]),
            distance=np.array([0.0, 1.0]),
            track_length_m=-100.0
        )
    
    assert "track_length_m must be positive" in str(exc_info.value)


def test_zero_track_length():
    """Test that zero track_length_m raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(
            track_id="test",
            centerline=np.array([[0, 0], [1, 1]]),
            curvature=np.array([0.0, 0.0]),
            elevation=np.array([0.0, 0.0]),
            distance=np.array([0.0, 1.0]),
            track_length_m=0.0
        )
    
    assert "track_length_m must be positive" in str(exc_info.value)


def test_invalid_centerline_shape_1d(valid_track_data):
    """Test that 1D centerline array raises ValueError."""
    valid_track_data["centerline"] = np.array([0.0, 1.0, 2.0])  # 1D array
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "centerline must be Nx2 array" in str(exc_info.value)


def test_invalid_centerline_shape_wrong_columns(valid_track_data):
    """Test that centerline with wrong number of columns raises ValueError."""
    # Create Nx3 array instead of Nx2
    valid_track_data["centerline"] = np.column_stack([
        valid_track_data["centerline"],
        np.zeros(len(valid_track_data["centerline"]))
    ])
    
    with pytest.raises(ValueError) as exc_info:
        TrackProfile(**valid_track_data)
    
    assert "centerline must be Nx2 array" in str(exc_info.value)


def test_optional_track_id(valid_track_data):
    """Test that track_id can be None."""
    valid_track_data["track_id"] = None
    profile = TrackProfile(**valid_track_data)
    
    assert profile.track_id is None


# ============================================================================
# Interpolation Tests
# ============================================================================

def test_get_curvature_at_exact_point(valid_track_profile):
    """Test curvature interpolation at exact distance point."""
    # Get curvature at exact distance point (index 50)
    distance = valid_track_profile.distance[50]
    expected_curvature = valid_track_profile.curvature[50]
    
    result = valid_track_profile.get_curvature_at(distance)
    
    assert result == pytest.approx(expected_curvature, rel=1e-9)


def test_get_curvature_at_interpolated(valid_track_profile):
    """Test curvature interpolation between two points."""
    # Get curvature midway between two points
    distance1 = valid_track_profile.distance[50]
    distance2 = valid_track_profile.distance[51]
    mid_distance = (distance1 + distance2) / 2
    
    curv1 = valid_track_profile.curvature[50]
    curv2 = valid_track_profile.curvature[51]
    expected_curv = (curv1 + curv2) / 2  # Linear interpolation
    
    result = valid_track_profile.get_curvature_at(mid_distance)
    
    assert result == pytest.approx(expected_curv, rel=1e-6)


def test_get_curvature_at_start(valid_track_profile):
    """Test curvature at track start."""
    result = valid_track_profile.get_curvature_at(0.0)
    expected = valid_track_profile.curvature[0]
    
    assert result == pytest.approx(expected, rel=1e-9)


def test_get_curvature_at_end(valid_track_profile):
    """Test curvature at track end."""
    result = valid_track_profile.get_curvature_at(valid_track_profile.track_length_m)
    expected = valid_track_profile.curvature[-1]
    
    assert result == pytest.approx(expected, rel=1e-9)


def test_get_elevation_at_exact_point(valid_track_profile):
    """Test elevation interpolation at exact distance point."""
    distance = valid_track_profile.distance[50]
    expected_elevation = valid_track_profile.elevation[50]
    
    result = valid_track_profile.get_elevation_at(distance)
    
    assert result == pytest.approx(expected_elevation, rel=1e-9)


def test_get_elevation_at_interpolated(valid_track_profile):
    """Test elevation interpolation between two points."""
    distance1 = valid_track_profile.distance[50]
    distance2 = valid_track_profile.distance[51]
    mid_distance = (distance1 + distance2) / 2
    
    elev1 = valid_track_profile.elevation[50]
    elev2 = valid_track_profile.elevation[51]
    expected_elev = (elev1 + elev2) / 2
    
    result = valid_track_profile.get_elevation_at(mid_distance)
    
    assert result == pytest.approx(expected_elev, rel=1e-6)


def test_get_elevation_at_boundaries_extrapolation(valid_track_profile):
    """Test elevation extrapolation beyond track boundaries."""
    # Beyond end of track - should extrapolate to last value
    result_beyond = valid_track_profile.get_elevation_at(
        valid_track_profile.track_length_m + 100
    )
    expected_beyond = valid_track_profile.elevation[-1]
    
    # Before start of track - should extrapolate to first value
    result_before = valid_track_profile.get_elevation_at(-100)
    expected_before = valid_track_profile.elevation[0]
    
    assert result_beyond == pytest.approx(expected_beyond, rel=1e-9)
    assert result_before == pytest.approx(expected_before, rel=1e-9)


def test_get_slope_at_flat_section():
    """Test slope calculation on flat track section."""
    # Create flat track (constant elevation)
    distance = np.linspace(0, 1000, 100)
    centerline = np.column_stack([distance, np.zeros(100)])
    curvature = np.zeros(100)
    elevation = np.full(100, 50.0)  # Constant elevation
    
    profile = TrackProfile(
        track_id="flat_track",
        centerline=centerline,
        curvature=curvature,
        elevation=elevation,
        distance=distance,
        track_length_m=1000.0
    )
    
    # Slope should be ~0 anywhere on flat track
    slope_mid = profile.get_slope_at(500.0)
    
    assert slope_mid == pytest.approx(0.0, abs=1e-6)


def test_get_slope_at_uphill_section():
    """Test slope calculation on uphill section."""
    # Create track with constant uphill gradient
    distance = np.linspace(0, 1000, 100)
    centerline = np.column_stack([distance, np.zeros(100)])
    curvature = np.zeros(100)
    # 5% gradient: 50m elevation gain over 1000m
    elevation = distance * 0.05
    
    profile = TrackProfile(
        track_id="uphill_track",
        centerline=centerline,
        curvature=curvature,
        elevation=elevation,
        distance=distance,
        track_length_m=1000.0
    )
    
    # Slope should be ~0.05 (5% gradient) anywhere on track
    slope_mid = profile.get_slope_at(500.0)
    
    assert slope_mid == pytest.approx(0.05, abs=1e-3)


def test_get_slope_at_downhill_section():
    """Test slope calculation on downhill section."""
    # Create track with constant downhill gradient
    distance = np.linspace(0, 1000, 100)
    centerline = np.column_stack([distance, np.zeros(100)])
    curvature = np.zeros(100)
    # -3% gradient: 30m elevation loss over 1000m
    elevation = 100 - (distance * 0.03)
    
    profile = TrackProfile(
        track_id="downhill_track",
        centerline=centerline,
        curvature=curvature,
        elevation=elevation,
        distance=distance,
        track_length_m=1000.0
    )
    
    # Slope should be ~-0.03 (-3% gradient)
    slope_mid = profile.get_slope_at(500.0)
    
    assert slope_mid == pytest.approx(-0.03, abs=1e-3)


def test_get_slope_at_single_point_track():
    """Test slope returns 0 for track with single point."""
    profile = TrackProfile(
        track_id="single_point",
        centerline=np.array([[0.0, 0.0]]),
        curvature=np.array([0.0]),
        elevation=np.array([50.0]),
        distance=np.array([0.0]),
        track_length_m=1.0
    )
    
    slope = profile.get_slope_at(0.0)
    
    assert slope == 0.0


# ============================================================================
# Section Extraction Tests
# ============================================================================

def test_get_section_valid_range(valid_track_profile):
    """Test extracting valid track section."""
    # Extract middle section (300m to 700m)
    section = valid_track_profile.get_section(300.0, 700.0)
    
    # Check section properties
    assert section.track_id == valid_track_profile.track_id
    # Distance is approximate due to circular arc geometry (not linear distance)
    assert section.track_length_m == pytest.approx(400.0, abs=10.0)
    
    # Distance should start from 0
    assert section.distance[0] == pytest.approx(0.0, abs=1e-6)
    
    # Check that section has reasonable number of points
    # Original has 100 points over 1000m, so ~40% should have ~40 points
    assert 30 <= len(section.distance) <= 50


def test_get_section_start_to_mid(valid_track_profile):
    """Test extracting section from start to middle."""
    section = valid_track_profile.get_section(0.0, 500.0)
    
    # Distance is approximate due to circular arc geometry
    assert section.track_length_m == pytest.approx(500.0, abs=10.0)
    assert section.distance[0] == pytest.approx(0.0, abs=1e-6)


def test_get_section_mid_to_end(valid_track_profile):
    """Test extracting section from middle to end."""
    section = valid_track_profile.get_section(500.0, 1000.0)
    
    # Distance is approximate due to circular arc geometry
    assert section.track_length_m == pytest.approx(500.0, abs=10.0)
    assert section.distance[0] == pytest.approx(0.0, abs=1e-6)


def test_get_section_invalid_range_reversed(valid_track_profile):
    """Test that start >= end raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        valid_track_profile.get_section(700.0, 300.0)
    
    assert "start_distance must be < end_distance" in str(exc_info.value)


def test_get_section_invalid_range_equal(valid_track_profile):
    """Test that start == end raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        valid_track_profile.get_section(500.0, 500.0)
    
    assert "start_distance must be < end_distance" in str(exc_info.value)


def test_get_section_empty_range(valid_track_profile):
    """Test that section with no points raises ValueError."""
    # Request section way beyond track length where no points exist
    with pytest.raises(ValueError) as exc_info:
        valid_track_profile.get_section(2000.0, 3000.0)
    
    assert "No data points found in distance range" in str(exc_info.value)


def test_get_section_preserves_track_id(valid_track_profile):
    """Test that section preserves parent track_id."""
    section = valid_track_profile.get_section(100.0, 200.0)
    
    assert section.track_id == valid_track_profile.track_id


def test_get_section_arrays_consistent_length(valid_track_profile):
    """Test that section maintains array length consistency."""
    section = valid_track_profile.get_section(200.0, 800.0)
    
    # All arrays should have same length
    assert len(section.centerline) == len(section.curvature)
    assert len(section.curvature) == len(section.elevation)
    assert len(section.elevation) == len(section.distance)


# ============================================================================
# Equality and Hashing Tests
# ============================================================================

def test_equality_same_data(valid_track_data):
    """Test that two profiles with same data are equal."""
    profile1 = TrackProfile(**valid_track_data)
    profile2 = TrackProfile(**valid_track_data)
    
    assert profile1 == profile2


def test_equality_different_track_id(valid_track_data):
    """Test that profiles with different track_id are not equal."""
    profile1 = TrackProfile(**valid_track_data)
    
    data2 = valid_track_data.copy()
    data2["track_id"] = "different_track"
    profile2 = TrackProfile(**data2)
    
    assert profile1 != profile2


def test_equality_different_arrays(valid_track_data):
    """Test that profiles with different array data are not equal."""
    profile1 = TrackProfile(**valid_track_data)
    
    data2 = valid_track_data.copy()
    data2["curvature"] = data2["curvature"] * 2.0  # Different curvature
    profile2 = TrackProfile(**data2)
    
    assert profile1 != profile2


def test_equality_with_non_track_profile(valid_track_profile):
    """Test equality with non-TrackProfile object returns False."""
    assert valid_track_profile != "not a track profile"
    assert valid_track_profile != 42
    assert valid_track_profile != None


def test_hash_consistency(valid_track_data):
    """Test that hash is consistent for same data."""
    profile1 = TrackProfile(**valid_track_data)
    profile2 = TrackProfile(**valid_track_data)
    
    assert hash(profile1) == hash(profile2)


def test_hash_different_for_different_data(valid_track_data):
    """Test that hash differs for different data."""
    profile1 = TrackProfile(**valid_track_data)
    
    data2 = valid_track_data.copy()
    data2["track_id"] = "different"
    profile2 = TrackProfile(**data2)
    
    # Hashes should be different (with very high probability)
    assert hash(profile1) != hash(profile2)


# ============================================================================
# String Representation Tests
# ============================================================================

def test_str_representation(valid_track_profile):
    """Test __str__ returns human-readable format."""
    result = str(valid_track_profile)
    
    assert "TrackProfile" in result
    assert "test_track" in result
    assert "1000.0m" in result
    assert "points=100" in result


def test_str_representation_no_track_id(valid_track_data):
    """Test __str__ with None track_id."""
    valid_track_data["track_id"] = None
    profile = TrackProfile(**valid_track_data)
    
    result = str(profile)
    
    assert "unknown" in result


def test_repr_representation(valid_track_profile):
    """Test __repr__ returns detailed format."""
    result = repr(valid_track_profile)
    
    assert "TrackProfile" in result
    assert "track_id='test_track'" in result
    assert "centerline=array" in result
    assert "shape=" in result
    assert "track_length_m=1000.0" in result


# ============================================================================
# Edge Cases and Special Scenarios
# ============================================================================

def test_minimal_valid_track():
    """Test creating minimal valid track (2 points)."""
    profile = TrackProfile(
        track_id="minimal",
        centerline=np.array([[0.0, 0.0], [100.0, 0.0]]),
        curvature=np.array([0.0, 0.0]),
        elevation=np.array([0.0, 0.0]),
        distance=np.array([0.0, 100.0]),
        track_length_m=100.0
    )
    
    assert len(profile.distance) == 2
    assert profile.track_length_m == 100.0


def test_large_track():
    """Test creating track with large number of points."""
    n_points = 10000
    distance = np.linspace(0, 5000, n_points)
    centerline = np.column_stack([distance, np.zeros(n_points)])
    curvature = np.zeros(n_points)
    elevation = np.zeros(n_points)
    
    profile = TrackProfile(
        track_id="large_track",
        centerline=centerline,
        curvature=curvature,
        elevation=elevation,
        distance=distance,
        track_length_m=5000.0
    )
    
    assert len(profile.distance) == 10000


def test_immutability():
    """Test that TrackProfile is immutable (frozen dataclass)."""
    profile = TrackProfile(
        track_id="test",
        centerline=np.array([[0, 0], [1, 1]]),
        curvature=np.array([0.0, 0.0]),
        elevation=np.array([0.0, 0.0]),
        distance=np.array([0.0, 1.0]),
        track_length_m=1.0
    )
    
    # Attempting to modify should raise error
    with pytest.raises(Exception):  # FrozenInstanceError in Python 3.7+
        profile.track_id = "modified"
