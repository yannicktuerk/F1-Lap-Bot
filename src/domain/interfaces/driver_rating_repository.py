"""Repository interface for driver rating persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.driver_rating import DriverRating


class DriverRatingRepository(ABC):
    """Abstract repository interface for driver rating persistence."""
    
    @abstractmethod
    async def save(self, driver_rating: DriverRating) -> None:
        """Save or update a driver rating."""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[DriverRating]:
        """Find driver rating by user ID."""
        pass
    
    @abstractmethod
    async def find_all_ratings(self) -> List[DriverRating]:
        """Find all driver ratings."""
        pass
    
    @abstractmethod
    async def find_top_ratings(self, limit: int = 10) -> List[DriverRating]:
        """Find top driver ratings by ELO."""
        pass
    
    @abstractmethod
    async def get_user_rank(self, user_id: str) -> Optional[int]:
        """Get the rank of a specific user based on ELO."""
        pass
    
    @abstractmethod
    async def update_username(self, user_id: str, new_username: str) -> bool:
        """Update the username for a driver rating."""
        pass
    
    @abstractmethod
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete a driver rating by user ID."""
        pass
    
    @abstractmethod
    async def reset_all_data(self) -> bool:
        """Reset all driver rating data in the database."""
        pass
