"""Pattern matching service for detecting coaching attempt patterns in telemetry."""
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from statistics import mean, stdev

from ..value_objects.review_outcomes import (
    AttemptPattern, PatternDetection, PerformanceMetrics
)


class PatternMatcher:
    """
    Service for detecting specific coaching patterns in telemetry data.
    
    Analyzes telemetry sequences to detect whether the driver attempted
    the suggested coaching action and classifies the execution quality.
    """
    
    def __init__(self):
        """Initialize pattern matcher with detection thresholds."""
        self.logger = logging.getLogger(__name__)
        
        # Detection thresholds for different patterns
        self.brake_earlier_threshold_m = 15.0  # 15m earlier brake point
        self.pressure_faster_threshold = 0.3   # 30% faster pressure buildup
        self.release_earlier_threshold_deg = 5.0  # 5 degrees before apex
        self.throttle_earlier_threshold_deg = 3.0  # 3 degrees earlier throttle
        self.steering_reduction_threshold = 0.15   # 15% less steering input
        
        # Confidence thresholds
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.6
    
    def detect_pattern(self, 
                      pattern: AttemptPattern,
                      baseline_telemetry: List[Dict],
                      evaluation_telemetry: List[Dict]) -> PatternDetection:
        """
        Detect if a specific pattern was attempted in the evaluation telemetry.
        
        Args:
            pattern: Pattern to detect
            baseline_telemetry: Reference telemetry from before coaching
            evaluation_telemetry: Telemetry from after coaching
            
        Returns:
            PatternDetection with detection result and confidence
        """
        try:
            if pattern == AttemptPattern.BRAKE_EARLIER:
                return self._detect_brake_earlier(baseline_telemetry, evaluation_telemetry)
            elif pattern == AttemptPattern.PRESSURE_FASTER:
                return self._detect_pressure_faster(baseline_telemetry, evaluation_telemetry)
            elif pattern == AttemptPattern.RELEASE_EARLIER:
                return self._detect_release_earlier(baseline_telemetry, evaluation_telemetry)
            elif pattern == AttemptPattern.THROTTLE_EARLIER:
                return self._detect_throttle_earlier(baseline_telemetry, evaluation_telemetry)
            elif pattern == AttemptPattern.REDUCE_STEERING:
                return self._detect_reduce_steering(baseline_telemetry, evaluation_telemetry)
            else:
                self.logger.warning(f"Unknown pattern: {pattern}")
                return PatternDetection(
                    pattern=pattern,
                    detected=False,
                    confidence=0.0,
                    evidence={}
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error detecting pattern {pattern}: {e}")
            return PatternDetection(
                pattern=pattern,
                detected=False,
                confidence=0.0,
                evidence={"error": str(e)}
            )
    
    def _detect_brake_earlier(self, baseline: List[Dict], evaluation: List[Dict]) -> PatternDetection:
        """Detect earlier braking pattern."""
        try:
            # Extract brake points (distance where brake > 0.1)
            baseline_brake_points = self._extract_brake_points(baseline)
            evaluation_brake_points = self._extract_brake_points(evaluation)
            
            if not baseline_brake_points or not evaluation_brake_points:
                return PatternDetection(
                    pattern=AttemptPattern.BRAKE_EARLIER,
                    detected=False,
                    confidence=0.0,
                    evidence={"reason": "insufficient_brake_data"}
                )
            
            # Calculate average brake point shift
            baseline_avg = mean(baseline_brake_points)
            evaluation_avg = mean(evaluation_brake_points)
            brake_shift_m = baseline_avg - evaluation_avg  # Positive = earlier
            
            # Check for coast detection (endless coast would be bad)
            has_endless_coast = self._detect_endless_coast(evaluation)
            
            # Determine detection
            detected = (
                brake_shift_m >= self.brake_earlier_threshold_m and 
                not has_endless_coast
            )
            
            # Calculate confidence based on consistency and magnitude
            confidence = min(1.0, abs(brake_shift_m) / (self.brake_earlier_threshold_m * 2))
            if has_endless_coast:
                confidence *= 0.5  # Reduce confidence if coasting detected
            
            evidence = {
                "brake_shift_m": brake_shift_m,
                "baseline_brake_point_m": baseline_avg,
                "evaluation_brake_point_m": evaluation_avg,
                "has_endless_coast": has_endless_coast,
                "sample_count": len(evaluation_brake_points)
            }
            
            return PatternDetection(
                pattern=AttemptPattern.BRAKE_EARLIER,
                detected=detected,
                confidence=confidence,
                evidence=evidence
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error in brake earlier detection: {e}")
            return PatternDetection(
                pattern=AttemptPattern.BRAKE_EARLIER,
                detected=False,
                confidence=0.0,
                evidence={"error": str(e)}
            )
    
    def _detect_pressure_faster(self, baseline: List[Dict], evaluation: List[Dict]) -> PatternDetection:
        """Detect faster pressure buildup pattern."""
        try:
            # Extract brake pressure buildup rates
            baseline_rates = self._extract_pressure_rates(baseline)
            evaluation_rates = self._extract_pressure_rates(evaluation)
            
            if not baseline_rates or not evaluation_rates:
                return PatternDetection(
                    pattern=AttemptPattern.PRESSURE_FASTER,
                    detected=False,
                    confidence=0.0,
                    evidence={"reason": "insufficient_pressure_data"}
                )
            
            # Calculate average pressure buildup rate
            baseline_avg_rate = mean(baseline_rates)
            evaluation_avg_rate = mean(evaluation_rates)
            rate_improvement = (evaluation_avg_rate - baseline_avg_rate) / baseline_avg_rate
            
            # Check for front slip red (which would be bad)
            has_front_slip_red = self._detect_front_slip_red(evaluation)
            
            detected = (
                rate_improvement >= self.pressure_faster_threshold and
                not has_front_slip_red
            )
            
            confidence = min(1.0, rate_improvement / self.pressure_faster_threshold)
            if has_front_slip_red:
                confidence *= 0.3  # Heavily penalize front slip
            
            evidence = {
                "rate_improvement": rate_improvement,
                "baseline_avg_rate": baseline_avg_rate,
                "evaluation_avg_rate": evaluation_avg_rate,
                "has_front_slip_red": has_front_slip_red,
                "sample_count": len(evaluation_rates)
            }
            
            return PatternDetection(
                pattern=AttemptPattern.PRESSURE_FASTER,
                detected=detected,
                confidence=confidence,
                evidence=evidence
            )
            
        except Exception as e:
            return PatternDetection(
                pattern=AttemptPattern.PRESSURE_FASTER,
                detected=False,
                confidence=0.0,
                evidence={"error": str(e)}
            )
    
    def _detect_release_earlier(self, baseline: List[Dict], evaluation: List[Dict]) -> PatternDetection:
        """Detect earlier brake release pattern."""
        try:
            # Extract brake release points (where brake drops below 0.1)
            baseline_release_points = self._extract_brake_release_points(baseline)
            evaluation_release_points = self._extract_brake_release_points(evaluation)
            
            if not baseline_release_points or not evaluation_release_points:
                return PatternDetection(
                    pattern=AttemptPattern.RELEASE_EARLIER,
                    detected=False,
                    confidence=0.0,
                    evidence={"reason": "insufficient_release_data"}
                )
            
            # Calculate release point shift (in track position degrees)
            baseline_avg = mean(baseline_release_points)
            evaluation_avg = mean(evaluation_release_points)
            release_shift_deg = baseline_avg - evaluation_avg  # Positive = earlier
            
            # Check for "calmer hands" (less steering input variation)
            steering_calmness = self._measure_steering_calmness(evaluation) - self._measure_steering_calmness(baseline)
            
            detected = release_shift_deg >= self.release_earlier_threshold_deg
            
            confidence = min(1.0, release_shift_deg / (self.release_earlier_threshold_deg * 2))
            if steering_calmness > 0:
                confidence *= 1.2  # Bonus for calmer steering
            
            evidence = {
                "release_shift_deg": release_shift_deg,
                "baseline_release_deg": baseline_avg,
                "evaluation_release_deg": evaluation_avg,
                "steering_calmness_improvement": steering_calmness,
                "sample_count": len(evaluation_release_points)
            }
            
            return PatternDetection(
                pattern=AttemptPattern.RELEASE_EARLIER,
                detected=detected,
                confidence=min(1.0, confidence),
                evidence=evidence
            )
            
        except Exception as e:
            return PatternDetection(
                pattern=AttemptPattern.RELEASE_EARLIER,
                detected=False,
                confidence=0.0,
                evidence={"error": str(e)}
            )
    
    def _detect_throttle_earlier(self, baseline: List[Dict], evaluation: List[Dict]) -> PatternDetection:
        """Detect earlier throttle application pattern."""
        try:
            # Extract throttle application points
            baseline_throttle_points = self._extract_throttle_application_points(baseline)
            evaluation_throttle_points = self._extract_throttle_application_points(evaluation)
            
            if not baseline_throttle_points or not evaluation_throttle_points:
                return PatternDetection(
                    pattern=AttemptPattern.THROTTLE_EARLIER,
                    detected=False,
                    confidence=0.0,
                    evidence={"reason": "insufficient_throttle_data"}
                )
            
            # Calculate throttle application shift
            baseline_avg = mean(baseline_throttle_points)
            evaluation_avg = mean(evaluation_throttle_points)
            throttle_shift_deg = baseline_avg - evaluation_avg  # Positive = earlier
            
            # Check for wheelspin (which would be bad)
            has_wheelspin = self._detect_wheelspin(evaluation)
            
            detected = (
                throttle_shift_deg >= self.throttle_earlier_threshold_deg and
                not has_wheelspin
            )
            
            confidence = min(1.0, throttle_shift_deg / (self.throttle_earlier_threshold_deg * 2))
            if has_wheelspin:
                confidence *= 0.2  # Heavily penalize wheelspin
            
            evidence = {
                "throttle_shift_deg": throttle_shift_deg,
                "baseline_throttle_deg": baseline_avg,
                "evaluation_throttle_deg": evaluation_avg,
                "has_wheelspin": has_wheelspin,
                "sample_count": len(evaluation_throttle_points)
            }
            
            return PatternDetection(
                pattern=AttemptPattern.THROTTLE_EARLIER,
                detected=detected,
                confidence=confidence,
                evidence=evidence
            )
            
        except Exception as e:
            return PatternDetection(
                pattern=AttemptPattern.THROTTLE_EARLIER,
                detected=False,
                confidence=0.0,
                evidence={"error": str(e)}
            )
    
    def _detect_reduce_steering(self, baseline: List[Dict], evaluation: List[Dict]) -> PatternDetection:
        """Detect steering reduction pattern."""
        try:
            # Extract steering plateaus (max steering input in corner)
            baseline_steering = self._extract_max_steering_inputs(baseline)
            evaluation_steering = self._extract_max_steering_inputs(evaluation)
            
            if not baseline_steering or not evaluation_steering:
                return PatternDetection(
                    pattern=AttemptPattern.REDUCE_STEERING,
                    detected=False,
                    confidence=0.0,
                    evidence={"reason": "insufficient_steering_data"}
                )
            
            # Calculate steering reduction
            baseline_avg = mean(baseline_steering)
            evaluation_avg = mean(evaluation_steering)
            steering_reduction = (baseline_avg - evaluation_avg) / baseline_avg
            
            # Check for less counter-steering
            baseline_counter_steer = self._measure_counter_steering(baseline)
            evaluation_counter_steer = self._measure_counter_steering(evaluation)
            counter_steer_reduction = baseline_counter_steer - evaluation_counter_steer
            
            detected = steering_reduction >= self.steering_reduction_threshold
            
            confidence = min(1.0, steering_reduction / self.steering_reduction_threshold)
            if counter_steer_reduction > 0:
                confidence *= 1.3  # Bonus for less counter-steering
            
            evidence = {
                "steering_reduction": steering_reduction,
                "baseline_avg_steering": baseline_avg,
                "evaluation_avg_steering": evaluation_avg,
                "counter_steer_reduction": counter_steer_reduction,
                "sample_count": len(evaluation_steering)
            }
            
            return PatternDetection(
                pattern=AttemptPattern.REDUCE_STEERING,
                detected=detected,
                confidence=min(1.0, confidence),
                evidence=evidence
            )
            
        except Exception as e:
            return PatternDetection(
                pattern=AttemptPattern.REDUCE_STEERING,
                detected=False,
                confidence=0.0,
                evidence={"error": str(e)}
            )
    
    # Helper methods for telemetry analysis
    
    def _extract_brake_points(self, telemetry: List[Dict]) -> List[float]:
        """Extract brake application points from telemetry."""
        brake_points = []
        for sample in telemetry:
            if sample.get('brake', 0) > 0.1 and sample.get('distance_from_corner', 0) > 0:
                brake_points.append(sample['distance_from_corner'])
        return brake_points
    
    def _extract_pressure_rates(self, telemetry: List[Dict]) -> List[float]:
        """Extract brake pressure buildup rates."""
        rates = []
        prev_brake = 0
        prev_time = 0
        
        for sample in telemetry:
            brake = sample.get('brake', 0)
            time = sample.get('timestamp', 0)
            
            if time > prev_time and brake > prev_brake:
                rate = (brake - prev_brake) / (time - prev_time)
                rates.append(rate)
            
            prev_brake = brake
            prev_time = time
        
        return rates
    
    def _extract_brake_release_points(self, telemetry: List[Dict]) -> List[float]:
        """Extract brake release points in track position."""
        release_points = []
        prev_brake = 1.0
        
        for sample in telemetry:
            brake = sample.get('brake', 0)
            track_pos = sample.get('track_position_degrees', 0)
            
            if prev_brake > 0.1 and brake <= 0.1:
                release_points.append(track_pos)
            
            prev_brake = brake
        
        return release_points
    
    def _extract_throttle_application_points(self, telemetry: List[Dict]) -> List[float]:
        """Extract throttle application points."""
        throttle_points = []
        prev_throttle = 0
        
        for sample in telemetry:
            throttle = sample.get('throttle', 0)
            track_pos = sample.get('track_position_degrees', 0)
            
            if prev_throttle <= 0.1 and throttle > 0.1:
                throttle_points.append(track_pos)
            
            prev_throttle = throttle
        
        return throttle_points
    
    def _extract_max_steering_inputs(self, telemetry: List[Dict]) -> List[float]:
        """Extract maximum steering inputs in corners."""
        steering_inputs = []
        for sample in telemetry:
            steering = abs(sample.get('steering', 0))
            if steering > 0.1:  # Only count actual steering input
                steering_inputs.append(steering)
        return steering_inputs
    
    def _detect_endless_coast(self, telemetry: List[Dict]) -> bool:
        """Detect if driver is coasting too long after braking."""
        coast_duration = 0
        max_coast = 0
        
        for sample in telemetry:
            brake = sample.get('brake', 0)
            throttle = sample.get('throttle', 0)
            
            if brake <= 0.05 and throttle <= 0.05:
                coast_duration += 1
            else:
                max_coast = max(max_coast, coast_duration)
                coast_duration = 0
        
        # Consider > 1 second of coasting as "endless"
        return max_coast > 60  # 60 samples at ~60Hz
    
    def _detect_front_slip_red(self, telemetry: List[Dict]) -> bool:
        """Detect red front slip during braking."""
        for sample in telemetry:
            front_slip = sample.get('front_slip_ratio', 0)
            if front_slip > 0.15:  # Red slip threshold
                return True
        return False
    
    def _detect_wheelspin(self, telemetry: List[Dict]) -> bool:
        """Detect wheelspin during throttle application."""
        for sample in telemetry:
            rear_slip = sample.get('rear_slip_ratio', 0)
            throttle = sample.get('throttle', 0)
            if throttle > 0.3 and rear_slip > 0.12:  # Wheelspin threshold
                return True
        return False
    
    def _measure_steering_calmness(self, telemetry: List[Dict]) -> float:
        """Measure steering input smoothness (lower = calmer)."""
        steering_inputs = [sample.get('steering', 0) for sample in telemetry]
        if len(steering_inputs) < 2:
            return 0.0
        
        # Calculate standard deviation of steering changes
        steering_changes = [abs(steering_inputs[i] - steering_inputs[i-1]) 
                          for i in range(1, len(steering_inputs))]
        
        return stdev(steering_changes) if steering_changes else 0.0
    
    def _measure_counter_steering(self, telemetry: List[Dict]) -> float:
        """Measure amount of counter-steering."""
        counter_steer_count = 0
        prev_steering = 0
        
        for sample in telemetry:
            steering = sample.get('steering', 0)
            
            # Detect rapid steering direction changes
            if abs(steering - prev_steering) > 0.2:
                counter_steer_count += 1
            
            prev_steering = steering
        
        return counter_steer_count / max(1, len(telemetry))