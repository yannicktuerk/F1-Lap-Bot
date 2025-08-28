"""Reviewer service for classifying coaching attempts and adjusting intensity."""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from statistics import mean

from ...domain.value_objects.review_outcomes import (
    ReviewOutcome, AttemptPattern, PatternDetection, PerformanceMetrics,
    ReviewClassification, PendingReview, IntensityAdjustment, ReviewerReaction
)
from ...domain.services.pattern_matcher import PatternMatcher


class ReviewerService:
    """
    Service for evaluating coaching effectiveness and adjusting strategy.
    
    Watches next 1-3 valid laps after coaching to classify attempt patterns,
    evaluate outcomes, and recommend intensity adjustments or strategy changes.
    """
    
    def __init__(self, pattern_matcher: Optional[PatternMatcher] = None):
        """
        Initialize reviewer service.
        
        Args:
            pattern_matcher: Pattern detection service (auto-created if None)
        """
        self.logger = logging.getLogger(__name__)
        self.pattern_matcher = pattern_matcher or PatternMatcher()
        
        # Tracking pending reviews
        self.pending_reviews: Dict[str, PendingReview] = {}
        
        # Classification thresholds
        self.success_thresholds = {
            "min_improvement_ms": 20.0,
            "max_slip_red_duration_ms": 200.0,
            "min_confidence": 0.7
        }
        
        self.overshoot_thresholds = {
            "min_time_loss_ms": 50.0,
            "max_slip_red_duration_ms": 100.0,
            "min_instability_score": 0.6
        }
        
        # Intensity adjustment mappings
        self.intensity_levels = ["light", "medium", "aggressive"]
        self.intensity_adjustments = {
            ReviewOutcome.SUCCESS: "maintain_or_progress",
            ReviewOutcome.OVERSHOOT: "reduce_intensity",
            ReviewOutcome.NO_ATTEMPT: "micro_drill",
            ReviewOutcome.INCONCLUSIVE: "maintain"
        }
    
    async def track_coaching_action(self, 
                                  action_id: str,
                                  corner_id: str, 
                                  action_pattern: AttemptPattern,
                                  intensity_level: str,
                                  baseline_telemetry: List[Dict]) -> bool:
        """
        Start tracking a coaching action for future evaluation.
        
        Args:
            action_id: Unique identifier for the coaching action
            corner_id: Corner where coaching was applied
            action_pattern: Type of pattern that was coached
            intensity_level: Intensity of the coaching
            baseline_telemetry: Telemetry from before coaching
            
        Returns:
            True if tracking started successfully
        """
        try:
            # Extract baseline performance metrics
            baseline_metrics = self._extract_performance_metrics(baseline_telemetry)
            
            # Create pending review
            pending_review = PendingReview(
                action_id=action_id,
                corner_id=corner_id,
                action_pattern=action_pattern,
                intensity_level=intensity_level,
                coaching_timestamp=datetime.utcnow(),
                baseline_metrics=baseline_metrics
            )
            
            self.pending_reviews[action_id] = pending_review
            
            self.logger.info(f"📋 Started tracking coaching action {action_id} for {corner_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error starting coaching tracking: {e}")
            return False
    
    async def evaluate_lap(self, action_id: str, lap_telemetry: List[Dict]) -> Optional[ReviewClassification]:
        """
        Evaluate a lap following coaching action.
        
        Args:
            action_id: ID of the coaching action being evaluated
            lap_telemetry: Telemetry data from the evaluation lap
            
        Returns:
            Final classification if evaluation is complete, None if more laps needed
        """
        try:
            if action_id not in self.pending_reviews:
                self.logger.warning(f"No pending review found for action {action_id}")
                return None
            
            pending_review = self.pending_reviews[action_id]
            
            if pending_review.is_complete:
                return pending_review.final_classification
            
            # Extract performance metrics from this lap
            lap_metrics = self._extract_performance_metrics(lap_telemetry)
            pending_review.add_evaluation_lap(lap_metrics)
            
            self.logger.debug(f"Added evaluation lap {pending_review.laps_evaluated} for action {action_id}")
            
            # Check if we have enough data for classification
            if pending_review.has_sufficient_data and pending_review.laps_evaluated >= 2:
                return await self._complete_review(pending_review, lap_telemetry)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating lap for action {action_id}: {e}")
            return None
    
    async def _complete_review(self, pending_review: PendingReview, latest_telemetry: List[Dict]) -> ReviewClassification:
        """Complete the review and generate final classification."""
        try:
            # Detect patterns in the latest telemetry
            pattern_detection = self.pattern_matcher.detect_pattern(
                pending_review.action_pattern,
                [pending_review.baseline_metrics],  # Convert metrics back to telemetry-like format
                latest_telemetry
            )
            
            # Analyze performance improvement
            performance_improvement = self._analyze_performance_improvement(pending_review)
            
            # Classify the outcome
            outcome = self._classify_outcome(
                pattern_detection, 
                performance_improvement, 
                pending_review.evaluation_metrics[-1]
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(outcome, pending_review)
            
            # Create classification
            classification = ReviewClassification(
                outcome=outcome,
                confidence=pattern_detection.confidence,
                pattern_detections=[pattern_detection],
                primary_pattern=pending_review.action_pattern if pattern_detection.detected else None,
                performance_metrics=pending_review.evaluation_metrics[-1],
                performance_improvement=performance_improvement,
                classification_reason=self._generate_classification_reason(
                    outcome, pattern_detection, performance_improvement
                ),
                recommendations=recommendations
            )
            
            # Complete the review
            pending_review.complete_review(classification)
            
            self.logger.info(f"✅ Completed review for action {pending_review.action_id}: "
                           f"outcome={outcome.value}, confidence={classification.confidence:.2f}")
            
            return classification
            
        except Exception as e:
            self.logger.error(f"❌ Error completing review: {e}")
            # Return inconclusive classification as fallback
            return ReviewClassification(
                outcome=ReviewOutcome.INCONCLUSIVE,
                confidence=0.0,
                pattern_detections=[],
                primary_pattern=None,
                performance_metrics=pending_review.evaluation_metrics[-1] if pending_review.evaluation_metrics else None,
                performance_improvement=False,
                classification_reason=f"Error in review: {e}",
                recommendations=["retry_evaluation"]
            )
    
    def _classify_outcome(self, 
                         pattern_detection: PatternDetection,
                         performance_improvement: bool,
                         latest_metrics: PerformanceMetrics) -> ReviewOutcome:
        """Classify the outcome based on pattern detection and performance."""
        
        # Check for overshoot conditions first
        if self._is_overshoot(pattern_detection, latest_metrics):
            return ReviewOutcome.OVERSHOOT
        
        # Check for success
        if self._is_success(pattern_detection, performance_improvement, latest_metrics):
            return ReviewOutcome.SUCCESS
        
        # Check for no attempt
        if not pattern_detection.detected or pattern_detection.confidence < 0.4:
            return ReviewOutcome.NO_ATTEMPT
        
        # Default to inconclusive
        return ReviewOutcome.INCONCLUSIVE
    
    def _is_success(self, pattern_detection: PatternDetection, 
                   performance_improvement: bool, metrics: PerformanceMetrics) -> bool:
        """Check if the outcome qualifies as success."""
        return (
            pattern_detection.detected and
            pattern_detection.confidence >= self.success_thresholds["min_confidence"] and
            performance_improvement and
            metrics.sector_delta_ms >= self.success_thresholds["min_improvement_ms"] and
            metrics.slip_red_duration_ms <= self.success_thresholds["max_slip_red_duration_ms"]
        )
    
    def _is_overshoot(self, pattern_detection: PatternDetection, metrics: PerformanceMetrics) -> bool:
        """Check if the outcome qualifies as overshoot."""
        has_wheelspin = metrics.max_rear_slip > 0.12
        has_front_slip = metrics.max_front_slip > 0.15
        has_time_loss = metrics.sector_delta_ms < -self.overshoot_thresholds["min_time_loss_ms"]
        has_long_slip_red = metrics.slip_red_duration_ms > self.overshoot_thresholds["max_slip_red_duration_ms"]
        
        return (
            pattern_detection.detected and  # They tried but overdid it
            (has_wheelspin or has_front_slip or has_time_loss or has_long_slip_red)
        )
    
    def _analyze_performance_improvement(self, pending_review: PendingReview) -> bool:
        """Analyze if there was overall performance improvement."""
        if not pending_review.baseline_metrics or not pending_review.evaluation_metrics:
            return False
        
        baseline = pending_review.baseline_metrics
        evaluation_avg = self._average_performance_metrics(pending_review.evaluation_metrics)
        
        # Compare key metrics
        sector_improvement = evaluation_avg.sector_delta_ms > baseline.sector_delta_ms
        exit_speed_improvement = evaluation_avg.exit_speed_kmh > baseline.exit_speed_kmh
        stability_improvement = (
            evaluation_avg.steering_smoothness < baseline.steering_smoothness and
            evaluation_avg.slip_red_duration_ms <= baseline.slip_red_duration_ms
        )
        
        # Success if 2 out of 3 key areas improved
        improvements = sum([sector_improvement, exit_speed_improvement, stability_improvement])
        return improvements >= 2
    
    def generate_reaction(self, classification: ReviewClassification, 
                         current_intensity: str) -> ReviewerReaction:
        """
        Generate appropriate reaction to review outcome.
        
        Args:
            classification: The review classification
            current_intensity: Current coaching intensity level
            
        Returns:
            Complete reaction with intensity adjustments and strategy
        """
        try:
            outcome = classification.outcome
            
            # Determine intensity adjustment
            intensity_adjustment = self._determine_intensity_adjustment(outcome, current_intensity)
            
            # Determine next strategy
            next_strategy = self._determine_next_strategy(outcome, classification)
            
            # Determine cooldown
            apply_cooldown, cooldown_duration = self._determine_cooldown(outcome, current_intensity)
            
            # Determine bandit update
            update_bandit, bandit_reward = self._determine_bandit_update(outcome, classification)
            
            # Generate reasoning
            reasoning = self._generate_reaction_reasoning(
                outcome, intensity_adjustment, next_strategy
            )
            
            return ReviewerReaction(
                outcome=outcome,
                intensity_adjustment=intensity_adjustment,
                next_coaching_strategy=next_strategy,
                apply_cooldown=apply_cooldown,
                cooldown_duration_minutes=cooldown_duration,
                update_bandit=update_bandit,
                bandit_reward_ms=bandit_reward,
                reasoning=reasoning
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error generating reaction: {e}")
            # Safe fallback reaction
            return ReviewerReaction(
                outcome=ReviewOutcome.INCONCLUSIVE,
                intensity_adjustment=None,
                next_coaching_strategy="maintain_current",
                apply_cooldown=True,
                cooldown_duration_minutes=30,
                update_bandit=False,
                bandit_reward_ms=0.0,
                reasoning=f"Error in reaction generation: {e}"
            )
    
    def _determine_intensity_adjustment(self, outcome: ReviewOutcome, 
                                      current_intensity: str) -> Optional[IntensityAdjustment]:
        """Determine appropriate intensity adjustment."""
        current_index = self.intensity_levels.index(current_intensity) if current_intensity in self.intensity_levels else 1
        
        if outcome == ReviewOutcome.SUCCESS:
            # Success: maintain or progress to next bottleneck
            return IntensityAdjustment(
                current_intensity=current_intensity,
                recommended_intensity=current_intensity,
                adjustment_reason="success_maintain"
            )
        
        elif outcome == ReviewOutcome.OVERSHOOT:
            # Overshoot: reduce intensity or switch to stability
            new_index = max(0, current_index - 1)
            new_intensity = self.intensity_levels[new_index]
            
            return IntensityAdjustment(
                current_intensity=current_intensity,
                recommended_intensity=new_intensity,
                adjustment_reason="overshoot_reduce",
                alternative_action="stability_focus"
            )
        
        elif outcome == ReviewOutcome.NO_ATTEMPT:
            # No attempt: micro-drill (same theme, focus)
            return IntensityAdjustment(
                current_intensity=current_intensity,
                recommended_intensity=current_intensity,
                adjustment_reason="no_attempt_focus"
            )
        
        else:  # INCONCLUSIVE
            return None
    
    def _determine_next_strategy(self, outcome: ReviewOutcome, 
                               classification: ReviewClassification) -> str:
        """Determine next coaching strategy."""
        if outcome == ReviewOutcome.SUCCESS:
            return "next_bottleneck"
        elif outcome == ReviewOutcome.OVERSHOOT:
            return "stability_focus"
        elif outcome == ReviewOutcome.NO_ATTEMPT:
            return "micro_drill"
        else:
            return "repeat_coaching"
    
    def _determine_cooldown(self, outcome: ReviewOutcome, intensity: str) -> tuple:
        """Determine if cooldown should be applied and duration."""
        if outcome == ReviewOutcome.SUCCESS:
            return False, 0  # No cooldown on success
        elif outcome == ReviewOutcome.OVERSHOOT:
            return True, 30  # Longer cooldown for overshoot
        elif outcome == ReviewOutcome.NO_ATTEMPT:
            return True, 15  # Moderate cooldown for no attempt
        else:
            return True, 20  # Default cooldown for inconclusive
    
    def _determine_bandit_update(self, outcome: ReviewOutcome, 
                               classification: ReviewClassification) -> tuple:
        """Determine if bandit should be updated and reward value."""
        if outcome == ReviewOutcome.SUCCESS:
            reward = classification.performance_metrics.sector_delta_ms
            return True, reward
        elif outcome == ReviewOutcome.OVERSHOOT:
            # Negative reward for overshoot
            reward = -abs(classification.performance_metrics.sector_delta_ms)
            return True, reward
        elif outcome == ReviewOutcome.NO_ATTEMPT:
            # Neutral reward for no attempt
            return True, 0.0
        else:
            # Don't update bandit for inconclusive
            return False, 0.0
    
    def _extract_performance_metrics(self, telemetry: List[Dict]) -> PerformanceMetrics:
        """Extract performance metrics from telemetry data."""
        try:
            # Extract key metrics
            apex_speed = max([sample.get('speed_kmh', 0) for sample in telemetry if sample.get('is_apex', False)], default=0)
            exit_speed = max([sample.get('speed_kmh', 0) for sample in telemetry if sample.get('is_exit', False)], default=0)
            sector_time = telemetry[-1].get('sector_time_ms', 0) if telemetry else 0
            
            # Slip metrics
            max_front_slip = max([sample.get('front_slip_ratio', 0) for sample in telemetry], default=0)
            max_rear_slip = max([sample.get('rear_slip_ratio', 0) for sample in telemetry], default=0)
            slip_red_duration = sum([1 for sample in telemetry if sample.get('slip_red', False)]) * 16.67  # ~60Hz to ms
            
            # Stability metrics
            steering_values = [abs(sample.get('steering', 0)) for sample in telemetry]
            steering_smoothness = sum([abs(steering_values[i] - steering_values[i-1]) 
                                     for i in range(1, len(steering_values))]) if len(steering_values) > 1 else 0
            
            throttle_progression = self._calculate_throttle_progression(telemetry)
            brake_consistency = self._calculate_brake_consistency(telemetry)
            
            # Delta metrics
            sector_delta = telemetry[-1].get('sector_delta_ms', 0) if telemetry else 0
            corner_delta = telemetry[-1].get('corner_delta_ms', 0) if telemetry else 0
            
            return PerformanceMetrics(
                apex_speed_kmh=apex_speed,
                exit_speed_kmh=exit_speed,
                sector_time_ms=sector_time,
                max_front_slip=max_front_slip,
                max_rear_slip=max_rear_slip,
                slip_red_duration_ms=slip_red_duration,
                steering_smoothness=steering_smoothness,
                throttle_progression=throttle_progression,
                brake_consistency=brake_consistency,
                sector_delta_ms=sector_delta,
                corner_delta_ms=corner_delta
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting performance metrics: {e}")
            # Return default metrics
            return PerformanceMetrics(
                apex_speed_kmh=0, exit_speed_kmh=0, sector_time_ms=0,
                max_front_slip=0, max_rear_slip=0, slip_red_duration_ms=0,
                steering_smoothness=0, throttle_progression=0, brake_consistency=0,
                sector_delta_ms=0, corner_delta_ms=0
            )
    
    def _calculate_throttle_progression(self, telemetry: List[Dict]) -> float:
        """Calculate throttle progression smoothness (0-1, higher is better)."""
        throttle_values = [sample.get('throttle', 0) for sample in telemetry]
        if len(throttle_values) < 2:
            return 0.0
        
        # Calculate average rate of throttle increase
        increases = [throttle_values[i] - throttle_values[i-1] 
                    for i in range(1, len(throttle_values)) 
                    if throttle_values[i] > throttle_values[i-1]]
        
        if not increases:
            return 0.0
        
        # Progressive throttle has consistent, moderate increases
        avg_increase = mean(increases)
        return min(1.0, avg_increase * 10)  # Scale to 0-1
    
    def _calculate_brake_consistency(self, telemetry: List[Dict]) -> float:
        """Calculate brake consistency (lower is better)."""
        brake_values = [sample.get('brake', 0) for sample in telemetry if sample.get('brake', 0) > 0.1]
        if len(brake_values) < 2:
            return 0.0
        
        # Calculate variance in brake pressure
        avg_brake = mean(brake_values)
        variance = sum([(b - avg_brake) ** 2 for b in brake_values]) / len(brake_values)
        return variance
    
    def _average_performance_metrics(self, metrics_list: List[PerformanceMetrics]) -> PerformanceMetrics:
        """Calculate average of multiple performance metrics."""
        if not metrics_list:
            return self._extract_performance_metrics([])
        
        return PerformanceMetrics(
            apex_speed_kmh=mean([m.apex_speed_kmh for m in metrics_list]),
            exit_speed_kmh=mean([m.exit_speed_kmh for m in metrics_list]),
            sector_time_ms=mean([m.sector_time_ms for m in metrics_list]),
            max_front_slip=mean([m.max_front_slip for m in metrics_list]),
            max_rear_slip=mean([m.max_rear_slip for m in metrics_list]),
            slip_red_duration_ms=mean([m.slip_red_duration_ms for m in metrics_list]),
            steering_smoothness=mean([m.steering_smoothness for m in metrics_list]),
            throttle_progression=mean([m.throttle_progression for m in metrics_list]),
            brake_consistency=mean([m.brake_consistency for m in metrics_list]),
            sector_delta_ms=mean([m.sector_delta_ms for m in metrics_list]),
            corner_delta_ms=mean([m.corner_delta_ms for m in metrics_list])
        )
    
    def _generate_classification_reason(self, outcome: ReviewOutcome, 
                                      pattern_detection: PatternDetection,
                                      performance_improvement: bool) -> str:
        """Generate human-readable reason for classification."""
        if outcome == ReviewOutcome.SUCCESS:
            return f"Pattern detected with {pattern_detection.confidence:.1%} confidence, performance improved"
        elif outcome == ReviewOutcome.OVERSHOOT:
            return "Pattern attempted but resulted in slip/time loss"
        elif outcome == ReviewOutcome.NO_ATTEMPT:
            return f"Pattern not detected (confidence: {pattern_detection.confidence:.1%})"
        else:
            return "Insufficient data or mixed signals for clear classification"
    
    def _generate_recommendations(self, outcome: ReviewOutcome, pending_review: PendingReview) -> List[str]:
        """Generate recommendations based on outcome."""
        recommendations = []
        
        if outcome == ReviewOutcome.SUCCESS:
            recommendations.append("Continue to next improvement opportunity")
            recommendations.append("Consider consistency drills")
        elif outcome == ReviewOutcome.OVERSHOOT:
            recommendations.append("Reduce coaching intensity")
            recommendations.append("Focus on stability before speed")
        elif outcome == ReviewOutcome.NO_ATTEMPT:
            recommendations.append("Use more specific micro-drills")
            recommendations.append("Ensure clear communication")
        else:
            recommendations.append("Continue monitoring")
            recommendations.append("Consider alternative coaching approach")
        
        return recommendations
    
    def _generate_reaction_reasoning(self, outcome: ReviewOutcome,
                                   intensity_adjustment: Optional[IntensityAdjustment],
                                   next_strategy: str) -> str:
        """Generate reasoning for the reaction."""
        base_reason = f"Outcome classified as {outcome.value}"
        
        if intensity_adjustment:
            if intensity_adjustment.is_intensity_change:
                base_reason += f", adjusting intensity from {intensity_adjustment.current_intensity} to {intensity_adjustment.recommended_intensity}"
            elif intensity_adjustment.is_theme_switch:
                base_reason += f", switching to {intensity_adjustment.alternative_action}"
        
        base_reason += f", next strategy: {next_strategy}"
        
        return base_reason
    
    def get_reviewer_status(self) -> Dict[str, Any]:
        """Get status of the reviewer service."""
        active_reviews = [r for r in self.pending_reviews.values() if not r.is_complete]
        completed_reviews = [r for r in self.pending_reviews.values() if r.is_complete]
        
        return {
            "total_reviews": len(self.pending_reviews),
            "active_reviews": len(active_reviews),
            "completed_reviews": len(completed_reviews),
            "success_rate": len([r for r in completed_reviews 
                               if r.final_classification and r.final_classification.outcome == ReviewOutcome.SUCCESS]) / max(1, len(completed_reviews)),
            "average_evaluation_laps": mean([r.laps_evaluated for r in completed_reviews]) if completed_reviews else 0,
            "thresholds": {
                "success": self.success_thresholds,
                "overshoot": self.overshoot_thresholds
            }
        }