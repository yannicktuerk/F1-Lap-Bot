"""Corner ranking service for identifying improvement opportunities."""
from typing import List, Dict, Optional, Tuple
from ..entities.corner_analysis import CornerImpact
from ..entities.telemetry_sample import PlayerTelemetrySample
from ..interfaces.corner_reference_repository import CornerReference
from .statistics_service import StatisticsService


class CornerRanker:
    """Service for ranking corners by improvement potential using IQR-normalized impact."""
    
    def __init__(self, statistics_service: StatisticsService):
        self.statistics_service = statistics_service
    
    def rank_corners_by_impact(
        self,
        driver_corner_times: Dict[int, List[float]],  # corner_id -> list of times
        corner_references: List[CornerReference],
        max_corners: int = 3
    ) -> List[CornerImpact]:
        """
        Rank corners by IQR-normalized impact for coaching prioritization.
        
        Args:
            driver_corner_times: Dictionary mapping corner_id to list of driver's times
            corner_references: List of statistical references for each corner
            max_corners: Maximum number of corners to return
            
        Returns:
            List of CornerImpact objects sorted by improvement potential
        """
        corner_impacts = []
        
        # Build reference lookup
        ref_lookup = {ref.corner_id: ref for ref in corner_references}
        
        for corner_id, times in driver_corner_times.items():
            if corner_id not in ref_lookup or len(times) < 2:
                continue
            
            reference = ref_lookup[corner_id]
            
            # Filter outliers from driver times
            filtered_times, _ = self.statistics_service.detect_outliers(times)
            
            if len(filtered_times) < 2:
                continue
            
            # Calculate driver statistics
            driver_stats = self.statistics_service.calculate_percentiles(filtered_times)
            driver_median = driver_stats['p50']
            
            # Calculate delta vs reference
            delta_ms = driver_median - reference.median_time_ms
            
            # Calculate normalized impact (IQR-normalized)
            normalized_impact = self.statistics_service.calculate_normalized_impact(
                driver_median, reference.median_time_ms, reference.iqr_ms
            )
            
            # Calculate consistency score
            consistency_score = self.statistics_service.calculate_consistency_score(
                filtered_times, reference.iqr_ms
            )
            
            corner_impact = CornerImpact(
                corner_id=corner_id,
                delta_ms=delta_ms,
                normalized_impact=normalized_impact,
                consistency_score=consistency_score,
                sample_count=len(filtered_times),
                reference_median_ms=reference.median_time_ms,
                reference_iqr_ms=reference.iqr_ms
            )
            
            corner_impacts.append(corner_impact)
        
        # Sort by improvement potential (normalized impact) - highest first
        ranked_impacts = sorted(
            corner_impacts,
            key=lambda x: x.improvement_potential,
            reverse=True
        )
        
        return ranked_impacts[:max_corners]
    
    def identify_coaching_priorities(
        self,
        corner_impacts: List[CornerImpact],
        consistency_threshold: float = 2.0
    ) -> Tuple[List[CornerImpact], List[CornerImpact]]:
        """
        Separate corners into consistency drills vs pace improvement opportunities.
        
        Args:
            corner_impacts: List of corner impact analyses
            consistency_threshold: Threshold for flagging consistency issues
            
        Returns:
            Tuple of (pace_opportunities, consistency_drills)
        """
        pace_opportunities = []
        consistency_drills = []
        
        for impact in corner_impacts:
            if impact.consistency_score > consistency_threshold:
                consistency_drills.append(impact)
            else:
                pace_opportunities.append(impact)
        
        # Sort each list by impact/priority
        pace_opportunities.sort(key=lambda x: x.improvement_potential, reverse=True)
        consistency_drills.sort(key=lambda x: x.consistency_score, reverse=True)
        
        return pace_opportunities, consistency_drills
    
    def select_coaching_corners(
        self,
        corner_impacts: List[CornerImpact],
        max_corners: int = 3,
        prioritize_consistency: bool = True
    ) -> List[int]:
        """
        Select corners for coaching based on impact and consistency requirements.
        
        Args:
            corner_impacts: List of corner impact analyses
            max_corners: Maximum number of corners to select
            prioritize_consistency: Whether to prioritize consistency over pace
            
        Returns:
            List of corner IDs selected for coaching
        """
        pace_opportunities, consistency_drills = self.identify_coaching_priorities(corner_impacts)
        
        selected_corners = []
        
        if prioritize_consistency and consistency_drills:
            # First address consistency issues
            consistency_needed = min(len(consistency_drills), max_corners)
            selected_corners.extend([
                impact.corner_id for impact in consistency_drills[:consistency_needed]
            ])
            max_corners -= consistency_needed
        
        # Fill remaining slots with pace opportunities
        if max_corners > 0 and pace_opportunities:
            pace_needed = min(len(pace_opportunities), max_corners)
            selected_corners.extend([
                impact.corner_id for impact in pace_opportunities[:pace_needed]
            ])
        
        return selected_corners
    
    def calculate_reference_quality_score(self, reference: CornerReference) -> float:
        """
        Calculate a quality score for a corner reference based on sample size and recency.
        
        Args:
            reference: Corner reference to evaluate
            
        Returns:
            Quality score (0.0-1.0, higher is better)
        """
        # Sample size component (more samples = better quality)
        sample_score = min(1.0, reference.sample_count / 50)  # Optimal at 50+ samples
        
        # Recency component (if we have last_updated)
        recency_score = 1.0
        if reference.last_updated:
            from datetime import datetime, timedelta
            days_old = (datetime.now() - reference.last_updated).days
            recency_score = max(0.2, 1.0 - (days_old / 30))  # Decay over 30 days
        
        # IQR reasonableness (not too wide or too narrow)
        iqr_ratio = reference.iqr_ms / reference.median_time_ms if reference.median_time_ms > 0 else 0
        iqr_score = 1.0
        if iqr_ratio < 0.01 or iqr_ratio > 0.2:  # Too narrow or too wide
            iqr_score = 0.5
        
        # Weighted combination
        quality_score = (
            sample_score * 0.5 +
            recency_score * 0.3 +
            iqr_score * 0.2
        )
        
        return quality_score
    
    def filter_high_quality_references(
        self,
        references: List[CornerReference],
        min_quality: float = 0.6
    ) -> List[CornerReference]:
        """
        Filter references to only include high-quality ones.
        
        Args:
            references: List of corner references to filter
            min_quality: Minimum quality score required
            
        Returns:
            Filtered list of high-quality references
        """
        return [
            ref for ref in references
            if self.calculate_reference_quality_score(ref) >= min_quality
        ]
    
    def extract_corner_times_from_telemetry(
        self,
        telemetry_samples: List[PlayerTelemetrySample],
        corner_definitions: Dict[int, Tuple[float, float]]  # corner_id -> (start_distance, end_distance)
    ) -> Dict[int, List[float]]:
        """
        Extract corner times from telemetry samples.
        
        Args:
            telemetry_samples: List of telemetry samples from a session
            corner_definitions: Dictionary defining corner boundaries by track distance
            
        Returns:
            Dictionary mapping corner_id to list of times through that corner
        """
        corner_times = {corner_id: [] for corner_id in corner_definitions.keys()}
        
        # This is a simplified implementation - in practice, you'd need sophisticated
        # algorithms to detect corner entry/exit and calculate times
        # For now, we'll return empty data as a placeholder
        
        # TODO: Implement proper corner detection from telemetry
        # - Detect braking points, apex, throttle pickup
        # - Calculate time deltas for entry/rotation/exit phases
        # - Handle lap boundaries and distance wrapping
        
        return corner_times