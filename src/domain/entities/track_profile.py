"""Value object representing complete track geometry profile.

This module defines the TrackProfile value object which encapsulates
all geometric properties of a track: centerline, curvature, elevation,
and distance progression. It is the unified output of track reconstruction
algorithms and provides interpolation methods for querying track properties
at arbitrary distances.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TrackProfile:
    """Immutable value object for track geometry profile.
    
    Encapsulates complete track geometry derived from telemetry data via
    track reconstruction algorithms (centerline, curvature, elevation).
    All arrays must have consistent length N representing discretized points
    along the track.
    
    This value object enables:
    - Track geometry storage and retrieval
    - Interpolation of track properties at arbitrary distances
    - Extraction of track sections for analysis
    - Comparison between different track reconstructions
    
    Attributes:
        track_id (Optional[str]): Track identifier (e.g., "monaco", "silverstone").
        centerline (np.ndarray): Nx2 array of (x, z) world coordinates in meters.
            Represents the racing line or track centerline in world space.
        curvature (np.ndarray): N-element array of curvature κ (kappa) in 1/meters.
            Measures how sharply the track curves at each point.
            Higher values = tighter corners.
        elevation (np.ndarray): N-element array of elevation h in meters.
            Height above ground level at each point along centerline.
        distance (np.ndarray): N-element array of cumulative distance in meters.
            Must be monotonically increasing. Represents arc length along centerline.
        track_length_m (float): Total track length in meters.
            Should match distance[-1] (last distance value).
    
    Invariants:
        - All arrays must have same length N
        - distance must be monotonically increasing
        - track_length_m must be positive
        - centerline must be Nx2 shape
    
    Example:
        >>> # Build from TrackReconstructor outputs
        >>> reconstructor = TrackReconstructor()
        >>> centerline, distances = reconstructor.compute_centerline(samples, track_length)
        >>> curvature = reconstructor.compute_curvature(centerline, distances)
        >>> elevation = reconstructor.compute_elevation(samples, track_length)
        >>> 
        >>> profile = TrackProfile(
        ...     track_id="monaco",
        ...     centerline=centerline,
        ...     curvature=curvature,
        ...     elevation=elevation,
        ...     distance=distances,
        ...     track_length_m=track_length
        ... )
        >>> 
        >>> # Query track properties at specific distance
        >>> curv_at_500m = profile.get_curvature_at(500.0)
        >>> elev_at_500m = profile.get_elevation_at(500.0)
        >>> slope_at_500m = profile.get_slope_at(500.0)
    """
    
    track_id: Optional[str]
    centerline: np.ndarray
    curvature: np.ndarray
    elevation: np.ndarray
    distance: np.ndarray
    track_length_m: float
    
    def __post_init__(self):
        """Validate track profile data after initialization.
        
        Enforces domain invariants:
        - Array length consistency (all arrays same length N)
        - Monotonic distance progression (strictly increasing)
        - Positive track length
        - Correct centerline shape (Nx2)
        
        Raises:
            ValueError: If any invariant is violated with descriptive error.
        """
        # Validate track_length_m
        if self.track_length_m <= 0:
            raise ValueError(
                f"track_length_m must be positive, got {self.track_length_m}"
            )
        
        # Validate centerline shape (must be Nx2)
        if len(self.centerline.shape) != 2 or self.centerline.shape[1] != 2:
            raise ValueError(
                f"centerline must be Nx2 array, got shape {self.centerline.shape}"
            )
        
        # Extract array lengths
        n_centerline = len(self.centerline)
        n_curvature = len(self.curvature)
        n_elevation = len(self.elevation)
        n_distance = len(self.distance)
        
        # Validate all arrays have same length
        if not (n_centerline == n_curvature == n_elevation == n_distance):
            raise ValueError(
                f"All arrays must have same length. Got centerline={n_centerline}, "
                f"curvature={n_curvature}, elevation={n_elevation}, distance={n_distance}"
            )
        
        # Validate distance is monotonically increasing
        # Use np.diff to compute differences between consecutive elements
        # All differences must be > 0 for strict monotonic increase
        if len(self.distance) > 1:
            distance_diffs = np.diff(self.distance)
            if not np.all(distance_diffs > 0):
                # Find first violation for error message
                first_violation_idx = np.where(distance_diffs <= 0)[0][0]
                raise ValueError(
                    f"distance array must be monotonically increasing. "
                    f"Violation at index {first_violation_idx}: "
                    f"distance[{first_violation_idx}]={self.distance[first_violation_idx]:.3f}, "
                    f"distance[{first_violation_idx + 1}]={self.distance[first_violation_idx + 1]:.3f}"
                )
    
    def get_curvature_at(self, distance: float) -> float:
        """Get curvature value at specified distance via linear interpolation.
        
        Interpolates curvature κ(s) at arbitrary distance s along track.
        Uses linear interpolation between discrete curvature measurements.
        
        Args:
            distance: Distance along track in meters (0 ≤ distance ≤ track_length_m).
        
        Returns:
            Interpolated curvature value in 1/meters.
            Extrapolates to nearest value if distance outside [0, track_length_m].
        
        Example:
            >>> profile.get_curvature_at(500.0)
            0.0234  # 1/meters (corresponds to ~43m corner radius)
        """
        return float(np.interp(distance, self.distance, self.curvature))
    
    def get_elevation_at(self, distance: float) -> float:
        """Get elevation value at specified distance via linear interpolation.
        
        Interpolates elevation h(s) at arbitrary distance s along track.
        Uses linear interpolation between discrete elevation measurements.
        
        Args:
            distance: Distance along track in meters (0 ≤ distance ≤ track_length_m).
        
        Returns:
            Interpolated elevation value in meters above ground level.
            Extrapolates to nearest value if distance outside [0, track_length_m].
        
        Example:
            >>> profile.get_elevation_at(500.0)
            42.7  # meters above ground level
        """
        return float(np.interp(distance, self.distance, self.elevation))
    
    def get_slope_at(self, distance: float) -> float:
        """Calculate track gradient (slope) at specified distance.
        
        Computes dh/ds (rate of elevation change with respect to distance)
        at given distance using central differences on interpolated elevation.
        
        Slope interpretation:
        - slope > 0: Uphill section
        - slope < 0: Downhill section
        - slope ≈ 0: Flat section
        - |slope| = 0.05: 5% gradient (5m elevation change per 100m distance)
        
        Args:
            distance: Distance along track in meters (0 ≤ distance ≤ track_length_m).
        
        Returns:
            Track slope (gradient) as dimensionless ratio dh/ds.
            Returns 0.0 if distance array has < 2 points.
        
        Example:
            >>> profile.get_slope_at(500.0)
            0.03  # 3% uphill gradient
        
        Note:
            Uses numerical differentiation with small delta (0.1% of track length).
            For boundary points, uses forward/backward differences.
        """
        if len(self.distance) < 2:
            return 0.0
        
        # Use small delta for numerical gradient calculation
        # Delta = 0.1% of track length or 1m, whichever is larger
        delta = max(self.track_length_m * 0.001, 1.0)
        
        # Get elevation at distance +/- delta using interpolation
        # This implements central difference: dh/ds ≈ (h(s+δ) - h(s-δ)) / (2δ)
        distance_before = distance - delta
        distance_after = distance + delta
        
        # Clamp to track boundaries for extrapolation
        distance_before = max(distance_before, self.distance[0])
        distance_after = min(distance_after, self.distance[-1])
        
        # Interpolate elevations
        elev_before = float(np.interp(distance_before, self.distance, self.elevation))
        elev_after = float(np.interp(distance_after, self.distance, self.elevation))
        
        # Compute slope via central difference
        actual_delta = distance_after - distance_before
        if actual_delta > 0:
            slope = (elev_after - elev_before) / actual_delta
        else:
            # At boundaries where delta collapses, return 0
            slope = 0.0
        
        return slope
    
    def get_section(self, start_distance: float, end_distance: float) -> "TrackProfile":
        """Extract track section between two distances as new TrackProfile.
        
        Creates a new TrackProfile containing only data points within the
        specified distance range. Useful for analyzing specific track sections
        (e.g., sector 1, or a particular corner sequence).
        
        Args:
            start_distance: Start of section in meters (inclusive).
            end_distance: End of section in meters (inclusive).
        
        Returns:
            New TrackProfile containing only data within [start_distance, end_distance].
            Distance array is adjusted to start from 0.
        
        Raises:
            ValueError: If start_distance >= end_distance.
            ValueError: If section is empty (no points in range).
        
        Example:
            >>> # Extract first sector (0-2000m)
            >>> sector1 = profile.get_section(0.0, 2000.0)
            >>> sector1.track_length_m
            2000.0
        """
        # Validate range
        if start_distance >= end_distance:
            raise ValueError(
                f"start_distance must be < end_distance, got "
                f"start={start_distance}, end={end_distance}"
            )
        
        # Find indices within distance range
        # Use boolean mask to select points where start <= distance <= end
        mask = (self.distance >= start_distance) & (self.distance <= end_distance)
        
        # Check if section is empty
        if not np.any(mask):
            raise ValueError(
                f"No data points found in distance range [{start_distance}, {end_distance}]. "
                f"Track distance range: [{self.distance[0]:.1f}, {self.distance[-1]:.1f}]"
            )
        
        # Extract arrays for section
        section_centerline = self.centerline[mask]
        section_curvature = self.curvature[mask]
        section_elevation = self.elevation[mask]
        section_distance = self.distance[mask]
        
        # Adjust distance to start from 0 (relative to section start)
        section_distance = section_distance - section_distance[0]
        
        # Calculate section length
        section_length = float(section_distance[-1])
        
        # Create new TrackProfile for section
        # Note: track_id is preserved from parent profile
        return TrackProfile(
            track_id=self.track_id,
            centerline=section_centerline,
            curvature=section_curvature,
            elevation=section_elevation,
            distance=section_distance,
            track_length_m=section_length
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on all field values.
        
        Two TrackProfile instances are equal if all their arrays and metadata match.
        Uses numpy array comparison for numeric arrays.
        
        Args:
            other: Object to compare with.
        
        Returns:
            True if all fields are equal, False otherwise.
        """
        if not isinstance(other, TrackProfile):
            return False
        
        return (
            self.track_id == other.track_id
            and np.array_equal(self.centerline, other.centerline)
            and np.array_equal(self.curvature, other.curvature)
            and np.array_equal(self.elevation, other.elevation)
            and np.array_equal(self.distance, other.distance)
            and self.track_length_m == other.track_length_m
        )
    
    def __hash__(self) -> int:
        """Generate hash for TrackProfile.
        
        Note: Hashing numpy arrays is non-trivial and potentially expensive.
        This implementation uses array bytes for hashing. If TrackProfile
        instances will be used as dict keys frequently, consider an alternative
        approach (e.g., hash based on track_id and length only).
        
        Returns:
            Hash value for this track profile.
        """
        return hash((
            self.track_id,
            self.centerline.tobytes(),
            self.curvature.tobytes(),
            self.elevation.tobytes(),
            self.distance.tobytes(),
            self.track_length_m
        ))
    
    def __str__(self) -> str:
        """Human-readable string representation.
        
        Returns:
            Compact string showing track_id and key dimensions.
        """
        track_name = self.track_id or "unknown"
        return (
            f"TrackProfile(track='{track_name}', "
            f"length={self.track_length_m:.1f}m, "
            f"points={len(self.distance)})"
        )
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging.
        
        Returns:
            String showing all field values (arrays abbreviated).
        """
        return (
            f"TrackProfile(track_id='{self.track_id}', "
            f"centerline=array(shape={self.centerline.shape}), "
            f"curvature=array(len={len(self.curvature)}), "
            f"elevation=array(len={len(self.elevation)}), "
            f"distance=array(len={len(self.distance)}), "
            f"track_length_m={self.track_length_m:.1f})"
        )
