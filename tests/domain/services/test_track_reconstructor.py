"""Unit tests for TrackReconstructor domain service.

Tests centerline computation algorithm with synthetic track data, edge cases,
and performance requirements.
"""

import numpy as np
import pytest
import time
from src.domain.services.track_reconstructor import TrackReconstructor
from src.domain.value_objects.telemetry_sample import TelemetrySample


class TestTrackReconstructor:
    """Test suite for track centerline computation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reconstructor = TrackReconstructor()
    
    def _create_sample(
        self,
        x: float,
        z: float,
        lap_distance: float,
        lap_number: int = 1
    ) -> TelemetrySample:
        """Helper to create TelemetrySample with minimal required fields."""
        return TelemetrySample(
            timestamp_ms=0,
            world_position_x=x,
            world_position_y=0.0,
            world_position_z=z,
            world_velocity_x=0.0,
            world_velocity_y=0.0,
            world_velocity_z=0.0,
            g_force_lateral=0.0,
            g_force_longitudinal=0.0,
            yaw=0.0,
            speed=100.0,
            throttle=1.0,
            steer=0.0,
            brake=0.0,
            gear=5,
            engine_rpm=8000,
            drs=0,
            lap_distance=lap_distance,
            lap_number=lap_number
        )
    
    def test_perfect_circle_track(self):
        """Test centerline computation on a perfect circular track.
        
        Validates:
        - Smooth, closed-loop centerline
        - Correct ordering by lap distance
        - Centerline forms approximate circle
        """
        # Generate circular track: radius 500m
        radius = 500.0
        track_length = 2 * np.pi * radius  # ~3141 meters
        num_samples = 1000
        
        samples = []
        for i in range(num_samples):
            angle = (i / num_samples) * 2 * np.pi
            x = radius * np.cos(angle)
            z = radius * np.sin(angle)
            lap_distance = (i / num_samples) * track_length
            samples.append(self._create_sample(x, z, lap_distance))
        
        # Compute centerline
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # Validate results
        assert centerline.shape[0] > 0, "Centerline should have points"
        assert centerline.shape[1] == 2, "Centerline should be Nx2"
        assert len(distances) == len(centerline), "Distances match centerline length"
        
        # Check centerline forms approximate circle
        # Compute radius from centerline points
        centerline_radii = np.sqrt(centerline[:, 0]**2 + centerline[:, 1]**2)
        mean_radius = np.mean(centerline_radii)
        std_radius = np.std(centerline_radii)
        
        # Mean radius should be close to 500m (within 5%)
        assert abs(mean_radius - radius) / radius < 0.05, \
            f"Mean radius {mean_radius} deviates >5% from expected {radius}"
        
        # Radius variation should be small (smooth circle)
        assert std_radius / radius < 0.05, \
            f"Radius std {std_radius} too high for smooth circle"
        
        # Distance should be monotonically increasing
        assert np.all(np.diff(distances) >= 0), "Distances must be monotonic"
    
    def test_s_curve_track(self):
        """Test centerline computation on S-curve track.
        
        Validates:
        - Correct ordering through curves
        - No self-intersection
        - Smooth transitions
        """
        # Generate S-curve: two opposing curves
        track_length = 2000.0
        num_samples = 1000
        
        samples = []
        for i in range(num_samples):
            progress = i / num_samples
            lap_distance = progress * track_length
            
            # S-curve: sin wave along z-axis, linear along x-axis
            x = progress * 1000.0  # Linear progression
            z = 200.0 * np.sin(progress * 4 * np.pi)  # Two complete sine waves
            
            samples.append(self._create_sample(x, z, lap_distance))
        
        # Compute centerline
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # Validate results
        assert centerline.shape[0] > 0, "Centerline should have points"
        assert len(distances) == len(centerline), "Distances match centerline length"
        
        # Check x-coordinates are monotonically increasing (no backtracking)
        x_coords = centerline[:, 0]
        assert np.all(np.diff(x_coords) > 0), "X-coords should increase monotonically"
        
        # Distance should be monotonically increasing
        assert np.all(np.diff(distances) >= 0), "Distances must be monotonic"
        
        # Check smoothness: no sudden jumps
        segment_lengths = np.diff(centerline, axis=0)
        segment_distances = np.sqrt(np.sum(segment_lengths**2, axis=1))
        max_segment = np.max(segment_distances)
        mean_segment = np.mean(segment_distances)
        
        # No segment should be more than 5x the mean (indicates jump)
        assert max_segment < 5 * mean_segment, \
            f"Max segment {max_segment} indicates discontinuity"
    
    def test_real_track_simulation_monza_straight(self):
        """Test with Monza-like data: long straight then chicane.
        
        Validates handling of:
        - High-speed straight sections
        - Sharp direction changes
        - Realistic track geometry
        """
        track_length = 5793.0  # Monza approximate length
        num_samples = 2000
        
        samples = []
        for i in range(num_samples):
            progress = i / num_samples
            lap_distance = progress * track_length
            
            # Simulate: long straight (70%) then tight chicane (30%)
            if progress < 0.7:
                # Straight: minimal lateral movement
                x = progress * 4000.0
                z = 5.0 * np.sin(progress * 10)  # Slight wobble
            else:
                # Chicane: sharp left-right-left
                chicane_progress = (progress - 0.7) / 0.3
                x = 2800.0 + chicane_progress * 500.0
                z = 100.0 * np.sin(chicane_progress * 6 * np.pi)
            
            samples.append(self._create_sample(x, z, lap_distance))
        
        # Compute centerline
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # Validate results
        assert centerline.shape[0] > 0, "Centerline should have points"
        assert len(distances) == len(centerline), "Distances match centerline length"
        
        # Final distance should be within a reasonable range.
        # Note: The Euclidean arc length along the smoothed/binned centerline can
        # differ from the nominal track_length derived from lap progression.
        final_distance = distances[-1]
        assert final_distance > 1000.0, "Final distance should be > 1km"
        assert final_distance < 10000.0, "Final distance should be < 10km"
    
    def test_insufficient_samples_raises_error(self):
        """Test that insufficient samples raise ValueError.
        
        Edge case: Less than MIN_SAMPLES_REQUIRED (100) samples.
        """
        # Create only 50 samples (below threshold)
        samples = []
        for i in range(50):
            progress = i / 50
            samples.append(self._create_sample(
                x=progress * 1000.0,
                z=0.0,
                lap_distance=progress * 1000.0
            ))
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Insufficient samples"):
            self.reconstructor.compute_centerline(samples, 1000.0)
    
    def test_outliers_handled_by_median(self):
        """Test that outliers (pit lane, off-track) are handled robustly.
        
        Edge case: 10% of samples are outliers far from racing line.
        """
        track_length = 5000.0
        num_samples = 1000
        num_outliers = 100  # 10% outliers
        
        samples = []
        outlier_indices = set(np.random.choice(num_samples, num_outliers, replace=False))
        
        for i in range(num_samples):
            progress = i / num_samples
            lap_distance = progress * track_length
            
            if i in outlier_indices:
                # Outlier: far off track (pit lane, excursion)
                x = progress * 4000.0 + np.random.uniform(-500, 500)
                z = np.random.uniform(-500, 500)
            else:
                # Normal racing line: straight track
                x = progress * 4000.0
                z = 0.0
            
            samples.append(self._create_sample(x, z, lap_distance))
        
        # Compute centerline (should handle outliers)
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # Validate results
        assert centerline.shape[0] > 0, "Centerline should have points"
        
        # Z-coordinates should be close to 0 (median filters outliers)
        z_coords = centerline[:, 1]
        mean_z = np.mean(np.abs(z_coords))
        
        # Mean absolute z should be small (outliers filtered)
        assert mean_z < 50.0, \
            f"Mean |z| = {mean_z} indicates outliers not filtered properly"
    
    def test_performance_10k_samples(self):
        """Test performance with 10,000 samples.
        
        Acceptance: Runtime < 1 second for 10K samples.
        """
        track_length = 5000.0
        num_samples = 10000
        
        # Generate large dataset
        samples = []
        for i in range(num_samples):
            progress = i / num_samples
            angle = progress * 2 * np.pi
            x = 500.0 * np.cos(angle)
            z = 500.0 * np.sin(angle)
            lap_distance = progress * track_length
            samples.append(self._create_sample(x, z, lap_distance))
        
        # Measure runtime
        start_time = time.time()
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        elapsed_time = time.time() - start_time
        
        # Validate results
        assert centerline.shape[0] > 0, "Centerline should have points"
        assert len(distances) == len(centerline), "Distances match centerline length"
        
        # Performance requirement: < 1 second
        assert elapsed_time < 1.0, \
            f"Runtime {elapsed_time:.3f}s exceeds 1 second for 10K samples"
    
    def test_multiple_laps_data(self):
        """Test handling of multiple laps (>3 laps) of data.
        
        Validates:
        - Correct handling of lap distance wrapping
        - Consistent centerline from multiple laps
        """
        track_length = 5000.0
        num_laps = 4
        samples_per_lap = 300
        
        samples = []
        for lap in range(1, num_laps + 1):
            for i in range(samples_per_lap):
                progress = i / samples_per_lap
                angle = progress * 2 * np.pi
                
                # Add slight variation per lap (different racing lines)
                noise_x = np.random.uniform(-5, 5)
                noise_z = np.random.uniform(-5, 5)
                
                x = 500.0 * np.cos(angle) + noise_x
                z = 500.0 * np.sin(angle) + noise_z
                lap_distance = progress * track_length
                
                samples.append(self._create_sample(x, z, lap_distance, lap))
        
        # Compute centerline from all laps
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # Validate results
        assert centerline.shape[0] > 0, "Centerline should have points"
        assert len(distances) == len(centerline), "Distances match centerline length"
        
        # Centerline should form approximate circle (median filters lap variation)
        centerline_radii = np.sqrt(centerline[:, 0]**2 + centerline[:, 1]**2)
        mean_radius = np.mean(centerline_radii)
        std_radius = np.std(centerline_radii)
        
        # Radius should be close to 500m (within 5%)
        assert abs(mean_radius - 500.0) / 500.0 < 0.05, \
            f"Mean radius {mean_radius} deviates >5% from expected 500m"
        
        # Variation should be small (multiple laps averaged well)
        assert std_radius / mean_radius < 0.05, \
            f"Radius variation {std_radius / mean_radius:.3%} too high"
    
    def test_centerline_deviation_from_ground_truth(self):
        """Test deviation from known ground truth centerline.
        
        Acceptance: <5% deviation from ground truth.
        """
        # Ground truth: perfect circle, radius 500m
        radius = 500.0
        track_length = 2 * np.pi * radius
        
        # Generate samples with noise (simulating real telemetry)
        num_samples = 1000
        samples = []
        
        for i in range(num_samples):
            angle = (i / num_samples) * 2 * np.pi
            
            # Ground truth position
            true_x = radius * np.cos(angle)
            true_z = radius * np.sin(angle)
            
            # Add realistic noise (±10m racing line variation)
            noise_x = np.random.uniform(-10, 10)
            noise_z = np.random.uniform(-10, 10)
            
            x = true_x + noise_x
            z = true_z + noise_z
            lap_distance = (i / num_samples) * track_length
            
            samples.append(self._create_sample(x, z, lap_distance))
        
        # Compute centerline
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # Compute ground truth centerline at same angular positions
        num_centerline_points = len(centerline)
        ground_truth = np.zeros((num_centerline_points, 2))
        
        for i in range(num_centerline_points):
            angle = (i / num_centerline_points) * 2 * np.pi
            ground_truth[i, 0] = radius * np.cos(angle)
            ground_truth[i, 1] = radius * np.sin(angle)
        
        # Compute deviation: point-wise Euclidean distance
        deviations = np.sqrt(np.sum((centerline - ground_truth)**2, axis=1))
        mean_deviation = np.mean(deviations)
        max_deviation = np.max(deviations)
        
        # Mean deviation should be <5% of radius
        deviation_percent = mean_deviation / radius
        assert deviation_percent < 0.05, \
            f"Mean deviation {mean_deviation:.2f}m ({deviation_percent:.2%}) exceeds 5% of radius"
        
        # Max deviation should be reasonable (<10% of radius)
        max_deviation_percent = max_deviation / radius
        assert max_deviation_percent < 0.10, \
            f"Max deviation {max_deviation:.2f}m ({max_deviation_percent:.2%}) exceeds 10% of radius"
    
    def test_invalid_track_length_raises_error(self):
        """Test that invalid track length raises ValueError."""
        # Create valid samples
        samples = []
        for i in range(200):
            progress = i / 200
            samples.append(self._create_sample(
                x=progress * 1000.0,
                z=0.0,
                lap_distance=progress * 1000.0
            ))
        
        # Invalid track length: zero
        with pytest.raises(ValueError, match="track_length_m must be positive"):
            self.reconstructor.compute_centerline(samples, 0.0)
        
        # Invalid track length: negative
        with pytest.raises(ValueError, match="track_length_m must be positive"):
            self.reconstructor.compute_centerline(samples, -1000.0)
    
    def test_centerline_distances_are_cumulative(self):
        """Test that returned distances are cumulative and start at 0."""
        # Simple straight track
        track_length = 1000.0
        num_samples = 200
        
        samples = []
        for i in range(num_samples):
            progress = i / num_samples
            samples.append(self._create_sample(
                x=progress * 1000.0,
                z=0.0,
                lap_distance=progress * track_length
            ))
        
        # Compute centerline
        centerline, distances = self.reconstructor.compute_centerline(
            samples, track_length
        )
        
        # First distance should be 0
        assert distances[0] == 0.0, "First distance should be 0"
        
        # Distances should be monotonically increasing
        assert np.all(np.diff(distances) >= 0), "Distances must be monotonic"
        
        # Last distance should be > 0
        assert distances[-1] > 0, "Final distance should be positive"
