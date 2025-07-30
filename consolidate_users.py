#!/usr/bin/env python3
"""
Script to consolidate duplicate user entries.
This merges lap times from duplicate user_ids into a single user_id.
"""

import sqlite3
from typing import Dict, List, Tuple

# Define the user ID mappings (old_user_id -> new_user_id)
USER_CONSOLIDATIONS = {
    # Wadlbeißer and Quentin are the same person
    "686989749373632533": "686989749373632532",  # Wadlbeißer -> Quentin
    
    # GuaderTyp and Pasi are the same person  
    "421082604054511638": "421082604054511639",  # GuaderTyp -> Pasi
}

def consolidate_lap_times():
    """Consolidate lap times by merging duplicate user IDs."""
    print("🔄 Consolidating duplicate user entries...")
    
    conn = sqlite3.connect('data/lap_times.db')
    cursor = conn.cursor()
    
    # Process each consolidation
    for old_user_id, new_user_id in USER_CONSOLIDATIONS.items():
        print(f"🔀 Merging {old_user_id} -> {new_user_id}")
        
        # Get the preferred username (most recent)
        cursor.execute("""
            SELECT username FROM lap_times 
            WHERE user_id IN (?, ?) 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (old_user_id, new_user_id))
        
        result = cursor.fetchone()
        preferred_username = result[0] if result else "Unknown"
        print(f"  📝 Using username: {preferred_username}")
        
        # Update all lap times from old_user_id to new_user_id
        cursor.execute("""
            UPDATE lap_times 
            SET user_id = ?, username = ?
            WHERE user_id = ?
        """, (new_user_id, preferred_username, old_user_id))
        
        updated_rows = cursor.rowcount
        print(f"  ✅ Updated {updated_rows} lap time records")
        
        # Also update any existing records with the new_user_id to have consistent username
        cursor.execute("""
            UPDATE lap_times 
            SET username = ?
            WHERE user_id = ?
        """, (preferred_username, new_user_id))
        
        updated_existing = cursor.rowcount
        print(f"  📝 Updated {updated_existing} existing records with consistent username")
    
    conn.commit()
    conn.close()
    
    print("✅ User consolidation complete!")

def consolidate_elo_ratings():
    """Consolidate ELO ratings by removing old user IDs."""
    print("🔄 Cleaning up ELO ratings...")
    
    try:
        conn = sqlite3.connect('data/f1_lap_bot.db')
        cursor = conn.cursor()
        
        # Remove old user IDs from ELO ratings (they will be recalculated)
        for old_user_id in USER_CONSOLIDATIONS.keys():
            cursor.execute("DELETE FROM driver_ratings WHERE user_id = ?", (old_user_id,))
            deleted_rows = cursor.rowcount
            print(f"🗑️ Removed old ELO rating for {old_user_id} ({deleted_rows} records)")
        
        conn.commit()
        conn.close()
        print("✅ ELO ratings cleanup complete!")
        
    except Exception as e:
        print(f"⚠️ ELO cleanup failed (this is OK if table doesn't exist): {e}")

def show_consolidation_summary():
    """Show summary of users after consolidation."""
    print("\n📊 User summary after consolidation:")
    
    conn = sqlite3.connect('data/lap_times.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, username, COUNT(*) as lap_count
        FROM lap_times 
        GROUP BY user_id, username
        ORDER BY username
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    for user_id, username, lap_count in results:
        print(f"  👤 {username} ({user_id}): {lap_count} laps")

if __name__ == "__main__":
    consolidate_lap_times()
    consolidate_elo_ratings()
    show_consolidation_summary()
    
    print("\n🏁 Now run 'python calculate_elo.py' to recalculate ELO ratings with consolidated data!")
