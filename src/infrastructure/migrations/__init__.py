"""Database migration module for telemetry system.

This module provides schema migration functionality for the telemetry database.
Migrations are SQL-file based and applied in sequential order with version tracking.
"""

from .migration_runner import MigrationRunner, run_telemetry_migrations

__all__ = ["MigrationRunner", "run_telemetry_migrations"]
