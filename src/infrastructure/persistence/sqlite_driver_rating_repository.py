"""SQLite implementation of the driver rating repository."""

import sqlite3
from datetime import datetime
from typing import List, Optional
from ...domain.entities.driver_rating import DriverRating
from ...domain.interfaces.driver_rating_repository import DriverRatingRepository


class SQLiteDriverRatingRepository(DriverRatingRepository):
    """SQLite implementation of driver rating repository."""
    
    def __init__(self, db_path: str = "data/f1_lap_bot.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS driver_ratings (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    current_elo INTEGER NOT NULL DEFAULT 1500,
                    peak_elo INTEGER NOT NULL DEFAULT 1500,
                    matches_played INTEGER NOT NULL DEFAULT 0,
                    wins INTEGER NOT NULL DEFAULT 0,
                    losses INTEGER NOT NULL DEFAULT 0,
                    last_updated TEXT NOT NULL
                )
            """)
            conn.commit()
    
    async def save(self, driver_rating: DriverRating) -> None:
        """Save or update a driver rating."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO driver_ratings 
                (user_id, username, current_elo, peak_elo, matches_played, wins, losses, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                driver_rating.user_id,
                driver_rating.username,
                driver_rating.current_elo,
                driver_rating.peak_elo,
                driver_rating.matches_played,
                driver_rating.wins,
                driver_rating.losses,
                driver_rating.last_updated.isoformat()
            ))
            conn.commit()
    
    async def find_by_user_id(self, user_id: str) -> Optional[DriverRating]:
        """Find driver rating by user ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, current_elo, peak_elo, matches_played, 
                       wins, losses, last_updated
                FROM driver_ratings 
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return DriverRating(
                user_id=row[0],
                username=row[1],
                current_elo=row[2],
                peak_elo=row[3],
                matches_played=row[4],
                wins=row[5],
                losses=row[6],
                last_updated=datetime.fromisoformat(row[7])
            )
    
    async def find_all_ratings(self) -> List[DriverRating]:
        """Find all driver ratings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, current_elo, peak_elo, matches_played, 
                       wins, losses, last_updated
                FROM driver_ratings
                ORDER BY current_elo DESC
            """)
            
            ratings = []
            for row in cursor.fetchall():
                ratings.append(DriverRating(
                    user_id=row[0],
                    username=row[1],
                    current_elo=row[2],
                    peak_elo=row[3],
                    matches_played=row[4],
                    wins=row[5],
                    losses=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                ))
            
            return ratings
    
    async def find_top_ratings(self, limit: int = 10) -> List[DriverRating]:
        """Find top driver ratings by ELO."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, current_elo, peak_elo, matches_played, 
                       wins, losses, last_updated
                FROM driver_ratings
                ORDER BY current_elo DESC
                LIMIT ?
            """, (limit,))
            
            ratings = []
            for row in cursor.fetchall():
                ratings.append(DriverRating(
                    user_id=row[0],
                    username=row[1],
                    current_elo=row[2],
                    peak_elo=row[3],
                    matches_played=row[4],
                    wins=row[5],
                    losses=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                ))
            
            return ratings
    
    async def get_user_rank(self, user_id: str) -> Optional[int]:
        """Get the rank of a specific user based on ELO."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM driver_ratings
                WHERE current_elo > (
                    SELECT current_elo 
                    FROM driver_ratings 
                    WHERE user_id = ?
                )
            """, (user_id,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                # Check if user exists in database
                cursor.execute("SELECT 1 FROM driver_ratings WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    return result[0]
            
            return None
    
    async def update_username(self, user_id: str, new_username: str) -> bool:
        """Update the username for a driver rating."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE driver_ratings SET username = ? WHERE user_id = ?",
                    (new_username, user_id)
                )
                conn.commit()
                
                # Return True if at least one row was updated
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ Error updating username in driver ratings: {e}")
            return False
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete a driver rating by user ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM driver_ratings WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    async def reset_all_data(self) -> bool:
        """Reset all driver rating data in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Delete all records from the driver_ratings table
                cursor.execute("DELETE FROM driver_ratings")
                conn.commit()
                
                # Reset the auto-increment counter if using INTEGER PRIMARY KEY
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='driver_ratings'")
                conn.commit()
                
            return True
            
        except Exception as e:
            print(f"❌ Error resetting driver rating data: {e}")
            return False
