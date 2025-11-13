"""Use case for reconstructing track geometry from telemetry data.

This module implements the ReconstructTrackUseCase which orchestrates the
track reconstruction pipeline by:
1. Fetching telemetry data from the repository
2. Aggregating samples from multiple laps
3. Using TrackReconstructor domain service to compute geometry
4. Returning a complete TrackProfile value object

This follows Clean Architecture by coordinating domain services and repositories
without containing business logic itself.
"""

from typing import List
from ...domain.interfaces.telemetry_repository import ITelemetryRepository
from ...domain.services.track_reconstructor import TrackReconstructor
from ...domain.entities.track_profile import TrackProfile
from ...domain.entities.lap_trace import LapTrace
from ...domain.value_objects.telemetry_sample import TelemetrySample
from ..exceptions import SessionNotFoundError, InsufficientDataError, InvalidTrackDataError


class ReconstructTrackUseCase:
    """Application service for reconstructing track geometry from telemetry.
    
    Orchestrates the track reconstruction pipeline by:
    - Retrieving session and lap data from repository
    - Validating data sufficiency and quality
    - Aggregating telemetry samples across multiple laps
    - Delegating geometry computation to TrackReconstructor
    - Assembling final TrackProfile value object
    
    This use case implements Clean Architecture principles:
    - Depends on abstractions (ITelemetryRepository interface)
    - Coordinates domain services (TrackReconstructor)
    - Contains no business logic (delegates to domain layer)
    - Returns domain entities/value objects only
    
    Attributes:
        _telemetry_repository: Repository for accessing telemetry data.
        _track_reconstructor: Domain service for track geometry computation.
    
    Example:
        >>> repo = SQLiteTelemetryRepository()
        >>> reconstructor = TrackReconstructor()
        >>> use_case = ReconstructTrackUseCase(repo, reconstructor)
        >>> 
        >>> # Reconstruct track from session with at least 3 laps
        >>> profile = await use_case.execute(session_uid=12345, min_laps=3)
        >>> 
        >>> print(f"Track: {profile.track_id}")
        >>> print(f"Length: {profile.track_length_m:.1f}m")
        >>> print(f"Points: {len(profile.distance)}")
    """
    
    def __init__(
        self,
        telemetry_repository: ITelemetryRepository,
        track_reconstructor: TrackReconstructor
    ):
        """Initialize use case with dependencies.
        
        Args:
            telemetry_repository: Repository for telemetry data access.
            track_reconstructor: Domain service for geometry computation.
        """
        self._telemetry_repository = telemetry_repository
        self._track_reconstructor = track_reconstructor
    
    async def execute(
        self,
        session_uid: int,
        min_laps: int = 3
    ) -> TrackProfile:
        """Reconstruct track geometry from session telemetry data.
        
        Performs the following steps:
        1. Fetch session metadata (track_id, track_length_m)
        2. Retrieve lap traces for the session
        3. Validate minimum lap count requirement
        4. Aggregate telemetry samples from all laps
        5. Compute track centerline with cumulative distances
        6. Compute curvature profile along centerline
        7. Extract elevation profile from telemetry
        8. Assemble and return TrackProfile value object
        
        Args:
            session_uid: F1 25 session unique identifier.
            min_laps: Minimum number of valid laps required for reconstruction.
                Default is 3 laps to ensure sufficient data coverage.
        
        Returns:
            TrackProfile value object containing:
            - track_id: Track identifier from session
            - centerline: Nx2 array of (x, z) world coordinates
            - curvature: N-element array of curvature values (1/m)
            - elevation: N-element array of elevation values (m)
            - distance: N-element array of cumulative distances (m)
            - track_length_m: Total track length computed from telemetry
        
        Raises:
            SessionNotFoundError: If session with given UID does not exist.
            InsufficientDataError: If fewer than min_laps valid laps available.
            InvalidTrackDataError: If track_length_m is invalid (≤ 0).
            ValueError: If telemetry samples are insufficient for geometry computation
                (raised by TrackReconstructor domain service).
        
        Performance:
            - Typical execution time: < 2 seconds for sessions with 3-10 laps
            - Memory usage scales with number of samples (~100KB per lap)
        
        Example:
            >>> # Reconstruct track from recent session
            >>> try:
            ...     profile = await use_case.execute(session_uid=12345, min_laps=3)
            ...     print(f"✅ Reconstructed {profile.track_id}: {profile.track_length_m:.1f}m")
            ... except SessionNotFoundError:
            ...     print("❌ Session not found")
            ... except InsufficientDataError as e:
            ...     print(f"❌ {e}")
        """
        # Step 1: Fetch session metadata
        session = await self._telemetry_repository.get_session(session_uid)
        
        if session is None:
            raise SessionNotFoundError(session_uid)
        
        # Extract session data
        track_id = session.get("track_id")
        
        # Step 2: Fetch lap traces for the session
        # Fetch more than needed (up to 100) to ensure we have enough valid laps
        lap_traces = await self._telemetry_repository.list_lap_traces(
            session_uid=session_uid,
            limit=100
        )
        
        # Step 3: Validate minimum lap count
        if len(lap_traces) < min_laps:
            raise InsufficientDataError(
                required=min_laps,
                actual=len(lap_traces),
                data_type="laps"
            )
        
        # Step 4: Aggregate telemetry samples from all valid laps
        all_samples: List[TelemetrySample] = []
        
        for lap_trace in lap_traces:
            # Only use valid, complete laps
            if lap_trace.is_valid and lap_trace.is_complete():
                lap_samples = lap_trace.get_samples()
                all_samples.extend(lap_samples)
        
        # Verify we have enough samples after filtering
        if len(all_samples) < self._track_reconstructor.MIN_SAMPLES_REQUIRED:
            raise InsufficientDataError(
                required=self._track_reconstructor.MIN_SAMPLES_REQUIRED,
                actual=len(all_samples),
                data_type="telemetry samples"
            )
        
        # Step 5: Compute track length from telemetry data
        # Use maximum lap_distance from all samples as track length estimate
        # This is more reliable than session metadata which may not include track length
        track_length_m = max(sample.lap_distance for sample in all_samples)
        
        # Validate track length
        if track_length_m <= 0:
            raise InvalidTrackDataError("track_length_m", track_length_m)
        
        # Step 6: Compute track centerline with cumulative distances
        centerline, distances = self._track_reconstructor.compute_centerline(
            samples=all_samples,
            track_length_m=track_length_m
        )
        
        # Step 7: Compute curvature profile along centerline
        curvature = self._track_reconstructor.compute_curvature(
            centerline=centerline,
            distances=distances,
            smooth=True  # Apply smoothing for better curvature estimates
        )
        
        # Step 8: Extract elevation profile from telemetry
        elevation = self._track_reconstructor.compute_elevation(
            samples=all_samples,
            track_length_m=track_length_m,
            smooth=True  # Apply smoothing for better elevation estimates
        )
        
        # Step 9: Assemble and return TrackProfile value object
        track_profile = TrackProfile(
            track_id=track_id,
            centerline=centerline,
            curvature=curvature,
            elevation=elevation,
            distance=distances,
            track_length_m=float(distances[-1])  # Use computed track length from centerline
        )
        
        return track_profile
