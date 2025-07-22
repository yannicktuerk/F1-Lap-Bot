"""
Safe track deletion utility that handles ELO ratings and existing lap times properly.

This utility ensures that when tracks are removed from the TRACK_DATA, 
existing lap times and ELO calculations remain functional.
"""

import sqlite3
from typing import List, Dict, Any
import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from src.domain.value_objects.track_name import TrackName


class SafeTrackDeletion:
    """Utility for safely removing tracks while preserving ELO integrity."""
    
    def __init__(self, db_path: str = "f1_lap_bot.db"):
        self.db_path = db_path
    
    def get_orphaned_tracks(self) -> List[str]:
        """Find track_keys in database that no longer exist in TRACK_DATA."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT track_key FROM lap_times")
            db_tracks = {row[0] for row in cursor.fetchall()}
            
            valid_tracks = set(TrackName.TRACK_DATA.keys())
            orphaned = db_tracks - valid_tracks
            
            return list(orphaned)
    
    def get_track_statistics(self, track_key: str) -> Dict[str, Any]:
        """Get statistics for a specific track before deletion."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count lap times
            cursor.execute("SELECT COUNT(*) FROM lap_times WHERE track_key = ?", (track_key,))
            lap_count = cursor.fetchone()[0]
            
            # Count unique users
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM lap_times WHERE track_key = ?", (track_key,))
            user_count = cursor.fetchone()[0]
            
            # Get fastest time
            cursor.execute("""
                SELECT username, total_milliseconds, created_at 
                FROM lap_times 
                WHERE track_key = ? 
                ORDER BY total_milliseconds ASC 
                LIMIT 1
            """, (track_key,))
            fastest_time = cursor.fetchone()
            
            return {
                'track_key': track_key,
                'total_laps': lap_count,
                'unique_users': user_count,
                'fastest_time': fastest_time,
                'can_delete_safely': lap_count == 0  # Only safe if no lap times exist
            }
    
    def delete_track_safely(self, track_key: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Safely delete a track and all associated data.
        
        Args:
            track_key: The track key to delete
            confirm: Must be True to actually perform deletion
            
        Returns:
            Dictionary with deletion results and statistics
        """
        stats = self.get_track_statistics(track_key)
        
        if not confirm:
            return {
                'status': 'preview',
                'message': 'Preview mode - no data deleted',
                'statistics': stats,
                'warning': 'Set confirm=True to actually delete data'
            }
        
        if stats['total_laps'] == 0:
            return {
                'status': 'success',
                'message': f'Track {track_key} had no lap times - safe to remove from TRACK_DATA',
                'statistics': stats
            }
        
        # Track has data - perform full cleanup
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Delete all lap times for this track
                cursor.execute("DELETE FROM lap_times WHERE track_key = ?", (track_key,))
                deleted_laps = cursor.rowcount
                
                # Note: ELO ratings are user-based, not track-based, so they remain intact
                # This is actually good because user skill ratings persist
                
                conn.commit()
                
                return {
                    'status': 'success',
                    'message': f'Successfully deleted track {track_key}',
                    'deleted_lap_times': deleted_laps,
                    'statistics': stats,
                    'elo_note': 'ELO ratings preserved - user skills remain intact'
                }
                
            except Exception as e:
                conn.rollback()
                return {
                    'status': 'error',
                    'message': f'Failed to delete track: {str(e)}',
                    'statistics': stats
                }
    
    def preview_deletion_impact(self) -> Dict[str, Any]:
        """Preview what would happen if orphaned tracks are cleaned up."""
        orphaned = self.get_orphaned_tracks()
        
        if not orphaned:
            return {
                'status': 'clean',
                'message': 'No orphaned tracks found - database is clean',
                'orphaned_tracks': []
            }
        
        impact = []
        total_affected_laps = 0
        total_affected_users = 0
        
        for track_key in orphaned:
            stats = self.get_track_statistics(track_key)
            impact.append(stats)
            total_affected_laps += stats['total_laps']
            total_affected_users += stats['unique_users']
        
        return {
            'status': 'orphaned_found',
            'message': f'Found {len(orphaned)} orphaned tracks',
            'orphaned_tracks': orphaned,
            'impact_details': impact,
            'total_affected_laps': total_affected_laps,
            'total_affected_users': total_affected_users,
            'elo_impact': 'ELO ratings will remain intact (user-based, not track-based)'
        }
    
    def cleanup_orphaned_tracks(self, confirm: bool = False) -> Dict[str, Any]:
        """Clean up all orphaned tracks at once."""
        impact = self.preview_deletion_impact()
        
        if impact['status'] == 'clean':
            return impact
        
        if not confirm:
            return {
                **impact,
                'status': 'preview',
                'warning': 'Set confirm=True to actually delete orphaned data'
            }
        
        results = []
        for track_key in impact['orphaned_tracks']:
            result = self.delete_track_safely(track_key, confirm=True)
            results.append({
                'track': track_key,
                'result': result
            })
        
        return {
            'status': 'cleanup_complete',
            'message': f'Cleaned up {len(impact["orphaned_tracks"])} orphaned tracks',
            'results': results,
            'original_impact': impact
        }


def demonstrate_safe_deletion():
    """Demonstrate how to safely delete tracks."""
    cleaner = SafeTrackDeletion()
    
    print("🔍 Checking for orphaned tracks...")
    preview = cleaner.preview_deletion_impact()
    print(f"Status: {preview['status']}")
    print(f"Message: {preview['message']}")
    
    if preview['status'] == 'orphaned_found':
        print(f"\n📊 Impact Summary:")
        print(f"- Orphaned tracks: {len(preview['orphaned_tracks'])}")
        print(f"- Total affected lap times: {preview['total_affected_laps']}")
        print(f"- Total affected users: {preview['total_affected_users']}")
        print(f"- ELO impact: {preview['elo_impact']}")
        
        print(f"\n📋 Detailed breakdown:")
        for detail in preview['impact_details']:
            print(f"  • {detail['track_key']}: {detail['total_laps']} laps, {detail['unique_users']} users")
        
        print(f"\n💡 To actually clean up, run:")
        print(f"   cleaner.cleanup_orphaned_tracks(confirm=True)")
    
    return preview


if __name__ == "__main__":
    demonstrate_safe_deletion()
