"""Use case for processing real-time telemetry data."""
import logging
from typing import List, Optional

from src.domain.entities.telemetry_sample import (
    PlayerTelemetrySample,
    SessionInfo,
    LapInfo,
    CarTelemetryInfo,
    TimeTrialInfo
)
from src.domain.interfaces.telemetry_ingest_port import TelemetryIngestPort
from src.domain.services.gating_service import GatingService
from src.domain.services.marker_detector import MarkerDetector, PhaseSegmenter, TurnSegment


class ProcessTelemetryUseCase(TelemetryIngestPort):
    """Use case for processing real-time F1 telemetry data."""
    
    def __init__(self, 
                 gating_service: Optional[GatingService] = None,
                 marker_detector: Optional[MarkerDetector] = None,
                 phase_segmenter: Optional[PhaseSegmenter] = None):
        """
        Initialize telemetry processing use case.
        
        Args:
            gating_service: Service for applying gating rules
            marker_detector: Service for detecting telemetry markers
            phase_segmenter: Service for segmenting turn phases
        """
        self.logger = logging.getLogger(__name__)
        self.gating_service = gating_service or GatingService()
        self.marker_detector = marker_detector or MarkerDetector()
        self.phase_segmenter = phase_segmenter or PhaseSegmenter()
        
        # State tracking
        self._current_session: Optional[SessionInfo] = None
        self._completed_turns: List[TurnSegment] = []
        self._is_active = False
    
    async def start(self) -> None:
        """Start the telemetry processing."""
        self._is_active = True
        self.logger.info("Telemetry processing started")
    
    async def stop(self) -> None:
        """Stop the telemetry processing."""
        self._is_active = False
        self.gating_service.log_metrics()
        self.logger.info(f"Telemetry processing stopped. Completed turns: {len(self._completed_turns)}")
    
    async def on_session(self, session_info: SessionInfo) -> None:
        """Handle session information update."""
        if not self._is_active:
            return
        
        self._current_session = session_info
        self.logger.info(
            f"Session update: type={session_info.session_type}, "
            f"track={session_info.track_id}, "
            f"is_tt={session_info.is_time_trial}"
        )
        
        # Reset turn tracking on session change
        if session_info.is_time_trial:
            self._completed_turns.clear()
            self.logger.info("Time Trial session detected - turn tracking reset")
    
    async def on_lap_data(self, lap_info: LapInfo) -> None:
        """Handle lap data update.""" 
        if not self._is_active:
            return
        
        self.logger.debug(
            f"Lap data: lap={lap_info.current_lap_number}, "
            f"valid={lap_info.is_valid_lap}, "
            f"distance={lap_info.lap_distance:.1f}m"
        )
        
        # Additional processing for lap data could be added here
        # For example, detecting lap start/end markers
    
    async def on_car_telemetry(self, car_telemetry: CarTelemetryInfo) -> None:
        """Handle car telemetry update."""
        if not self._is_active:
            return
        
        # Only process in Time Trial sessions
        if not self._current_session or not self._current_session.is_time_trial:
            return
        
        # Use session time as timestamp
        timestamp = self._current_session.session_time
        
        # Detect markers in telemetry
        markers = self.marker_detector.detect_markers(car_telemetry, timestamp)
        
        if markers:
            self.logger.debug(f"Detected {len(markers)} markers: {[m[0] for m in markers]}")
        
        # Process markers for turn segmentation
        completed_turn = self.phase_segmenter.process_markers(markers, timestamp)
        
        if completed_turn:
            self._completed_turns.append(completed_turn)
            self.logger.info(
                f"Turn completed: entry={completed_turn.entry_duration_ms:.0f}ms, "
                f"rotation={completed_turn.rotation_duration_ms:.0f}ms, "
                f"trail_braking={completed_turn.trail_braking_duration_ms:.0f}ms"
            )
            
            # Here you could trigger further analysis like:
            # - Candidate generation for coaching tips
            # - Safety gate checks
            # - Utility estimation
            await self._analyze_completed_turn(completed_turn)
    
    async def on_time_trial(self, time_trial_info: TimeTrialInfo) -> None:
        """Handle time trial specific information."""
        if not self._is_active:
            return
        
        self.logger.debug(
            f"Time trial info: pb={time_trial_info.is_personal_best}, "
            f"best_overall={time_trial_info.is_best_overall}"
        )
        
        # Process time trial specific information
        # This could trigger specific coaching logic for PB attempts
    
    async def on_player_telemetry_sample(self, sample: PlayerTelemetrySample) -> None:
        """Handle complete player telemetry sample."""
        if not self._is_active:
            return
        
        # The complete sample processing happens via the individual callbacks
        # This method could be used for holistic analysis that requires all data
        self.logger.debug(
            f"Complete telemetry sample: speed={sample.car_telemetry.speed:.1f}, "
            f"throttle={sample.car_telemetry.throttle:.2f}, "
            f"brake={sample.car_telemetry.brake:.2f}"
        )
    
    async def _analyze_completed_turn(self, turn: TurnSegment) -> None:
        """Analyze a completed turn for coaching opportunities."""
        # This is where the TT-Coach logic would be implemented
        # For now, just log the analysis
        
        markers = turn.markers
        analysis = []
        
        # Analyze braking performance
        if markers.entry_speed and markers.min_speed:
            speed_reduction = markers.entry_speed - markers.min_speed
            if speed_reduction > 50:  # Significant braking
                analysis.append(f"Heavy braking: {speed_reduction:.1f} km/h reduction")
        
        # Analyze trail braking
        if turn.trail_braking_duration_ms and turn.trail_braking_duration_ms > 200:
            analysis.append(f"Trail braking: {turn.trail_braking_duration_ms:.0f}ms")
        
        # Analyze phase timing
        if turn.entry_duration_ms and turn.rotation_duration_ms:
            total_turn_time = turn.entry_duration_ms + turn.rotation_duration_ms
            if turn.exit_duration_ms:
                total_turn_time += turn.exit_duration_ms
            analysis.append(f"Turn time: {total_turn_time:.0f}ms")
        
        if analysis:
            self.logger.info(f"Turn analysis: {', '.join(analysis)}")
    
    def get_completed_turns(self) -> List[TurnSegment]:
        """Get list of completed turns."""
        return self._completed_turns.copy()
    
    def get_gating_metrics(self):
        """Get current gating metrics."""
        return self.gating_service.get_metrics()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.gating_service.reset_metrics()
        self._completed_turns.clear()
        self.logger.info("All metrics reset")