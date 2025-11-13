"""Migration runner for telemetry database schema management.

This module provides a migration system for evolving the telemetry database
schema over time. It supports:
- Forward-only migration application (no rollbacks)
- Schema version tracking via schema_migrations table
- Idempotent execution (safe to run multiple times)
- Foreign key constraint enforcement
- SQL file-based migrations

Design principles:
- Migrations are immutable once applied (never modify applied migrations)
- Each migration is a single SQL file numbered sequentially (001, 002, etc.)
- Migration state tracked in schema_migrations table
- Forward-only: no rollback support (use new migrations to fix issues)
"""

import os
import aiosqlite
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Manages database schema migrations for telemetry database.
    
    Applies SQL migrations in sequential order, tracking version state
    to ensure each migration is applied exactly once.
    """
    
    def __init__(self, database_path: str):
        """Initialize migration runner.
        
        Args:
            database_path: Path to SQLite database file (will be created if not exists).
        """
        self._database_path = database_path
        self._migrations_dir = Path(__file__).parent
    
    async def run_migrations(self) -> None:
        """Apply all pending migrations to the database.
        
        Migrations are applied in sequential order based on filename numbering.
        Each migration is executed within a transaction for atomicity.
        
        Raises:
            Exception: If migration fails (database remains in previous state).
        """
        logger.info(f"Starting migration runner for database: {self._database_path}")
        
        # Enable foreign keys globally for the migration process
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.commit()
        
        # Get list of migration files
        migration_files = self._discover_migration_files()
        logger.info(f"Found {len(migration_files)} migration file(s)")
        
        if not migration_files:
            logger.warning("No migration files found in migrations directory")
            return
        
        # Get current schema version
        current_version = await self._get_current_version()
        logger.info(f"Current schema version: {current_version}")
        
        # Apply each pending migration
        for migration_file in migration_files:
            migration_version = self._extract_version_from_filename(migration_file)
            
            if migration_version <= current_version:
                logger.debug(f"Skipping already applied migration: {migration_file}")
                continue
            
            logger.info(f"Applying migration: {migration_file}")
            await self._apply_migration(migration_file, migration_version)
            logger.info(f"Successfully applied migration {migration_version}")
        
        final_version = await self._get_current_version()
        logger.info(f"Migration complete. Final schema version: {final_version}")
    
    def _discover_migration_files(self) -> List[str]:
        """Discover SQL migration files in migrations directory.
        
        Returns:
            List of migration filenames sorted by version number.
            Example: ["001_telemetry_schema.sql", "002_add_indexes.sql"]
        """
        migration_files = []
        
        if not self._migrations_dir.exists():
            logger.error(f"Migrations directory not found: {self._migrations_dir}")
            return migration_files
        
        # Find all .sql files
        for file in self._migrations_dir.glob("*.sql"):
            filename = file.name
            
            # Skip non-migration SQL files (must start with digits)
            if not filename[0].isdigit():
                logger.debug(f"Skipping non-migration file: {filename}")
                continue
            
            migration_files.append(filename)
        
        # Sort by version number (extracted from filename)
        migration_files.sort(key=self._extract_version_from_filename)
        
        return migration_files
    
    def _extract_version_from_filename(self, filename: str) -> int:
        """Extract version number from migration filename.
        
        Args:
            filename: Migration filename (e.g., "001_telemetry_schema.sql")
            
        Returns:
            Version number as integer (e.g., 1)
            
        Raises:
            ValueError: If filename doesn't match expected format.
        """
        try:
            # Extract digits from start of filename
            version_str = ""
            for char in filename:
                if char.isdigit():
                    version_str += char
                else:
                    break
            
            if not version_str:
                raise ValueError(f"No version number found in filename: {filename}")
            
            return int(version_str)
        
        except Exception as e:
            logger.error(f"Failed to extract version from filename '{filename}': {e}")
            raise ValueError(f"Invalid migration filename format: {filename}") from e
    
    async def _get_current_version(self) -> int:
        """Get current schema version from database.
        
        Returns:
            Current schema version (0 if no migrations applied yet).
        """
        try:
            async with aiosqlite.connect(self._database_path) as db:
                # Check if schema_migrations table exists
                cursor = await db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_migrations'
                """)
                table_exists = await cursor.fetchone()
                
                if not table_exists:
                    logger.debug("schema_migrations table does not exist yet")
                    return 0
                
                # Get maximum version from schema_migrations
                cursor = await db.execute("""
                    SELECT COALESCE(MAX(version), 0) FROM schema_migrations
                """)
                result = await cursor.fetchone()
                return result[0] if result else 0
        
        except Exception as e:
            logger.error(f"Failed to get current schema version: {e}")
            raise
    
    async def _apply_migration(self, filename: str, version: int) -> None:
        """Apply a single migration file to the database.
        
        Executes the SQL file within a transaction. If migration fails,
        the transaction is rolled back and database remains unchanged.
        
        Args:
            filename: Migration SQL filename.
            version: Version number of this migration.
            
        Raises:
            Exception: If migration fails.
        """
        migration_path = self._migrations_dir / filename
        
        if not migration_path.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_path}")
        
        # Read migration SQL
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        if not migration_sql.strip():
            raise ValueError(f"Migration file is empty: {filename}")
        
        # Apply migration within transaction
        async with aiosqlite.connect(self._database_path) as db:
            try:
                # Enable foreign keys for this connection
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Execute migration SQL
                await db.executescript(migration_sql)
                
                # Commit transaction
                await db.commit()
                
                logger.info(f"Migration {version} applied successfully")
            
            except Exception as e:
                logger.error(f"Migration {version} failed: {e}")
                # Transaction automatically rolled back on exception
                raise
    
    async def get_migration_status(self) -> dict:
        """Get current migration status and history.
        
        Returns:
            Dictionary with migration information:
            - current_version: int (current schema version)
            - applied_migrations: List[dict] (history of applied migrations)
            - pending_migrations: List[str] (filenames of pending migrations)
        """
        current_version = await self._get_current_version()
        migration_files = self._discover_migration_files()
        
        # Get applied migrations history
        applied_migrations = []
        try:
            async with aiosqlite.connect(self._database_path) as db:
                cursor = await db.execute("""
                    SELECT version, applied_at 
                    FROM schema_migrations 
                    ORDER BY version
                """)
                rows = await cursor.fetchall()
                
                for row in rows:
                    applied_migrations.append({
                        "version": row[0],
                        "applied_at": row[1]
                    })
        except:
            # schema_migrations table doesn't exist yet
            pass
        
        # Get pending migrations
        pending_migrations = [
            f for f in migration_files
            if self._extract_version_from_filename(f) > current_version
        ]
        
        return {
            "current_version": current_version,
            "applied_migrations": applied_migrations,
            "pending_migrations": pending_migrations
        }


async def run_telemetry_migrations(database_path: Optional[str] = None) -> None:
    """Convenience function to run telemetry database migrations.
    
    Args:
        database_path: Optional path to telemetry database.
            If None, uses default location in project root.
    """
    if database_path is None:
        # Default: telemetry.db in project root (next to lap_times.db)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        database_path = str(project_root / "telemetry.db")
    
    runner = MigrationRunner(database_path)
    await runner.run_migrations()


# For direct execution (testing)
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(run_telemetry_migrations())
