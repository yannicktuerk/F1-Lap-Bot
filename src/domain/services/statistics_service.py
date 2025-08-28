"""Statistics service for IQR calculations and corner analysis."""
import numpy as np
from typing import List, Tuple, Optional, Dict
from ..entities.telemetry_sample import PlayerTelemetrySample


class StatisticsService:
    """Service for statistical calculations used in corner analysis."""
    
    def calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate key percentiles for a dataset.
        
        Args:
            values: List of numerical values
            
        Returns:
            Dictionary with percentiles (p25, p50, p75) and IQR
        """
        if not values:
            return {
                'p25': 0.0,
                'p50': 0.0,
                'p75': 0.0,
                'iqr': 0.0,
                'count': 0
            }
        
        np_values = np.array(values)
        
        return {
            'p25': float(np.percentile(np_values, 25)),
            'p50': float(np.percentile(np_values, 50)),  # median
            'p75': float(np.percentile(np_values, 75)),
            'iqr': float(np.percentile(np_values, 75) - np.percentile(np_values, 25)),
            'count': len(values)
        }
    
    def calculate_normalized_impact(
        self, 
        value: float, 
        reference_median: float, 
        reference_iqr: float
    ) -> float:
        """
        Calculate IQR-normalized impact score.
        
        Args:
            value: The value to normalize
            reference_median: Reference median value
            reference_iqr: Reference IQR for normalization
            
        Returns:
            Normalized impact score (0.0 = at reference, 1.0 = 1 IQR worse)
        """
        if reference_iqr <= 0:
            return 0.0
        
        delta = value - reference_median
        # Positive normalized impact = worse than reference
        return max(0.0, delta / reference_iqr)
    
    def calculate_consistency_score(
        self, 
        values: List[float], 
        reference_iqr: float
    ) -> float:
        """
        Calculate consistency score for a driver's performance.
        
        Args:
            values: List of the driver's times for this corner
            reference_iqr: Reference IQR for normalization
            
        Returns:
            Consistency score (lower = more consistent)
        """
        if len(values) < 2 or reference_iqr <= 0:
            return 0.0
        
        driver_stats = self.calculate_percentiles(values)
        driver_iqr = driver_stats['iqr']
        
        # Normalize driver's IQR against reference IQR
        return driver_iqr / reference_iqr
    
    def detect_outliers(
        self, 
        values: List[float], 
        method: str = "iqr"
    ) -> Tuple[List[float], List[int]]:
        """
        Detect and filter outliers from a dataset.
        
        Args:
            values: List of numerical values
            method: Outlier detection method ("iqr" or "zscore")
            
        Returns:
            Tuple of (filtered_values, outlier_indices)
        """
        if len(values) < 4:  # Need minimum samples for outlier detection
            return values, []
        
        np_values = np.array(values)
        outlier_indices = []
        
        if method == "iqr":
            q1 = np.percentile(np_values, 25)
            q3 = np.percentile(np_values, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_indices = [
                i for i, val in enumerate(values)
                if val < lower_bound or val > upper_bound
            ]
        
        elif method == "zscore":
            mean = np.mean(np_values)
            std = np.std(np_values)
            
            if std > 0:
                z_scores = np.abs((np_values - mean) / std)
                outlier_indices = [
                    i for i, z in enumerate(z_scores)
                    if z > 2.5  # 2.5 standard deviations
                ]
        
        filtered_values = [
            val for i, val in enumerate(values)
            if i not in outlier_indices
        ]
        
        return filtered_values, outlier_indices
    
    def calculate_corner_impact_ranking(
        self, 
        corner_deltas: Dict[int, float],
        corner_references: Dict[int, Tuple[float, float]]  # (median, iqr)
    ) -> List[Tuple[int, float]]:
        """
        Rank corners by normalized impact for coaching prioritization.
        
        Args:
            corner_deltas: Dictionary of corner_id -> delta_ms
            corner_references: Dictionary of corner_id -> (median_ms, iqr_ms)
            
        Returns:
            List of (corner_id, normalized_impact) sorted by impact (highest first)
        """
        corner_impacts = []
        
        for corner_id, delta_ms in corner_deltas.items():
            if corner_id in corner_references:
                median_ms, iqr_ms = corner_references[corner_id]
                normalized_impact = self.calculate_normalized_impact(
                    delta_ms, 0.0, iqr_ms  # delta already calculated vs median
                )
                corner_impacts.append((corner_id, normalized_impact))
        
        # Sort by impact (highest = worst performance = most improvement potential)
        return sorted(corner_impacts, key=lambda x: x[1], reverse=True)
    
    def identify_performance_mode(
        self, 
        lap_times: List[float], 
        min_samples: int = 5
    ) -> Optional[str]:
        """
        Identify the preferred performance mode (line) when multiple exist.
        
        Args:
            lap_times: List of lap times to analyze
            min_samples: Minimum samples needed for mode detection
            
        Returns:
            Mode identifier ("fast" or "consistent") or None
        """
        if len(lap_times) < min_samples:
            return None
        
        # Remove outliers first
        filtered_times, _ = self.detect_outliers(lap_times)
        
        if len(filtered_times) < min_samples:
            return None
        
        stats = self.calculate_percentiles(filtered_times)
        
        # If IQR is small relative to median, it's a "consistent" mode
        # If fastest times are significantly faster, it's a "fast" mode
        consistency_ratio = stats['iqr'] / stats['p50'] if stats['p50'] > 0 else 0
        
        if consistency_ratio < 0.02:  # Very consistent (< 2% variation)
            return "consistent"
        else:
            # Check if there are significantly faster laps at the low end
            fastest_10_percent = sorted(filtered_times)[:max(1, len(filtered_times) // 10)]
            if fastest_10_percent:
                fastest_avg = np.mean(fastest_10_percent)
                if (stats['p50'] - fastest_avg) / stats['p50'] > 0.01:  # >1% faster
                    return "fast"
        
        return "consistent"
    
    def calculate_expected_improvement(
        self,
        current_performance: float,
        reference_performance: float,
        action_difficulty: float = 0.5
    ) -> float:
        """
        Calculate expected improvement from a coaching action.
        
        Args:
            current_performance: Current lap time or corner time
            reference_performance: Reference/target performance
            action_difficulty: Difficulty of the action (0.0=easy, 1.0=hard)
            
        Returns:
            Expected improvement in milliseconds
        """
        max_potential = max(0.0, current_performance - reference_performance)
        
        # Difficulty factor reduces expected improvement
        difficulty_factor = 1.0 - (action_difficulty * 0.7)  # Max 70% reduction
        
        # Conservative estimate: achieve 30-70% of potential depending on difficulty
        expected_improvement = max_potential * 0.3 * difficulty_factor
        
        return expected_improvement