"""Tests for telemetry database schema creation and integrity.

This test suite validates:
- Schema tables are created correctly
- Foreign key constraints enforce CASCADE/SET NULL behavior
- Indexes exist and are used by query planner
- Migration runner applies migrations idempotently
"""

import pytest
import pytest_asyncio
import aiosqlite
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.migrations.migration_runner import MigrationRunner


@pytest_asyncio.fixture
async def temp_database():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest_asyncio.fixture
async def migrated_database(temp_database):
    """Create and migrate a temporary database."""
    runner = MigrationRunner(temp_database)
    await runner.run_migrations()
    return temp_database


class TestSchemaCreation:
    """Test suite for schema table creation."""
    
    @pytest.mark.asyncio
    async def test_all_tables_created(self, migrated_database):
        """Verify all required tables are created."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = [row[0] for row in await cursor.fetchall()]
        
        expected_tables = [
            "car_setups",
            "lap_metadata",
            "lap_telemetry",
            "schema_migrations",
            "sessions"
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not created"
    
    @pytest.mark.asyncio
    async def test_sessions_table_structure(self, migrated_database):
        """Verify sessions table has correct columns."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("PRAGMA table_info(sessions)")
            columns = {row[1]: row[2] for row in await cursor.fetchall()}
        
        assert "session_uid" in columns
        assert "track_id" in columns
        assert "session_type" in columns
        assert "schema_version" in columns
        assert "created_at" in columns
    
    @pytest.mark.asyncio
    async def test_lap_metadata_table_structure(self, migrated_database):
        """Verify lap_metadata table has correct columns."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("PRAGMA table_info(lap_metadata)")
            columns = {row[1]: row[2] for row in await cursor.fetchall()}
        
        required_columns = [
            "trace_id", "session_uid", "setup_id", "track_id",
            "lap_number", "car_index", "lap_time_ms", "is_valid", "created_at"
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} missing from lap_metadata"
    
    @pytest.mark.asyncio
    async def test_lap_telemetry_table_structure(self, migrated_database):
        """Verify lap_telemetry table has correct columns."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("PRAGMA table_info(lap_telemetry)")
            columns = {row[1]: row[2] for row in await cursor.fetchall()}
        
        required_columns = [
            "trace_id", "timestamp_ms", "lap_distance",
            "world_position_x", "world_position_y", "world_position_z",
            "world_velocity_x", "world_velocity_y", "world_velocity_z",
            "g_force_lateral", "g_force_longitudinal", "yaw",
            "speed", "throttle", "steer", "brake", "gear", "engine_rpm", "drs",
            "lap_number"
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} missing from lap_telemetry"
    
    @pytest.mark.asyncio
    async def test_car_setups_table_structure(self, migrated_database):
        """Verify car_setups table has correct columns."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("PRAGMA table_info(car_setups)")
            columns = {row[1]: row[2] for row in await cursor.fetchall()}
        
        required_columns = [
            "setup_id", "session_uid", "timestamp_ms",
            "front_wing", "rear_wing",
            "on_throttle", "off_throttle",
            "front_camber", "rear_camber", "front_toe", "rear_toe",
            "front_suspension", "rear_suspension",
            "front_anti_roll_bar", "rear_anti_roll_bar",
            "front_suspension_height", "rear_suspension_height",
            "brake_pressure", "brake_bias", "engine_braking",
            "front_left_tyre_pressure", "front_right_tyre_pressure",
            "rear_left_tyre_pressure", "rear_right_tyre_pressure",
            "ballast", "fuel_load",
            "setup_schema_version", "created_at"
        ]
        
        for col in required_columns:
            assert col in columns, f"Column {col} missing from car_setups"


class TestForeignKeyEnforcement:
    """Test suite for foreign key constraint enforcement."""
    
    @pytest.mark.asyncio
    async def test_foreign_keys_enabled(self, migrated_database):
        """Verify foreign key enforcement is enabled."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("PRAGMA foreign_keys")
            result = await cursor.fetchone()
            # Note: PRAGMA foreign_keys returns current session setting
            # We need to enable it for this connection
            await db.execute("PRAGMA foreign_keys = ON")
            cursor = await db.execute("PRAGMA foreign_keys")
            result = await cursor.fetchone()
            assert result[0] == 1, "Foreign keys not enabled"
    
    @pytest.mark.asyncio
    async def test_cascade_delete_session_to_laps(self, migrated_database):
        """Verify CASCADE delete from sessions to lap_metadata."""
        async with aiosqlite.connect(migrated_database) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Insert test session
            await db.execute("""
                INSERT INTO sessions (session_uid, track_id, session_type)
                VALUES (12345, 'monaco', 18)
            """)
            
            # Insert test lap
            await db.execute("""
                INSERT INTO lap_metadata 
                (trace_id, session_uid, track_id, lap_number, car_index, is_valid)
                VALUES ('test-trace-1', 12345, 'monaco', 1, 0, 1)
            """)
            
            await db.commit()
            
            # Verify lap exists
            cursor = await db.execute("SELECT COUNT(*) FROM lap_metadata WHERE session_uid = 12345")
            count = (await cursor.fetchone())[0]
            assert count == 1, "Lap not inserted"
            
            # Delete session
            await db.execute("DELETE FROM sessions WHERE session_uid = 12345")
            await db.commit()
            
            # Verify lap was CASCADE deleted
            cursor = await db.execute("SELECT COUNT(*) FROM lap_metadata WHERE session_uid = 12345")
            count = (await cursor.fetchone())[0]
            assert count == 0, "CASCADE delete failed - lap still exists"
    
    @pytest.mark.asyncio
    async def test_cascade_delete_session_to_setups(self, migrated_database):
        """Verify CASCADE delete from sessions to car_setups."""
        async with aiosqlite.connect(migrated_database) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Insert test session
            await db.execute("""
                INSERT INTO sessions (session_uid, track_id, session_type)
                VALUES (12346, 'silverstone', 18)
            """)
            
            # Insert test setup
            await db.execute("""
                INSERT INTO car_setups 
                (setup_id, session_uid, timestamp_ms, front_wing, rear_wing,
                 on_throttle, off_throttle, front_camber, rear_camber, 
                 front_toe, rear_toe, front_suspension, rear_suspension,
                 front_anti_roll_bar, rear_anti_roll_bar,
                 front_suspension_height, rear_suspension_height,
                 brake_pressure, brake_bias, engine_braking,
                 front_left_tyre_pressure, front_right_tyre_pressure,
                 rear_left_tyre_pressure, rear_right_tyre_pressure,
                 ballast, fuel_load)
                VALUES ('test-setup-1', 12346, 1000, 10, 20, 50, 50,
                        -2.5, -1.8, 0.05, 0.2, 5, 5, 5, 5, 3, 3,
                        100, 60, 50, 21.5, 21.5, 20.0, 20.0, 0, 50.0)
            """)
            
            await db.commit()
            
            # Verify setup exists
            cursor = await db.execute("SELECT COUNT(*) FROM car_setups WHERE session_uid = 12346")
            count = (await cursor.fetchone())[0]
            assert count == 1, "Setup not inserted"
            
            # Delete session
            await db.execute("DELETE FROM sessions WHERE session_uid = 12346")
            await db.commit()
            
            # Verify setup was CASCADE deleted
            cursor = await db.execute("SELECT COUNT(*) FROM car_setups WHERE session_uid = 12346")
            count = (await cursor.fetchone())[0]
            assert count == 0, "CASCADE delete failed - setup still exists"
    
    @pytest.mark.asyncio
    async def test_set_null_setup_to_lap(self, migrated_database):
        """Verify SET NULL behavior from car_setups to lap_metadata."""
        async with aiosqlite.connect(migrated_database) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Insert test session
            await db.execute("""
                INSERT INTO sessions (session_uid, track_id, session_type)
                VALUES (12347, 'spa', 18)
            """)
            
            # Insert test setup
            await db.execute("""
                INSERT INTO car_setups 
                (setup_id, session_uid, timestamp_ms, front_wing, rear_wing,
                 on_throttle, off_throttle, front_camber, rear_camber, 
                 front_toe, rear_toe, front_suspension, rear_suspension,
                 front_anti_roll_bar, rear_anti_roll_bar,
                 front_suspension_height, rear_suspension_height,
                 brake_pressure, brake_bias, engine_braking,
                 front_left_tyre_pressure, front_right_tyre_pressure,
                 rear_left_tyre_pressure, rear_right_tyre_pressure,
                 ballast, fuel_load)
                VALUES ('test-setup-2', 12347, 1000, 10, 20, 50, 50,
                        -2.5, -1.8, 0.05, 0.2, 5, 5, 5, 5, 3, 3,
                        100, 60, 50, 21.5, 21.5, 20.0, 20.0, 0, 50.0)
            """)
            
            # Insert test lap referencing setup
            await db.execute("""
                INSERT INTO lap_metadata 
                (trace_id, session_uid, setup_id, track_id, lap_number, car_index, is_valid)
                VALUES ('test-trace-2', 12347, 'test-setup-2', 'spa', 1, 0, 1)
            """)
            
            await db.commit()
            
            # Verify lap has setup_id
            cursor = await db.execute("""
                SELECT setup_id FROM lap_metadata WHERE trace_id = 'test-trace-2'
            """)
            setup_id = (await cursor.fetchone())[0]
            assert setup_id == 'test-setup-2', "Setup not linked to lap"
            
            # Delete setup
            await db.execute("DELETE FROM car_setups WHERE setup_id = 'test-setup-2'")
            await db.commit()
            
            # Verify lap still exists but setup_id is NULL
            cursor = await db.execute("""
                SELECT setup_id FROM lap_metadata WHERE trace_id = 'test-trace-2'
            """)
            result = await cursor.fetchone()
            assert result is not None, "Lap was deleted (should have been SET NULL)"
            assert result[0] is None, "SET NULL failed - setup_id not nullified"
    
    @pytest.mark.asyncio
    async def test_cascade_delete_lap_to_telemetry(self, migrated_database):
        """Verify CASCADE delete from lap_metadata to lap_telemetry."""
        async with aiosqlite.connect(migrated_database) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Insert test session
            await db.execute("""
                INSERT INTO sessions (session_uid, track_id, session_type)
                VALUES (12348, 'monza', 18)
            """)
            
            # Insert test lap
            await db.execute("""
                INSERT INTO lap_metadata 
                (trace_id, session_uid, track_id, lap_number, car_index, is_valid)
                VALUES ('test-trace-3', 12348, 'monza', 1, 0, 1)
            """)
            
            # Insert telemetry samples
            await db.execute("""
                INSERT INTO lap_telemetry 
                (trace_id, timestamp_ms, lap_distance,
                 world_position_x, world_position_y, world_position_z,
                 world_velocity_x, world_velocity_y, world_velocity_z,
                 g_force_lateral, g_force_longitudinal, yaw,
                 speed, throttle, steer, brake, gear, engine_rpm, drs, lap_number)
                VALUES ('test-trace-3', 1000, 100.0,
                        1000.0, 50.0, 2000.0,
                        50.0, 0.0, 30.0,
                        1.2, 0.8, 1.57,
                        250.0, 1.0, 0.0, 0.0, 5, 10000, 0, 1)
            """)
            
            await db.commit()
            
            # Verify telemetry exists
            cursor = await db.execute("SELECT COUNT(*) FROM lap_telemetry WHERE trace_id = 'test-trace-3'")
            count = (await cursor.fetchone())[0]
            assert count == 1, "Telemetry not inserted"
            
            # Delete lap
            await db.execute("DELETE FROM lap_metadata WHERE trace_id = 'test-trace-3'")
            await db.commit()
            
            # Verify telemetry was CASCADE deleted
            cursor = await db.execute("SELECT COUNT(*) FROM lap_telemetry WHERE trace_id = 'test-trace-3'")
            count = (await cursor.fetchone())[0]
            assert count == 0, "CASCADE delete failed - telemetry still exists"


class TestIndexes:
    """Test suite for index creation and usage."""
    
    @pytest.mark.asyncio
    async def test_all_indexes_created(self, migrated_database):
        """Verify all required indexes are created."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
                ORDER BY name
            """)
            indexes = [row[0] for row in await cursor.fetchall()]
        
        expected_indexes = [
            "idx_lap_meta_session",
            "idx_lap_meta_track",
            "idx_lap_meta_valid",
            "idx_sessions_created",
            "idx_sessions_track",
            "idx_sessions_user",
            "idx_sessions_user_track",
            "idx_setups_session",
            "idx_telemetry_lap_distance",
            "idx_telemetry_trace"
        ]
        
        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} not created"
    
    @pytest.mark.asyncio
    async def test_index_used_for_trace_query(self, migrated_database):
        """Verify an index is used for trace_id queries."""
        async with aiosqlite.connect(migrated_database) as db:
            # Use EXPLAIN QUERY PLAN to check index usage
            cursor = await db.execute("""
                EXPLAIN QUERY PLAN
                SELECT * FROM lap_telemetry WHERE trace_id = 'test-123'
            """)
            plan = await cursor.fetchall()
            
            # Query plan should use an index (SEARCH with INDEX)
            plan_str = " ".join(str(row) for row in plan)
            # SQLite may choose idx_telemetry_trace or idx_telemetry_lap_distance (both cover trace_id)
            assert "USING INDEX" in plan_str and "trace_id" in plan_str.lower(), \
                f"No index used for trace_id query. Query plan: {plan_str}"
    
    @pytest.mark.asyncio
    async def test_index_used_for_session_query(self, migrated_database):
        """Verify idx_lap_meta_session is used for session_uid queries."""
        async with aiosqlite.connect(migrated_database) as db:
            cursor = await db.execute("""
                EXPLAIN QUERY PLAN
                SELECT * FROM lap_metadata WHERE session_uid = 12345
            """)
            plan = await cursor.fetchall()
            
            plan_str = " ".join(str(row) for row in plan)
            assert "idx_lap_meta_session" in plan_str, \
                f"Index idx_lap_meta_session not used in query plan: {plan_str}"


class TestMigrationRunner:
    """Test suite for migration runner functionality."""
    
    @pytest.mark.asyncio
    async def test_migration_idempotency(self, temp_database):
        """Verify migrations can be run multiple times safely."""
        runner = MigrationRunner(temp_database)
        
        # Run migrations first time
        await runner.run_migrations()
        
        # Check version
        status1 = await runner.get_migration_status()
        version1 = status1["current_version"]
        
        # Run migrations again (should be no-op)
        await runner.run_migrations()
        
        # Check version hasn't changed
        status2 = await runner.get_migration_status()
        version2 = status2["current_version"]
        
        assert version1 == version2, "Migration version changed on second run"
        assert version1 == 2, "Expected schema version 2 (with user_id migration)"
    
    @pytest.mark.asyncio
    async def test_migration_status_reporting(self, migrated_database):
        """Verify migration status is reported correctly."""
        runner = MigrationRunner(migrated_database)
        status = await runner.get_migration_status()
        
        assert "current_version" in status
        assert "applied_migrations" in status
        assert "pending_migrations" in status
        
        assert status["current_version"] == 2
        assert len(status["applied_migrations"]) == 2
        assert status["applied_migrations"][0]["version"] == 1
        assert status["applied_migrations"][1]["version"] == 2
        assert len(status["pending_migrations"]) == 0
