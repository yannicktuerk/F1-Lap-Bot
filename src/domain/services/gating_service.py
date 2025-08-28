"""Gating service for TT-only, Valid-only, Player-only filtering."""
import logging
from dataclasses import dataclass
from typing import Optional

from src.domain.entities.telemetry_sample import PlayerTelemetrySample, SessionInfo, LapInfo


@dataclass
class GatingMetrics:
    """Metrics for observability of gating decisions."""
    total_packets: int = 0
    filtered_non_tt_sessions: int = 0
    filtered_invalid_laps: int = 0
    filtered_non_player_cars: int = 0
    passed_samples: int = 0
    
    def increment_total(self) -> None:
        self.total_packets += 1
    
    def increment_non_tt_filtered(self) -> None:
        self.filtered_non_tt_sessions += 1
    
    def increment_invalid_lap_filtered(self) -> None:
        self.filtered_invalid_laps += 1
    
    def increment_non_player_filtered(self) -> None:
        self.filtered_non_player_cars += 1
    
    def increment_passed(self) -> None:
        self.passed_samples += 1
    
    @property
    def pass_rate(self) -> float:
        """Calculate percentage of packets that passed gating."""
        if self.total_packets == 0:
            return 0.0
        return (self.passed_samples / self.total_packets) * 100.0


class GatingService:
    """Service for applying TT-only, Valid-only, Player-only gating rules."""
    
    # Session type constants (from F1 spec)
    SESSION_TYPE_TIME_TRIAL = 12  # Time Trial session type
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = GatingMetrics()
        self._current_session_type: Optional[int] = None
        self._current_player_car_index: Optional[int] = None
    
    def should_process_session(self, session_info: SessionInfo, player_car_index: int) -> bool:
        """
        Check if session should be processed based on TT-only rule.
        
        Args:
            session_info: Session information from telemetry
            player_car_index: Index of player car from packet header
            
        Returns:
            True if session should be processed, False otherwise
        """
        self.metrics.increment_total()
        
        # Update current session tracking
        self._current_session_type = session_info.session_type
        self._current_player_car_index = player_car_index
        
        # Rule 1: TT-Only - Only Time Trial sessions are processed
        if not session_info.is_time_trial:
            self.metrics.increment_non_tt_filtered()
            self.logger.debug(f"Filtered non-TT session: type={session_info.session_type}")
            return False
        
        self.logger.debug(f"TT session accepted: type={session_info.session_type}")
        return True
    
    def should_process_lap(self, lap_info: LapInfo, car_index: int) -> bool:
        """
        Check if lap data should be processed based on Valid-only and Player-only rules.
        
        Args:
            lap_info: Lap information from telemetry
            car_index: Index of the car this lap data is for
            
        Returns:
            True if lap should be processed, False otherwise
        """
        # Rule 2: Player-Only - Only player car data is processed
        if self._current_player_car_index is not None and car_index != self._current_player_car_index:
            self.metrics.increment_non_player_filtered()
            self.logger.debug(f"Filtered non-player car: car_index={car_index}, player_index={self._current_player_car_index}")
            return False
        
        # Rule 3: Valid-Only - Only valid laps flow into analysis
        if not lap_info.is_valid_lap:
            self.metrics.increment_invalid_lap_filtered()
            self.logger.debug(f"Filtered invalid lap: lap_number={lap_info.current_lap_number}")
            return False
        
        self.logger.debug(f"Lap accepted: lap_number={lap_info.current_lap_number}, car_index={car_index}")
        return True
    
    def should_process_telemetry_sample(self, sample: PlayerTelemetrySample) -> bool:
        """
        Check if complete telemetry sample should be processed.
        
        Args:
            sample: Complete player telemetry sample
            
        Returns:
            True if sample should be processed, False otherwise
        """
        # Use the built-in validation from the domain object
        if sample.is_valid_telemetry:
            self.metrics.increment_passed()
            self.logger.debug(f"Telemetry sample passed gating: session_time={sample.session_info.session_time}")
            return True
        else:
            # The sample validation handles TT check and valid lap check
            self.logger.debug(f"Telemetry sample failed validation: is_tt={sample.is_time_trial_session}, is_valid={sample.lap_info.is_valid_lap}")
            return False
    
    def get_metrics(self) -> GatingMetrics:
        """Get current gating metrics for observability."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset gating metrics."""
        self.metrics = GatingMetrics()
        self.logger.info("Gating metrics reset")
    
    def log_metrics(self) -> None:
        """Log current gating metrics."""
        m = self.metrics
        self.logger.info(
            f"Gating metrics: total={m.total_packets}, "
            f"non_tt_filtered={m.filtered_non_tt_sessions}, "
            f"invalid_lap_filtered={m.filtered_invalid_laps}, "
            f"non_player_filtered={m.filtered_non_player_cars}, "
            f"passed={m.passed_samples}, "
            f"pass_rate={m.pass_rate:.1f}%"
        )