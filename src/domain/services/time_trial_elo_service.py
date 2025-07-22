"""Service for ELO calculations in time trial scenarios."""

import datetime
from ..entities.driver_rating import DriverRating

class TimeTrialEloService:
    """Service for calculating and updating ELO ratings based on time trials."""
    
    def calculate_virtual_matches(self, new_lap_time, track):
        """
        Create virtual matches based on time comparisons:
        - New lap vs. all other drivers on the same track
        - Weight by recency of the compared times
        """
        # Retrieve all other best times for this track
        # Placeholder for repository call
        other_drivers_times = []  # repository.find_all_best_by_track(track)
        
        virtual_matches = []
        for opponent_time in other_drivers_times:
            if opponent_time.user_id != new_lap_time.user_id:
                match = {
                    'winner_id': new_lap_time.user_id if new_lap_time.is_faster_than(opponent_time) else opponent_time.user_id,
                    'time_difference': abs(new_lap_time.get_time_difference_to(opponent_time)),
                    'track': track,
                    'recency_weight': self._calculate_recency_weight(opponent_time.created_at)
                }
                virtual_matches.append(match)
        
        return virtual_matches
    
    def _calculate_recency_weight(self, compare_time):
        """Calculate a recency weight for the comparison, less recent times have less weight."""
        now = datetime.datetime.utcnow()
        age_days = (now - compare_time).days
        
        # Simplistic weight calculation, improve with actual function later
        return max(0.1, 1.0 - age_days * 0.01)
    
    def update_elo_from_virtual_matches(self, user_rating: DriverRating, virtual_matches):
        """
        Update ELO based on virtual matches with time trial specific adjustments.
        """
        elo_change_sum = 0.0
        matches_count = 0
        
        for match in virtual_matches:
            opponent_id = match['winner_id'] if match['winner_id'] != user_rating.user_id else new_lap_time.user_id
            opponent_rating = DriverRating(user_id=opponent_id, username="")  # Placeholder 
            expected_score = user_rating.calculate_expected_score(opponent_rating.current_elo)
            actual_score = 1.0 if user_rating.user_id == match['winner_id'] else 0.0
            
            time_diff = match['time_difference']
            recency_weight = match['recency_weight']
            k_factor = self._calculate_adaptive_k_factor(time_diff, recency_weight)
            elo_change = k_factor * (actual_score - expected_score)
            elo_change_sum += elo_change
            matches_count += 1
        
        if matches_count > 0:
            avg_elo_change = elo_change_sum / matches_count
            user_rating.update_after_matches(avg_elo_change, int(actual_score), int(1 - actual_score))
    
    def _calculate_adaptive_k_factor(self, time_difference, recency_weight):
        """
        Adaptive K-Factor for time trials:
        - Higher for small time differences
        - Lower for very old comparison times
        """
        base_k = 32
        
        # Time-based adjustment
        if time_difference < 0.1:      # Very close
            time_multiplier = 1.5
        elif time_difference < 0.5:    # Close
            time_multiplier = 1.2
        elif time_difference < 2.0:    # Moderate
            time_multiplier = 1.0
        else:                          # Large
            time_multiplier = 0.7
        
        return base_k * time_multiplier * recency_weight
