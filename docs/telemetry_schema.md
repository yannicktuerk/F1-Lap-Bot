# Telemetry Database Schema Documentation

## Overview

The telemetry database schema provides structured storage for F1 25 UDP telemetry data. The design enables:

- **Complete lap trace capture**: Store every telemetry sample for detailed replay and analysis
- **Car setup tracking**: Correlate lap performance with car configuration
- **Session management**: Group laps and setups by gameplay session
- **Query performance**: Indexes optimize common query patterns (track, session, distance)
- **Data integrity**: Foreign key constraints enforce referential integrity

## Architecture

### Database Separation

The F1 Lap Bot uses **two separate SQLite databases**:

1. **Application Database** (`lap_times.db`): Fast operational data
   - Lap times for leaderboards
   - ELO ratings
   - Driver statistics
   - Optimized for real-time Discord bot queries

2. **Telemetry Database** (`telemetry.db`): Heavy analytical data
   - Complete lap traces with 300-500 samples per lap
   - Detailed car setup snapshots
   - Used for AI training, data science, advanced analytics
   - Separate to avoid impacting bot performance

**Why separate?**
- The application DB handles high-frequency read queries (leaderboards, ratings)
- The telemetry DB contains large volumes of data unsuitable for real-time queries
- Clean Architecture: domain/application layers are unchanged, only infrastructure adapters differ
- Independent scaling and optimization strategies

### Schema Version: 1

Current schema version is tracked in the `schema_migrations` table. The migration system applies SQL files sequentially and records applied versions.

## Table Structure

### 1. sessions

**Purpose**: Container for F1 25 gameplay sessions (Time Trial, Practice, etc.)

```sql
CREATE TABLE sessions (
    session_uid INTEGER PRIMARY KEY NOT NULL,  -- F1 25 session UID
    track_id TEXT NOT NULL,                   -- Track identifier
    session_type INTEGER NOT NULL,            -- F1 25 session type code
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);
```

**Indexes**:
- `idx_sessions_track`: Fast track-based queries
- `idx_sessions_created`: Chronological ordering

**Relationships**:
- One session → Many laps (lap_metadata)
- One session → Many car setups

### 2. car_setups

**Purpose**: Snapshot of complete car configuration (23 parameters from F1 25)

```sql
CREATE TABLE car_setups (
    setup_id TEXT PRIMARY KEY NOT NULL,       -- UUID
    session_uid INTEGER NOT NULL,             -- FK → sessions
    timestamp_ms INTEGER NOT NULL,
    
    -- Aerodynamics
    front_wing INTEGER NOT NULL,
    rear_wing INTEGER NOT NULL,
    
    -- Differential
    on_throttle INTEGER NOT NULL,
    off_throttle INTEGER NOT NULL,
    
    -- Camber & Toe
    front_camber REAL NOT NULL,
    rear_camber REAL NOT NULL,
    front_toe REAL NOT NULL,
    rear_toe REAL NOT NULL,
    
    -- Suspension
    front_suspension INTEGER NOT NULL,
    rear_suspension INTEGER NOT NULL,
    front_anti_roll_bar INTEGER NOT NULL,
    rear_anti_roll_bar INTEGER NOT NULL,
    front_suspension_height INTEGER NOT NULL,
    rear_suspension_height INTEGER NOT NULL,
    
    -- Brakes
    brake_pressure INTEGER NOT NULL,
    brake_bias INTEGER NOT NULL,
    engine_braking INTEGER NOT NULL,
    
    -- Tyres
    front_left_tyre_pressure REAL NOT NULL,
    front_right_tyre_pressure REAL NOT NULL,
    rear_left_tyre_pressure REAL NOT NULL,
    rear_right_tyre_pressure REAL NOT NULL,
    
    -- Weight
    ballast INTEGER NOT NULL,
    fuel_load REAL NOT NULL,
    
    setup_schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    
    FOREIGN KEY (session_uid) 
        REFERENCES sessions(session_uid) 
        ON DELETE CASCADE
);
```

**Indexes**:
- `idx_setups_session`: Query setups by session

**Foreign Keys**:
- `session_uid → sessions.session_uid` (CASCADE): Deleting session removes all setups

### 3. lap_metadata

**Purpose**: Summary metadata for each lap in a session

```sql
CREATE TABLE lap_metadata (
    trace_id TEXT PRIMARY KEY NOT NULL,       -- UUID (LapTrace.trace_id)
    session_uid INTEGER NOT NULL,             -- FK → sessions
    setup_id TEXT,                            -- FK → car_setups (optional)
    track_id TEXT NOT NULL,                   -- Denormalized for query perf
    lap_number INTEGER NOT NULL,
    car_index INTEGER NOT NULL,
    lap_time_ms INTEGER,                      -- NULL if lap incomplete
    is_valid INTEGER NOT NULL DEFAULT 1,      -- 0 = penalties/invalid
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    
    FOREIGN KEY (session_uid) 
        REFERENCES sessions(session_uid) 
        ON DELETE CASCADE,
    
    FOREIGN KEY (setup_id) 
        REFERENCES car_setups(setup_id) 
        ON DELETE SET NULL
);
```

**Indexes**:
- `idx_lap_meta_session`: Query laps by session
- `idx_lap_meta_track`: Query laps by track across all sessions
- `idx_lap_meta_valid`: Filter valid laps and order by time

**Foreign Keys**:
- `session_uid → sessions.session_uid` (CASCADE): Deleting session removes all laps
- `setup_id → car_setups.setup_id` (SET NULL): Deleting setup keeps lap but nullifies setup reference

**Design Notes**:
- `track_id` is denormalized (also in sessions) for query performance
- `setup_id` is optional: not all laps have an associated setup snapshot
- `is_valid` uses INTEGER (0/1) because SQLite has no native BOOLEAN

### 4. lap_telemetry

**Purpose**: Detailed telemetry samples for each lap (typically 300-500 per lap)

```sql
CREATE TABLE lap_telemetry (
    trace_id TEXT NOT NULL,                   -- FK → lap_metadata
    timestamp_ms INTEGER NOT NULL,
    lap_distance REAL NOT NULL,
    
    -- Position (world space, meters)
    world_position_x REAL NOT NULL,
    world_position_y REAL NOT NULL,
    world_position_z REAL NOT NULL,
    
    -- Velocity (world space, m/s)
    world_velocity_x REAL NOT NULL,
    world_velocity_y REAL NOT NULL,
    world_velocity_z REAL NOT NULL,
    
    -- G-forces
    g_force_lateral REAL NOT NULL,
    g_force_longitudinal REAL NOT NULL,
    
    -- Orientation
    yaw REAL NOT NULL,
    
    -- Car telemetry
    speed REAL NOT NULL,
    throttle REAL NOT NULL,
    steer REAL NOT NULL,
    brake REAL NOT NULL,
    gear INTEGER NOT NULL,
    engine_rpm INTEGER NOT NULL,
    drs INTEGER NOT NULL,
    
    -- Lap metadata
    lap_number INTEGER NOT NULL,
    
    FOREIGN KEY (trace_id) 
        REFERENCES lap_metadata(trace_id) 
        ON DELETE CASCADE
);
```

**Indexes**:
- `idx_telemetry_trace`: **Critical** for querying samples by lap (most common query)
- `idx_telemetry_lap_distance`: Spatial queries (sector analysis, corner analysis)

**Foreign Keys**:
- `trace_id → lap_metadata.trace_id` (CASCADE): Deleting lap removes all telemetry samples

**Design Notes**:
- No primary key: Multiple samples per lap, no natural unique identifier
- Composite index `(trace_id, lap_distance)` enables efficient range queries
- This table grows rapidly: ~400 rows per lap × many laps
- Index on `trace_id` is essential for query performance

### 5. schema_migrations

**Purpose**: Track applied migrations for version control

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);
```

**Usage**: Managed automatically by `MigrationRunner`. Do not modify manually.

## Relationships Diagram

```
sessions (1)
    ├──CASCADE──> car_setups (N)
    └──CASCADE──> lap_metadata (N)
                      ├──SET NULL──> car_setups (1)
                      └──CASCADE──> lap_telemetry (N)
```

**Cascade Behavior**:
- Delete session → deletes all laps and setups
- Delete lap → deletes all telemetry samples
- Delete setup → keeps laps but nullifies setup_id reference

## Query Patterns & Performance

### Common Queries

**1. Get all telemetry for a specific lap**
```sql
SELECT * FROM lap_telemetry 
WHERE trace_id = ? 
ORDER BY timestamp_ms;
```
Uses: `idx_telemetry_trace` (index scan)

**2. Find laps on a specific track**
```sql
SELECT * FROM lap_metadata 
WHERE track_id = ? AND is_valid = 1 
ORDER BY lap_time_ms ASC;
```
Uses: `idx_lap_meta_track` + filter on `is_valid`

**3. Telemetry in distance range (sector analysis)**
```sql
SELECT * FROM lap_telemetry 
WHERE trace_id = ? AND lap_distance BETWEEN ? AND ?;
```
Uses: `idx_telemetry_lap_distance` (range scan)

**4. All laps in a session**
```sql
SELECT * FROM lap_metadata 
WHERE session_uid = ? 
ORDER BY lap_number;
```
Uses: `idx_lap_meta_session` (index scan)

### Performance Considerations

**Telemetry Table Size**:
- Typical lap: 400 samples
- 100 laps = 40,000 rows
- 1,000 laps = 400,000 rows

**Index Maintenance**:
- Indexes speed up reads but slow down writes
- For bulk telemetry ingestion, consider:
  1. Disable indexes: `DROP INDEX idx_name`
  2. Insert data in transaction
  3. Rebuild indexes: `CREATE INDEX ...`

**Foreign Key Overhead**:
- Foreign keys add constraint checks on write
- Enable: `PRAGMA foreign_keys = ON` (default OFF in SQLite)
- Required for referential integrity

## Migration System

### How It Works

Migrations are SQL files in `src/infrastructure/migrations/`:
- `001_telemetry_schema.sql` - Initial schema
- `002_add_new_feature.sql` - Future migration
- `003_performance_tuning.sql` - Future migration

**MigrationRunner**:
1. Discovers `.sql` files numbered sequentially
2. Checks `schema_migrations` table for current version
3. Applies pending migrations in order
4. Records version after successful application
5. Idempotent: Safe to run multiple times

### Adding a New Migration

1. Create new file: `00X_description.sql`
2. Write SQL (CREATE, ALTER, DROP, etc.)
3. Test locally: `python -m src.infrastructure.migrations.migration_runner`
4. Commit migration file (never modify existing migrations)
5. Run on production: Migrations auto-apply on next startup

**Example Migration**:
```sql
-- 002_add_lap_status.sql
ALTER TABLE lap_metadata ADD COLUMN status TEXT DEFAULT 'complete';
CREATE INDEX idx_lap_meta_status ON lap_metadata(status);
INSERT INTO schema_migrations (version) VALUES (2);
```

### Migration Best Practices

- **Never modify applied migrations**: Create new migration to fix issues
- **Test on backup first**: Migrations can't be rolled back
- **Use transactions**: Migration runner wraps each migration in transaction
- **Keep migrations small**: One conceptual change per migration
- **Document breaking changes**: Update this doc when schema changes

## Foreign Key Enforcement

SQLite **disables foreign keys by default**. The migration system and all repository code must explicitly enable them:

```python
async with aiosqlite.connect(db_path) as db:
    await db.execute("PRAGMA foreign_keys = ON")
    # ... rest of code
```

**Why this matters**:
- Without FK enforcement, orphaned records can exist (e.g., lap without session)
- Cascade deletes won't work
- Data integrity is compromised

## Data Integrity Rules

### Enforced by Schema

1. **Sessions must exist before laps/setups**
   - Foreign key constraint prevents orphaned laps
   
2. **Lap metadata must exist before telemetry**
   - Cannot insert telemetry samples without parent lap

3. **Cascade deletes maintain consistency**
   - Deleting session automatically removes all child records

### Not Enforced (Application Layer)

1. **Telemetry samples are chronologically ordered**
   - Application (LapTrace entity) enforces ordering
   - Database doesn't prevent out-of-order inserts

2. **Setup parameter validation**
   - CarSetupSnapshot entity validates ranges (e.g., wing 0-50)
   - Database allows any INTEGER/REAL values

3. **Lap time validation**
   - Application validates realistic lap times
   - Database allows any positive INTEGER

## Backup & Maintenance

### Backup Strategy

```bash
# Manual backup (file copy)
cp telemetry.db backups/telemetry_$(date +%Y%m%d).db

# SQLite backup (online, safe during writes)
sqlite3 telemetry.db ".backup backups/telemetry_backup.db"
```

### Cleanup Old Data

```sql
-- Delete sessions older than 6 months (cascades to laps/setups/telemetry)
DELETE FROM sessions 
WHERE created_at < datetime('now', '-6 months');

-- Vacuum to reclaim disk space
VACUUM;
```

### Statistics

```sql
-- Table sizes
SELECT 
    name, 
    (SELECT COUNT(*) FROM sqlite_master sm WHERE sm.name = m.name) as count
FROM sqlite_master m 
WHERE type = 'table';

-- Telemetry sample count
SELECT 
    COUNT(*) as total_samples,
    COUNT(DISTINCT trace_id) as total_laps,
    ROUND(AVG(sample_count), 1) as avg_samples_per_lap
FROM (
    SELECT trace_id, COUNT(*) as sample_count
    FROM lap_telemetry
    GROUP BY trace_id
);

-- Disk usage
SELECT page_count * page_size / 1024 / 1024 as size_mb
FROM pragma_page_count(), pragma_page_size();
```

## Future Enhancements

### Planned Schema Changes

1. **Sector time tracking**: Add `sector1_ms`, `sector2_ms`, `sector3_ms` to `lap_metadata`
2. **Weather data**: New table for session weather conditions
3. **Penalty records**: Track penalties separately from lap validity
4. **Tire wear tracking**: Sample tire temperature/wear alongside telemetry

### Performance Optimizations

1. **Partial indexes**: Index only valid laps for leaderboard queries
   ```sql
   CREATE INDEX idx_valid_laps ON lap_metadata(track_id, lap_time_ms) 
   WHERE is_valid = 1;
   ```

2. **Telemetry compression**: Sample rate reduction for non-critical laps
3. **Materialized views**: Pre-aggregate statistics for common queries

## Troubleshooting

### Foreign Key Violations

**Error**: `FOREIGN KEY constraint failed`

**Causes**:
- Inserting lap without creating session first
- Inserting telemetry before lap metadata

**Fix**: Insert in correct order (sessions → laps → telemetry)

### Missing Indexes

**Symptom**: Slow queries, full table scans

**Diagnosis**:
```sql
EXPLAIN QUERY PLAN 
SELECT * FROM lap_telemetry WHERE trace_id = 'abc123';
```

**Expected**: `USING INDEX idx_telemetry_trace`  
**Problem**: `SCAN lap_telemetry` (no index)

**Fix**: Rebuild index
```sql
CREATE INDEX IF NOT EXISTS idx_telemetry_trace ON lap_telemetry(trace_id);
```

### Large Database Size

**Symptom**: `telemetry.db` growing beyond available disk space

**Solutions**:
1. Delete old sessions (see Cleanup section)
2. Archive historical data to separate database
3. Implement retention policy (auto-delete after N months)
4. Sample rate reduction: Store every Nth sample for old laps

## References

- **F1 25 UDP Specification**: Maps packet fields to schema columns
- **Domain Entities**: `LapTrace`, `CarSetupSnapshot`, `TelemetrySample`
- **Repository Interface**: `ITelemetryRepository` (domain/interfaces)
- **Migration Runner**: `src/infrastructure/migrations/migration_runner.py`
- **Test Suite**: `tests/infrastructure/test_telemetry_schema.py`
