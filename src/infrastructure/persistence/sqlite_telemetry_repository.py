"""SQLite implementation of ITelemetryRepository interface.

This module provides the concrete adapter for telemetry data persistence using
SQLite with aiosqlite for async operations. It implements all methods defined
in ITelemetryRepository interface.

Architecture:
- Infrastructure layer adapter (Clean Architecture)
- Maps between domain entities and database rows
- Handles SQLite-specific concerns (foreign keys, transactions, NULL handling)
- Enforces referential integrity via foreign key constraints
"""

import aiosqlite
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.interfaces.telemetry_repository import ITelemetryRepository
from ...domain.entities.lap_trace import LapTrace
from ...domain.entities.car_setup_snapshot import CarSetupSnapshot
from ...domain.value_objects.telemetry_sample import TelemetrySample


class SQLiteTelemetryRepository(ITelemetryRepository):
    """SQLite adapter implementing ITelemetryRepository port.
    
    Provides persistence for telemetry data using SQLite with foreign key
    enforcement and transaction support.
    """
    
    def __init__(self, database_path: Optional[str] = None):
        """Initialize repository with database path.
        
        Args:
            database_path: Path to SQLite database file. If None, uses default
                         location (telemetry.db in project root).
        """
        if database_path is None:
            # Default: telemetry.db in project root
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent.parent
            self._database_path = str(project_root / "telemetry.db")
        else:
            self._database_path = database_path
    
    # =========================================================================
    # LapTrace Operations
    # =========================================================================
    
    async def save_lap_trace(self, lap_trace: LapTrace) -> None:
        """Persist complete lap trace with all telemetry samples.
        
        Saves lap metadata and all telemetry samples in a single transaction.
        If lap has an associated car setup, saves the setup first.
        
        Args:
            lap_trace: LapTrace entity to persist.
            
        Raises:
            Exception: If save operation fails (transaction rolled back).
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            try:
                # Save car setup if present
                if lap_trace.car_setup is not None:
                    await self._save_setup_internal(db, lap_trace.car_setup)
                
                # Save lap metadata
                await db.execute("""
                    INSERT INTO lap_metadata (
                        trace_id, session_uid, setup_id, track_id,
                        lap_number, car_index, lap_time_ms, is_valid, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lap_trace.trace_id,
                    lap_trace.session_uid,
                    lap_trace.car_setup.setup_id if lap_trace.car_setup else None,
                    lap_trace.track_id,
                    lap_trace.lap_number,
                    lap_trace.car_index,
                    lap_trace.lap_time_ms,
                    1 if lap_trace.is_valid else 0,
                    lap_trace.created_at.isoformat()
                ))
                
                # Save all telemetry samples
                samples = lap_trace.get_samples()
                if samples:
                    await db.executemany("""
                        INSERT INTO lap_telemetry (
                            trace_id, timestamp_ms, lap_distance,
                            world_position_x, world_position_y, world_position_z,
                            world_velocity_x, world_velocity_y, world_velocity_z,
                            g_force_lateral, g_force_longitudinal, yaw,
                            speed, throttle, steer, brake, gear, engine_rpm, drs,
                            lap_number
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        (
                            lap_trace.trace_id,
                            sample.timestamp_ms,
                            sample.lap_distance,
                            sample.world_position_x,
                            sample.world_position_y,
                            sample.world_position_z,
                            sample.world_velocity_x,
                            sample.world_velocity_y,
                            sample.world_velocity_z,
                            sample.g_force_lateral,
                            sample.g_force_longitudinal,
                            sample.yaw,
                            sample.speed,
                            sample.throttle,
                            sample.steer,
                            sample.brake,
                            sample.gear,
                            sample.engine_rpm,
                            sample.drs,
                            sample.lap_number
                        )
                        for sample in samples
                    ])
                
                await db.commit()
            
            except Exception as e:
                await db.rollback()
                raise Exception(f"Failed to save lap trace {lap_trace.trace_id}: {e}") from e
    
    async def get_lap_trace(self, trace_id: str) -> Optional[LapTrace]:
        """Retrieve complete lap trace by ID.
        
        Reconstructs LapTrace entity with all telemetry samples and car setup.
        
        Args:
            trace_id: UUID of the lap trace.
            
        Returns:
            LapTrace entity if found, None otherwise.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            # Get lap metadata
            cursor = await db.execute("""
                SELECT * FROM lap_metadata WHERE trace_id = ?
            """, (trace_id,))
            lap_row = await cursor.fetchone()
            
            if lap_row is None:
                return None
            
            # Get car setup if present
            car_setup = None
            if lap_row["setup_id"]:
                car_setup = await self._get_setup_internal(db, lap_row["setup_id"])
            
            # Get telemetry samples
            cursor = await db.execute("""
                SELECT * FROM lap_telemetry 
                WHERE trace_id = ? 
                ORDER BY timestamp_ms ASC
            """, (trace_id,))
            sample_rows = await cursor.fetchall()
            
            # Reconstruct LapTrace entity
            lap_trace = LapTrace(
                session_uid=lap_row["session_uid"],
                lap_number=lap_row["lap_number"],
                car_index=lap_row["car_index"],
                is_valid=bool(lap_row["is_valid"]),
                track_id=lap_row["track_id"],
                lap_time_ms=lap_row["lap_time_ms"],
                car_setup=car_setup,
                trace_id=lap_row["trace_id"],
                created_at=datetime.fromisoformat(lap_row["created_at"])
            )
            
            # Mark as complete if has lap time
            if lap_row["lap_time_ms"] is not None:
                lap_trace._is_complete = True
            
            # Add telemetry samples
            for sample_row in sample_rows:
                sample = self._row_to_telemetry_sample(sample_row)
                # Bypass validation by directly appending (samples already validated)
                lap_trace._samples.append(sample)
            
            return lap_trace
    
    async def get_latest_lap_trace(self, session_uid: int) -> Optional[LapTrace]:
        """Get most recent lap trace for a session.
        
        Args:
            session_uid: F1 25 session unique identifier.
            
        Returns:
            Most recent LapTrace for the session, or None if no laps exist.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT trace_id FROM lap_metadata
                WHERE session_uid = ?
                ORDER BY lap_number DESC
                LIMIT 1
            """, (session_uid,))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return await self.get_lap_trace(row["trace_id"])
    
    async def list_lap_traces(
        self,
        session_uid: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[LapTrace]:
        """List lap traces for a session with pagination.
        
        Args:
            session_uid: F1 25 session unique identifier.
            limit: Maximum number of laps to return.
            offset: Number of laps to skip for pagination.
            
        Returns:
            List of LapTrace entities ordered by lap_number desc.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT trace_id FROM lap_metadata
                WHERE session_uid = ?
                ORDER BY lap_number DESC
                LIMIT ? OFFSET ?
            """, (session_uid, limit, offset))
            rows = await cursor.fetchall()
            
            # Fetch complete lap traces
            lap_traces = []
            for row in rows:
                lap_trace = await self.get_lap_trace(row["trace_id"])
                if lap_trace:
                    lap_traces.append(lap_trace)
            
            return lap_traces
    
    async def list_lap_traces_by_track(
        self,
        track_id: str,
        limit: int = 100,
        valid_only: bool = True
    ) -> List[LapTrace]:
        """Get all lap traces for a specific track across all sessions.
        
        Args:
            track_id: F1 25 track identifier.
            limit: Maximum number of laps to return.
            valid_only: If True, return only valid laps.
            
        Returns:
            List of LapTrace entities for the track.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            if valid_only:
                cursor = await db.execute("""
                    SELECT trace_id FROM lap_metadata
                    WHERE track_id = ? AND is_valid = 1
                    ORDER BY lap_time_ms ASC
                    LIMIT ?
                """, (track_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT trace_id FROM lap_metadata
                    WHERE track_id = ?
                    ORDER BY lap_time_ms ASC
                    LIMIT ?
                """, (track_id, limit))
            
            rows = await cursor.fetchall()
            
            # Fetch complete lap traces
            lap_traces = []
            for row in rows:
                lap_trace = await self.get_lap_trace(row["trace_id"])
                if lap_trace:
                    lap_traces.append(lap_trace)
            
            return lap_traces
    
    async def get_fastest_lap_trace(
        self,
        track_id: Optional[str] = None,
        session_uid: Optional[int] = None
    ) -> Optional[LapTrace]:
        """Get fastest valid lap trace, optionally filtered.
        
        Args:
            track_id: Optional track filter.
            session_uid: Optional session filter.
            
        Returns:
            Fastest LapTrace matching filters, or None if no valid laps exist.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            conditions = ["is_valid = 1", "lap_time_ms IS NOT NULL"]
            params = []
            
            if track_id:
                conditions.append("track_id = ?")
                params.append(track_id)
            
            if session_uid:
                conditions.append("session_uid = ?")
                params.append(session_uid)
            
            where_clause = " AND ".join(conditions)
            
            cursor = await db.execute(f"""
                SELECT trace_id FROM lap_metadata
                WHERE {where_clause}
                ORDER BY lap_time_ms ASC
                LIMIT 1
            """, params)
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return await self.get_lap_trace(row["trace_id"])
    
    async def delete_lap_trace(self, trace_id: str) -> bool:
        """Delete lap trace and all associated telemetry samples.
        
        Args:
            trace_id: UUID of the lap trace to delete.
            
        Returns:
            True if lap was deleted, False if lap not found.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            cursor = await db.execute("""
                DELETE FROM lap_metadata WHERE trace_id = ?
            """, (trace_id,))
            await db.commit()
            
            return cursor.rowcount > 0
    
    # =========================================================================
    # CarSetupSnapshot Operations
    # =========================================================================
    
    async def save_setup_snapshot(self, setup: CarSetupSnapshot) -> None:
        """Persist car setup snapshot.
        
        Args:
            setup: CarSetupSnapshot entity to persist.
            
        Raises:
            Exception: If save operation fails.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await self._save_setup_internal(db, setup)
            await db.commit()
    
    async def _save_setup_internal(
        self, 
        db: aiosqlite.Connection, 
        setup: CarSetupSnapshot
    ) -> None:
        """Internal method to save setup within existing transaction."""
        await db.execute("""
            INSERT OR REPLACE INTO car_setups (
                setup_id, session_uid, timestamp_ms,
                front_wing, rear_wing,
                on_throttle, off_throttle,
                front_camber, rear_camber, front_toe, rear_toe,
                front_suspension, rear_suspension,
                front_anti_roll_bar, rear_anti_roll_bar,
                front_suspension_height, rear_suspension_height,
                brake_pressure, brake_bias, engine_braking,
                front_left_tyre_pressure, front_right_tyre_pressure,
                rear_left_tyre_pressure, rear_right_tyre_pressure,
                ballast, fuel_load,
                setup_schema_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            setup.setup_id,
            setup.session_uid,
            setup.timestamp_ms,
            setup.front_wing,
            setup.rear_wing,
            setup.on_throttle,
            setup.off_throttle,
            setup.front_camber,
            setup.rear_camber,
            setup.front_toe,
            setup.rear_toe,
            setup.front_suspension,
            setup.rear_suspension,
            setup.front_anti_roll_bar,
            setup.rear_anti_roll_bar,
            setup.front_suspension_height,
            setup.rear_suspension_height,
            setup.brake_pressure,
            setup.brake_bias,
            setup.engine_braking,
            setup.front_left_tyre_pressure,
            setup.front_right_tyre_pressure,
            setup.rear_left_tyre_pressure,
            setup.rear_right_tyre_pressure,
            setup.ballast,
            setup.fuel_load,
            setup.setup_schema_version,
            setup.created_at.isoformat()
        ))
    
    async def get_setup_snapshot(self, setup_id: str) -> Optional[CarSetupSnapshot]:
        """Retrieve car setup snapshot by ID.
        
        Args:
            setup_id: UUID of the setup snapshot.
            
        Returns:
            CarSetupSnapshot entity if found, None otherwise.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            return await self._get_setup_internal(db, setup_id)
    
    async def _get_setup_internal(
        self,
        db: aiosqlite.Connection,
        setup_id: str
    ) -> Optional[CarSetupSnapshot]:
        """Internal method to get setup within existing connection."""
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute("""
            SELECT * FROM car_setups WHERE setup_id = ?
        """, (setup_id,))
        row = await cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_car_setup(row)
    
    async def get_setup_for_lap(self, trace_id: str) -> Optional[CarSetupSnapshot]:
        """Find car setup used for a specific lap.
        
        Args:
            trace_id: UUID of the lap trace.
            
        Returns:
            CarSetupSnapshot used for the lap, or None if no setup associated.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT setup_id FROM lap_metadata WHERE trace_id = ?
            """, (trace_id,))
            row = await cursor.fetchone()
            
            if row is None or row["setup_id"] is None:
                return None
            
            return await self._get_setup_internal(db, row["setup_id"])
    
    async def list_setup_snapshots(
        self,
        session_uid: int,
        limit: int = 50
    ) -> List[CarSetupSnapshot]:
        """List all setup snapshots captured in a session.
        
        Args:
            session_uid: F1 25 session unique identifier.
            limit: Maximum number of setups to return.
            
        Returns:
            List of CarSetupSnapshot entities ordered by timestamp.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT * FROM car_setups
                WHERE session_uid = ?
                ORDER BY timestamp_ms ASC
                LIMIT ?
            """, (session_uid, limit))
            rows = await cursor.fetchall()
            
            return [self._row_to_car_setup(row) for row in rows]
    
    # =========================================================================
    # Session Operations
    # =========================================================================
    
    async def save_session(
        self,
        session_uid: int,
        track_id: str,
        session_type: int,
        started_at: Optional[datetime] = None
    ) -> None:
        """Initialize or update session metadata.
        
        Args:
            session_uid: F1 25 session unique identifier.
            track_id: F1 25 track identifier.
            session_type: F1 25 session type.
            started_at: Optional session start timestamp.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            created_at = started_at.isoformat() if started_at else datetime.utcnow().isoformat()
            
            await db.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_uid, track_id, session_type, created_at
                ) VALUES (?, ?, ?, ?)
            """, (session_uid, track_id, session_type, created_at))
            
            await db.commit()
    
    async def get_session(self, session_uid: int) -> Optional[Dict[str, Any]]:
        """Retrieve session metadata.
        
        Args:
            session_uid: F1 25 session unique identifier.
            
        Returns:
            Dictionary with session metadata or None if not found.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT * FROM sessions WHERE session_uid = ?
            """, (session_uid,))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            # Count laps in session
            cursor = await db.execute("""
                SELECT COUNT(*) FROM lap_metadata WHERE session_uid = ?
            """, (session_uid,))
            lap_count = (await cursor.fetchone())[0]
            
            return {
                "session_uid": row["session_uid"],
                "track_id": row["track_id"],
                "session_type": row["session_type"],
                "started_at": datetime.fromisoformat(row["created_at"]),
                "lap_count": lap_count
            }
    
    async def list_sessions(
        self,
        track_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List all sessions, optionally filtered by track.
        
        Args:
            track_id: Optional track filter.
            limit: Maximum number of sessions to return.
            
        Returns:
            List of session metadata dictionaries ordered by started_at desc.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            
            if track_id:
                cursor = await db.execute("""
                    SELECT * FROM sessions
                    WHERE track_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (track_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT * FROM sessions
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            rows = await cursor.fetchall()
            
            sessions = []
            for row in rows:
                # Count laps for each session
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM lap_metadata WHERE session_uid = ?
                """, (row["session_uid"],))
                lap_count = (await cursor.fetchone())[0]
                
                sessions.append({
                    "session_uid": row["session_uid"],
                    "track_id": row["track_id"],
                    "session_type": row["session_type"],
                    "started_at": datetime.fromisoformat(row["created_at"]),
                    "lap_count": lap_count
                })
            
            return sessions
    
    # =========================================================================
    # Bulk Operations & Maintenance
    # =========================================================================
    
    async def get_telemetry_statistics(self) -> Dict[str, Any]:
        """Get overall telemetry database statistics.
        
        Returns:
            Dictionary with statistics.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Total sessions
            cursor = await db.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = (await cursor.fetchone())[0]
            
            # Total laps
            cursor = await db.execute("SELECT COUNT(*) FROM lap_metadata")
            total_laps = (await cursor.fetchone())[0]
            
            # Total telemetry samples
            cursor = await db.execute("SELECT COUNT(*) FROM lap_telemetry")
            total_samples = (await cursor.fetchone())[0]
            
            # Total setups
            cursor = await db.execute("SELECT COUNT(*) FROM car_setups")
            total_setups = (await cursor.fetchone())[0]
            
            # Oldest session
            cursor = await db.execute("""
                SELECT MIN(created_at) FROM sessions
            """)
            oldest = await cursor.fetchone()
            oldest_session = datetime.fromisoformat(oldest[0]) if oldest[0] else None
            
            # Newest session
            cursor = await db.execute("""
                SELECT MAX(created_at) FROM sessions
            """)
            newest = await cursor.fetchone()
            newest_session = datetime.fromisoformat(newest[0]) if newest[0] else None
            
            return {
                "total_sessions": total_sessions,
                "total_laps": total_laps,
                "total_samples": total_samples,
                "total_setups": total_setups,
                "oldest_session": oldest_session,
                "newest_session": newest_session
            }
    
    async def cleanup_old_data(self, before_date: datetime) -> int:
        """Delete telemetry data older than specified date.
        
        Args:
            before_date: Delete all data from sessions started before this date.
            
        Returns:
            Number of sessions deleted.
        """
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            cursor = await db.execute("""
                DELETE FROM sessions 
                WHERE created_at < ?
            """, (before_date.isoformat(),))
            
            await db.commit()
            
            return cursor.rowcount
    
    async def reset_all_telemetry_data(self) -> bool:
        """Reset all telemetry data in the database.
        
        Returns:
            True if reset was successful, False otherwise.
        """
        try:
            async with aiosqlite.connect(self._database_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Delete in correct order (respecting FK constraints)
                # lap_telemetry has FK to lap_metadata (CASCADE handles this)
                # lap_metadata has FK to sessions (CASCADE handles this)
                # car_setups has FK to sessions (CASCADE handles this)
                await db.execute("DELETE FROM sessions")
                
                await db.commit()
                
            return True
        
        except Exception:
            return False
    
    # =========================================================================
    # Domain Entity Mapping Helpers
    # =========================================================================
    
    def _row_to_telemetry_sample(self, row: aiosqlite.Row) -> TelemetrySample:
        """Convert database row to TelemetrySample value object.
        
        Args:
            row: Database row from lap_telemetry table.
            
        Returns:
            TelemetrySample value object.
        """
        return TelemetrySample(
            timestamp_ms=row["timestamp_ms"],
            world_position_x=row["world_position_x"],
            world_position_y=row["world_position_y"],
            world_position_z=row["world_position_z"],
            world_velocity_x=row["world_velocity_x"],
            world_velocity_y=row["world_velocity_y"],
            world_velocity_z=row["world_velocity_z"],
            g_force_lateral=row["g_force_lateral"],
            g_force_longitudinal=row["g_force_longitudinal"],
            yaw=row["yaw"],
            speed=row["speed"],
            throttle=row["throttle"],
            steer=row["steer"],
            brake=row["brake"],
            gear=row["gear"],
            engine_rpm=row["engine_rpm"],
            drs=row["drs"],
            lap_distance=row["lap_distance"],
            lap_number=row["lap_number"]
        )
    
    def _row_to_car_setup(self, row: aiosqlite.Row) -> CarSetupSnapshot:
        """Convert database row to CarSetupSnapshot entity.
        
        Args:
            row: Database row from car_setups table.
            
        Returns:
            CarSetupSnapshot entity.
        """
        return CarSetupSnapshot(
            session_uid=row["session_uid"],
            timestamp_ms=row["timestamp_ms"],
            front_wing=row["front_wing"],
            rear_wing=row["rear_wing"],
            on_throttle=row["on_throttle"],
            off_throttle=row["off_throttle"],
            front_camber=row["front_camber"],
            rear_camber=row["rear_camber"],
            front_toe=row["front_toe"],
            rear_toe=row["rear_toe"],
            front_suspension=row["front_suspension"],
            rear_suspension=row["rear_suspension"],
            front_anti_roll_bar=row["front_anti_roll_bar"],
            rear_anti_roll_bar=row["rear_anti_roll_bar"],
            front_suspension_height=row["front_suspension_height"],
            rear_suspension_height=row["rear_suspension_height"],
            brake_pressure=row["brake_pressure"],
            brake_bias=row["brake_bias"],
            engine_braking=row["engine_braking"],
            front_left_tyre_pressure=row["front_left_tyre_pressure"],
            front_right_tyre_pressure=row["front_right_tyre_pressure"],
            rear_left_tyre_pressure=row["rear_left_tyre_pressure"],
            rear_right_tyre_pressure=row["rear_right_tyre_pressure"],
            ballast=row["ballast"],
            fuel_load=row["fuel_load"],
            setup_id=row["setup_id"],
            setup_schema_version=row["setup_schema_version"],
            created_at=datetime.fromisoformat(row["created_at"])
        )
