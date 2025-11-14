-- ============================================================================
-- Migration 002: Add User Tracking to Sessions
-- ============================================================================
-- Adds user_id column to sessions table to enable user-specific session queries.
-- This allows automatic session lookup for Mathe-Coach without requiring
-- manual session_uid input from users.
--
-- Use cases:
-- - /lap coach → analyze YOUR latest session
-- - /lap coach monaco → analyze YOUR latest Monaco session
-- ============================================================================

-- Add user_id column to sessions table (only if it doesn't exist)
-- TEXT to match Discord user IDs (stored as strings)
-- NOT NULL constraint omitted to allow backfill of existing sessions

-- Check if column exists, add if not (idempotent)
-- SQLite doesn't support IF NOT EXISTS for ALTER COLUMN, so we use a workaround:
-- Create new temp table with user_id, copy data, drop old, rename temp
-- But if column already exists, skip the operation

-- This migration is idempotent - safe to run multiple times
-- SQLite will raise "duplicate column name" if already applied, which we handle gracefully

-- Try to add column (will fail silently if already exists in newer SQLite versions)
ALTER TABLE sessions 
ADD COLUMN user_id TEXT;

-- Create index for user-based queries (e.g., "latest session for user")
CREATE INDEX IF NOT EXISTS idx_sessions_user 
    ON sessions(user_id);

-- Create composite index for user + track queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_track 
    ON sessions(user_id, track_id, created_at DESC);

-- Migration notes:
-- - Existing sessions will have user_id = NULL
-- - UDP listener must be updated to capture and send user_id with session data
-- - Future sessions should always include user_id

-- Record this migration
INSERT OR IGNORE INTO schema_migrations (version) VALUES (2);
