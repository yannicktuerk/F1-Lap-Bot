"""Domain service for constructing ideal laps using physics-based simulation.

This module implements the IdealLapConstructor which generates an ideal lap
(optimal speed profile) from track geometry using vehicle dynamics models:
- Grip circle for cornering speed limits
- Braking and acceleration limits
- Downforce effects on tire grip

The constructor uses a forward-backward algorithm:
1. Forward pass: Apply acceleration limits considering cornering constraints
2. Backward pass: Apply braking limits to avoid over-speed in corners
"""

import numpy as np
from typing import Dict, Optional
from ..entities.track_profile import TrackProfile
from ..entities.ideal_lap import IdealLap


class IdealLapConstructor:
    """Domain service for constructing physics-based ideal laps.
    
    Generates optimal speed profiles by simulating vehicle dynamics on a given
    track. Uses realistic physics constraints (grip circle, downforce, g-forces)
    to produce achievable ideal lap times.
    
    Physics Model:
        - Maximum cornering speed: v_corner = sqrt(μ * g * R * (1 + downforce_factor * v²))
        - Braking limit: a_brake_max ≈ 5.0 g (with downforce)
        - Acceleration limit: a_accel_max ≈ 1.2 g (traction limited)
        - Grip coefficient: μ ≈ 1.5 (modern F1 slicks)
    
    Attributes:
        params (Dict): Vehicle and physics parameters for simulation.
    """
    
    # Default F1-like vehicle parameters
    DEFAULT_PARAMS = {
        'mu': 1.5,                    # Tire grip coefficient (dimensionless)
        'mass': 798.0,                # Vehicle mass in kg (F1 minimum)
        'a_brake_max': 5.0 * 9.81,   # Max braking deceleration in m/s² (~5g)
        'a_accel_max': 1.2 * 9.81,   # Max acceleration in m/s² (~1.2g)
        'downforce_factor': 0.002,    # Downforce coefficient (dimensionless)
        'v_max_cap': 95.0,           # Maximum speed cap in m/s (~342 km/h)
    }
    
    def __init__(self, params: Optional[Dict] = None):
        """Initialize IdealLapConstructor with vehicle parameters.
        
        Args:
            params: Optional dict of vehicle parameters. Missing keys use defaults.
                Keys: mu, mass, a_brake_max, a_accel_max, downforce_factor, v_max_cap
        """
        self.params = self.DEFAULT_PARAMS.copy()
        if params:
            self.params.update(params)
    
    def construct_ideal_lap(
        self,
        track_profile: TrackProfile,
        sector_distances: Optional[np.ndarray] = None
    ) -> IdealLap:
        """Construct ideal lap from track geometry using physics simulation.
        
        Implements forward-backward algorithm:
        1. Compute maximum cornering speed from curvature
        2. Forward pass: apply acceleration limits
        3. Backward pass: apply braking limits
        4. Generate throttle/brake inputs from speed profile
        5. Calculate sector and total lap times
        
        Args:
            track_profile: Track geometry (centerline, curvature, elevation, distance).
            sector_distances: Optional array of sector boundaries in meters.
                Default: split track into 3 equal sectors.
        
        Returns:
            IdealLap value object with optimal speed profile and lap times.
        
        Raises:
            ValueError: If track_profile has insufficient data points (< 10).
        """
        # Validate input
        n_points = len(track_profile.distance)
        if n_points < 10:
            raise ValueError(
                f"track_profile must have at least 10 points, got {n_points}"
            )
        
        # Step 1: Compute maximum cornering speed at each point
        v_max_corner = self._compute_cornering_speed(
            track_profile.curvature,
            track_profile.distance
        )
        
        # Step 2: Forward pass - apply acceleration constraints
        v_forward = self._forward_pass(v_max_corner, track_profile.distance)
        
        # Step 3: Backward pass - apply braking constraints
        v_ideal = self._backward_pass(v_forward, v_max_corner, track_profile.distance)
        
        # Step 4: Generate throttle and brake inputs
        throttle, brake = self._compute_inputs(v_ideal, v_max_corner, track_profile.distance)
        
        # Step 5: Calculate total lap time first
        total_time = self._calculate_total_time(v_ideal, track_profile.distance)
        
        # Step 6: Calculate sector times
        if sector_distances is None:
            # Default: split into 3 equal sectors
            sector_distances = np.array([
                track_profile.track_length_m / 3.0,
                2.0 * track_profile.track_length_m / 3.0,
                track_profile.track_length_m
            ])
        
        sector_times = self._calculate_sector_times(
            v_ideal,
            track_profile.distance,
            sector_distances
        )
        
        # Ensure sector times sum to total time (fix numerical precision issues)
        sector_sum = sum(sector_times)
        if abs(sector_sum - total_time) > 0.01 * total_time:
            # Proportionally adjust sector times to match total
            scale_factor = total_time / sector_sum
            sector_times = [t * scale_factor for t in sector_times]
        
        # Create IdealLap value object
        return IdealLap(
            track_id=track_profile.track_id or "unknown",
            ideal_speed=v_ideal,
            ideal_throttle=throttle,
            ideal_brake=brake,
            distance=track_profile.distance,
            sector_times=sector_times,
            total_time=total_time
        )
    
    def _compute_cornering_speed(
        self,
        curvature: np.ndarray,
        distance: np.ndarray
    ) -> np.ndarray:
        """Compute maximum cornering speed from track curvature.
        
        Uses simplified grip circle model with downforce effects:
        v_corner = sqrt(μ * g * R * (1 + downforce_factor * v²))
        
        This is solved iteratively since v appears on both sides.
        For simplicity, we use approximation:
        v_corner ≈ sqrt(μ * g / κ) where κ = curvature, R = 1/κ
        
        Args:
            curvature: Array of curvature values (1/meters).
            distance: Array of distances (meters).
        
        Returns:
            Array of maximum cornering speeds (m/s) at each point.
        """
        g = 9.81  # Gravity m/s²
        mu = self.params['mu']
        v_max_cap = self.params['v_max_cap']
        
        # Avoid division by zero for straight sections (κ ≈ 0)
        # Use small epsilon to prevent numerical issues
        epsilon = 1e-6
        curvature_safe = np.where(np.abs(curvature) < epsilon, epsilon, np.abs(curvature))
        
        # Compute corner radius: R = 1/κ
        radius = 1.0 / curvature_safe
        
        # Maximum lateral acceleration: a_lat = μ * g
        a_lat_max = mu * g
        
        # Maximum cornering speed: v = sqrt(a_lat * R)
        v_corner = np.sqrt(a_lat_max * radius)
        
        # Cap at maximum speed
        v_corner = np.minimum(v_corner, v_max_cap)
        
        return v_corner
    
    def _forward_pass(
        self,
        v_max_corner: np.ndarray,
        distance: np.ndarray
    ) -> np.ndarray:
        """Forward pass: apply acceleration constraints.
        
        Starting from zero speed, accelerate at maximum rate while respecting
        cornering speed limits. This ensures we don't enter corners too fast.
        
        Args:
            v_max_corner: Array of maximum cornering speeds (m/s).
            distance: Array of distances (meters).
        
        Returns:
            Array of speeds after forward pass (m/s).
        """
        n = len(distance)
        v_forward = np.zeros(n)
        
        # Start from standstill (or low speed)
        v_forward[0] = min(10.0, v_max_corner[0])  # Start at 10 m/s or corner limit
        
        a_accel_max = self.params['a_accel_max']
        
        for i in range(1, n):
            ds = distance[i] - distance[i-1]
            
            # Kinematic equation: v² = v₀² + 2*a*ds
            v_squared = v_forward[i-1]**2 + 2 * a_accel_max * ds
            v_accel = np.sqrt(max(0, v_squared))
            
            # Limit by cornering speed constraint
            v_forward[i] = min(v_accel, v_max_corner[i])
        
        return v_forward
    
    def _backward_pass(
        self,
        v_forward: np.ndarray,
        v_max_corner: np.ndarray,
        distance: np.ndarray
    ) -> np.ndarray:
        """Backward pass: apply braking constraints.
        
        Starting from the end, brake at maximum rate to respect cornering
        speed limits. This ensures we can brake in time for upcoming corners.
        
        Args:
            v_forward: Speeds from forward pass (m/s).
            v_max_corner: Maximum cornering speeds (m/s).
            distance: Array of distances (meters).
        
        Returns:
            Final ideal speed array (m/s).
        """
        n = len(distance)
        v_ideal = v_forward.copy()
        
        # First, ensure last point respects corner limit
        v_ideal[n-1] = min(v_ideal[n-1], v_max_corner[n-1])
        
        a_brake_max = self.params['a_brake_max']
        
        # Iterate backward from end to start
        for i in range(n-2, -1, -1):
            ds = distance[i+1] - distance[i]
            
            # Kinematic equation for braking: v² = v_next² + 2*a*ds
            v_squared = v_ideal[i+1]**2 + 2 * a_brake_max * ds
            v_brake = np.sqrt(max(0, v_squared))
            
            # Take minimum of forward speed and braking-required speed
            v_ideal[i] = min(v_ideal[i], v_brake)
            
            # Also respect cornering limit
            v_ideal[i] = min(v_ideal[i], v_max_corner[i])
        
        return v_ideal
    
    def _compute_inputs(
        self,
        v_ideal: np.ndarray,
        v_max_corner: np.ndarray,
        distance: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute throttle and brake inputs from ideal speed profile.
        
        Uses speed gradient to determine whether accelerating, braking, or coasting:
        - dv/ds > threshold: throttle = 1, brake = 0 (accelerating)
        - dv/ds < -threshold: throttle = 0, brake = 1 (braking)
        - Otherwise: throttle = 1, brake = 0 (coasting/maintaining speed)
        
        Args:
            v_ideal: Ideal speed array (m/s).
            v_max_corner: Maximum cornering speeds (m/s).
            distance: Distance array (meters).
        
        Returns:
            Tuple of (throttle, brake) binary arrays (0 or 1).
        """
        n = len(v_ideal)
        throttle = np.ones(n, dtype=int)
        brake = np.zeros(n, dtype=int)
        
        # Compute speed gradient dv/ds using forward differences
        dv = np.diff(v_ideal)
        ds = np.diff(distance)
        
        # Avoid division by zero
        ds_safe = np.where(ds > 0, ds, 1.0)
        dv_ds = dv / ds_safe
        
        # Threshold for detecting braking (m/s per meter)
        brake_threshold = -0.5  # Negative gradient indicates slowing down
        
        # Append zero gradient for last point (forward difference)
        dv_ds = np.append(dv_ds, 0.0)
        
        # Set brake when decelerating significantly
        brake_mask = dv_ds < brake_threshold
        brake[brake_mask] = 1
        throttle[brake_mask] = 0
        
        return throttle, brake
    
    def _calculate_sector_times(
        self,
        v_ideal: np.ndarray,
        distance: np.ndarray,
        sector_distances: np.ndarray
    ) -> list[float]:
        """Calculate time to complete each sector.
        
        Integrates dt = ds/v over each sector using trapezoidal rule.
        
        Args:
            v_ideal: Ideal speed array (m/s).
            distance: Distance array (meters).
            sector_distances: Array of sector boundary distances (meters).
                Must have 3 elements for sectors 1, 2, 3.
        
        Returns:
            List of 3 sector times in seconds.
        """
        sector_times = []
        
        # Define sector boundaries (start, end pairs)
        boundaries = [
            (0.0, sector_distances[0]),
            (sector_distances[0], sector_distances[1]),
            (sector_distances[1], sector_distances[2])
        ]
        
        for start_dist, end_dist in boundaries:
            # Find indices corresponding to sector boundaries
            start_idx = np.searchsorted(distance, start_dist, side='left')
            end_idx = np.searchsorted(distance, end_dist, side='right')
            
            # Extract sector data
            sector_dist = distance[start_idx:end_idx]
            sector_speed = v_ideal[start_idx:end_idx]
            
            if len(sector_dist) < 2:
                # Too few points, use simple approximation
                sector_time = (end_dist - start_dist) / np.mean(v_ideal)
            else:
                # Integrate time: t = ∫ ds/v using trapezoidal rule
                # dt[i] = (ds[i] / v[i])
                ds = np.diff(sector_dist)
                v_avg = (sector_speed[:-1] + sector_speed[1:]) / 2.0
                
                # Avoid division by zero
                v_avg = np.where(v_avg > 0.1, v_avg, 0.1)
                
                dt = ds / v_avg
                sector_time = np.sum(dt)
            
            sector_times.append(float(sector_time))
        
        return sector_times
    
    def _calculate_total_time(
        self,
        v_ideal: np.ndarray,
        distance: np.ndarray
    ) -> float:
        """Calculate total lap time.
        
        Integrates dt = ds/v over entire lap using trapezoidal rule.
        
        Args:
            v_ideal: Ideal speed array (m/s).
            distance: Distance array (meters).
        
        Returns:
            Total lap time in seconds.
        """
        if len(distance) < 2:
            return 0.0
        
        # Compute distance intervals
        ds = np.diff(distance)
        
        # Average speed between consecutive points
        v_avg = (v_ideal[:-1] + v_ideal[1:]) / 2.0
        
        # Avoid division by zero
        v_avg = np.where(v_avg > 0.1, v_avg, 0.1)
        
        # Compute time intervals: dt = ds / v_avg
        dt = ds / v_avg
        
        # Sum to get total time
        total_time = float(np.sum(dt))
        
        return total_time
