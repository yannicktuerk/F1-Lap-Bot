"""Telemetry sample domain entities."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SessionInfo:
    """Session information from F1 telemetry."""
    session_uid: int
    session_type: int  # Session type (practice, qualifying, race, time trial, etc.)
    track_id: int
    session_time: float
    remaining_time: float
    is_time_trial: bool
    frame_identifier: int
    overall_frame_identifier: int


@dataclass
class LapInfo:
    """Lap information from F1 telemetry."""
    lap_time_ms: Optional[int]  # Current lap time in milliseconds
    sector1_time_ms: Optional[int]
    sector2_time_ms: Optional[int] 
    sector3_time_ms: Optional[int]
    lap_distance: float  # Distance through current lap
    total_distance: float  # Total distance traveled
    is_valid_lap: bool
    current_lap_number: int
    car_position: int
    

@dataclass
class CarTelemetryInfo:
    """Car telemetry information from F1 telemetry."""
    speed: float  # Speed in km/h
    throttle: float  # 0.0 to 1.0
    steer: float  # -1.0 to 1.0
    brake: float  # 0.0 to 1.0
    clutch: float  # 0.0 to 1.0
    gear: int
    engine_rpm: int
    drs: bool
    rev_lights_percent: int
    brake_temperature: list[float]  # 4 corners: RL, RR, FL, FR
    tyre_surface_temperature: list[float]  # 4 corners: RL, RR, FL, FR
    tyre_inner_temperature: list[float]  # 4 corners: RL, RR, FL, FR
    engine_temperature: float
    

@dataclass
class TimeTrialInfo:
    """Time Trial specific information from F1 telemetry."""
    is_personal_best: bool
    is_best_overall: bool
    sector1_personal_best_ms: Optional[int]
    sector2_personal_best_ms: Optional[int]
    sector3_personal_best_ms: Optional[int]
    sector1_best_overall_ms: Optional[int]
    sector2_best_overall_ms: Optional[int]
    sector3_best_overall_ms: Optional[int]


@dataclass
class PlayerTelemetrySample:
    """Complete telemetry sample for the player car."""
    timestamp: datetime
    session_info: SessionInfo
    lap_info: LapInfo
    car_telemetry: CarTelemetryInfo
    time_trial_info: Optional[TimeTrialInfo] = None
    player_car_index: int = 0
    
    @property
    def is_time_trial_session(self) -> bool:
        """Check if this is a Time Trial session."""
        return self.session_info.is_time_trial
    
    @property
    def is_valid_telemetry(self) -> bool:
        """Check if this telemetry sample is valid for processing."""
        return (
            self.is_time_trial_session and
            self.lap_info.is_valid_lap and
            self.session_info.session_time > 0
        )