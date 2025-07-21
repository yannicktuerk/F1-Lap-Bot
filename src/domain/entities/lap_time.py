"""Domain entity representing a lap time entry."""
from datetime import datetime
from typing import Optional
from ..value_objects.time_format import TimeFormat
from ..value_objects.track_name import TrackName


class LapTime:
    """Rich domain entity for lap times with business rules and validation."""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        time_format: TimeFormat,
        track_name: TrackName,
        lap_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._lap_id = lap_id
        self._user_id = user_id
        self._username = username
        self._time_format = time_format
        self._track_name = track_name
        self._created_at = created_at or datetime.utcnow()
        self._is_personal_best = False
        self._is_overall_best = False
    
    @property
    def lap_id(self) -> Optional[str]:
        return self._lap_id
    
    @property
    def user_id(self) -> str:
        return self._user_id
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def time_format(self) -> TimeFormat:
        return self._time_format
    
    @property
    def track_name(self) -> TrackName:
        return self._track_name
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def is_personal_best(self) -> bool:
        return self._is_personal_best
    
    @property
    def is_overall_best(self) -> bool:
        return self._is_overall_best
    
    def mark_as_personal_best(self) -> None:
        """Mark this lap time as a personal best for the user."""
        self._is_personal_best = True
    
    def mark_as_overall_best(self) -> None:
        """Mark this lap time as the overall best time."""
        self._is_overall_best = True
        self._is_personal_best = True  # Overall best is always personal best too
    
    def is_faster_than(self, other_lap_time: 'LapTime') -> bool:
        """Compare lap times to determine if this one is faster."""
        if not isinstance(other_lap_time, LapTime):
            raise ValueError("Can only compare with another LapTime")
        
        # Only compare lap times on the same track
        if self._track_name != other_lap_time._track_name:
            raise ValueError("Cannot compare lap times from different tracks")
        
        return self._time_format.total_milliseconds < other_lap_time._time_format.total_milliseconds
    
    def get_time_difference_to(self, other_lap_time: 'LapTime') -> float:
        """Get time difference in seconds between this and another lap time."""
        if not isinstance(other_lap_time, LapTime):
            raise ValueError("Can only compare with another LapTime")
        
        if self._track_name != other_lap_time._track_name:
            raise ValueError("Cannot compare lap times from different tracks")
        
        difference_ms = abs(self._time_format.total_milliseconds - other_lap_time._time_format.total_milliseconds)
        return difference_ms / 1000.0
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, LapTime):
            return False
        
        return (
            self._user_id == other._user_id and
            self._time_format == other._time_format and
            self._track_name == other._track_name
        )
    
    def __str__(self) -> str:
        return f"{self._username}: {self._time_format} on {self._track_name}"
    
    def __repr__(self) -> str:
        return f"LapTime(user_id='{self._user_id}', time='{self._time_format}', track='{self._track_name}')"
