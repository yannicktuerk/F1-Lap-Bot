#!/usr/bin/env python3
"""
Complete history recalculation tool for the F1 Lap Bot.

This script rebuilds all derived data from scratch, ensuring 100% data consistency.
It processes all lap times chronologically and recalculates:
- Personal Bests (PBs)
- Overall Track Records (TRs)
- ELO Ratings

Run this script on the server to fix any data inconsistencies.
"""

import asyncio
import sqlite3
import sys
import os
from datetime import datetime

# --- Setup paths to import from src ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.infrastructure.persistence.sqlite_lap_time_repository import SQLiteLapTimeRepository
from src.infrastructure.persistence.sqlite_driver_rating_repository import SQLiteDriverRatingRepository
from src.application.use_cases.update_elo_ratings import UpdateEloRatingsUseCase
from src.domain.entities.lap_time import LapTime
from src.domain.value_objects.time_format import TimeFormat
from src.domain.value_objects.track_name import TrackName

# --- Database Paths ---
# Determine the correct path - databases are in project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Try different possible locations for the databases
POSSIBLE_DB_DIRS = [
    SCRIPT_DIR,  # Same directory as script
    os.path.join(SCRIPT_DIR, "data"),  # data subdirectory
    os.path.dirname(SCRIPT_DIR),  # Parent directory (if script is in src/)
]

# Find the correct database directory
DB_DIR = None
for possible_dir in POSSIBLE_DB_DIRS:
    test_lap_db = os.path.join(possible_dir, "lap_times.db")
    if os.path.exists(test_lap_db):
        DB_DIR = possible_dir
        break

if DB_DIR is None:
    print("❌ Could not find lap_times.db in any expected location!")
    print("Searched in:")
    for dir_path in POSSIBLE_DB_DIRS:
        print(f"  - {dir_path}")
    sys.exit(1)

LAP_TIMES_DB = os.path.join(DB_DIR, "lap_times.db")
ELO_DB = os.path.join(DB_DIR, "f1_lap_bot.db")


async def clear_derived_data():
    """Wipe all calculated data to prepare for a fresh rebuild."""
    print("🔥 Clearing all derived data (ELO, PBs, TRs)...")
    print(f"  📂 Script directory: {SCRIPT_DIR}")
    print(f"  📂 Database directory: {DB_DIR}")
    print(f"  📄 Lap times DB: {LAP_TIMES_DB}")
    print(f"  📄 ELO DB: {ELO_DB}")
    
    # Database existence is already checked during path discovery
    
    # Clear ELO ratings
    try:
        os.remove(ELO_DB)
        print("  🗑️ Deleted old ELO database.")
    except FileNotFoundError:
        print("  🤷 No old ELO database to delete.")
        
    # Reset PB/TR flags in lap_times
    conn = sqlite3.connect(LAP_TIMES_DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE lap_times SET is_personal_best = 0, is_overall_best = 0")
    conn.commit()
    conn.close()
    print("  🚩 Reset all Personal Best and Track Record flags.")


async def fix_null_sectors():
    """Fix NULL sectors in the database by setting them to 0."""
    print("\n🛠️ Fixing NULL sectors in database...")
    
    conn = sqlite3.connect(LAP_TIMES_DB)
    cursor = conn.cursor()
    
    # Count NULL sectors first
    cursor.execute("SELECT COUNT(*) FROM lap_times WHERE sector1_ms IS NULL OR sector2_ms IS NULL OR sector3_ms IS NULL")
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        print(f"  🔧 Found {null_count} lap times with NULL sectors, fixing...")
        
        # Fix NULL sectors by setting them to 0
        cursor.execute("UPDATE lap_times SET sector1_ms = COALESCE(sector1_ms, 0), sector2_ms = COALESCE(sector2_ms, 0), sector3_ms = COALESCE(sector3_ms, 0)")
        conn.commit()
        
        print(f"  ✅ Fixed {null_count} lap times with NULL sectors.")
    else:
        print("  ✅ No NULL sectors found, database is clean.")
    
    conn.close()


async def rebuild_history():
    """Re-process all lap times chronologically to fix all stats."""
    print("\n🔄 Starting historical recalculation...")
    
    lap_repo = SQLiteLapTimeRepository(LAP_TIMES_DB)
    elo_repo = SQLiteDriverRatingRepository(ELO_DB)
    update_elo_use_case = UpdateEloRatingsUseCase(elo_repo, lap_repo)

    # Load all lap times, sorted from oldest to newest
    conn = sqlite3.connect(LAP_TIMES_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lap_times ORDER BY created_at ASC")
    all_laps_rows = cursor.fetchall()
    conn.close()

    total_laps = len(all_laps_rows)
    print(f"  📂 Found {total_laps} lap times to process.")

    # In-memory tracking for current bests
    personal_bests = {}
    track_records = {}

    for i, row in enumerate(all_laps_rows):
        # Convert row to LapTime entity
        lap_entity = lap_repo._row_to_lap_time(row)
        
        # --- 1. Recalculate Personal Best ---
        pb_key = (lap_entity.user_id, lap_entity.track_name.key)
        is_pb = False
        if pb_key not in personal_bests or lap_entity.time_format.total_milliseconds < personal_bests[pb_key]:
            is_pb = True
            personal_bests[pb_key] = lap_entity.time_format.total_milliseconds

        # --- 2. Recalculate Track Record ---
        tr_key = lap_entity.track_name.key
        is_tr = False
        if tr_key not in track_records or lap_entity.time_format.total_milliseconds < track_records[tr_key]:
            is_tr = True
            track_records[tr_key] = lap_entity.time_format.total_milliseconds

        # --- 3. Update the Lap Record in DB ---
        conn = sqlite3.connect(LAP_TIMES_DB)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE lap_times SET is_personal_best = ?, is_overall_best = ? WHERE lap_id = ?",
            (is_pb, is_tr, lap_entity.lap_id)
        )
        conn.commit()
        conn.close()
        
        # --- 4. Update ELO based on this lap ---
        await update_elo_use_case.execute(lap_entity)

        if (i + 1) % 10 == 0 or (i + 1) == total_laps:
            print(f"  ⚡ Processed {i+1}/{total_laps} laps... (Current: {lap_entity.username} on {lap_entity.track_name.short_name})")

    print("\n✅ Historical data rebuild complete!")


async def finalize_data():
    """Update usernames and show final summary."""
    print("\n🎨 Finalizing data and updating usernames...")
    
    # Get all unique users and their latest names
    conn = sqlite3.connect(LAP_TIMES_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM lap_times")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    elo_conn = sqlite3.connect(ELO_DB)
    elo_cursor = elo_conn.cursor()

    for user_id in user_ids:
        # Get latest username from lap_times db
        laps_conn = sqlite3.connect(LAP_TIMES_DB)
        laps_cursor = laps_conn.cursor()
        laps_cursor.execute("SELECT username FROM lap_times WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        latest_username = laps_cursor.fetchone()[0]
        laps_conn.close()

        # Update the username in the ELO database
        elo_cursor.execute("UPDATE driver_ratings SET username = ? WHERE user_id = ?", (latest_username, user_id))
    
    elo_conn.commit()
    elo_conn.close()
    print("  ✨ Usernames synced to latest versions.")

    # --- Final Summary ---
    print("\n🏆 Final ELO Leaderboard:")
    elo_conn = sqlite3.connect(ELO_DB)
    elo_conn.row_factory = sqlite3.Row
    elo_cursor = elo_conn.cursor()
    elo_cursor.execute("SELECT * FROM driver_ratings ORDER BY current_elo DESC")
    final_ratings = elo_cursor.fetchall()
    elo_conn.close()
    
    for i, rating in enumerate(final_ratings):
        print(f"  {i+1}. {rating['username']}: {rating['current_elo']} ELO ({rating['wins']}W/{rating['losses']}L)")


async def main():
    await clear_derived_data()
    await fix_null_sectors()  # NEW: Fix NULL sectors before rebuilding
    await rebuild_history()
    await finalize_data()
    print("\n🎉 All stats have been successfully rebuilt from scratch!")


if __name__ == "__main__":
    asyncio.run(main())

