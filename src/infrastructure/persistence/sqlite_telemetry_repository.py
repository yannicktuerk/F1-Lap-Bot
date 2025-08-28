"""SQLite implementation of the TelemetryRepository interface."""
import sqlite3
import aiosqlite
import uuid
import json
from datetime import datetime
from typing import List, Optional
from ...domain.entities.telemetry_sample import (
    PlayerTelemetrySample, SessionInfo, LapInfo, CarTelemetryInfo, 
    MotionExInfo, TimeTrialInfo
)
from ...domain.interfaces.telemetry_repository import TelemetryRepository
from ...domain.value_objects.track_name import TrackName


class SQLiteTelemetryRepository(TelemetryRepository):
    """SQLite adapter implementing the TelemetryRepository port."""
    
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
    
    async def _ensure_tables_exist(self):
        """Create the telemetry tables if they don't exist."""
        async with aiosqlite.connect(self._database_path) as db:
            # Main telemetry samples table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_samples (
                    sample_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    player_car_index INTEGER NOT NULL,
                    session_uid INTEGER NOT NULL,
                    session_type INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    session_time REAL NOT NULL,
                    remaining_time REAL NOT NULL,
                    is_time_trial BOOLEAN NOT NULL,
                    frame_identifier INTEGER NOT NULL,
                    overall_frame_identifier INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Lap information table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_lap_info (
                    sample_id TEXT NOT NULL,
                    lap_time_ms INTEGER,
                    sector1_time_ms INTEGER,
                    sector2_time_ms INTEGER,
                    sector3_time_ms INTEGER,
                    lap_distance REAL NOT NULL,
                    total_distance REAL NOT NULL,
                    is_valid_lap BOOLEAN NOT NULL,
                    current_lap_number INTEGER NOT NULL,
                    car_position INTEGER NOT NULL,
                    FOREIGN KEY (sample_id) REFERENCES telemetry_samples (sample_id)
                )
            """)
            
            # Car telemetry table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_car_data (
                    sample_id TEXT NOT NULL,
                    speed REAL NOT NULL,
                    throttle REAL NOT NULL,
                    steer REAL NOT NULL,
                    brake REAL NOT NULL,
                    clutch REAL NOT NULL,
                    gear INTEGER NOT NULL,
                    engine_rpm INTEGER NOT NULL,
                    drs BOOLEAN NOT NULL,
                    rev_lights_percent INTEGER NOT NULL,
                    brake_temp_json TEXT NOT NULL,
                    tyre_surface_temp_json TEXT NOT NULL,
                    tyre_inner_temp_json TEXT NOT NULL,
                    engine_temperature REAL NOT NULL,
                    FOREIGN KEY (sample_id) REFERENCES telemetry_samples (sample_id)
                )
            """)
            
            # Motion Ex data table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_motion_ex (
                    sample_id TEXT NOT NULL,
                    wheel_slip_ratio_json TEXT NOT NULL,
                    wheel_slip_angle_json TEXT NOT NULL,
                    wheel_lat_force_json TEXT NOT NULL,
                    wheel_long_force_json TEXT NOT NULL,
                    wheel_speed_json TEXT NOT NULL,
                    local_velocity_x REAL NOT NULL,
                    local_velocity_y REAL NOT NULL,
                    local_velocity_z REAL NOT NULL,
                    front_wheels_angle REAL NOT NULL,
                    height_of_cog_above_ground REAL NOT NULL,
                    angular_velocity_x REAL NOT NULL,
                    angular_velocity_y REAL NOT NULL,
                    angular_velocity_z REAL NOT NULL,
                    FOREIGN KEY (sample_id) REFERENCES telemetry_samples (sample_id)
                )
            """)
            
            # Time trial data table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_time_trial (
                    sample_id TEXT NOT NULL,
                    is_personal_best BOOLEAN NOT NULL,
                    is_best_overall BOOLEAN NOT NULL,
                    sector1_personal_best_ms INTEGER,
                    sector2_personal_best_ms INTEGER,
                    sector3_personal_best_ms INTEGER,
                    sector1_best_overall_ms INTEGER,
                    sector2_best_overall_ms INTEGER,
                    sector3_best_overall_ms INTEGER,
                    FOREIGN KEY (sample_id) REFERENCES telemetry_samples (sample_id)
                )
            """)
            
            # Create indexes for better query performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry_samples(session_uid)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_track ON telemetry_samples(track_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_samples(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time_trial ON telemetry_samples(is_time_trial)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_lap_valid ON telemetry_lap_info(is_valid_lap)")
            
            await db.commit()
    
    async def save(self, sample: PlayerTelemetrySample) -> str:
        """Save a telemetry sample and return the generated ID."""
        await self._ensure_tables_exist()
        
        sample_id = str(uuid.uuid4())
        
        try:
            async with aiosqlite.connect(self._database_path) as db:
                # Save main sample data
                await db.execute("""
                    INSERT INTO telemetry_samples (
                        sample_id, timestamp, player_car_index, session_uid,
                        session_type, track_id, session_time, remaining_time,
                        is_time_trial, frame_identifier, overall_frame_identifier,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample_id,
                    sample.timestamp.isoformat(),
                    sample.player_car_index,
                    sample.session_info.session_uid,
                    sample.session_info.session_type,
                    sample.session_info.track_id,
                    sample.session_info.session_time,
                    sample.session_info.remaining_time,
                    sample.session_info.is_time_trial,
                    sample.session_info.frame_identifier,
                    sample.session_info.overall_frame_identifier,
                    datetime.now().isoformat()
                ))
                
                # Save lap info
                await db.execute("""
                    INSERT INTO telemetry_lap_info (
                        sample_id, lap_time_ms, sector1_time_ms, sector2_time_ms,
                        sector3_time_ms, lap_distance, total_distance, is_valid_lap,
                        current_lap_number, car_position
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample_id,
                    sample.lap_info.lap_time_ms,
                    sample.lap_info.sector1_time_ms,
                    sample.lap_info.sector2_time_ms,
                    sample.lap_info.sector3_time_ms,
                    sample.lap_info.lap_distance,
                    sample.lap_info.total_distance,
                    sample.lap_info.is_valid_lap,
                    sample.lap_info.current_lap_number,
                    sample.lap_info.car_position
                ))
                
                # Save car telemetry
                await db.execute("""
                    INSERT INTO telemetry_car_data (
                        sample_id, speed, throttle, steer, brake, clutch,
                        gear, engine_rpm, drs, rev_lights_percent,
                        brake_temp_json, tyre_surface_temp_json, tyre_inner_temp_json,
                        engine_temperature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample_id,
                    sample.car_telemetry.speed,
                    sample.car_telemetry.throttle,
                    sample.car_telemetry.steer,
                    sample.car_telemetry.brake,
                    sample.car_telemetry.clutch,
                    sample.car_telemetry.gear,
                    sample.car_telemetry.engine_rpm,
                    sample.car_telemetry.drs,
                    sample.car_telemetry.rev_lights_percent,
                    json.dumps(sample.car_telemetry.brake_temperature),
                    json.dumps(sample.car_telemetry.tyre_surface_temperature),
                    json.dumps(sample.car_telemetry.tyre_inner_temperature),
                    sample.car_telemetry.engine_temperature
                ))
                
                # Save motion ex data if available
                if sample.motion_ex_info:
                    await db.execute("""
                        INSERT INTO telemetry_motion_ex (
                            sample_id, wheel_slip_ratio_json, wheel_slip_angle_json,
                            wheel_lat_force_json, wheel_long_force_json, wheel_speed_json,
                            local_velocity_x, local_velocity_y, local_velocity_z,
                            front_wheels_angle, height_of_cog_above_ground,
                            angular_velocity_x, angular_velocity_y, angular_velocity_z
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sample_id,
                        json.dumps(sample.motion_ex_info.wheel_slip_ratio),
                        json.dumps(sample.motion_ex_info.wheel_slip_angle),
                        json.dumps(sample.motion_ex_info.wheel_lat_force),
                        json.dumps(sample.motion_ex_info.wheel_long_force),
                        json.dumps(sample.motion_ex_info.wheel_speed),
                        sample.motion_ex_info.local_velocity_x,
                        sample.motion_ex_info.local_velocity_y,
                        sample.motion_ex_info.local_velocity_z,
                        sample.motion_ex_info.front_wheels_angle,
                        sample.motion_ex_info.height_of_cog_above_ground,
                        sample.motion_ex_info.angular_velocity_x,
                        sample.motion_ex_info.angular_velocity_y,
                        sample.motion_ex_info.angular_velocity_z
                    ))
                
                # Save time trial data if available
                if sample.time_trial_info:
                    await db.execute("""
                        INSERT INTO telemetry_time_trial (
                            sample_id, is_personal_best, is_best_overall,
                            sector1_personal_best_ms, sector2_personal_best_ms, sector3_personal_best_ms,
                            sector1_best_overall_ms, sector2_best_overall_ms, sector3_best_overall_ms
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sample_id,
                        sample.time_trial_info.is_personal_best,
                        sample.time_trial_info.is_best_overall,
                        sample.time_trial_info.sector1_personal_best_ms,
                        sample.time_trial_info.sector2_personal_best_ms,
                        sample.time_trial_info.sector3_personal_best_ms,
                        sample.time_trial_info.sector1_best_overall_ms,
                        sample.time_trial_info.sector2_best_overall_ms,
                        sample.time_trial_info.sector3_best_overall_ms
                    ))
                
                await db.commit()
                
        except Exception as save_error:
            print(f"❌ TELEMETRY REPOSITORY: Save error: {save_error}")
            raise
        
        return sample_id
    
    async def find_by_id(self, sample_id: str) -> Optional[PlayerTelemetrySample]:
        """Find a telemetry sample by its ID."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM telemetry_samples s
                LEFT JOIN telemetry_lap_info l ON s.sample_id = l.sample_id
                LEFT JOIN telemetry_car_data c ON s.sample_id = c.sample_id
                LEFT JOIN telemetry_motion_ex m ON s.sample_id = m.sample_id
                LEFT JOIN telemetry_time_trial t ON s.sample_id = t.sample_id
                WHERE s.sample_id = ?
            """, (sample_id,))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_telemetry_sample(row)
    
    async def find_by_session(self, session_uid: int, limit: int = 1000) -> List[PlayerTelemetrySample]:
        """Find telemetry samples by session UID."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM telemetry_samples s
                LEFT JOIN telemetry_lap_info l ON s.sample_id = l.sample_id
                LEFT JOIN telemetry_car_data c ON s.sample_id = c.sample_id
                LEFT JOIN telemetry_motion_ex m ON s.sample_id = m.sample_id
                LEFT JOIN telemetry_time_trial t ON s.sample_id = t.sample_id
                WHERE s.session_uid = ?
                ORDER BY s.timestamp ASC
                LIMIT ?
            """, (session_uid, limit))
            rows = await cursor.fetchall()
            
            return [self._row_to_telemetry_sample(row) for row in rows]
    
    async def find_by_track_and_timerange(
        self, 
        track: TrackName, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[PlayerTelemetrySample]:
        """Find telemetry samples by track and time range."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM telemetry_samples s
                LEFT JOIN telemetry_lap_info l ON s.sample_id = l.sample_id
                LEFT JOIN telemetry_car_data c ON s.sample_id = c.sample_id
                LEFT JOIN telemetry_motion_ex m ON s.sample_id = m.sample_id
                LEFT JOIN telemetry_time_trial t ON s.sample_id = t.sample_id
                WHERE s.track_id = ? AND s.timestamp BETWEEN ? AND ?
                ORDER BY s.timestamp ASC
            """, (track.id, start_time.isoformat(), end_time.isoformat()))
            rows = await cursor.fetchall()
            
            return [self._row_to_telemetry_sample(row) for row in rows]
    
    async def find_valid_samples_by_track(
        self, 
        track: TrackName, 
        limit: int = 1000
    ) -> List[PlayerTelemetrySample]:
        """Find valid telemetry samples for a track (TT-only, Valid-only)."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM telemetry_samples s
                LEFT JOIN telemetry_lap_info l ON s.sample_id = l.sample_id
                LEFT JOIN telemetry_car_data c ON s.sample_id = c.sample_id
                LEFT JOIN telemetry_motion_ex m ON s.sample_id = m.sample_id
                LEFT JOIN telemetry_time_trial t ON s.sample_id = t.sample_id
                WHERE s.track_id = ? AND s.is_time_trial = 1 AND l.is_valid_lap = 1
                ORDER BY s.timestamp DESC
                LIMIT ?
            """, (track.id, limit))
            rows = await cursor.fetchall()
            
            return [self._row_to_telemetry_sample(row) for row in rows]
    
    async def get_session_statistics(self, session_uid: int) -> dict:
        """Get statistics for a specific session."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Total samples
            cursor = await db.execute("SELECT COUNT(*) FROM telemetry_samples WHERE session_uid = ?", (session_uid,))
            total_samples = (await cursor.fetchone())[0]
            
            # Valid laps count
            cursor = await db.execute("""
                SELECT COUNT(*) FROM telemetry_samples s
                JOIN telemetry_lap_info l ON s.sample_id = l.sample_id
                WHERE s.session_uid = ? AND l.is_valid_lap = 1
            """, (session_uid,))
            valid_samples = (await cursor.fetchone())[0]
            
            # Time range
            cursor = await db.execute("""
                SELECT MIN(timestamp), MAX(timestamp) FROM telemetry_samples 
                WHERE session_uid = ?
            """, (session_uid,))
            time_range = await cursor.fetchone()
            
            return {
                'total_samples': total_samples,
                'valid_samples': valid_samples,
                'start_time': time_range[0],
                'end_time': time_range[1]
            }
    
    async def delete_by_session(self, session_uid: int) -> int:
        """Delete all telemetry samples for a session."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("DELETE FROM telemetry_samples WHERE session_uid = ?", (session_uid,))
            await db.commit()
            
            return cursor.rowcount
    
    def _row_to_telemetry_sample(self, row: aiosqlite.Row) -> PlayerTelemetrySample:
        """Convert a database row to a PlayerTelemetrySample entity."""
        try:
            # Session info
            session_info = SessionInfo(
                session_uid=row['session_uid'],
                session_type=row['session_type'],
                track_id=row['track_id'],
                session_time=row['session_time'],
                remaining_time=row['remaining_time'],
                is_time_trial=bool(row['is_time_trial']),
                frame_identifier=row['frame_identifier'],
                overall_frame_identifier=row['overall_frame_identifier']
            )
            
            # Lap info
            lap_info = LapInfo(
                lap_time_ms=row['lap_time_ms'],
                sector1_time_ms=row['sector1_time_ms'],
                sector2_time_ms=row['sector2_time_ms'],
                sector3_time_ms=row['sector3_time_ms'],
                lap_distance=row['lap_distance'],
                total_distance=row['total_distance'],
                is_valid_lap=bool(row['is_valid_lap']),
                current_lap_number=row['current_lap_number'],
                car_position=row['car_position']
            )
            
            # Car telemetry
            car_telemetry = CarTelemetryInfo(
                speed=row['speed'],
                throttle=row['throttle'],
                steer=row['steer'],
                brake=row['brake'],
                clutch=row['clutch'],
                gear=row['gear'],
                engine_rpm=row['engine_rpm'],
                drs=bool(row['drs']),
                rev_lights_percent=row['rev_lights_percent'],
                brake_temperature=json.loads(row['brake_temp_json']),
                tyre_surface_temperature=json.loads(row['tyre_surface_temp_json']),
                tyre_inner_temperature=json.loads(row['tyre_inner_temp_json']),
                engine_temperature=row['engine_temperature']
            )
            
            # Motion ex info (optional)
            motion_ex_info = None
            if row['wheel_slip_ratio_json'] is not None:
                motion_ex_info = MotionExInfo(
                    wheel_slip_ratio=json.loads(row['wheel_slip_ratio_json']),
                    wheel_slip_angle=json.loads(row['wheel_slip_angle_json']),
                    wheel_lat_force=json.loads(row['wheel_lat_force_json']),
                    wheel_long_force=json.loads(row['wheel_long_force_json']),
                    wheel_speed=json.loads(row['wheel_speed_json']),
                    local_velocity_x=row['local_velocity_x'],
                    local_velocity_y=row['local_velocity_y'],
                    local_velocity_z=row['local_velocity_z'],
                    front_wheels_angle=row['front_wheels_angle'],
                    height_of_cog_above_ground=row['height_of_cog_above_ground'],
                    angular_velocity_x=row['angular_velocity_x'],
                    angular_velocity_y=row['angular_velocity_y'],
                    angular_velocity_z=row['angular_velocity_z']
                )
            
            # Time trial info (optional)
            time_trial_info = None
            if row['is_personal_best'] is not None:
                time_trial_info = TimeTrialInfo(
                    is_personal_best=bool(row['is_personal_best']),
                    is_best_overall=bool(row['is_best_overall']),
                    sector1_personal_best_ms=row['sector1_personal_best_ms'],
                    sector2_personal_best_ms=row['sector2_personal_best_ms'],
                    sector3_personal_best_ms=row['sector3_personal_best_ms'],
                    sector1_best_overall_ms=row['sector1_best_overall_ms'],
                    sector2_best_overall_ms=row['sector2_best_overall_ms'],
                    sector3_best_overall_ms=row['sector3_best_overall_ms']
                )
            
            return PlayerTelemetrySample(
                timestamp=datetime.fromisoformat(row['timestamp']),
                session_info=session_info,
                lap_info=lap_info,
                car_telemetry=car_telemetry,
                motion_ex_info=motion_ex_info,
                time_trial_info=time_trial_info,
                player_car_index=row['player_car_index']
            )
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            sample_id = row['sample_id'] if 'sample_id' in row.keys() else "Unknown"
            print(f"Error converting row to PlayerTelemetrySample for sample_id={sample_id}: {e}")
            raise ValueError(f"Corrupt telemetry data for sample_id={sample_id}") from e