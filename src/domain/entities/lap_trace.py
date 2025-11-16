"""Domain entity representing a complete lap with telemetry trace.

This module defines the LapTrace entity which aggregates a sequence of
TelemetrySample points for a complete lap, maintaining ordering and
enforcing domain invariants.
"""

import uuid
from typing import List, Optional
from datetime import datetime
from ..value_objects.telemetry_sample import TelemetrySample
from .car_setup_snapshot import CarSetupSnapshot


class LapTrace:
    """Rich domain entity for a lap with complete telemetry trace.
    
    Represents a single lap in a session, aggregating all telemetry samples
    captured during that lap. Entity identity is based on trace_id (UUID).
    
    Attributes:
        trace_id (str): Unique identifier for this lap trace (UUID).
        session_uid (str): Session identifier from F1 25.
        lap_number (int): Lap number within the session.
        track_id (Optional[str]): Track identifier from F1 25.
        car_index (int): Player car index from F1 25.
        lap_time_ms (Optional[int]): Final lap time in milliseconds (None if incomplete).
        is_valid (bool): Whether lap is valid (no penalties, corner cutting, etc.).
        samples (List[TelemetrySample]): Ordered telemetry samples for this lap.
        car_setup (Optional[CarSetupSnapshot]): Car setup used for this lap.
        created_at (datetime): When this trace was created in the system.
    
    Invariants:
        - Samples must be chronologically ordered by timestamp_ms
        - Cannot add samples after lap is marked complete
        - All samples must have same lap_number
    """
    
    def __init__(
        self,
        session_uid: str,
        lap_number: int,
        car_index: int,
        is_valid: bool = True,
        track_id: Optional[str] = None,
        lap_time_ms: Optional[int] = None,
        car_setup: Optional[CarSetupSnapshot] = None,
        trace_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize lap trace with metadata.
        
        Args:
            session_uid: F1 25 session identifier.
            lap_number: Lap number within session (must be >= 1).
            car_index: Player car index from F1 25.
            is_valid: Whether lap is valid (default: True).
            track_id: Optional track identifier from F1 25.
            lap_time_ms: Optional final lap time in ms (set when lap completes).
            car_setup: Optional car setup snapshot used for this lap.
            trace_id: Optional custom trace ID (auto-generated if not provided).
            created_at: Optional creation timestamp (auto-set if not provided).
            
        Raises:
            ValueError: If lap_number < 1 or lap_time_ms < 0.
        """
        # Entity identity
        self._trace_id = trace_id or str(uuid.uuid4())
        self._created_at = created_at or datetime.utcnow()
        
        # Lap metadata validation
        if lap_number < 1:
            raise ValueError(f"lap_number must be at least 1, got {lap_number}")
        
        if lap_time_ms is not None and lap_time_ms < 0:
            raise ValueError(f"lap_time_ms must be non-negative, got {lap_time_ms}")
        
        # Lap metadata
        self._session_uid = session_uid
        self._lap_number = lap_number
        self._car_index = car_index
        self._track_id = track_id
        self._lap_time_ms = lap_time_ms
        self._is_valid = is_valid
        self._car_setup = car_setup
        
        # Telemetry data
        self._samples: List[TelemetrySample] = []
        self._is_complete = lap_time_ms is not None
    
    # Properties (read-only access)
    
    @property
    def trace_id(self) -> str:
        return self._trace_id
    
    @property
    def session_uid(self) -> str:
        return self._session_uid
    
    @property
    def lap_number(self) -> int:
        return self._lap_number
    
    @property
    def car_index(self) -> int:
        return self._car_index
    
    @property
    def track_id(self) -> Optional[str]:
        return self._track_id
    
    @property
    def lap_time_ms(self) -> Optional[int]:
        return self._lap_time_ms
    
    @property
    def is_valid(self) -> bool:
        return self._is_valid
    
    @property
    def car_setup(self) -> Optional[CarSetupSnapshot]:
        return self._car_setup
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def sample_count(self) -> int:
        """Get number of telemetry samples in this trace."""
        return len(self._samples)
    
    # Business logic methods
    
    def add_sample(self, sample: TelemetrySample) -> None:
        """Add telemetry sample to this lap trace.
        
        Maintains chronological ordering by timestamp_ms. Enforces invariants:
        - Cannot add samples after lap is complete
        - Sample must have matching lap_number
        - Samples must be chronologically ordered
        
        Args:
            sample: TelemetrySample to add to this trace.
            
        Raises:
            ValueError: If invariants are violated.
        """
        # Enforce: cannot add samples after lap is complete
        if self._is_complete:
            raise ValueError(
                f"Cannot add sample to completed lap (trace_id={self._trace_id})"
            )
        
        # Enforce: sample must have matching lap_number
        if sample.lap_number != self._lap_number:
            raise ValueError(
                f"Sample lap_number {sample.lap_number} does not match trace lap_number {self._lap_number}"
            )
        
        # Enforce: maintain chronological order
        if self._samples and sample.timestamp_ms < self._samples[-1].timestamp_ms:
            raise ValueError(
                f"Sample timestamp {sample.timestamp_ms}ms is before last sample "
                f"{self._samples[-1].timestamp_ms}ms (samples must be chronologically ordered)"
            )
        
        self._samples.append(sample)
    
    def get_samples(self) -> List[TelemetrySample]:
        """Get all telemetry samples in chronological order.
        
        Returns:
            List of TelemetrySample objects ordered by timestamp_ms.
        """
        return self._samples.copy()
    
    def is_complete(self) -> bool:
        """Check if lap is complete (has final lap time).
        
        Returns:
            True if lap has been marked complete with lap_time_ms, False otherwise.
        """
        return self._is_complete
    
    def mark_complete(self, lap_time_ms: int) -> None:
        """Mark lap as complete with final lap time.
        
        Args:
            lap_time_ms: Final lap time in milliseconds.
            
        Raises:
            ValueError: If lap_time_ms is negative or lap is already complete.
        """
        if self._is_complete:
            raise ValueError(
                f"Lap trace {self._trace_id} is already complete"
            )
        
        if lap_time_ms < 0:
            raise ValueError(
                f"lap_time_ms must be non-negative, got {lap_time_ms}"
            )
        
        self._lap_time_ms = lap_time_ms
        self._is_complete = True
    
    def mark_invalid(self) -> None:
        """Mark lap as invalid (penalty, corner cutting, etc.)."""
        self._is_valid = False
    
    def get_sample_at_distance(self, distance: float) -> Optional[TelemetrySample]:
        """Find telemetry sample nearest to specified lap distance.
        
        Args:
            distance: Target lap distance in meters.
            
        Returns:
            TelemetrySample closest to target distance, or None if no samples.
        """
        if not self._samples:
            return None
        
        # Find sample with minimum distance difference
        closest_sample = min(
            self._samples,
            key=lambda s: abs(s.lap_distance - distance)
        )
        
        return closest_sample
    
    def get_samples_in_distance_range(
        self,
        start_distance: float,
        end_distance: float
    ) -> List[TelemetrySample]:
        """Get telemetry samples within specified distance range.
        
        Args:
            start_distance: Start of distance range in meters.
            end_distance: End of distance range in meters.
            
        Returns:
            List of samples where start_distance <= lap_distance <= end_distance.
        """
        return [
            sample for sample in self._samples
            if start_distance <= sample.lap_distance <= end_distance
        ]
    
    def get_average_speed(self) -> Optional[float]:
        """Calculate average speed across all samples.
        
        Returns:
            Average speed in km/h, or None if no samples.
        """
        if not self._samples:
            return None
        
        total_speed = sum(sample.speed for sample in self._samples)
        return total_speed / len(self._samples)
    
    def get_max_speed(self) -> Optional[float]:
        """Get maximum speed reached during lap.
        
        Returns:
            Maximum speed in km/h, or None if no samples.
        """
        if not self._samples:
            return None
        
        return max(sample.speed for sample in self._samples)
    
    def set_car_setup(self, car_setup: CarSetupSnapshot) -> None:
        """Associate car setup with this lap trace.
        
        Args:
            car_setup: CarSetupSnapshot to associate with this lap.
        """
        self._car_setup = car_setup
    
    # Entity identity
    
    def __eq__(self, other) -> bool:
        """Entity equality based on trace_id (identity)."""
        if not isinstance(other, LapTrace):
            return False
        return self._trace_id == other._trace_id
    
    def __hash__(self) -> int:
        """Hash based on entity identity (trace_id)."""
        return hash(self._trace_id)
    
    def __str__(self) -> str:
        status = "complete" if self._is_complete else "incomplete"
        valid = "valid" if self._is_valid else "invalid"
        return (
            f"LapTrace(id={self._trace_id[:8]}, lap={self._lap_number}, "
            f"samples={len(self._samples)}, {status}, {valid})"
        )
    
    def __repr__(self) -> str:
        return (
            f"LapTrace(trace_id='{self._trace_id}', session_uid={self._session_uid}, "
            f"lap_number={self._lap_number}, samples={len(self._samples)}, "
            f"is_complete={self._is_complete}, is_valid={self._is_valid})"
        )
