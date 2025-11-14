"""Use case for generating physics-based lap coaching feedback.

This module implements the MatheCoachAnalysisUseCase which orchestrates the
complete lap analysis pipeline:
1. Reconstruct track profile (if needed)
2. Fetch driver's lap telemetry
3. Construct ideal lap using physics model
4. Compare driver lap against ideal
5. Generate human-readable coaching feedback

Follows Clean Architecture by coordinating domain services and repositories
without containing business logic itself.
"""

from typing import Optional
from ...domain.interfaces.telemetry_repository import ITelemetryRepository
from ...domain.services.ideal_lap_constructor import IdealLapConstructor
from ...domain.services.lap_comparator import LapComparator
from ...domain.services.mathe_coach_feedback import MatheCoachFeedbackGenerator
from .reconstruct_track import ReconstructTrackUseCase
from ..exceptions import SessionNotFoundError, LapNotFoundError


# Track segments cache - maps track_id to segment definitions
# TODO: Load from configuration file or database in future iterations
_TRACK_SEGMENTS = {
    "default": [
        {"name": "Sector 1", "distance_start": 0.0, "distance_end_ratio": 0.33},
        {"name": "Sector 2", "distance_start_ratio": 0.33, "distance_end_ratio": 0.67},
        {"name": "Sector 3", "distance_start_ratio": 0.67, "distance_end_ratio": 1.0},
    ]
}

# Track name mappings - maps track_id to human-readable names
# TODO: Load from configuration file or database
_TRACK_NAMES = {
    "default": "Unknown Track"
}


class MatheCoachAnalysisUseCase:
    """Application service for physics-based lap coaching feedback.
    
    Orchestrates the complete lap analysis workflow:
    - Reconstructs track geometry from telemetry
    - Retrieves driver's lap data
    - Constructs ideal lap using physics model
    - Compares driver lap against ideal
    - Generates actionable coaching feedback
    
    This use case implements Clean Architecture principles:
    - Depends on abstractions (interfaces)
    - Coordinates domain services
    - Contains no business logic (delegates to domain layer)
    - Returns formatted feedback string
    
    Attributes:
        _telemetry_repository: Repository for accessing telemetry data.
        _reconstruct_track: Use case for track reconstruction.
        _ideal_lap_constructor: Domain service for ideal lap construction.
        _lap_comparator: Domain service for lap comparison.
        _feedback_generator: Domain service for feedback generation.
    
    Example:
        >>> repo = SQLiteTelemetryRepository()
        >>> reconstructor = TrackReconstructor()
        >>> reconstruct_uc = ReconstructTrackUseCase(repo, reconstructor)
        >>> 
        >>> constructor = IdealLapConstructor(...)
        >>> comparator = LapComparator()
        >>> generator = MatheCoachFeedbackGenerator()
        >>> 
        >>> use_case = MatheCoachAnalysisUseCase(
        ...     repo, reconstruct_uc, constructor, comparator, generator
        ... )
        >>> 
        >>> # Analyze latest lap from session
        >>> feedback = await use_case.execute(session_uid=12345)
        >>> print(feedback)
    """
    
    def __init__(
        self,
        telemetry_repository: ITelemetryRepository,
        reconstruct_track: ReconstructTrackUseCase,
        ideal_lap_constructor: IdealLapConstructor,
        lap_comparator: LapComparator,
        feedback_generator: MatheCoachFeedbackGenerator
    ):
        """Initialize use case with dependencies.
        
        Args:
            telemetry_repository: Repository for telemetry data access.
            reconstruct_track: Use case for track reconstruction.
            ideal_lap_constructor: Domain service for ideal lap construction.
            lap_comparator: Domain service for lap comparison.
            feedback_generator: Domain service for feedback generation.
        """
        self._telemetry_repository = telemetry_repository
        self._reconstruct_track = reconstruct_track
        self._ideal_lap_constructor = ideal_lap_constructor
        self._lap_comparator = lap_comparator
        self._feedback_generator = feedback_generator
    
    async def execute(
        self,
        session_uid: int,
        lap_number: Optional[int] = None
    ) -> str:
        """Generate physics-based coaching feedback for a lap.
        
        Performs the following steps:
        1. Reconstruct track profile from session telemetry
        2. Fetch driver's lap (latest or specific lap number)
        3. Construct ideal lap using physics model
        4. Compare driver lap against ideal to identify errors
        5. Generate human-readable Markdown coaching feedback
        
        Args:
            session_uid: F1 25 session unique identifier.
            lap_number: Optional specific lap number to analyze.
                If None, analyzes the most recent lap in the session.
        
        Returns:
            Markdown-formatted coaching feedback string containing:
            - Track name and lap information
            - Total time loss vs ideal
            - Top improvement areas with specific advice
            - Physics principles explanation
            - Summary recommendation
        
        Raises:
            SessionNotFoundError: If session with given UID does not exist.
            LapNotFoundError: If no lap found (or specified lap_number not found).
            InsufficientDataError: If track reconstruction fails (< 3 laps).
            InvalidTrackDataError: If track data is invalid.
        
        Performance:
            Typical execution time: < 3 seconds for a complete analysis
        
        Example:
            >>> # Analyze latest lap
            >>> feedback = await use_case.execute(session_uid=12345)
            >>> 
            >>> # Analyze specific lap
            >>> feedback = await use_case.execute(
            ...     session_uid=12345,
            ...     lap_number=5
            ... )
        """
        # Step 1: Reconstruct track profile
        track_profile = await self._reconstruct_track.execute(session_uid)
        
        # Step 2: Fetch driver's lap
        if lap_number is None:
            # Get latest lap from session
            lap_trace = await self._telemetry_repository.get_latest_lap_trace(session_uid)
            if lap_trace is None:
                raise LapNotFoundError(f"No lap found for session {session_uid}")
        else:
            # Get specific lap by number
            all_laps = await self._telemetry_repository.list_lap_traces(
                session_uid=session_uid,
                limit=1000  # Fetch all to find specific lap_number
            )
            
            # Find lap with matching lap_number
            matching_laps = [lap for lap in all_laps if lap.lap_number == lap_number]
            if not matching_laps:
                raise LapNotFoundError(
                    f"Lap number {lap_number} not found in session {session_uid}"
                )
            lap_trace = matching_laps[0]
        
        # Step 3: Construct ideal lap using physics model
        ideal_lap = self._ideal_lap_constructor.construct_ideal_lap(track_profile)
        
        # Step 4: Compare driver lap against ideal
        # Get track segments for this track
        segments = self._get_track_segments(track_profile.track_id)
        
        comparison_segments = self._lap_comparator.compare_laps(
            driver_lap=lap_trace,
            ideal_lap=ideal_lap,
            track_profile=track_profile,
            segments=segments
        )
        
        # Step 5: Generate coaching feedback
        track_name = self._get_track_name(track_profile.track_id)
        
        feedback = self._feedback_generator.generate_feedback(
            comparison_segments=comparison_segments,
            track_profile=track_profile,
            track_name=track_name,
            top_n=5  # Show top 5 improvement areas
        )
        
        return feedback
    
    def _get_track_segments(self, track_id: str) -> list[dict]:
        """Get segment definitions for track.
        
        Segments define track sections for comparison analysis.
        Falls back to default 3-sector split if track not configured.
        
        Args:
            track_id: Track identifier from session.
        
        Returns:
            List of segment dictionaries with:
            - name: Human-readable segment name
            - distance_start: Start distance (m) or distance_start_ratio
            - distance_end: End distance (m) or distance_end_ratio
        """
        return _TRACK_SEGMENTS.get(track_id, _TRACK_SEGMENTS["default"])
    
    def _get_track_name(self, track_id: str) -> str:
        """Get human-readable track name.
        
        Args:
            track_id: Track identifier from session.
        
        Returns:
            Human-readable track name. Falls back to track_id if not found.
        """
        return _TRACK_NAMES.get(track_id, track_id)
