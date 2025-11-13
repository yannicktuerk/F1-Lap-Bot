"""Domain service for reconstructing track geometry from telemetry data.

This module implements the TrackReconstructor domain service which computes
track centerlines from F1 25 telemetry samples using spatial binning and
smoothing algorithms.
"""

import numpy as np
from scipy.signal import savgol_filter
from typing import List, Tuple
from ..value_objects.telemetry_sample import TelemetrySample


class TrackReconstructor:
    """Domain service for track geometry reconstruction from telemetry.
    
    This service implements algorithms to reconstruct track centerlines from
    raw telemetry position samples. The centerline is computed using spatial
    binning along lap distance to create an ordered, smooth representation
    of the track geometry.
    
    The algorithm is designed to be robust to:
    - Outliers (pit lane entries, off-track excursions)
    - Multiple laps of data with varying racing lines
    - Track crossings (e.g., Suzuka figure-8)
    - Gaps in telemetry coverage
    """
    
    # Algorithm configuration constants
    NUM_BINS = 1000  # Number of spatial bins along track
    MIN_SAMPLES_REQUIRED = 100  # Minimum samples for reliable reconstruction
    MIN_WINDOW_SIZE = 5  # Minimum Savitzky-Golay window size
    SAVGOL_POLY_ORDER = 3  # Polynomial order for smoothing
    
    def compute_centerline(
        self,
        samples: List[TelemetrySample],
        track_length_m: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute track centerline from telemetry samples.
        
        Reconstructs the track centerline by:
        1. Extracting world positions (x, z) and lap distances
        2. Normalizing lap progress to [0, 1]
        3. Binning samples by normalized lap distance
        4. Computing median centroid per bin (robust to outliers)
        5. Smoothing centroids with Savitzky-Golay filter
        6. Computing cumulative distance along centerline
        
        Args:
            samples: List of TelemetrySample points with position data.
            track_length_m: Track length in meters for normalization.
            
        Returns:
            Tuple of (centerline, distances) where:
            - centerline: Nx2 numpy array of (x, z) coordinates in meters
            - distances: N-element array of cumulative distance along centerline
            
        Raises:
            ValueError: If samples < MIN_SAMPLES_REQUIRED (100).
            ValueError: If track_length_m <= 0.
        """
        # Validate inputs
        if len(samples) < self.MIN_SAMPLES_REQUIRED:
            raise ValueError(
                f"Insufficient samples for centerline computation: "
                f"got {len(samples)}, need at least {self.MIN_SAMPLES_REQUIRED}"
            )
        
        if track_length_m <= 0:
            raise ValueError(
                f"track_length_m must be positive, got {track_length_m}"
            )
        
        # Extract position and lap distance data
        positions_x = np.array([s.world_position_x for s in samples])
        positions_z = np.array([s.world_position_z for s in samples])
        lap_distances = np.array([s.lap_distance for s in samples])
        
        # Normalize lap progress to [0, 1]
        normalized_progress = lap_distances / track_length_m
        
        # Create spatial bins along normalized lap progress
        bin_edges = np.linspace(0, 1, self.NUM_BINS + 1)
        bin_indices = np.digitize(normalized_progress, bin_edges) - 1
        
        # Clamp bin indices to valid range [0, NUM_BINS-1]
        bin_indices = np.clip(bin_indices, 0, self.NUM_BINS - 1)
        
        # Compute median centroid for each bin (robust to outliers)
        centroids = []
        bin_centers = []
        
        for bin_idx in range(self.NUM_BINS):
            # Find all samples in this bin
            mask = bin_indices == bin_idx
            
            if np.sum(mask) == 0:
                # No samples in this bin, skip it
                continue
            
            # Compute median position (more robust than mean)
            median_x = np.median(positions_x[mask])
            median_z = np.median(positions_z[mask])
            
            centroids.append([median_x, median_z])
            bin_centers.append((bin_edges[bin_idx] + bin_edges[bin_idx + 1]) / 2)
        
        # Convert to numpy arrays
        centroids = np.array(centroids)
        bin_centers = np.array(bin_centers)
        
        # Sort centroids by lap progression order
        sort_indices = np.argsort(bin_centers)
        centroids = centroids[sort_indices]
        
        # Smooth centerline with Savitzky-Golay filter
        # Window size must be odd and at least MIN_WINDOW_SIZE
        window_length = max(
            self.MIN_WINDOW_SIZE,
            min(51, len(centroids) // 10 * 2 + 1)
        )
        
        # Ensure window_length is odd
        if window_length % 2 == 0:
            window_length += 1
        
        # Ensure window_length doesn't exceed number of centroids
        window_length = min(window_length, len(centroids))
        
        # Ensure window_length > polynomial order
        if window_length <= self.SAVGOL_POLY_ORDER:
            # Not enough points for smoothing, return unsmoothed
            smoothed_centerline = centroids
        else:
            # Apply Savitzky-Golay filter to x and z coordinates separately
            smoothed_x = savgol_filter(
                centroids[:, 0],
                window_length,
                self.SAVGOL_POLY_ORDER
            )
            smoothed_z = savgol_filter(
                centroids[:, 1],
                window_length,
                self.SAVGOL_POLY_ORDER
            )
            smoothed_centerline = np.column_stack([smoothed_x, smoothed_z])
        
        # Compute cumulative Euclidean distance along centerline
        distances = self._compute_cumulative_distance(smoothed_centerline)
        
        return smoothed_centerline, distances
    
    def _compute_cumulative_distance(self, centerline: np.ndarray) -> np.ndarray:
        """Compute cumulative Euclidean distance along centerline.
        
        Args:
            centerline: Nx2 array of (x, z) coordinates.
            
        Returns:
            N-element array where distances[i] is the cumulative distance
            from the start to point i along the centerline.
        """
        # Compute pairwise distances between consecutive points
        deltas = np.diff(centerline, axis=0)
        segment_lengths = np.sqrt(np.sum(deltas**2, axis=1))
        
        # Cumulative sum with initial distance of 0
        cumulative_distances = np.concatenate([[0], np.cumsum(segment_lengths)])
        
        return cumulative_distances
