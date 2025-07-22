"""Use case for updating ELO ratings after lap time submission."""

from typing import List
from ...domain.entities.lap_time import LapTime
from ...domain.entities.driver_rating import DriverRating
from ...domain.interfaces.driver_rating_repository import DriverRatingRepository
from ...domain.interfaces.lap_time_repository import LapTimeRepository
from ...domain.value_objects.track_name import TrackName


class UpdateEloRatingsUseCase:
    """Application service for updating ELO ratings based on lap time submissions."""
    
    def __init__(
        self, 
        driver_rating_repository: DriverRatingRepository,
        lap_time_repository: LapTimeRepository
    ):
        self._driver_rating_repository = driver_rating_repository
        self._lap_time_repository = lap_time_repository
    
    async def execute(self, submitted_lap: LapTime) -> DriverRating:
        """
        Update ELO ratings after a lap time submission.
        
        Args:
            submitted_lap: The newly submitted lap time
            
        Returns:
            Updated driver rating for the submitting user
        """
        # Get or create driver rating for the submitting user
        user_rating = await self._driver_rating_repository.find_by_user_id(submitted_lap.user_id)
        if not user_rating:
            user_rating = DriverRating(
                user_id=submitted_lap.user_id,
                username=submitted_lap.username
            )
        
        # Get all other drivers' best times on this track for comparison
        track_competitors = await self._get_track_competitors(
            submitted_lap.track_name, 
            exclude_user_id=submitted_lap.user_id
        )
        
        if not track_competitors:
            # No competitors yet, just save the initial rating
            await self._driver_rating_repository.save(user_rating)
            return user_rating
        
        # Calculate virtual matches and update ELO
        elo_change, wins, losses = await self._calculate_elo_changes(
            submitted_lap, 
            user_rating, 
            track_competitors
        )
        
        # Update the user's rating
        user_rating.update_after_matches(elo_change, wins, losses)
        await self._driver_rating_repository.save(user_rating)
        
        return user_rating
    
    async def _get_track_competitors(self, track: TrackName, exclude_user_id: str) -> List[LapTime]:
        """Get all other drivers' best times on the specified track."""
        all_track_times = await self._lap_time_repository.find_top_by_track(track, limit=100)
        
        # Group by user and get each user's best time
        user_best_times = {}
        for lap_time in all_track_times:
            if lap_time.user_id != exclude_user_id:
                if (lap_time.user_id not in user_best_times or 
                    lap_time.is_faster_than(user_best_times[lap_time.user_id])):
                    user_best_times[lap_time.user_id] = lap_time
        
        return list(user_best_times.values())
    
    async def _calculate_elo_changes(
        self, 
        submitted_lap: LapTime, 
        user_rating: DriverRating, 
        competitors: List[LapTime]
    ) -> tuple[float, int, int]:
        """
        Calculate ELO changes based on virtual matches against competitors.
        
        Returns:
            Tuple of (total_elo_change, wins, losses)
        """
        total_elo_change = 0.0
        wins = 0
        losses = 0
        
        for competitor_lap in competitors:
            # Get competitor's rating (or create default)
            competitor_rating = await self._driver_rating_repository.find_by_user_id(
                competitor_lap.user_id
            )
            if not competitor_rating:
                competitor_rating = DriverRating(
                    user_id=competitor_lap.user_id,
                    username=competitor_lap.username
                )
            
            # Calculate expected score
            expected_score = user_rating.calculate_expected_score(competitor_rating.current_elo)
            
            # Determine actual result
            user_wins = submitted_lap.is_faster_than(competitor_lap)
            actual_score = 1.0 if user_wins else 0.0
            
            # Calculate K-factor based on time difference and recency
            time_diff = abs(submitted_lap.get_time_difference_to(competitor_lap))
            recency_weight = self._calculate_recency_weight(competitor_lap.created_at)
            k_factor = self._calculate_adaptive_k_factor(time_diff, recency_weight)
            
            # Calculate ELO change for this match
            elo_change = k_factor * (actual_score - expected_score)
            total_elo_change += elo_change
            
            # Update win/loss counters
            if user_wins:
                wins += 1
            else:
                losses += 1
            
            # Also update competitor's rating
            competitor_elo_change = k_factor * ((1.0 - actual_score) - (1.0 - expected_score))
            competitor_rating.update_after_matches(
                competitor_elo_change, 
                0 if user_wins else 1, 
                1 if user_wins else 0
            )
            await self._driver_rating_repository.save(competitor_rating)
        
        # Return average ELO change if there were matches
        if len(competitors) > 0:
            total_elo_change /= len(competitors)
        
        return total_elo_change, wins, losses
    
    def _calculate_recency_weight(self, lap_time_created_at) -> float:
        """Calculate weight based on how recent the comparison lap time is."""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        age = now - lap_time_created_at
        
        # Times older than 90 days get reduced weight
        if age > timedelta(days=90):
            return 0.5
        elif age > timedelta(days=30):
            return 0.8
        else:
            return 1.0
    
    def _calculate_adaptive_k_factor(self, time_difference: float, recency_weight: float) -> float:
        """
        Calculate adaptive K-factor based on time difference and recency.
        
        Args:
            time_difference: Time difference in seconds between lap times
            recency_weight: Weight factor based on age of comparison time
        """
        base_k = 32
        
        # Adjust based on time difference - closer times are more significant
        if time_difference < 0.1:      # Very close (within 0.1s)
            time_multiplier = 1.5
        elif time_difference < 0.5:    # Close (within 0.5s)
            time_multiplier = 1.2
        elif time_difference < 2.0:    # Moderate (within 2s)
            time_multiplier = 1.0
        else:                          # Large difference (>2s)
            time_multiplier = 0.7
        
        return base_k * time_multiplier * recency_weight
