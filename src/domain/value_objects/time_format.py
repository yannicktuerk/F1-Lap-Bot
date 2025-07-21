"""Value object for lap time format validation and operations."""
import re
from typing import Optional


class TimeFormat:
    """Immutable value object representing a lap time with validation."""
    
    # Regex patterns for different time formats
    PATTERNS = {
        'mm:ss.mmm': re.compile(r'^(\d{1,2}):([0-5]\d)\.(\d{3})$'),  # 1:23.456
        'ss.mmm': re.compile(r'^([0-5]?\d)\.(\d{3})$'),              # 23.456
        'm:ss.mmm': re.compile(r'^(\d):([0-5]\d)\.(\d{3})$')          # 1:23.456
    }
    
    def __init__(self, time_string: str):
        self._original_string = time_string.strip()
        self._minutes, self._seconds, self._milliseconds = self._parse_time(self._original_string)
        self._total_milliseconds = self._calculate_total_milliseconds()
    
    def _parse_time(self, time_string: str) -> tuple[int, int, int]:
        """Parse time string into minutes, seconds, milliseconds."""
        time_string = time_string.strip()
        
        # Try mm:ss.mmm format first
        match = self.PATTERNS['mm:ss.mmm'].match(time_string)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            milliseconds = int(match.group(3))
            
            # Validate reasonable lap time (30 seconds to 5 minutes)
            total_seconds = minutes * 60 + seconds + milliseconds / 1000
            if not (30 <= total_seconds <= 300):
                raise ValueError(f"Lap time {time_string} is not plausible (must be between 30s and 5min)")
            
            return minutes, seconds, milliseconds
        
        # Try ss.mmm format
        match = self.PATTERNS['ss.mmm'].match(time_string)
        if match:
            seconds = int(match.group(1))
            milliseconds = int(match.group(2))
            
            # Validate reasonable lap time
            total_seconds = seconds + milliseconds / 1000
            if not (30 <= total_seconds <= 300):
                raise ValueError(f"Lap time {time_string} is not plausible (must be between 30s and 5min)")
            
            return 0, seconds, milliseconds
        
        # Try m:ss.mmm format
        match = self.PATTERNS['m:ss.mmm'].match(time_string)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            milliseconds = int(match.group(3))
            
            # Validate reasonable lap time
            total_seconds = minutes * 60 + seconds + milliseconds / 1000
            if not (30 <= total_seconds <= 300):
                raise ValueError(f"Lap time {time_string} is not plausible (must be between 30s and 5min)")
            
            return minutes, seconds, milliseconds
        
        raise ValueError(f"Invalid time format: {time_string}. Use formats like '1:23.456', '83.456', or '1:23.456'")
    
    def _calculate_total_milliseconds(self) -> int:
        """Calculate total milliseconds for easy comparison."""
        return (self._minutes * 60 * 1000) + (self._seconds * 1000) + self._milliseconds
    
    @property
    def minutes(self) -> int:
        return self._minutes
    
    @property
    def seconds(self) -> int:
        return self._seconds
    
    @property
    def milliseconds(self) -> int:
        return self._milliseconds
    
    @property
    def total_milliseconds(self) -> int:
        return self._total_milliseconds
    
    @property
    def total_seconds(self) -> float:
        """Get total time in seconds as float."""
        return self._total_milliseconds / 1000.0
    
    def formatted_display(self) -> str:
        """Return formatted time for display (always in mm:ss.mmm format)."""
        if self._minutes > 0:
            return f"{self._minutes}:{self._seconds:02d}.{self._milliseconds:03d}"
        else:
            return f"{self._seconds}.{self._milliseconds:03d}"
    
    def __str__(self) -> str:
        return self.formatted_display()
    
    def __repr__(self) -> str:
        return f"TimeFormat('{self._original_string}')"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeFormat):
            return False
        return self._total_milliseconds == other._total_milliseconds
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, TimeFormat):
            raise TypeError("Can only compare with another TimeFormat")
        return self._total_milliseconds < other._total_milliseconds
    
    def __le__(self, other) -> bool:
        if not isinstance(other, TimeFormat):
            raise TypeError("Can only compare with another TimeFormat")
        return self._total_milliseconds <= other._total_milliseconds
    
    def __gt__(self, other) -> bool:
        if not isinstance(other, TimeFormat):
            raise TypeError("Can only compare with another TimeFormat")
        return self._total_milliseconds > other._total_milliseconds
    
    def __ge__(self, other) -> bool:
        if not isinstance(other, TimeFormat):
            raise TypeError("Can only compare with another TimeFormat")
        return self._total_milliseconds >= other._total_milliseconds
    
    def __hash__(self) -> int:
        return hash(self._total_milliseconds)
