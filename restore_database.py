#!/usr/bin/env python3
"""
Database restoration script for F1 Lap Bot.

This script:
1. Reads the existing lap_times.db (if it exists)
2. Extracts all lap time data
3. Creates a clean new lap_times.db with proper structure
4. Inserts all data back with NULL sector fixes
5. Ensures data integrity

Run this before rebuild_and_recalculate.py to fix database issues.
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

def find_database_path():
    """Find the correct database path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, "lap_times.db"),  # Project root
        os.path.join(script_dir, "data", "lap_times.db"),  # data folder
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Return project root path as default (will be created)
    return possible_paths[0]

def backup_existing_database(db_path):
    """Create a backup of the existing database."""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"  📋 Created backup: {backup_path}")
        return backup_path
    return None

def extract_lap_data(db_path):
    """Extract all lap time data from existing database."""
    if not os.path.exists(db_path):
        print(f"  ⚠️  No existing database found at {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lap_times'")
        if not cursor.fetchone():
            print("  ⚠️  No lap_times table found in database")
            conn.close()
            return []
        
        # Extract all data
        cursor.execute("SELECT * FROM lap_times ORDER BY created_at ASC")
        rows = cursor.fetchall()
        conn.close()
        
        print(f"  📂 Extracted {len(rows)} lap times from existing database")
        return [dict(row) for row in rows]
        
    except Exception as e:
        print(f"  ❌ Error reading existing database: {e}")
        return []

def create_clean_database(db_path):
    """Create a new, clean database with proper structure."""
    # Remove old database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  🗑️ Removed old database")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table with proper structure
    cursor.execute("""
        CREATE TABLE lap_times (
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
            is_bot BOOLEAN DEFAULT 0,
            sector1_ms INTEGER DEFAULT 0,
            sector2_ms INTEGER DEFAULT 0,
            sector3_ms INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX idx_track_time ON lap_times(track_key, total_milliseconds)")
    cursor.execute("CREATE INDEX idx_user_track ON lap_times(user_id, track_key)")
    cursor.execute("CREATE INDEX idx_created_at ON lap_times(created_at DESC)")
    
    conn.commit()
    conn.close()
    print(f"  ✅ Created clean database with proper structure")

def insert_lap_data(db_path, lap_data):
    """Insert lap data into the clean database."""
    if not lap_data:
        print("  ⚠️  No data to insert")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    fixed_sectors_count = 0
    
    for lap in lap_data:
        try:
            # Fix NULL sectors
            sector1_ms = lap.get('sector1_ms') or 0
            sector2_ms = lap.get('sector2_ms') or 0  
            sector3_ms = lap.get('sector3_ms') or 0
            
            if lap.get('sector1_ms') is None or lap.get('sector2_ms') is None or lap.get('sector3_ms') is None:
                fixed_sectors_count += 1
            
            # Generate lap_id if missing
            lap_id = lap.get('lap_id')
            if not lap_id:
                import uuid
                lap_id = str(uuid.uuid4())
            
            # Ensure required fields exist
            user_id = lap.get('user_id', 'unknown')
            username = lap.get('username', 'Unknown User')
            track_key = lap.get('track_key', 'unknown')
            
            # Time components
            time_minutes = lap.get('time_minutes', 0)
            time_seconds = lap.get('time_seconds', 0)
            time_milliseconds = lap.get('time_milliseconds', 0)
            total_milliseconds = lap.get('total_milliseconds', 0)
            
            # Flags
            is_personal_best = lap.get('is_personal_best', 0)
            is_overall_best = lap.get('is_overall_best', 0)
            is_bot = lap.get('is_bot', 0)
            
            # Created at
            created_at = lap.get('created_at')
            if not created_at:
                created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO lap_times (
                    lap_id, user_id, username, track_key,
                    time_minutes, time_seconds, time_milliseconds, total_milliseconds,
                    is_personal_best, is_overall_best, is_bot,
                    sector1_ms, sector2_ms, sector3_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lap_id, user_id, username, track_key,
                time_minutes, time_seconds, time_milliseconds, total_milliseconds,
                is_personal_best, is_overall_best, is_bot,
                sector1_ms, sector2_ms, sector3_ms, created_at
            ))
            
            inserted_count += 1
            
        except Exception as e:
            print(f"  ⚠️  Error inserting lap {lap.get('lap_id', 'unknown')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Inserted {inserted_count} lap times")
    if fixed_sectors_count > 0:
        print(f"  🔧 Fixed {fixed_sectors_count} lap times with NULL sectors")

def verify_database(db_path):
    """Verify the restored database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count total records
    cursor.execute("SELECT COUNT(*) FROM lap_times")
    total_count = cursor.fetchone()[0]
    
    # Count NULL sectors (should be 0 now)
    cursor.execute("SELECT COUNT(*) FROM lap_times WHERE sector1_ms IS NULL OR sector2_ms IS NULL OR sector3_ms IS NULL")
    null_sectors = cursor.fetchone()[0]
    
    # Count unique users
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM lap_times")
    unique_users = cursor.fetchone()[0]
    
    # Count unique tracks
    cursor.execute("SELECT COUNT(DISTINCT track_key) FROM lap_times")
    unique_tracks = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n📊 Database Verification:")
    print(f"  Total lap times: {total_count}")
    print(f"  Unique users: {unique_users}")
    print(f"  Unique tracks: {unique_tracks}")
    print(f"  NULL sectors: {null_sectors} (should be 0)")
    
    return null_sectors == 0

def main():
    print("🔄 Starting database restoration...")
    
    # Find database path
    db_path = find_database_path()
    print(f"📂 Database path: {db_path}")
    
    # Create backup of existing database
    backup_path = backup_existing_database(db_path)
    
    # Extract data from existing database
    print("\n📋 Extracting existing data...")
    lap_data = extract_lap_data(db_path)
    
    # Create clean database
    print("\n🏗️ Creating clean database...")
    create_clean_database(db_path)
    
    # Insert data
    print("\n📥 Inserting lap time data...")
    insert_lap_data(db_path, lap_data)
    
    # Verify database
    print("\n🔍 Verifying restored database...")
    if verify_database(db_path):
        print("\n✅ Database restoration completed successfully!")
        print("\nNext steps:")
        print("1. Run: python3 rebuild_and_recalculate.py")
        print("2. Restart the bot")
        print("3. Test with /stats, /global, /rating commands")
    else:
        print("\n⚠️  Database restoration completed with warnings.")
        print("Check the verification results above.")
    
    if backup_path:
        print(f"\n💾 Original database backed up to: {backup_path}")

if __name__ == "__main__":
    main()
