#!/usr/bin/env python3
"""
Script to calculate ELO ratings based on existing lap times.
This simulates the ELO system by processing all lap times chronologically.
"""

import sqlite3
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class DriverRating:
    def __init__(self, user_id: str, username: str, current_elo: int = 1500):
        self.user_id = user_id
        self.username = username
        self.current_elo = current_elo
        self.peak_elo = current_elo
        self.matches_played = 0
        self.wins = 0
        self.losses = 0
        self.last_updated = datetime.now()
    
    def calculate_expected_score(self, opponent_elo: int) -> float:
        """Calculate expected score against opponent using ELO formula."""
        return 1.0 / (1.0 + 10.0 ** ((opponent_elo - self.current_elo) / 400.0))
    
    def update_after_match(self, opponent_elo: int, won: bool, k_factor: int = 32):
        """Update ELO after a match."""
        expected = self.calculate_expected_score(opponent_elo)
        actual = 1.0 if won else 0.0
        
        # Calculate ELO change
        elo_change = k_factor * (actual - expected)
        self.current_elo = max(800, int(self.current_elo + elo_change))  # Min ELO 800
        
        # Update statistics
        self.matches_played += 1
        if won:
            self.wins += 1
        else:
            self.losses += 1
        
        # Update peak
        if self.current_elo > self.peak_elo:
            self.peak_elo = self.current_elo
        
        self.last_updated = datetime.now()

def load_lap_times() -> List[Tuple]:
    """Load all lap times ordered chronologically."""
    conn = sqlite3.connect('data/lap_times.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, track_key, total_milliseconds, created_at
        FROM lap_times 
        ORDER BY created_at ASC
    """)
    
    lap_times = cursor.fetchall()
    conn.close()
    
    return lap_times

def save_driver_rating(rating: DriverRating):
    """Save a driver rating to the database."""
    conn = sqlite3.connect('data/f1_lap_bot.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO driver_ratings 
        (user_id, username, current_elo, peak_elo, matches_played, wins, losses, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rating.user_id,
        rating.username,
        rating.current_elo,
        rating.peak_elo,
        rating.matches_played,
        rating.wins,
        rating.losses,
        rating.last_updated.isoformat()
    ))
    
    conn.commit()
    conn.close()

def calculate_elo_ratings():
    """Calculate ELO ratings for all drivers based on lap times."""
    print("🔄 Calculating ELO ratings based on lap times...")
    
    # Load all lap times
    lap_times = load_lap_times()
    
    # Initialize driver ratings
    drivers: Dict[str, DriverRating] = {}
    
    # Process lap times chronologically
    processed = 0
    for user_id, username, track_key, total_ms, created_at in lap_times:
        # Initialize driver if not exists
        if user_id not in drivers:
            drivers[user_id] = DriverRating(user_id, username)
            print(f"📊 Initialized {username} with 1500 ELO")
        
        # Find all other drivers who have times on this track
        # Create virtual matches against them
        track_drivers = []
        for other_user_id, other_rating in drivers.items():
            if other_user_id != user_id:
                # Check if other driver has a time on this track
                # (This is a simplified approach - we assume they compete against all active drivers)
                track_drivers.append(other_rating)
        
        # Simulate matches against other drivers based on relative performance
        current_driver = drivers[user_id]
        
        for opponent in track_drivers:
            # Determine who wins based on their track performance
            # This is simplified - we assume the better overall ELO wins slightly more often
            
            # Use current ELO as proxy for performance
            win_probability = current_driver.calculate_expected_score(opponent.current_elo)
            
            # Add some randomness based on track time (better times = slightly higher win chance)
            # Normalize time performance (faster = better)
            time_bonus = max(0, min(0.2, (120000 - total_ms) / 500000))  # Small bonus for faster times
            adjusted_win_prob = min(0.9, max(0.1, win_probability + time_bonus))
            
            # Simulate match result
            import random
            won = random.random() < adjusted_win_prob
            
            # Update both drivers
            current_driver.update_after_match(opponent.current_elo, won)
            opponent.update_after_match(current_driver.current_elo, not won)
        
        processed += 1
        if processed % 10 == 0:
            print(f"⚡ Processed {processed}/{len(lap_times)} lap times...")
    
    # Save all driver ratings
    print("💾 Saving ELO ratings to database...")
    for driver in drivers.values():
        save_driver_rating(driver)
        skill_level = get_skill_level(driver.current_elo)
        print(f"🏁 {driver.username}: {driver.current_elo} ELO ({skill_level}) - {driver.wins}W/{driver.losses}L")
    
    print(f"✅ ELO calculation complete! Processed {len(drivers)} drivers.")

def get_skill_level(elo: int) -> str:
    """Get skill level based on ELO rating."""
    if elo >= 2200:
        return "Legendary 👑"
    elif elo >= 2000:
        return "Master 🔥"
    elif elo >= 1800:
        return "Expert ⚡"
    elif elo >= 1600:
        return "Advanced 🎯"
    elif elo >= 1400:
        return "Intermediate 📈"
    elif elo >= 1200:
        return "Novice 🌱"
    else:
        return "Beginner 🏁"

if __name__ == "__main__":
    calculate_elo_ratings()
