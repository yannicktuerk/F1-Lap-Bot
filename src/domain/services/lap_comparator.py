"""Domain service for comparing actual laps against ideal laps.

This module implements LapComparator which analyzes the difference between
a driver's actual lap and the physics-based ideal lap. It identifies where
time is being lost and classifies the type of driving errors.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from ..entities.lap_trace import LapTrace
from ..entities.ideal_lap import IdealLap
from ..entities.track_profile import TrackProfile


class ErrorType(Enum):
    """Classification of driving errors causing time loss."""
    
    EARLY_BRAKING = "early_braking"
    LATE_BRAKING = "late_braking"
    SLOW_CORNER = "slow_corner"
    LATE_THROTTLE = "late_throttle"
    LINE_ERROR = "line_error"


@dataclass(frozen=True)
class ComparisonSegment:
    """Value object representing comparison result for a track segment.
    
    Encapsulates the analysis of one corner or section where time is lost
    compared to the ideal lap.
    
    Attributes:
        segment_id (int): Unique identifier for this segment (e.g., corner number).
        distance_start (float): Start distance in meters.
        distance_end (float): End distance in meters.
        time_loss (float): Total time lost in this segment (seconds).
        speed_delta_entry (float): Speed difference at entry (m/s), negative = slower.
        speed_delta_apex (float): Speed difference at apex (m/s), negative = slower.
        speed_delta_exit (float): Speed difference at exit (m/s), negative = slower.
        error_type (ErrorType): Classified error type.
        explanation (str): Human-readable explanation of the issue.
    """
    
    segment_id: int
    distance_start: float
    distance_end: float
    time_loss: float
    speed_delta_entry: float
    speed_delta_apex: float
    speed_delta_exit: float
    error_type: ErrorType
    explanation: str
    
    def __post_init__(self):
        """Validate ComparisonSegment fields."""
        if self.distance_end <= self.distance_start:
            raise ValueError(
                f"distance_end {self.distance_end} must be greater than "
                f"distance_start {self.distance_start}"
            )
        
        if not isinstance(self.error_type, ErrorType):
            raise ValueError(
                f"error_type must be ErrorType enum, got {type(self.error_type)}"
            )


class LapComparator:
    """Domain service for comparing actual laps to ideal laps.
    
    Analyzes telemetry from a driver's lap against the physics-based ideal lap
    to identify where time is being lost and why. Segments the lap into corners
    and straights, computes time loss per segment, and classifies driving errors.
    """
    
    def __init__(self, min_time_loss_threshold: float = 0.05):
        """Initialize LapComparator.
        
        Args:
            min_time_loss_threshold: Minimum time loss in seconds to report
                a segment (default: 0.05s = 50ms). Filters out insignificant losses.
        """
        self.min_time_loss_threshold = min_time_loss_threshold
    
    def compare_laps(
        self,
        actual_lap: LapTrace,
        ideal_lap: IdealLap,
        track_profile: TrackProfile,
        num_segments: int = 10
    ) -> List[ComparisonSegment]:
        """Compare actual lap against ideal lap and identify time loss segments.
        
        Args:
            actual_lap: Driver's actual lap with telemetry samples.
            ideal_lap: Physics-based ideal lap.
            track_profile: Track geometry for identifying corners/straights.
            num_segments: Number of segments to divide the lap into (default: 10).
        
        Returns:
            List of ComparisonSegment objects sorted by time_loss (descending).
            Only segments with time_loss > threshold are included.
        
        Raises:
            ValueError: If actual_lap has no samples or track mismatch.
        """
        # Validate inputs
        samples = actual_lap.get_samples()
        if len(samples) == 0:
            raise ValueError("actual_lap has no telemetry samples")
        
        if actual_lap.track_id and ideal_lap.track_id != actual_lap.track_id:
            raise ValueError(
                f"Track mismatch: actual={actual_lap.track_id}, ideal={ideal_lap.track_id}"
            )
        
        # Step 1: Divide lap into segments based on track geometry
        segment_boundaries = self._create_segments(
            track_profile,
            num_segments
        )
        
        # Step 2: Analyze each segment
        comparison_segments = []
        for i, (start_dist, end_dist) in enumerate(segment_boundaries):
            segment = self._analyze_segment(
                segment_id=i,
                start_dist=start_dist,
                end_dist=end_dist,
                actual_lap=actual_lap,
                ideal_lap=ideal_lap,
                track_profile=track_profile
            )
            
            # Filter by threshold
            if segment and segment.time_loss >= self.min_time_loss_threshold:
                comparison_segments.append(segment)
        
        # Step 3: Sort by time loss (descending - most impactful first)
        comparison_segments.sort(key=lambda s: s.time_loss, reverse=True)
        
        return comparison_segments
    
    def _create_segments(
        self,
        track_profile: TrackProfile,
        num_segments: int
    ) -> List[tuple[float, float]]:
        """Divide track into segments for analysis.
        
        Creates equal-length segments along the track. Future enhancement:
        segment by corners (curvature peaks) instead of fixed intervals.
        
        Args:
            track_profile: Track geometry.
            num_segments: Number of segments to create.
        
        Returns:
            List of (start_distance, end_distance) tuples in meters.
        """
        track_length = track_profile.track_length_m
        segment_length = track_length / num_segments
        
        segments = []
        for i in range(num_segments):
            start = i * segment_length
            end = (i + 1) * segment_length
            segments.append((start, end))
        
        return segments
    
    def _analyze_segment(
        self,
        segment_id: int,
        start_dist: float,
        end_dist: float,
        actual_lap: LapTrace,
        ideal_lap: IdealLap,
        track_profile: TrackProfile
    ) -> Optional[ComparisonSegment]:
        """Analyze a single segment for time loss and error classification.
        
        Args:
            segment_id: Segment identifier.
            start_dist: Segment start distance (meters).
            end_dist: Segment end distance (meters).
            actual_lap: Driver's actual lap.
            ideal_lap: Physics-based ideal lap.
            track_profile: Track geometry.
        
        Returns:
            ComparisonSegment if analysis successful, None if insufficient data.
        """
        # Get samples in this segment
        samples = actual_lap.get_samples()
        segment_samples = [
            s for s in samples
            if start_dist <= s.lap_distance < end_dist
        ]
        
        if len(segment_samples) < 3:
            # Not enough data points in segment
            return None
        
        # Calculate time loss in segment
        time_loss = ideal_lap.compute_total_time_loss(segment_samples)
        
        if time_loss < 0:
            # Driver was faster than ideal (shouldn't happen often)
            time_loss = 0.0
        
        # Find apex (highest curvature point in segment)
        apex_dist = self._find_apex(start_dist, end_dist, track_profile)
        
        # Calculate speed deltas at entry, apex, exit
        entry_sample = segment_samples[0]
        exit_sample = segment_samples[-1]
        apex_sample = self._find_closest_sample(segment_samples, apex_dist)
        
        speed_delta_entry = self._calculate_speed_delta(
            entry_sample, ideal_lap
        )
        speed_delta_apex = self._calculate_speed_delta(
            apex_sample, ideal_lap
        )
        speed_delta_exit = self._calculate_speed_delta(
            exit_sample, ideal_lap
        )
        
        # Classify error type
        error_type = self._classify_error(
            speed_delta_entry,
            speed_delta_apex,
            speed_delta_exit,
            track_profile,
            start_dist,
            end_dist
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            error_type,
            speed_delta_entry,
            speed_delta_apex,
            speed_delta_exit,
            time_loss
        )
        
        return ComparisonSegment(
            segment_id=segment_id,
            distance_start=start_dist,
            distance_end=end_dist,
            time_loss=time_loss,
            speed_delta_entry=speed_delta_entry,
            speed_delta_apex=speed_delta_apex,
            speed_delta_exit=speed_delta_exit,
            error_type=error_type,
            explanation=explanation
        )
    
    def _find_apex(
        self,
        start_dist: float,
        end_dist: float,
        track_profile: TrackProfile
    ) -> float:
        """Find apex (point of maximum curvature) in segment.
        
        Args:
            start_dist: Segment start distance.
            end_dist: Segment end distance.
            track_profile: Track geometry.
        
        Returns:
            Distance of apex point in meters.
        """
        # Sample curvature at multiple points in segment
        num_samples = 20
        distances = np.linspace(start_dist, end_dist, num_samples)
        curvatures = np.array([
            abs(track_profile.get_curvature_at(d)) for d in distances
        ])
        
        # Find peak curvature
        apex_idx = np.argmax(curvatures)
        apex_dist = distances[apex_idx]
        
        return apex_dist
    
    def _find_closest_sample(self, samples, target_distance):
        """Find telemetry sample closest to target distance."""
        if not samples:
            return samples[0] if samples else None
        
        closest = min(samples, key=lambda s: abs(s.lap_distance - target_distance))
        return closest
    
    def _calculate_speed_delta(self, sample, ideal_lap: IdealLap) -> float:
        """Calculate speed difference between actual and ideal.
        
        Args:
            sample: TelemetrySample from actual lap.
            ideal_lap: Ideal lap reference.
        
        Returns:
            Speed delta in m/s. Negative = driver slower than ideal.
        """
        actual_speed_ms = sample.speed / 3.6  # Convert km/h to m/s
        ideal_speed_ms = ideal_lap.get_speed_at(sample.lap_distance)
        
        return actual_speed_ms - ideal_speed_ms
    
    def _classify_error(
        self,
        speed_delta_entry: float,
        speed_delta_apex: float,
        speed_delta_exit: float,
        track_profile: TrackProfile,
        start_dist: float,
        end_dist: float
    ) -> ErrorType:
        """Classify the type of driving error in segment.
        
        Logic:
        - Early braking: Slow entry, normal apex/exit
        - Late braking: Fast entry, slow apex
        - Slow corner: Slow throughout (entry/apex/exit)
        - Late throttle: Normal entry/apex, slow exit
        - Line error: Inconsistent pattern
        
        Args:
            speed_delta_entry: Speed difference at entry (m/s).
            speed_delta_apex: Speed difference at apex (m/s).
            speed_delta_exit: Speed difference at exit (m/s).
            track_profile: Track geometry.
            start_dist: Segment start.
            end_dist: Segment end.
        
        Returns:
            ErrorType classification.
        """
        # Get average curvature in segment to determine if it's a corner
        mid_dist = (start_dist + end_dist) / 2.0
        avg_curvature = abs(track_profile.get_curvature_at(mid_dist))
        is_corner = avg_curvature > 0.01  # Threshold for "corner" vs "straight"
        
        # Classification thresholds (m/s)
        slow_threshold = -2.0  # Significantly slower than ideal
        
        if not is_corner:
            # Straight section - likely line error or late throttle
            if speed_delta_exit < slow_threshold:
                return ErrorType.LATE_THROTTLE
            return ErrorType.LINE_ERROR
        
        # Corner analysis
        if speed_delta_entry < slow_threshold and speed_delta_apex >= slow_threshold:
            # Slow entry but recovered at apex
            return ErrorType.EARLY_BRAKING
        
        if speed_delta_entry >= slow_threshold and speed_delta_apex < slow_threshold:
            # Fast entry but slow apex
            return ErrorType.LATE_BRAKING
        
        if speed_delta_apex < slow_threshold and speed_delta_exit < slow_threshold:
            # Slow through corner
            if speed_delta_entry < slow_threshold:
                return ErrorType.SLOW_CORNER
            else:
                return ErrorType.LATE_THROTTLE
        
        # Check specifically for late throttle (slow exit only)
        if speed_delta_exit < slow_threshold:
            return ErrorType.LATE_THROTTLE
        
        # Default to line error if pattern unclear
        return ErrorType.LINE_ERROR
    
    def _generate_explanation(
        self,
        error_type: ErrorType,
        speed_delta_entry: float,
        speed_delta_apex: float,
        speed_delta_exit: float,
        time_loss: float
    ) -> str:
        """Generate human-readable explanation of the issue.
        
        Args:
            error_type: Classified error type.
            speed_delta_entry: Speed difference at entry.
            speed_delta_apex: Speed difference at apex.
            speed_delta_exit: Speed difference at exit.
            time_loss: Total time lost.
        
        Returns:
            String explanation for the driver.
        """
        time_loss_ms = int(time_loss * 1000)
        
        if error_type == ErrorType.EARLY_BRAKING:
            return (
                f"Early braking cost {time_loss_ms}ms. Entry {abs(speed_delta_entry):.1f} m/s slower. "
                f"Brake later to carry more speed."
            )
        
        if error_type == ErrorType.LATE_BRAKING:
            return (
                f"Late braking cost {time_loss_ms}ms. Apex {abs(speed_delta_apex):.1f} m/s slower. "
                f"Brake earlier to hit correct apex speed."
            )
        
        if error_type == ErrorType.SLOW_CORNER:
            return (
                f"Slow through entire corner, cost {time_loss_ms}ms. "
                f"Apex {abs(speed_delta_apex):.1f} m/s slower. "
                f"Carry more speed and trust the grip."
            )
        
        if error_type == ErrorType.LATE_THROTTLE:
            return (
                f"Late throttle cost {time_loss_ms}ms. Exit {abs(speed_delta_exit):.1f} m/s slower. "
                f"Apply throttle earlier on corner exit."
            )
        
        # LINE_ERROR
        return (
            f"Suboptimal line cost {time_loss_ms}ms. "
            f"Review racing line for this section."
        )
