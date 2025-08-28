"""Domain service for calculating slip metrics from telemetry data."""
import math
import logging
from typing import Optional

from src.domain.entities.telemetry_sample import MotionExInfo, CarTelemetryInfo
from src.domain.value_objects.slip_indicators import SlipMetrics


class SlipCalculator:
    """Domain service for computing slip metrics from F1 telemetry data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Wheel indices (as per F1® 25 specification)
        self.REAR_LEFT = 0
        self.REAR_RIGHT = 1
        self.FRONT_LEFT = 2
        self.FRONT_RIGHT = 3
    
    def calculate_slip_metrics(
        self, 
        motion_ex: MotionExInfo,
        car_telemetry: CarTelemetryInfo
    ) -> SlipMetrics:
        """
        Calculate comprehensive slip metrics from Motion Ex and telemetry data.
        
        Args:
            motion_ex: Extended motion data with slip ratios and angles
            car_telemetry: Basic car telemetry for validation
            
        Returns:
            SlipMetrics: Calculated slip indicators
        """
        try:
            # Extract slip ratios (already provided by Motion Ex packet)
            slip_ratios = motion_ex.wheel_slip_ratio
            slip_angles = motion_ex.wheel_slip_angle
            
            # Calculate average slip ratios for front/rear axles
            front_slip_ratio = (slip_ratios[self.FRONT_LEFT] + slip_ratios[self.FRONT_RIGHT]) / 2.0
            rear_slip_ratio = (slip_ratios[self.REAR_LEFT] + slip_ratios[self.REAR_RIGHT]) / 2.0
            max_slip_ratio = max(abs(ratio) for ratio in slip_ratios)
            
            # Calculate average slip angles for front/rear axles
            front_slip_angle = (slip_angles[self.FRONT_LEFT] + slip_angles[self.FRONT_RIGHT]) / 2.0
            rear_slip_angle = (slip_angles[self.REAR_LEFT] + slip_angles[self.REAR_RIGHT]) / 2.0
            max_slip_angle = max(abs(angle) for angle in slip_angles)
            
            # Calculate combined slip factor using vector magnitude
            # This represents overall grip utilization (0.0 = perfect, 1.0 = maximum)
            combined_slip_factor = self._calculate_combined_slip_factor(
                front_slip_ratio, rear_slip_ratio, 
                front_slip_angle, rear_slip_angle
            )
            
            # Validate results
            combined_slip_factor = max(0.0, min(1.0, combined_slip_factor))
            
            return SlipMetrics(
                front_slip_ratio=front_slip_ratio,
                rear_slip_ratio=rear_slip_ratio,
                max_slip_ratio=max_slip_ratio,
                front_slip_angle=front_slip_angle,
                rear_slip_angle=rear_slip_angle,
                max_slip_angle=max_slip_angle,
                combined_slip_factor=combined_slip_factor
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating slip metrics: {e}")
            # Return safe fallback metrics
            return self._create_fallback_metrics()
    
    def _calculate_combined_slip_factor(
        self, 
        front_slip_ratio: float, 
        rear_slip_ratio: float,
        front_slip_angle: float, 
        rear_slip_angle: float
    ) -> float:
        """
        Calculate combined slip factor representing overall grip utilization.
        
        This uses a normalized combination of longitudinal and lateral slip
        to provide a single 0-1 indicator of how close the car is to the
        grip limit.
        
        Args:
            front_slip_ratio: Average front wheel slip ratio
            rear_slip_ratio: Average rear wheel slip ratio
            front_slip_angle: Average front wheel slip angle (radians)
            rear_slip_angle: Average rear wheel slip angle (radians)
            
        Returns:
            float: Combined slip factor (0.0 = perfect grip, 1.0 = at limit)
        """
        # Normalize slip ratios (typical racing range is 0-0.3 for good grip)
        longitudinal_factor = min(1.0, max(abs(front_slip_ratio), abs(rear_slip_ratio)) / 0.3)
        
        # Normalize slip angles (typical racing range is 0-0.2 radians ~11 degrees)
        lateral_factor = min(1.0, max(abs(front_slip_angle), abs(rear_slip_angle)) / 0.2)
        
        # Combine using vector magnitude (represents total grip circle utilization)
        combined = math.sqrt(longitudinal_factor**2 + lateral_factor**2)
        
        # Normalize to 0-1 range (sqrt(2) would be theoretical maximum)
        return min(1.0, combined / math.sqrt(2))
    
    def _create_fallback_metrics(self) -> SlipMetrics:
        """Create safe fallback metrics when calculation fails."""
        return SlipMetrics(
            front_slip_ratio=0.0,
            rear_slip_ratio=0.0,
            max_slip_ratio=0.0,
            front_slip_angle=0.0,
            rear_slip_angle=0.0,
            max_slip_angle=0.0,
            combined_slip_factor=0.0
        )
    
    def is_wheelspin_detected(self, motion_ex: MotionExInfo, threshold: float = 0.15) -> bool:
        """
        Detect wheelspin condition from slip ratios.
        
        Args:
            motion_ex: Motion data with slip ratios
            threshold: Slip ratio threshold for wheelspin detection
            
        Returns:
            bool: True if wheelspin is detected
        """
        try:
            # Check rear wheels primarily (drive wheels in F1)
            rear_slip = max(
                abs(motion_ex.wheel_slip_ratio[self.REAR_LEFT]),
                abs(motion_ex.wheel_slip_ratio[self.REAR_RIGHT])
            )
            
            return rear_slip > threshold
            
        except Exception as e:
            self.logger.error(f"Error detecting wheelspin: {e}")
            return False
    
    def is_understeer_detected(self, slip_metrics: SlipMetrics, threshold: float = 0.05) -> bool:
        """
        Detect understeer condition from slip angles.
        
        Args:
            slip_metrics: Calculated slip metrics
            threshold: Slip angle difference threshold (radians)
            
        Returns:
            bool: True if understeer is detected
        """
        try:
            # Understeer: front slip angle significantly higher than rear
            slip_diff = abs(slip_metrics.front_slip_angle) - abs(slip_metrics.rear_slip_angle)
            return slip_diff > threshold
            
        except Exception as e:
            self.logger.error(f"Error detecting understeer: {e}")
            return False
    
    def is_oversteer_detected(self, slip_metrics: SlipMetrics, threshold: float = 0.05) -> bool:
        """
        Detect oversteer condition from slip angles.
        
        Args:
            slip_metrics: Calculated slip metrics
            threshold: Slip angle difference threshold (radians)
            
        Returns:
            bool: True if oversteer is detected
        """
        try:
            # Oversteer: rear slip angle significantly higher than front
            slip_diff = abs(slip_metrics.rear_slip_angle) - abs(slip_metrics.front_slip_angle)
            return slip_diff > threshold
            
        except Exception as e:
            self.logger.error(f"Error detecting oversteer: {e}")
            return False