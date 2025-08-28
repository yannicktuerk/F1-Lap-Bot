"""SQLite implementation of the CornerReferenceRepository interface."""
import sqlite3
import aiosqlite
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from ...domain.interfaces.corner_reference_repository import (
    CornerReferenceRepository, CornerReference
)
from ...domain.value_objects.track_name import TrackName


class SQLiteCornerReferenceRepository(CornerReferenceRepository):
    """SQLite adapter implementing the CornerReferenceRepository port."""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
            # Auto-detect database location - prioritize project root
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..", "..", "..")
            possible_paths = [
                os.path.join(project_root, "f1_lap_bot.db"),  # Project root (server location)
                os.path.join(project_root, "data", "f1_lap_bot.db"),  # data folder (local dev)
            ]
            
            # Use the first path that exists, or default to project root
            for path in possible_paths:
                if os.path.exists(path):
                    self._database_path = path
                    break
            else:
                # Default to project root if none exist yet
                self._database_path = possible_paths[0]
        else:
            self._database_path = database_path
    
    async def _ensure_table_exists(self):
        """Create the corner_references table if it doesn't exist."""
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS corner_references (
                    reference_id TEXT PRIMARY KEY,
                    track_id INTEGER NOT NULL,
                    corner_id INTEGER NOT NULL,
                    median_time_ms REAL NOT NULL,
                    iqr_ms REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    assists_filter TEXT NOT NULL,
                    device_filter TEXT NOT NULL,
                    preferred_line TEXT,
                    last_updated TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for better query performance
            await db.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_corner_unique 
                ON corner_references(track_id, corner_id, assists_filter, device_filter)
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_corner_track ON corner_references(track_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_corner_updated ON corner_references(last_updated)")
            
            await db.commit()
    
    async def save_reference(self, reference: CornerReference) -> str:
        """Save a corner reference and return the generated ID."""
        await self._ensure_table_exists()
        
        reference_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        try:
            async with aiosqlite.connect(self._database_path) as db:
                # Check if reference already exists (upsert behavior)
                existing_cursor = await db.execute("""
                    SELECT reference_id FROM corner_references 
                    WHERE track_id = ? AND corner_id = ? AND assists_filter = ? AND device_filter = ?
                """, (reference.track_id, reference.corner_id, reference.assists_filter, reference.device_filter))
                existing_row = await existing_cursor.fetchone()
                
                if existing_row:
                    # Update existing reference
                    await db.execute("""
                        UPDATE corner_references SET
                            median_time_ms = ?, iqr_ms = ?, sample_count = ?,
                            preferred_line = ?, last_updated = ?
                        WHERE reference_id = ?
                    """, (
                        reference.median_time_ms,
                        reference.iqr_ms,
                        reference.sample_count,
                        reference.preferred_line,
                        now,
                        existing_row[0]
                    ))
                    reference_id = existing_row[0]
                else:
                    # Insert new reference
                    await db.execute("""
                        INSERT INTO corner_references (
                            reference_id, track_id, corner_id, median_time_ms, iqr_ms,
                            sample_count, assists_filter, device_filter, preferred_line,
                            last_updated, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reference_id,
                        reference.track_id,
                        reference.corner_id,
                        reference.median_time_ms,
                        reference.iqr_ms,
                        reference.sample_count,
                        reference.assists_filter,
                        reference.device_filter,
                        reference.preferred_line,
                        now,
                        now
                    ))
                
                await db.commit()
                
        except Exception as save_error:
            print(f"❌ CORNER REFERENCE REPOSITORY: Save error: {save_error}")
            raise
        
        return reference_id
    
    async def find_by_corner(
        self, 
        track: TrackName, 
        corner_id: int,
        assists_filter: str,
        device_filter: str
    ) -> Optional[CornerReference]:
        """Find corner reference by track, corner, and filters."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM corner_references 
                WHERE track_id = ? AND corner_id = ? AND assists_filter = ? AND device_filter = ?
            """, (track.id, corner_id, assists_filter, device_filter))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_corner_reference(row)
    
    async def find_all_by_track(
        self, 
        track: TrackName,
        assists_filter: str,
        device_filter: str
    ) -> List[CornerReference]:
        """Find all corner references for a track with given filters."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM corner_references 
                WHERE track_id = ? AND assists_filter = ? AND device_filter = ?
                ORDER BY corner_id ASC
            """, (track.id, assists_filter, device_filter))
            rows = await cursor.fetchall()
            
            return [self._row_to_corner_reference(row) for row in rows]
    
    async def update_reference(
        self,
        track: TrackName,
        corner_id: int,
        assists_filter: str,
        device_filter: str,
        median_time_ms: float,
        iqr_ms: float,
        sample_count: int
    ) -> bool:
        """Update an existing corner reference."""
        await self._ensure_table_exists()
        
        try:
            async with aiosqlite.connect(self._database_path) as db:
                cursor = await db.execute("""
                    UPDATE corner_references SET
                        median_time_ms = ?, iqr_ms = ?, sample_count = ?, last_updated = ?
                    WHERE track_id = ? AND corner_id = ? AND assists_filter = ? AND device_filter = ?
                """, (
                    median_time_ms, iqr_ms, sample_count, datetime.now().isoformat(),
                    track.id, corner_id, assists_filter, device_filter
                ))
                await db.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ Error updating corner reference: {e}")
            return False
    
    async def get_corner_statistics(self, track: TrackName) -> Dict[str, any]:
        """Get corner statistics for a track."""
        await self._ensure_table_exists()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Total corners with references
            cursor = await db.execute("""
                SELECT COUNT(DISTINCT corner_id) FROM corner_references WHERE track_id = ?
            """, (track.id,))
            total_corners = (await cursor.fetchone())[0]
            
            # Total references (across all filter combinations)
            cursor = await db.execute("""
                SELECT COUNT(*) FROM corner_references WHERE track_id = ?
            """, (track.id,))
            total_references = (await cursor.fetchone())[0]
            
            # Average sample count
            cursor = await db.execute("""
                SELECT AVG(sample_count) FROM corner_references WHERE track_id = ?
            """, (track.id,))
            avg_sample_count = (await cursor.fetchone())[0] or 0
            
            # Most recent update
            cursor = await db.execute("""
                SELECT MAX(last_updated) FROM corner_references WHERE track_id = ?
            """, (track.id,))
            most_recent_update = (await cursor.fetchone())[0]
            
            return {
                'total_corners': total_corners,
                'total_references': total_references,
                'avg_sample_count': avg_sample_count,
                'most_recent_update': most_recent_update
            }
    
    async def delete_old_references(self, days_old: int) -> int:
        """Delete corner references older than specified days."""
        await self._ensure_table_exists()
        
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                DELETE FROM corner_references WHERE last_updated < ?
            """, (cutoff_date,))
            await db.commit()
            
            return cursor.rowcount
    
    def _row_to_corner_reference(self, row: aiosqlite.Row) -> CornerReference:
        """Convert a database row to a CornerReference entity."""
        try:
            last_updated = None
            if row['last_updated']:
                last_updated = datetime.fromisoformat(row['last_updated'])
            
            return CornerReference(
                track_id=row['track_id'],
                corner_id=row['corner_id'],
                median_time_ms=row['median_time_ms'],
                iqr_ms=row['iqr_ms'],
                sample_count=row['sample_count'],
                assists_filter=row['assists_filter'],
                device_filter=row['device_filter'],
                preferred_line=row['preferred_line'],
                last_updated=last_updated
            )
        except (KeyError, ValueError) as e:
            reference_id = row['reference_id'] if 'reference_id' in row.keys() else "Unknown"
            print(f"Error converting row to CornerReference for reference_id={reference_id}: {e}")
            raise ValueError(f"Corrupt corner reference data for reference_id={reference_id}") from e