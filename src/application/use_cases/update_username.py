"""Use case for updating user display names across all data repositories."""
from ...domain.interfaces.lap_time_repository import LapTimeRepository
from ...domain.interfaces.driver_rating_repository import DriverRatingRepository


class UpdateUsernameUseCase:
    """Use case for updating a user's display name across all data repositories."""
    
    def __init__(
        self, 
        lap_time_repository: LapTimeRepository,
        driver_rating_repository: DriverRatingRepository
    ):
        self._lap_time_repository = lap_time_repository
        self._driver_rating_repository = driver_rating_repository
    
    async def execute(self, user_id: str, new_username: str) -> dict:
        """
        Update username across all repositories.
        
        Args:
            user_id: Discord user ID
            new_username: New display name to use
            
        Returns:
            Dictionary with update results for each repository
        """
        results = {
            'lap_times_updated': False,
            'driver_rating_updated': False,
            'total_lap_times_affected': 0
        }
        
        # Get user's current lap times count for reporting
        user_lap_times = await self._lap_time_repository.find_all_by_user(user_id)
        results['total_lap_times_affected'] = len(user_lap_times)
        
        # Update username in lap times repository
        lap_times_success = await self._lap_time_repository.update_username(
            user_id, new_username
        )
        results['lap_times_updated'] = lap_times_success
        
        # Update username in driver rating repository
        driver_rating_success = await self._driver_rating_repository.update_username(
            user_id, new_username
        )
        results['driver_rating_updated'] = driver_rating_success
        
        return results
