"""Marker detection and phase segmentation domain services."""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

from src.domain.entities.telemetry_sample import CarTelemetryInfo


class TurnPhase(Enum):
    """Turn phases for segmentation."""
    ENTRY = "entry"
    ROTATION = "rotation"
    EXIT = "exit"


@dataclass
class BrakeMarker:
    """Brake marker event."""
    timestamp: float
    brake_start: bool  # True for brake start, False for brake release
    brake_pressure: float
    speed: float


@dataclass
class ThrottleMarker:
    """Throttle marker event."""
    timestamp: float
    throttle_pickup: bool  # True for pickup, False for release
    throttle_position: float
    speed: float


@dataclass
class TurnMarkers:
    """Collection of markers for a turn."""
    brake_start: Optional[BrakeMarker] = None
    brake_peak: Optional[BrakeMarker] = None
    brake_release: Optional[BrakeMarker] = None
    throttle_pickup: Optional[ThrottleMarker] = None
    throttle_opening: Optional[ThrottleMarker] = None
    apex_marker: Optional[float] = None  # Speed at apex
    entry_speed: Optional[float] = None
    min_speed: Optional[float] = None
    exit_speed: Optional[float] = None


@dataclass
class TurnSegment:
    """Complete turn segment with phases and markers."""
    turn_id: str
    start_time: float
    end_time: float
    phase: TurnPhase
    markers: TurnMarkers
    entry_duration_ms: Optional[float] = None
    rotation_duration_ms: Optional[float] = None
    exit_duration_ms: Optional[float] = None
    trail_braking_duration_ms: Optional[float] = None


class MarkerDetector:
    """Detects key markers in telemetry data with jitter resilience."""
    
    def __init__(self, 
                 brake_threshold: float = 0.1,
                 throttle_threshold: float = 0.1,
                 speed_change_threshold: float = 5.0,  # km/h
                 hysteresis_window: int = 3):  # frames
        """
        Initialize marker detector.
        
        Args:
            brake_threshold: Minimum brake pressure to consider as braking
            throttle_threshold: Minimum throttle position to consider as throttling
            speed_change_threshold: Minimum speed change to detect speed events
            hysteresis_window: Number of frames for hysteresis to avoid jitter
        """
        self.brake_threshold = brake_threshold
        self.throttle_threshold = throttle_threshold
        self.speed_change_threshold = speed_change_threshold
        self.hysteresis_window = hysteresis_window
        
        self.logger = logging.getLogger(__name__)
        
        # State tracking for jitter resistance
        self._brake_history: List[float] = []
        self._throttle_history: List[float] = []
        self._speed_history: List[float] = []
        self._last_brake_state = False
        self._last_throttle_state = False
        
        # Pending markers for hysteresis
        self._pending_brake_start: Optional[BrakeMarker] = None
        self._pending_brake_release: Optional[BrakeMarker] = None
        self._pending_throttle_pickup: Optional[ThrottleMarker] = None
        self._pending_throttle_release: Optional[ThrottleMarker] = None
    
    def detect_markers(self, telemetry: CarTelemetryInfo, timestamp: float) -> List[Tuple[str, any]]:
        """
        Detect markers in current telemetry sample.
        
        Args:
            telemetry: Car telemetry data
            timestamp: Current timestamp
            
        Returns:
            List of (marker_type, marker_data) tuples
        """
        markers = []
        
        # Update history for jitter resistance
        self._update_history(telemetry)
        
        # Detect brake markers
        brake_markers = self._detect_brake_markers(telemetry, timestamp)
        markers.extend(brake_markers)
        
        # Detect throttle markers
        throttle_markers = self._detect_throttle_markers(telemetry, timestamp)
        markers.extend(throttle_markers)
        
        # Detect speed-based markers
        speed_markers = self._detect_speed_markers(telemetry, timestamp)
        markers.extend(speed_markers)
        
        return markers
    
    def _update_history(self, telemetry: CarTelemetryInfo) -> None:
        """Update telemetry history for jitter resistance."""
        self._brake_history.append(telemetry.brake)
        self._throttle_history.append(telemetry.throttle)
        self._speed_history.append(telemetry.speed)
        
        # Keep only recent history
        max_history = self.hysteresis_window * 2
        if len(self._brake_history) > max_history:
            self._brake_history = self._brake_history[-max_history:]
        if len(self._throttle_history) > max_history:
            self._throttle_history = self._throttle_history[-max_history:]
        if len(self._speed_history) > max_history:
            self._speed_history = self._speed_history[-max_history:]
    
    def _detect_brake_markers(self, telemetry: CarTelemetryInfo, timestamp: float) -> List[Tuple[str, BrakeMarker]]:
        """Detect brake-related markers with hysteresis."""
        markers = []
        
        # Use filtered brake signal (average over hysteresis window)
        if len(self._brake_history) >= self.hysteresis_window:
            filtered_brake = sum(self._brake_history[-self.hysteresis_window:]) / self.hysteresis_window
        else:
            filtered_brake = telemetry.brake
        
        is_braking = filtered_brake > self.brake_threshold
        
        # Brake start detection
        if is_braking and not self._last_brake_state:
            marker = BrakeMarker(
                timestamp=timestamp,
                brake_start=True,
                brake_pressure=telemetry.brake,
                speed=telemetry.speed
            )
            markers.append(("brake_start", marker))
            self.logger.debug(f"Brake start detected: pressure={telemetry.brake:.3f}, speed={telemetry.speed:.1f}")
        
        # Brake release detection
        elif not is_braking and self._last_brake_state:
            marker = BrakeMarker(
                timestamp=timestamp,
                brake_start=False,
                brake_pressure=telemetry.brake,
                speed=telemetry.speed
            )
            markers.append(("brake_release", marker))
            self.logger.debug(f"Brake release detected: pressure={telemetry.brake:.3f}, speed={telemetry.speed:.1f}")
        
        # Brake peak detection (maximum pressure while braking)
        elif is_braking and len(self._brake_history) >= 2:
            if telemetry.brake > max(self._brake_history[-2:]) and telemetry.brake > 0.5:
                marker = BrakeMarker(
                    timestamp=timestamp,
                    brake_start=False,  # Not a start/release event
                    brake_pressure=telemetry.brake,
                    speed=telemetry.speed
                )
                markers.append(("brake_peak", marker))
                self.logger.debug(f"Brake peak detected: pressure={telemetry.brake:.3f}, speed={telemetry.speed:.1f}")
        
        self._last_brake_state = is_braking
        return markers
    
    def _detect_throttle_markers(self, telemetry: CarTelemetryInfo, timestamp: float) -> List[Tuple[str, ThrottleMarker]]:
        """Detect throttle-related markers with hysteresis."""
        markers = []
        
        # Use filtered throttle signal
        if len(self._throttle_history) >= self.hysteresis_window:
            filtered_throttle = sum(self._throttle_history[-self.hysteresis_window:]) / self.hysteresis_window
        else:
            filtered_throttle = telemetry.throttle
        
        is_throttling = filtered_throttle > self.throttle_threshold
        
        # Throttle pickup detection
        if is_throttling and not self._last_throttle_state:
            marker = ThrottleMarker(
                timestamp=timestamp,
                throttle_pickup=True,
                throttle_position=telemetry.throttle,
                speed=telemetry.speed
            )
            markers.append(("throttle_pickup", marker))
            self.logger.debug(f"Throttle pickup detected: position={telemetry.throttle:.3f}, speed={telemetry.speed:.1f}")
        
        # Throttle release detection
        elif not is_throttling and self._last_throttle_state:
            marker = ThrottleMarker(
                timestamp=timestamp,
                throttle_pickup=False,
                throttle_position=telemetry.throttle,
                speed=telemetry.speed
            )
            markers.append(("throttle_release", marker))
            self.logger.debug(f"Throttle release detected: position={telemetry.throttle:.3f}, speed={telemetry.speed:.1f}")
        
        # Throttle opening detection (increasing throttle while already on throttle)
        elif is_throttling and len(self._throttle_history) >= 2:
            throttle_increase = telemetry.throttle - self._throttle_history[-2]
            if throttle_increase > 0.1:  # Significant throttle increase
                marker = ThrottleMarker(
                    timestamp=timestamp,
                    throttle_pickup=False,  # Not a pickup event
                    throttle_position=telemetry.throttle,
                    speed=telemetry.speed
                )
                markers.append(("throttle_opening", marker))
                self.logger.debug(f"Throttle opening detected: position={telemetry.throttle:.3f}, speed={telemetry.speed:.1f}")
        
        self._last_throttle_state = is_throttling
        return markers
    
    def _detect_speed_markers(self, telemetry: CarTelemetryInfo, timestamp: float) -> List[Tuple[str, float]]:
        """Detect speed-based markers (apex, minimum speed)."""
        markers = []
        
        if len(self._speed_history) >= self.hysteresis_window:
            # Find local minimum (potential apex)
            recent_speeds = self._speed_history[-self.hysteresis_window:]
            current_speed = telemetry.speed
            
            # Check if current speed is a local minimum
            if all(current_speed <= s for s in recent_speeds):
                markers.append(("min_speed", current_speed))
                self.logger.debug(f"Minimum speed detected: {current_speed:.1f} km/h")
        
        return markers


class PhaseSegmenter:
    """Segments turns into Entry, Rotation, and Exit phases."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._current_turn: Optional[TurnSegment] = None
        self._turn_markers = TurnMarkers()
        self._turn_start_time: Optional[float] = None
        self._current_phase = TurnPhase.ENTRY
    
    def process_markers(self, markers: List[Tuple[str, any]], timestamp: float) -> Optional[TurnSegment]:
        """
        Process detected markers and segment into turn phases.
        
        Args:
            markers: List of detected markers
            timestamp: Current timestamp
            
        Returns:
            Completed turn segment if a turn is finished, None otherwise
        """
        completed_turn = None
        
        for marker_type, marker_data in markers:
            if marker_type == "brake_start":
                self._handle_brake_start(marker_data, timestamp)
            elif marker_type == "brake_peak":
                self._handle_brake_peak(marker_data)
            elif marker_type == "brake_release":
                self._handle_brake_release(marker_data)
            elif marker_type == "throttle_pickup":
                self._handle_throttle_pickup(marker_data)
            elif marker_type == "throttle_opening":
                self._handle_throttle_opening(marker_data)
            elif marker_type == "min_speed":
                self._handle_min_speed(marker_data, timestamp)
        
        # Check for phase transitions
        completed_turn = self._check_phase_transitions(timestamp)
        
        return completed_turn
    
    def _handle_brake_start(self, marker: BrakeMarker, timestamp: float) -> None:
        """Handle brake start marker - typically marks turn entry."""
        if self._turn_start_time is None:
            self._turn_start_time = timestamp
            self._current_phase = TurnPhase.ENTRY
            self._turn_markers.entry_speed = marker.speed
            self.logger.debug(f"Turn entry detected at {marker.speed:.1f} km/h")
        
        self._turn_markers.brake_start = marker
    
    def _handle_brake_peak(self, marker: BrakeMarker) -> None:
        """Handle brake peak marker."""
        self._turn_markers.brake_peak = marker
    
    def _handle_brake_release(self, marker: BrakeMarker) -> None:
        """Handle brake release marker - typically marks end of entry phase."""
        self._turn_markers.brake_release = marker
        
        if self._current_phase == TurnPhase.ENTRY:
            self._current_phase = TurnPhase.ROTATION
            self.logger.debug("Transitioning to rotation phase")
    
    def _handle_throttle_pickup(self, marker: ThrottleMarker) -> None:
        """Handle throttle pickup marker - typically marks start of exit phase."""
        self._turn_markers.throttle_pickup = marker
        
        if self._current_phase in [TurnPhase.ENTRY, TurnPhase.ROTATION]:
            self._current_phase = TurnPhase.EXIT
            self.logger.debug("Transitioning to exit phase")
    
    def _handle_throttle_opening(self, marker: ThrottleMarker) -> None:
        """Handle throttle opening marker."""
        self._turn_markers.throttle_opening = marker
    
    def _handle_min_speed(self, speed: float, timestamp: float) -> None:
        """Handle minimum speed marker - typically marks apex."""
        self._turn_markers.min_speed = speed
        self._turn_markers.apex_marker = speed
        
        if self._current_phase == TurnPhase.ENTRY:
            self._current_phase = TurnPhase.ROTATION
            self.logger.debug(f"Apex detected at {speed:.1f} km/h, transitioning to rotation")
    
    def _check_phase_transitions(self, timestamp: float) -> Optional[TurnSegment]:
        """Check if turn is complete and create turn segment."""
        # Turn is complete when we have throttle opening in exit phase
        if (self._current_phase == TurnPhase.EXIT and 
            self._turn_markers.throttle_opening is not None and
            self._turn_start_time is not None):
            
            # Calculate phase durations
            entry_duration = None
            rotation_duration = None
            exit_duration = None
            trail_duration = None
            
            if (self._turn_markers.brake_start and self._turn_markers.brake_release):
                entry_duration = (self._turn_markers.brake_release.timestamp - 
                                self._turn_markers.brake_start.timestamp) * 1000  # ms
            
            if (self._turn_markers.brake_release and self._turn_markers.throttle_pickup):
                rotation_duration = (self._turn_markers.throttle_pickup.timestamp - 
                                   self._turn_markers.brake_release.timestamp) * 1000  # ms
            
            # Trail braking duration (brake and throttle overlap)
            if (self._turn_markers.brake_start and self._turn_markers.throttle_pickup and
                self._turn_markers.brake_release and 
                self._turn_markers.throttle_pickup.timestamp < self._turn_markers.brake_release.timestamp):
                trail_duration = (self._turn_markers.brake_release.timestamp - 
                                self._turn_markers.throttle_pickup.timestamp) * 1000  # ms
            
            # Set exit speed
            if self._turn_markers.throttle_opening:
                self._turn_markers.exit_speed = self._turn_markers.throttle_opening.speed
            
            turn = TurnSegment(
                turn_id=f"turn_{int(timestamp)}",
                start_time=self._turn_start_time,
                end_time=timestamp,
                phase=TurnPhase.EXIT,
                markers=self._turn_markers,
                entry_duration_ms=entry_duration,
                rotation_duration_ms=rotation_duration,
                exit_duration_ms=exit_duration,
                trail_braking_duration_ms=trail_duration
            )
            
            self.logger.info(f"Turn completed: entry={entry_duration:.0f}ms, rotation={rotation_duration:.0f}ms, trail={trail_duration:.0f}ms")
            
            # Reset for next turn
            self._reset_turn_state()
            
            return turn
        
        return None
    
    def _reset_turn_state(self) -> None:
        """Reset state for next turn."""
        self._current_turn = None
        self._turn_markers = TurnMarkers()
        self._turn_start_time = None
        self._current_phase = TurnPhase.ENTRY