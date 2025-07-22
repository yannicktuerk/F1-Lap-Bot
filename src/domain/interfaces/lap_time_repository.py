"""Repository interface for lap time persistence (Port)."""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.lap_time import LapTime
from ..value_objects.track_name import TrackName


class LapTimeRepository(ABC):
    """Abstract repository interface for lap time persistence."""
    
    @abstractmethod
    async def save(self, lap_time: LapTime) -> str:
        """
        Save a lap time and return the generated ID.
        
        Args:
            lap_time: The lap time entity to save
            
        Returns:
            The generated unique ID for the saved lap time
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, lap_id: str) -> Optional[LapTime]:
        """
        Find a lap time by its ID.
        
        Args:
            lap_id: The unique identifier of the lap time
            
        Returns:
            The lap time if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_best_by_track(self, track: TrackName) -> Optional[LapTime]:
        """
        Find the best (fastest) lap time for a specific track.
        
        Args:
            track: The track to search for
            
        Returns:
            The fastest lap time for the track if any exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_user_best_by_track(self, user_id: str, track: TrackName) -> Optional[LapTime]:
        """
        Find the best lap time for a specific user on a specific track.
        
        Args:
            user_id: The Discord user ID
            track: The track to search for
            
        Returns:
            The user's fastest lap time for the track if any exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_top_by_track(self, track: TrackName, limit: int = 10) -> List[LapTime]:
        """
        Find the top lap times for a specific track.
        
        Args:
            track: The track to search for
            limit: Maximum number of results to return
            
        Returns:
            List of top lap times for the track, ordered by fastest first
        """
        pass
    
    @abstractmethod
    async def find_all_by_user(self, user_id: str) -> List[LapTime]:
        """
        Find all lap times for a specific user.
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            List of all lap times for the user, ordered by creation date
        """
        pass
    
    @abstractmethod
    async def find_recent_by_track(self, track: TrackName, limit: int = 10) -> List[LapTime]:
        """
        Find recent lap times for a specific track.
        
        Args:
            track: The track to search for
            limit: Maximum number of results to return
            
        Returns:
            List of recent lap times for the track, ordered by most recent first
        """
        pass
    
    @abstractmethod
    async def get_user_statistics(self, user_id: str) -> dict:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            Dictionary containing user statistics like total laps, best times, etc.
        """
        pass
    
    @abstractmethod
    async def get_track_statistics(self, track: TrackName) -> dict:
        """
        Get statistics for a specific track.
        
        Args:
            track: The track to get statistics for
            
        Returns:
            Dictionary containing track statistics like total laps, average time, etc.
        """
        pass
    
    @abstractmethod
    async def reset_all_data(self) -> bool:
        """
        Reset all lap time data in the database.
        
        Returns:
            True if reset was successful, False otherwise
        """
        pass
