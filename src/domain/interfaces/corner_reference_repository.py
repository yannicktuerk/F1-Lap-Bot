"""Repository interface for corner reference persistence (Port)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from ..value_objects.track_name import TrackName


@dataclass
class CornerReference:
    """Statistical reference data for a corner."""
    track_id: int
    corner_id: int
    median_time_ms: float    # p50 reference time
    iqr_ms: float           # Interquartile range for normalization
    sample_count: int       # Number of samples used
    assists_filter: str     # Assists configuration hash
    device_filter: str      # Input device filter
    preferred_line: Optional[str] = None  # Faster line mode if multiple exist
    last_updated: Optional[datetime] = None
    
    @property
    def q1_time_ms(self) -> float:
        """25th percentile time."""
        return self.median_time_ms - (self.iqr_ms / 2)
    
    @property  
    def q3_time_ms(self) -> float:
        """75th percentile time."""
        return self.median_time_ms + (self.iqr_ms / 2)


class CornerReferenceRepository(ABC):
    """Abstract repository interface for corner reference persistence."""
    
    @abstractmethod
    async def save_reference(self, reference: CornerReference) -> str:
        """
        Save a corner reference and return the generated ID.
        
        Args:
            reference: The corner reference to save
            
        Returns:
            The generated unique ID for the saved reference
        """
        pass
    
    @abstractmethod
    async def find_by_corner(
        self, 
        track: TrackName, 
        corner_id: int,
        assists_filter: str,
        device_filter: str
    ) -> Optional[CornerReference]:
        """
        Find corner reference by track, corner, and filters.
        
        Args:
            track: The track to search for
            corner_id: The corner identifier
            assists_filter: Assists configuration hash
            device_filter: Input device filter
            
        Returns:
            The corner reference if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_all_by_track(
        self, 
        track: TrackName,
        assists_filter: str,
        device_filter: str
    ) -> List[CornerReference]:
        """
        Find all corner references for a track with given filters.
        
        Args:
            track: The track to search for
            assists_filter: Assists configuration hash
            device_filter: Input device filter
            
        Returns:
            List of corner references for the track
        """
        pass
    
    @abstractmethod
    async def update_reference(
        self,
        track: TrackName,
        corner_id: int,
        assists_filter: str,
        device_filter: str,
        median_time_ms: float,
        iqr_ms: float,
        sample_count: int
    ) -> bool:
        """
        Update an existing corner reference.
        
        Args:
            track: The track identifier
            corner_id: The corner identifier
            assists_filter: Assists configuration hash
            device_filter: Input device filter
            median_time_ms: Updated median time
            iqr_ms: Updated IQR
            sample_count: Updated sample count
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_corner_statistics(self, track: TrackName) -> Dict[str, any]:
        """
        Get corner statistics for a track.
        
        Args:
            track: The track to get statistics for
            
        Returns:
            Dictionary containing corner statistics
        """
        pass
    
    @abstractmethod
    async def delete_old_references(self, days_old: int) -> int:
        """
        Delete corner references older than specified days.
        
        Args:
            days_old: Number of days threshold
            
        Returns:
            Number of deleted references
        """
        pass