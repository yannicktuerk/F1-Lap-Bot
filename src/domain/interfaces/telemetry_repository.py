"""Repository interface for telemetry data persistence (Port).

This module defines the ITelemetryRepository interface following Clean Architecture
and the Dependency Inversion Principle. The interface defines contracts for
persisting and retrieving telemetry data (LapTrace, CarSetupSnapshot, Sessions)
without any implementation details.

The interface is defined in the domain layer and implemented in the infrastructure
layer, allowing the domain to remain independent of persistence mechanisms.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..entities.lap_trace import LapTrace
from ..entities.car_setup_snapshot import CarSetupSnapshot


class ITelemetryRepository(ABC):
    """Abstract repository interface for telemetry data persistence.
    
    Defines contracts for persisting and retrieving:
    - LapTrace entities (laps with telemetry samples)
    - CarSetupSnapshot entities (car configuration snapshots)
    - Session metadata
    
    All methods are async to support async database operations.
    Methods return domain entities/value objects only - no infrastructure types.
    """
    
    # =============================================================================
    # LapTrace Operations
    # =============================================================================
    
    @abstractmethod
    async def save_lap_trace(self, lap_trace: LapTrace) -> None:
        """Persist complete lap trace with all telemetry samples.
        
        Saves the lap trace entity including:
        - Lap metadata (session_uid, lap_number, car_index, etc.)
        - All telemetry samples in chronological order
        - Associated car setup (if present)
        
        Args:
            lap_trace: LapTrace entity to persist.
            
        Raises:
            Exception: If persistence fails (implementation-specific).
        """
        pass
    
    @abstractmethod
    async def get_lap_trace(self, trace_id: str) -> Optional[LapTrace]:
        """Retrieve complete lap trace by ID.
        
        Reconstructs the full LapTrace entity including:
        - All telemetry samples in chronological order
        - Associated car setup snapshot (if exists)
        
        Args:
            trace_id: UUID of the lap trace to retrieve.
            
        Returns:
            LapTrace entity if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def get_latest_lap_trace(self, session_uid: str) -> Optional[LapTrace]:
        """Get most recent lap trace for a session.
        
        Returns the lap with the highest lap_number in the specified session.
        Useful for tracking current lap during live telemetry ingestion.
        
        Args:
            session_uid: F1 25 session unique identifier.
            
        Returns:
            Most recent LapTrace for the session, or None if no laps exist.
        """
        pass
    
    @abstractmethod
    async def list_lap_traces(
        self,
        session_uid: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[LapTrace]:
        """List lap traces for a session with pagination.
        
        Returns laps ordered by lap_number descending (most recent first).
        Supports pagination for large session with many laps.
        
        Args:
            session_uid: F1 25 session unique identifier.
            limit: Maximum number of laps to return (default: 50).
            offset: Number of laps to skip for pagination (default: 0).
            
        Returns:
            List of LapTrace entities ordered by lap_number desc.
            Empty list if no laps found.
        """
        pass
    
    @abstractmethod
    async def list_lap_traces_by_track(
        self,
        track_id: str,
        limit: int = 100,
        valid_only: bool = True
    ) -> List[LapTrace]:
        """Get all lap traces for a specific track across all sessions.
        
        Useful for track-specific analysis, finding personal bests per track,
        or comparing performance across sessions on the same circuit.
        
        Args:
            track_id: F1 25 track identifier (e.g., "monaco", "silverstone").
            limit: Maximum number of laps to return (default: 100).
            valid_only: If True, return only valid laps (default: True).
            
        Returns:
            List of LapTrace entities for the track.
            Empty list if no laps found.
        """
        pass
    
    @abstractmethod
    async def get_fastest_lap_trace(
        self,
        track_id: Optional[str] = None,
        session_uid: Optional[str] = None
    ) -> Optional[LapTrace]:
        """Get fastest valid lap trace, optionally filtered by track or session.
        
        Args:
            track_id: Optional track filter (if None, search all tracks).
            session_uid: Optional session filter (if None, search all sessions).
            
        Returns:
            Fastest LapTrace matching filters, or None if no valid laps exist.
        """
        pass
    
    @abstractmethod
    async def delete_lap_trace(self, trace_id: str) -> bool:
        """Delete lap trace and all associated telemetry samples.
        
        Cascading delete removes:
        - Lap metadata
        - All telemetry samples for this lap
        - Association with car setup (but not the setup itself)
        
        Args:
            trace_id: UUID of the lap trace to delete.
            
        Returns:
            True if lap was deleted, False if lap not found.
        """
        pass
    
    # =============================================================================
    # CarSetupSnapshot Operations
    # =============================================================================
    
    @abstractmethod
    async def save_setup_snapshot(self, setup: CarSetupSnapshot) -> None:
        """Persist car setup snapshot.
        
        Saves all 23 setup parameters from F1 25 PacketCarSetupData.
        Setup can be associated with multiple laps.
        
        Args:
            setup: CarSetupSnapshot entity to persist.
            
        Raises:
            Exception: If persistence fails (implementation-specific).
        """
        pass
    
    @abstractmethod
    async def get_setup_snapshot(self, setup_id: str) -> Optional[CarSetupSnapshot]:
        """Retrieve car setup snapshot by ID.
        
        Args:
            setup_id: UUID of the setup snapshot to retrieve.
            
        Returns:
            CarSetupSnapshot entity if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def get_setup_for_lap(self, trace_id: str) -> Optional[CarSetupSnapshot]:
        """Find car setup used for a specific lap.
        
        Args:
            trace_id: UUID of the lap trace.
            
        Returns:
            CarSetupSnapshot used for the lap, or None if no setup associated.
        """
        pass
    
    @abstractmethod
    async def list_setup_snapshots(
        self,
        session_uid: str,
        limit: int = 50
    ) -> List[CarSetupSnapshot]:
        """List all setup snapshots captured in a session.
        
        Useful for tracking setup changes during a session.
        
        Args:
            session_uid: F1 25 session unique identifier.
            limit: Maximum number of setups to return (default: 50).
            
        Returns:
            List of CarSetupSnapshot entities ordered by timestamp.
            Empty list if no setups found.
        """
        pass
    
    # =============================================================================
    # Session Operations
    # =============================================================================
    
    @abstractmethod
    async def save_session(
        self,
        session_uid: str,
        track_id: str,
        session_type: int,
        user_id: Optional[str] = None,
        started_at: Optional[datetime] = None
    ) -> None:
        """Initialize or update session metadata.
        
        Creates session record if not exists, updates if exists.
        Session serves as container for laps and setups.
        
        Args:
            session_uid: F1 25 session unique identifier.
            track_id: F1 25 track identifier.
            session_type: F1 25 session type (e.g., Time Trial = 18).
            user_id: Optional Discord user ID (for automatic session lookup).
            started_at: Optional session start timestamp (auto-set if None).
        """
        pass
    
    @abstractmethod
    async def get_session(self, session_uid: str) -> Optional[Dict[str, Any]]:
        """Retrieve session metadata.
        
        Args:
            session_uid: F1 25 session unique identifier.
            
        Returns:
            Dictionary with session metadata:
            - session_uid: str
            - track_id: str
            - session_type: int
            - started_at: datetime
            - lap_count: int (number of laps in session)
            Returns None if session not found.
        """
        pass
    
    @abstractmethod
    async def list_sessions(
        self,
        track_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List all sessions, optionally filtered by track.
        
        Args:
            track_id: Optional track filter (if None, return all sessions).
            limit: Maximum number of sessions to return (default: 50).
            
        Returns:
            List of session metadata dictionaries ordered by started_at desc.
            Empty list if no sessions found.
        """
        pass
    
    @abstractmethod
    async def get_latest_session_for_user(
        self,
        user_id: str
    ) -> Optional[str]:
        """Get the most recent session UID for a user.
        
        Args:
            user_id: Discord user ID.
            
        Returns:
            session_uid of the most recent session for this user,
            or None if user has no sessions.
        """
        pass
    
    @abstractmethod
    async def get_latest_session_for_user_and_track(
        self,
        user_id: str,
        track_id: str
    ) -> Optional[str]:
        """Get the most recent session UID for a user on a specific track.
        
        Args:
            user_id: Discord user ID.
            track_id: F1 25 track identifier.
            
        Returns:
            session_uid of the most recent session for this user on this track,
            or None if user has no sessions on this track.
        """
        pass
    
    # =============================================================================
    # Bulk Operations & Maintenance
    # =============================================================================
    
    @abstractmethod
    async def get_telemetry_statistics(self) -> Dict[str, Any]:
        """Get overall telemetry database statistics.
        
        Returns:
            Dictionary with statistics:
            - total_sessions: int
            - total_laps: int
            - total_samples: int
            - total_setups: int
            - oldest_session: Optional[datetime]
            - newest_session: Optional[datetime]
        """
        pass
    
    @abstractmethod
    async def cleanup_old_data(self, before_date: datetime) -> int:
        """Delete telemetry data older than specified date.
        
        Useful for data retention policies and disk space management.
        Cascading delete removes sessions, laps, samples, and orphaned setups.
        
        Args:
            before_date: Delete all data from sessions started before this date.
            
        Returns:
            Number of sessions deleted.
        """
        pass
    
    @abstractmethod
    async def reset_all_telemetry_data(self) -> bool:
        """Reset all telemetry data in the database.
        
        Deletes all sessions, laps, samples, and setups.
        Use with caution - irreversible operation.
        
        Returns:
            True if reset was successful, False otherwise.
        """
        pass
