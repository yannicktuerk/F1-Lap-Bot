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


class TestTrackReconstructorCurvature:
    """Test suite for curvature computation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reconstructor = TrackReconstructor()
    
    def test_straight_line_zero_curvature(self):
        """Test that a straight line has curvature ≈ 0."""
        # Create straight line: 1000m long
        num_points = 200
        x = np.linspace(0, 1000, num_points)
        z = np.zeros(num_points)
        centerline = np.column_stack([x, z])
        distances = x  # Distance equals x for straight line
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Validate results
        assert len(curvature) == num_points, "Curvature length matches centerline"
        assert np.all(np.isfinite(curvature)), "No NaN or Inf in curvature"
        
        # Curvature should be very close to 0 (within numerical precision)
        max_curvature = np.max(np.abs(curvature))
        assert max_curvature < 1e-6, f"Straight line curvature {max_curvature} should be ≈ 0"
    
    def test_perfect_circle_constant_curvature(self):
        """Test that a perfect circle has constant curvature κ = 1/R."""
        # Create circular track: radius 500m
        radius = 500.0
        num_points = 1000
        angles = np.linspace(0, 2 * np.pi, num_points)
        
        x = radius * np.cos(angles)
        z = radius * np.sin(angles)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Validate results
        assert len(curvature) == num_points, "Curvature length matches centerline"
        assert np.all(np.isfinite(curvature)), "No NaN or Inf in curvature"
        
        # Expected curvature: κ = 1/R = 1/500 = 0.002
        expected_curvature = 1.0 / radius
        mean_curvature = np.mean(curvature)
        std_curvature = np.std(curvature)
        
        # Mean curvature should match expected (within 1%)
        assert abs(mean_curvature - expected_curvature) / expected_curvature < 0.01, \
            f"Mean curvature {mean_curvature} deviates >1% from expected {expected_curvature}"
        
        # Curvature should be relatively constant (low std deviation)
        assert std_curvature / mean_curvature < 0.05, \
            f"Curvature std {std_curvature} too high for constant circle"
    
    def test_hairpin_high_curvature(self):
        """Test that a tight hairpin has high curvature κ > 0.05."""
        # Create hairpin: 180° turn with small radius (15m)
        radius = 15.0
        num_points = 100
        angles = np.linspace(0, np.pi, num_points)  # Half circle
        
        x = radius * np.cos(angles)
        z = radius * np.sin(angles)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Validate results
        assert np.all(np.isfinite(curvature)), "No NaN or Inf in curvature"
        
        # Expected curvature: κ = 1/15 ≈ 0.0667
        expected_curvature = 1.0 / radius
        mean_curvature = np.mean(curvature)
        
        # Curvature should be high (>0.05 for hairpin)
        assert mean_curvature > 0.05, \
            f"Hairpin curvature {mean_curvature} should be > 0.05"
        
        # Should match expected curvature (within 5%)
        assert abs(mean_curvature - expected_curvature) / expected_curvature < 0.05, \
            f"Hairpin curvature {mean_curvature} deviates from expected {expected_curvature}"
    
    def test_fast_corner_low_curvature(self):
        """Test that a fast corner has low curvature κ < 0.01."""
        # Create fast corner: large radius (150m)
        radius = 150.0
        num_points = 100
        angles = np.linspace(0, np.pi / 3, num_points)  # 60° turn
        
        x = radius * np.cos(angles)
        z = radius * np.sin(angles)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Validate results
        assert np.all(np.isfinite(curvature)), "No NaN or Inf in curvature"
        
        # Expected curvature: κ = 1/150 ≈ 0.00667
        expected_curvature = 1.0 / radius
        mean_curvature = np.mean(curvature)
        
        # Curvature should be low (<0.01 for fast corner)
        assert mean_curvature < 0.01, \
            f"Fast corner curvature {mean_curvature} should be < 0.01"
        
        # Should match expected curvature (within 5%)
        assert abs(mean_curvature - expected_curvature) / expected_curvature < 0.05, \
            f"Fast corner curvature {mean_curvature} deviates from expected {expected_curvature}"
    
    def test_s_curve_alternating_curvature(self):
        """Test S-curve has alternating positive curvature."""
        # Create S-curve: two opposing curves
        num_points = 500
        progress = np.linspace(0, 1, num_points)
        
        x = progress * 1000.0  # Linear progression
        z = 200.0 * np.sin(progress * 4 * np.pi)  # Two complete sine waves
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Validate results
        assert np.all(np.isfinite(curvature)), "No NaN or Inf in curvature"
        assert len(curvature) == num_points, "Curvature length matches"
        
        # Curvature should all be non-negative (absolute value in formula)
        assert np.all(curvature >= 0), "Curvature should be non-negative"
        
        # Should have regions of high curvature (curves) and low curvature (transitions)
        max_curvature = np.max(curvature)
        min_curvature = np.min(curvature)
        
        assert max_curvature > 0.001, "S-curve should have curved sections"
        assert min_curvature < max_curvature / 2, "S-curve should have varying curvature"
    
    def test_curvature_smoothing_reduces_noise(self):
        """Test that smoothing reduces noise in curvature signal."""
        # Create circle with added noise
        radius = 500.0
        num_points = 500
        angles = np.linspace(0, 2 * np.pi, num_points)
        
        # Add noise to positions
        noise_magnitude = 5.0  # ±5m noise
        x = radius * np.cos(angles) + np.random.uniform(-noise_magnitude, noise_magnitude, num_points)
        z = radius * np.sin(angles) + np.random.uniform(-noise_magnitude, noise_magnitude, num_points)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature with and without smoothing
        curvature_unsmoothed = self.reconstructor.compute_curvature(
            centerline, distances, smooth=False
        )
        curvature_smoothed = self.reconstructor.compute_curvature(
            centerline, distances, smooth=True
        )
        
        # Validate results
        assert np.all(np.isfinite(curvature_unsmoothed)), "No NaN in unsmoothed"
        assert np.all(np.isfinite(curvature_smoothed)), "No NaN in smoothed"
        
        # Smoothed curvature should have lower std deviation (less noisy)
        std_unsmoothed = np.std(curvature_unsmoothed)
        std_smoothed = np.std(curvature_smoothed)
        
        assert std_smoothed < std_unsmoothed, \
            f"Smoothed std {std_smoothed} should be < unsmoothed std {std_unsmoothed}"
    
    def test_insufficient_points_raises_error(self):
        """Test that < 3 points raises ValueError."""
        # Create centerline with only 2 points
        centerline = np.array([[0, 0], [100, 0]])
        distances = np.array([0, 100])
        
        with pytest.raises(ValueError, match="Need at least 3 points"):
            self.reconstructor.compute_curvature(centerline, distances)
    
    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched centerline and distances raises ValueError."""
        centerline = np.array([[0, 0], [50, 0], [100, 0]])
        distances = np.array([0, 50])  # Wrong length
        
        with pytest.raises(ValueError, match="centerline length"):
            self.reconstructor.compute_curvature(centerline, distances)
    
    def test_no_numerical_instability(self):
        """Test that curvature computation has no NaN or Inf values."""
        # Create track with various features
        num_points = 1000
        progress = np.linspace(0, 1, num_points)
        
        # Mix of straight, curves, and sharp turns
        x = progress * 2000.0
        z = 100.0 * np.sin(progress * 8 * np.pi) + 50.0 * np.sin(progress * 20 * np.pi)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Validate: absolutely no NaN or Inf
        assert np.all(np.isfinite(curvature)), "Curvature must have no NaN or Inf"
        assert not np.any(np.isnan(curvature)), "No NaN values allowed"
        assert not np.any(np.isinf(curvature)), "No Inf values allowed"
    
    def test_monza_parabolica_high_speed_corner(self):
        """Test Monza Parabolica-like high-speed corner (κ ≈ 0.008)."""
        # Monza Parabolica: ~130m radius, high-speed corner
        radius = 130.0
        num_points = 150
        angles = np.linspace(0, np.pi / 2, num_points)  # 90° turn
        
        x = radius * np.cos(angles)
        z = radius * np.sin(angles)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Expected curvature: κ = 1/130 ≈ 0.0077
        expected_curvature = 1.0 / radius
        mean_curvature = np.mean(curvature)
        
        # Validate: high-speed corner (0.005 < κ < 0.01)
        assert 0.005 < mean_curvature < 0.01, \
            f"Monza Parabolica curvature {mean_curvature} outside expected range"
        
        # Should match expected (within 10%)
        assert abs(mean_curvature - expected_curvature) / expected_curvature < 0.10, \
            f"Parabolica curvature {mean_curvature} deviates from expected {expected_curvature}"
    
    def test_silverstone_copse_fast_corner(self):
        """Test Silverstone Copse-like fast corner (κ ≈ 0.01)."""
        # Silverstone Copse: ~100m radius, fast corner
        radius = 100.0
        num_points = 120
        angles = np.linspace(0, np.pi / 3, num_points)  # 60° turn
        
        x = radius * np.cos(angles)
        z = radius * np.sin(angles)
        centerline = np.column_stack([x, z])
        
        # Compute distances
        distances = self.reconstructor._compute_cumulative_distance(centerline)
        
        # Compute curvature
        curvature = self.reconstructor.compute_curvature(centerline, distances)
        
        # Expected curvature: κ = 1/100 = 0.01
        expected_curvature = 1.0 / radius
        mean_curvature = np.mean(curvature)
        
        # Validate: fast corner (κ ≈ 0.01)
        assert 0.008 < mean_curvature < 0.012, \
            f"Silverstone Copse curvature {mean_curvature} outside expected range"
        
        # Should match expected (within 10%)
        assert abs(mean_curvature - expected_curvature) / expected_curvature < 0.10, \
            f"Copse curvature {mean_curvature} deviates from expected {expected_curvature}"
