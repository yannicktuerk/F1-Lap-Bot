"""Repository interface for telemetry persistence (Port)."""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..entities.telemetry_sample import PlayerTelemetrySample
from ..value_objects.track_name import TrackName


class TelemetryRepository(ABC):
    """Abstract repository interface for telemetry persistence."""
    
    @abstractmethod
    async def save(self, sample: PlayerTelemetrySample) -> str:
        """
        Save a telemetry sample and return the generated ID.
        
        Args:
            sample: The telemetry sample to save
            
        Returns:
            The generated unique ID for the saved sample
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, sample_id: str) -> Optional[PlayerTelemetrySample]:
        """
        Find a telemetry sample by its ID.
        
        Args:
            sample_id: The unique identifier of the sample
            
        Returns:
            The telemetry sample if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_session(self, session_uid: int, limit: int = 1000) -> List[PlayerTelemetrySample]:
        """
        Find telemetry samples by session UID.
        
        Args:
            session_uid: The session unique identifier
            limit: Maximum number of samples to return
            
        Returns:
            List of telemetry samples for the session
        """
        pass
    
    @abstractmethod
    async def find_by_track_and_timerange(
        self, 
        track: TrackName, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[PlayerTelemetrySample]:
        """
        Find telemetry samples by track and time range.
        
        Args:
            track: The track to search for
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of telemetry samples in the time range
        """
        pass
    
    @abstractmethod
    async def find_valid_samples_by_track(
        self, 
        track: TrackName, 
        limit: int = 1000
    ) -> List[PlayerTelemetrySample]:
        """
        Find valid telemetry samples for a track (TT-only, Valid-only).
        
        Args:
            track: The track to search for
            limit: Maximum number of samples to return
            
        Returns:
            List of valid telemetry samples for the track
        """
        pass
    
    @abstractmethod
    async def get_session_statistics(self, session_uid: int) -> dict:
        """
        Get statistics for a specific session.
        
        Args:
            session_uid: The session unique identifier
            
        Returns:
            Dictionary containing session statistics
        """
        pass
    
    @abstractmethod
    async def delete_by_session(self, session_uid: int) -> int:
        """
        Delete all telemetry samples for a session.
        
        Args:
            session_uid: The session unique identifier
            
        Returns:
            Number of deleted samples
        """
        pass