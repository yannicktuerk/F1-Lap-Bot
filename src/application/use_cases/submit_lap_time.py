"""Use case for submitting a new lap time."""
from typing import Optional, Tuple
from ...domain.entities.lap_time import LapTime
from ...domain.entities.driver_rating import DriverRating
from ...domain.interfaces.lap_time_repository import LapTimeRepository
from ...domain.interfaces.driver_rating_repository import DriverRatingRepository
from ...domain.value_objects.time_format import TimeFormat
from ...domain.value_objects.track_name import TrackName
from .update_elo_ratings import UpdateEloRatingsUseCase


class SubmitLapTimeUseCase:
    """Application service for submitting lap times with business logic."""
    
    def __init__(
        self, 
        lap_time_repository: LapTimeRepository,
        driver_rating_repository: Optional[DriverRatingRepository] = None
    ):
        self._repository = lap_time_repository
        self._driver_rating_repository = driver_rating_repository
        self._update_elo_use_case = None
        
        # Initialize ELO update use case if rating repository is provided
        if driver_rating_repository:
            self._update_elo_use_case = UpdateEloRatingsUseCase(
                driver_rating_repository, lap_time_repository
            )
    
    async def execute(
        self, 
        user_id: str, 
        username: str, 
        time_string: str, 
        track_string: str
    ) -> Tuple[LapTime, bool, bool]:
        """
        Submit a new lap time.
        
        Args:
            user_id: Discord user ID
            username: Discord username
            time_string: Time in format like "1:23.456"
            track_string: Track name
            
        Returns:
            Tuple of (lap_time, is_personal_best, is_overall_best)
            
        Raises:
            ValueError: If time format or track name is invalid
        """
        # Validate and create value objects
        try:
            time_format = TimeFormat(time_string)
        except ValueError as e:
            raise ValueError(f"Invalid time format: {e}")
        
        try:
            track_name = TrackName(track_string)
        except ValueError as e:
            raise ValueError(f"Invalid track name: {e}")
        
        # Create the lap time entity
        lap_time = LapTime(
            user_id=user_id,
            username=username,
            time_format=time_format,
            track_name=track_name
        )
        
        # Check if this is a personal best
        user_best = await self._repository.find_user_best_by_track(user_id, track_name)
        is_personal_best = user_best is None or lap_time.is_faster_than(user_best)
        
        # Validate that the new time is faster than the current personal best
        if user_best is not None and not lap_time.is_faster_than(user_best):
            time_difference = lap_time.get_time_difference_to(user_best)
            raise ValueError(f"Your submitted time ({lap_time.time_format}) is {time_difference:.3f}s slower than your current best time ({user_best.time_format}) on this track. You can only submit faster times!")
        
        # Check if this is an overall best
        overall_best = await self._repository.find_best_by_track(track_name)
        is_overall_best = overall_best is None or lap_time.is_faster_than(overall_best)
        
        # Mark the lap time appropriately
        if is_personal_best:
            lap_time.mark_as_personal_best()
        
        if is_overall_best:
            lap_time.mark_as_overall_best()
        
        # Save the lap time
        await self._repository.save(lap_time)
        
        # Update ELO ratings if the feature is enabled
        if self._update_elo_use_case:
            try:
                await self._update_elo_use_case.execute(lap_time)
            except Exception as e:
                # Log error but don't fail the lap submission
                print(f"Warning: ELO rating update failed: {e}")
        
        return lap_time, is_personal_best, is_overall_best
