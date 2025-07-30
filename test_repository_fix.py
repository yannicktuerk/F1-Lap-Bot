#!/usr/bin/env python3
"""Test script to verify the SQLite repository fix for NULL sector handling."""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.infrastructure.persistence.sqlite_lap_time_repository import SQLiteLapTimeRepository
from src.domain.value_objects.track_name import TrackName

async def test_repository_loading():
    """Test loading lap times from the database to check NULL sector handling."""
    print("🔧 Testing SQLite repository with NULL sector handling...")
    
    # Create repository instance
    repo = SQLiteLapTimeRepository("data/lap_times.db")
    
    try:
        # Try to load track statistics (this would fail if NULL handling is broken)
        track = TrackName("bahrain")
        stats = await repo.get_track_statistics(track)
        print(f"✅ Track statistics loaded successfully for {track.display_name}: {stats}")
        
        # Try to find recent lap times
        recent_times = await repo.find_recent_by_track(track, 5)
        print(f"✅ Recent lap times loaded: {len(recent_times)} entries")
        
        # Test loading specific lap times
        for i, lap_time in enumerate(recent_times[:2]):
            print(f"✅ Lap {i+1}: {lap_time.username} - {lap_time.time_format} (sectors: {lap_time.sector1_ms}, {lap_time.sector2_ms}, {lap_time.sector3_ms})")
        
        # Try to load best lap time
        best_lap = await repo.find_best_by_track(track)
        if best_lap:
            print(f"✅ Best lap loaded: {best_lap.username} - {best_lap.time_format}")
        
        print("🎉 All tests passed! NULL sector handling is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_repository_loading())
    sys.exit(0 if success else 1)
