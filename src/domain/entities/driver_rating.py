"""Domain entity representing a driver's ELO rating for time trial performance."""
from datetime import datetime
from typing import Optional


class DriverRating:
    """Rich domain entity for driver ELO ratings with time trial specific logic."""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        current_elo: int = 1500,
        peak_elo: Optional[int] = None,
        matches_played: int = 0,
        wins: int = 0,
        losses: int = 0,
        last_updated: Optional[datetime] = None
    ):
        self._user_id = user_id
        self._username = username
        self._current_elo = current_elo
        self._peak_elo = peak_elo or current_elo
        self._matches_played = matches_played
        self._wins = wins
        self._losses = losses
        self._last_updated = last_updated or datetime.utcnow()
    
    @property
    def user_id(self) -> str:
        return self._user_id
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def current_elo(self) -> int:
        return self._current_elo
    
    @property
    def peak_elo(self) -> int:
        return self._peak_elo
    
    @property
    def matches_played(self) -> int:
        return self._matches_played
    
    @property
    def wins(self) -> int:
        return self._wins
    
    @property
    def losses(self) -> int:
        return self._losses
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self._matches_played == 0:
            return 0.0
        return (self._wins / self._matches_played) * 100.0
    
    @property
    def last_updated(self) -> datetime:
        return self._last_updated
    
    @property
    def skill_level(self) -> str:
        """Determine skill level based on ELO rating."""
        if self._current_elo >= 2200:
            return "Legendary"
        elif self._current_elo >= 2000:
            return "Master"
        elif self._current_elo >= 1800:
            return "Expert"
        elif self._current_elo >= 1600:
            return "Advanced"
        elif self._current_elo >= 1400:
            return "Intermediate"
        elif self._current_elo >= 1200:
            return "Novice"
        else:
            return "Beginner"
    
    def update_after_matches(self, elo_change: float, wins_added: int, losses_added: int):
        """Update rating after virtual matches."""
        self._current_elo = max(800, int(self._current_elo + elo_change))  # Minimum ELO floor
        self._matches_played += wins_added + losses_added
        self._wins += wins_added
        self._losses += losses_added
        self._last_updated = datetime.utcnow()
        
        # Update peak if current is higher
        if self._current_elo > self._peak_elo:
            self._peak_elo = self._current_elo
    
    def calculate_expected_score(self, opponent_elo: int) -> float:
        """Calculate expected score against opponent using ELO formula."""
        return 1.0 / (1.0 + 10.0 ** ((opponent_elo - self._current_elo) / 400.0))
    
    def get_elo_trend(self, days: int = 30) -> int:
        """Get ELO trend over specified days (placeholder for future implementation)."""
        # This would be implemented with historical ELO tracking
        return 0
    
    def __str__(self) -> str:
        return f"{self._username}: {self._current_elo} ELO ({self.skill_level})"
    
    def __repr__(self) -> str:
        return f"DriverRating(user_id='{self._user_id}', elo={self._current_elo}, skill='{self.skill_level}')"
