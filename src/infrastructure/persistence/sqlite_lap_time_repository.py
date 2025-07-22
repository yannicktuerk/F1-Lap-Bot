"""SQLite implementation of the LapTimeRepository interface."""
import sqlite3
import aiosqlite
import uuid
from datetime import datetime
from typing import List, Optional
from ...domain.entities.lap_time import LapTime
from ...domain.interfaces.lap_time_repository import LapTimeRepository
from ...domain.value_objects.time_format import TimeFormat
from ...domain.value_objects.track_name import TrackName


class SQLiteLapTimeRepository(LapTimeRepository):
    """SQLite adapter implementing the LapTimeRepository port."""
    
    def __init__(self, database_path: str = "lap_times.db"):
        self._database_path = database_path
    
    async def _ensure_table_exists(self):
        """Create the lap_times table if it doesn't exist."""
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS lap_times (
                    lap_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    track_key TEXT NOT NULL,
                    time_minutes INTEGER NOT NULL,
                    time_seconds INTEGER NOT NULL,
                    time_milliseconds INTEGER NOT NULL,
                    total_milliseconds INTEGER NOT NULL,
                    is_personal_best BOOLEAN DEFAULT 0,
                    is_overall_best BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for better query performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_track_time ON lap_times(track_key, total_milliseconds)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_track ON lap_times(user_id, track_key)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON lap_times(created_at DESC)")
            
            await db.commit()
    
    async def save(self, lap_time: LapTime) -> str:
        """Save a lap time and return the generated ID."""
        await self._ensure_table_exists()
        
        lap_id = str(uuid.uuid4())
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO lap_times (
                    lap_id, user_id, username, track_key,
                    time_minutes, time_seconds, time_milliseconds, total_milliseconds,
                    is_personal_best, is_overall_best, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lap_id,
                lap_time.user_id,
                lap_time.username,
                lap_time.track_name.key,
                lap_time.time_format.minutes,
                lap_time.time_format.seconds,
                lap_time.time_format.milliseconds,
                lap_time.time_format.total_milliseconds,
                lap_time.is_personal_best,
                lap_time.is_overall_best,
                lap_time.created_at.isoformat()
            ))
            await db.commit()
        
        return lap_id
    
    async def find_by_id(self, lap_id: str) -> Optional[LapTime]:
        """Find a lap time by its ID."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM lap_times WHERE lap_id = ?", (lap_id,)
            )
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_lap_time(row)
    
    async def find_best_by_track(self, track: TrackName) -> Optional[LapTime]:
        """Find the best (fastest) lap time for a specific track."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE track_key = ? 
                ORDER BY total_milliseconds ASC 
                LIMIT 1
            """, (track.key,))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_lap_time(row)
    
    async def find_user_best_by_track(self, user_id: str, track: TrackName) -> Optional[LapTime]:
        """Find the best lap time for a specific user on a specific track."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE user_id = ? AND track_key = ?
                ORDER BY total_milliseconds ASC 
                LIMIT 1
            """, (user_id, track.key))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_lap_time(row)
    
    async def find_top_by_track(self, track: TrackName, limit: int = 10) -> List[LapTime]:
        """Find the top lap times for a specific track (absolute fastest times, not best per user)."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE track_key = ?
                ORDER BY total_milliseconds ASC 
                LIMIT ?
            """, (track.key, limit))
            rows = await cursor.fetchall()
            
            return [self._row_to_lap_time(row) for row in rows]
    
    async def find_all_by_user(self, user_id: str) -> List[LapTime]:
        """Find all lap times for a specific user."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = await cursor.fetchall()
            
            return [self._row_to_lap_time(row) for row in rows]
    
    async def find_recent_by_track(self, track: TrackName, limit: int = 10) -> List[LapTime]:
        """Find recent lap times for a specific track."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE track_key = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (track.key, limit))
            rows = await cursor.fetchall()
            
            return [self._row_to_lap_time(row) for row in rows]
    
    async def get_user_statistics(self, user_id: str) -> dict:
        """Get statistics for a specific user."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Total laps
            cursor = await db.execute("SELECT COUNT(*) FROM lap_times WHERE user_id = ?", (user_id,))
            total_laps = (await cursor.fetchone())[0]
            
            # Personal bests count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM lap_times WHERE user_id = ? AND is_personal_best = 1", 
                (user_id,)
            )
            personal_bests = (await cursor.fetchone())[0]
            
            # Overall bests count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM lap_times WHERE user_id = ? AND is_overall_best = 1", 
                (user_id,)
            )
            overall_bests = (await cursor.fetchone())[0]
            
            # Average time (across all tracks)
            cursor = await db.execute(
                "SELECT AVG(total_milliseconds) FROM lap_times WHERE user_id = ?", 
                (user_id,)
            )
            avg_time_ms = (await cursor.fetchone())[0]
            avg_time_seconds = avg_time_ms / 1000.0 if avg_time_ms else 0
            
            return {
                'total_laps': total_laps,
                'personal_bests': personal_bests,
                'overall_bests': overall_bests,
                'average_time_seconds': avg_time_seconds
            }
    
    async def get_track_statistics(self, track: TrackName) -> dict:
        """Get statistics for a specific track."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Total laps on track
            cursor = await db.execute("SELECT COUNT(*) FROM lap_times WHERE track_key = ?", (track.key,))
            total_laps = (await cursor.fetchone())[0]
            
            # Unique drivers
            cursor = await db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM lap_times WHERE track_key = ?", 
                (track.key,)
            )
            unique_drivers = (await cursor.fetchone())[0]
            
            # Best time
            cursor = await db.execute(
                "SELECT MIN(total_milliseconds) FROM lap_times WHERE track_key = ?", 
                (track.key,)
            )
            best_time_ms = (await cursor.fetchone())[0]
            best_time_seconds = best_time_ms / 1000.0 if best_time_ms else 0
            
            # Average time
            cursor = await db.execute(
                "SELECT AVG(total_milliseconds) FROM lap_times WHERE track_key = ?", 
                (track.key,)
            )
            avg_time_ms = (await cursor.fetchone())[0]
            avg_time_seconds = avg_time_ms / 1000.0 if avg_time_ms else 0
            
            return {
                'total_laps': total_laps,
                'unique_drivers': unique_drivers,
                'best_time_seconds': best_time_seconds,
                'average_time_seconds': avg_time_seconds
            }
    
    def _row_to_lap_time(self, row) -> LapTime:
        """Convert a database row to a LapTime entity."""
        # Reconstruct the time format from components
        time_string = f"{row['time_minutes']}:{row['time_seconds']:02d}.{row['time_milliseconds']:03d}"
        if row['time_minutes'] == 0:
            time_string = f"{row['time_seconds']}.{row['time_milliseconds']:03d}"
        
        time_format = TimeFormat(time_string)
        track_name = TrackName(row['track_key'])
        
        lap_time = LapTime(
            user_id=row['user_id'],
            username=row['username'],
            time_format=time_format,
            track_name=track_name,
            lap_id=row['lap_id'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
        
        if row['is_personal_best']:
            lap_time.mark_as_personal_best()
        
        if row['is_overall_best']:
            lap_time.mark_as_overall_best()
        
        return lap_time
    
    async def delete_lap_time(self, lap_id: str) -> bool:
        """Delete a lap time by ID. Returns True if successful."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("DELETE FROM lap_times WHERE lap_id = ?", (lap_id,))
            await db.commit()
            
            # Return True if a row was actually deleted
            return cursor.rowcount > 0
    
    async def find_user_times_by_track(self, user_id: str, track: TrackName) -> List[LapTime]:
        """Find all lap times for a user on a specific track, ordered by most recent first."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE user_id = ? AND track_key = ?
                ORDER BY created_at DESC
            """, (user_id, track.key))
            rows = await cursor.fetchall()
            
            return [self._row_to_lap_time(row) for row in rows]
    
    async def find_specific_lap_time(self, user_id: str, track: TrackName, total_milliseconds: int) -> Optional[LapTime]:
        """Find a specific lap time for a user on a track with exact time match."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM lap_times 
                WHERE user_id = ? AND track_key = ? AND total_milliseconds = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, track.key, total_milliseconds))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_lap_time(row)
    
    async def delete_all_user_times_by_track(self, user_id: str, track: TrackName) -> int:
        """Delete all lap times for a user on a specific track. Returns number of deleted records."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute(
                "DELETE FROM lap_times WHERE user_id = ? AND track_key = ?", 
                (user_id, track.key)
            )
            await db.commit()
            
            return cursor.rowcount
    
    async def reset_all_data(self) -> bool:
        """Reset all lap time data in the database."""
        try:
            await self._ensure_table_exists()
            
            async with aiosqlite.connect(self._database_path) as db:
                # Delete all records from the lap_times table
                await db.execute("DELETE FROM lap_times")
                await db.commit()
                
                # Optionally reset the auto-increment counter if using INTEGER PRIMARY KEY
                # This is not needed for our UUID-based lap_id, but good practice for cleanup
                await db.execute("DELETE FROM sqlite_sequence WHERE name='lap_times'")
                await db.commit()
                
            return True
            
        except Exception as e:
            print(f"❌ Error resetting lap time data: {e}")
            return False
