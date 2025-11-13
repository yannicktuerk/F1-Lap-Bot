"""Service layer for analytics calculations and data aggregation."""
import statistics
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from ...domain.entities.lap_time import LapTime
from ...domain.value_objects.track_name import TrackName


class AnalyticsService:
    """Service for calculating analytics and aggregating data efficiently."""
    
    @staticmethod
    def calculate_track_leaders(track_data: Dict) -> Dict[str, int]:
        """
        Calculate how many tracks each driver leads.
        
        Args:
            track_data: Dictionary with track data containing 'best' lap time
            
        Returns:
            Dictionary mapping driver names to number of tracks they lead
        """
        track_leaders = defaultdict(int)
        for data in track_data.values():
            if 'best' in data:
                track_leaders[data['best'].username] += 1
        return dict(track_leaders)
    
    @staticmethod
    def get_fastest_times(all_times: List[LapTime], limit: int = 5) -> List[LapTime]:
        """
        Get the fastest lap times across all tracks.
        
        Args:
            all_times: List of all lap times
            limit: Maximum number of times to return
            
        Returns:
            List of fastest lap times
        """
        return sorted(all_times, key=lambda x: x.time_format.total_seconds)[:limit]
    
    @staticmethod
    def calculate_track_difficulty(track_data: Dict, min_laps: int = 3) -> List[Tuple[str, float, float]]:
        """
        Calculate track difficulty based on average time and consistency.
        
        Args:
            track_data: Dictionary with track statistics
            min_laps: Minimum number of laps required for difficulty calculation
            
        Returns:
            List of tuples (track_key, difficulty_score, avg_time)
        """
        difficulty_scores = []
        
        for track_key, data in track_data.items():
            if data['count'] >= min_laps:
                times = [t.time_format.total_seconds for t in data['times']]
                std_dev = statistics.stdev(times) if len(times) > 1 else 0
                difficulty_score = data['avg'] + (std_dev * 2)
                difficulty_scores.append((track_key, difficulty_score, data['avg']))
        
        return sorted(difficulty_scores, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def calculate_consistency(user_performance: Dict[str, List[float]], min_laps: int = 5) -> List[Tuple[str, float, int]]:
        """
        Calculate driver consistency scores.
        
        Args:
            user_performance: Dictionary mapping usernames to lists of lap times
            min_laps: Minimum number of laps required for consistency calculation
            
        Returns:
            List of tuples (username, consistency_score, lap_count)
        """
        consistency_data = []
        
        for username, times in user_performance.items():
            if len(times) >= min_laps:
                std_dev = statistics.stdev(times)
                avg_time = statistics.mean(times)
                consistency_score = 100 - (std_dev / avg_time * 100)
                consistency_data.append((username, consistency_score, len(times)))
        
        return sorted(consistency_data, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def get_most_active_drivers(user_performance: Dict[str, List[float]], limit: int = 5) -> List[Tuple[str, int]]:
        """
        Get the most active drivers by lap count.
        
        Args:
            user_performance: Dictionary mapping usernames to lists of lap times
            limit: Maximum number of drivers to return
            
        Returns:
            List of tuples (username, lap_count)
        """
        activity_data = [(username, len(times)) for username, times in user_performance.items()]
        return sorted(activity_data, key=lambda x: x[1], reverse=True)[:limit]
    
    @staticmethod
    def calculate_rivalries(
        user_track_times: Dict[str, Dict[str, LapTime]],
        all_track_keys: List[str],
        min_battles: int = 3
    ) -> Dict[Tuple[str, str], Dict]:
        """
        Calculate head-to-head rivalries between drivers.
        
        Args:
            user_track_times: Nested dictionary {username: {track_key: LapTime}}
            all_track_keys: List of all track keys
            min_battles: Minimum number of head-to-head battles required
            
        Returns:
            Dictionary mapping driver pairs to rivalry statistics
        """
        rivalries = {}
        usernames = list(user_track_times.keys())
        
        for i, user1 in enumerate(usernames):
            for user2 in usernames[i+1:]:
                battles = 0
                user1_wins = 0
                user2_wins = 0
                
                # Check each track where both have times
                for track_key in all_track_keys:
                    user1_time = user_track_times[user1].get(track_key)
                    user2_time = user_track_times[user2].get(track_key)
                    
                    if user1_time and user2_time:
                        battles += 1
                        if user1_time.is_faster_than(user2_time):
                            user1_wins += 1
                        else:
                            user2_wins += 1
                
                if battles >= min_battles:
                    rivalry_key = tuple(sorted([user1, user2]))
                    rivalries[rivalry_key] = {
                        'battles': battles,
                        'user1': user1 if user1 == rivalry_key[0] else user2,
                        'user2': user2 if user1 == rivalry_key[0] else user1,
                        'user1_wins': user1_wins if user1 == rivalry_key[0] else user2_wins,
                        'user2_wins': user2_wins if user1 == rivalry_key[0] else user1_wins
                    }
        
        return rivalries
    
    @staticmethod
    def build_user_track_times(all_track_keys: List[str], times_getter) -> Dict[str, Dict[str, LapTime]]:
        """
        Build a nested dictionary of each user's best time per track.
        This is a helper to prepare data for rivalry calculations.
        
        Args:
            all_track_keys: List of all track keys
            times_getter: Async function that takes track_key and returns list of times
            
        Returns:
            Dictionary {username: {track_key: best_lap_time}}
        """
        # Note: This needs to be called from an async context
        # Left as a helper structure for now
        pass
    
    @staticmethod
    def aggregate_user_performance(all_times: List[LapTime]) -> Dict[str, List[float]]:
        """
        Aggregate all lap times by user for performance analysis.
        
        Args:
            all_times: List of all lap times
            
        Returns:
            Dictionary mapping usernames to lists of lap times in seconds
        """
        user_performance = defaultdict(list)
        for lap_time in all_times:
            user_performance[lap_time.username].append(lap_time.time_format.total_seconds)
        return dict(user_performance)
    
    @staticmethod
    def get_unique_drivers(all_times: List[LapTime]) -> Set[str]:
        """
        Get set of unique driver IDs from lap times.
        
        Args:
            all_times: List of all lap times
            
        Returns:
            Set of unique user IDs
        """
        return {lap_time.user_id for lap_time in all_times}
