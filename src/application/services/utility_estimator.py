"""ML Utility Estimator with GBDT and fallback heuristic."""
import logging
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from ...domain.value_objects.action_utility import (
    ActionUtility, UtilityFeatures, UtilityEvaluation, ConfidenceLevel
)
from ...infrastructure.persistence.model_persistence import ModelPersistence


class UtilityEstimatorService:
    """
    ML utility estimator using lightweight GBDT with confidence bands and fallback heuristic.
    
    Estimates expected time gain per candidate action using ML when sufficient data exists,
    falling back to conservative heuristics when confidence is low or data is sparse.
    """
    
    def __init__(self, model_persistence: Optional[ModelPersistence] = None):
        """
        Initialize utility estimator service.
        
        Args:
            model_persistence: Model persistence handler (auto-created if None)
        """
        self.logger = logging.getLogger(__name__)
        self.model_persistence = model_persistence or ModelPersistence()
        
        # ML model (XGBoost/scikit-learn)
        self.model = None
        self.is_model_trained = False
        self.training_data: List[Tuple[UtilityFeatures, UtilityEvaluation]] = []
        
        # Model parameters
        self.min_training_samples = 50
        self.confidence_threshold = 0.7
        self.model_update_interval = timedelta(hours=6)
        self.last_model_update = None
        
        # Heuristic parameters (conservative fallback)
        self.heuristic_gains = {
            "brake_earlier": {"slow": 30, "medium": 20, "fast": 15, "chicane": 25},
            "pressure_faster": {"slow": 15, "medium": 25, "fast": 20, "chicane": 20}, 
            "release_earlier": {"slow": 10, "medium": 15, "fast": 12, "chicane": 18},
            "throttle_earlier": {"slow": 20, "medium": 35, "fast": 45, "chicane": 15},
            "reduce_steering": {"slow": 5, "medium": 10, "fast": 15, "chicane": 8}
        }
        
        # Intensity multipliers
        self.intensity_multipliers = {
            "light": 0.6,
            "medium": 1.0, 
            "aggressive": 1.4
        }
        
        # Load existing model if available
        self._initialize_model()
    
    async def estimate_utility(self, features: UtilityFeatures) -> ActionUtility:
        """
        Estimate expected utility (time gain) for a coaching action.
        
        Args:
            features: Feature set describing the action and context
            
        Returns:
            ActionUtility with expected gain and confidence
        """
        try:
            # Try ML estimation first if model is available and confident
            if self.is_model_trained and self.model is not None:
                ml_utility = await self._estimate_with_ml(features)
                if ml_utility and ml_utility.confidence_level != ConfidenceLevel.LOW:
                    return ml_utility
                    
                self.logger.debug(f"ML estimate has low confidence, falling back to heuristic")
            
            # Fall back to heuristic estimation
            return self._estimate_with_heuristic(features)
            
        except Exception as e:
            self.logger.error(f"❌ Error in utility estimation: {e}")
            # Safe fallback to conservative heuristic
            return self._estimate_with_heuristic(features, conservative=True)
    
    async def _estimate_with_ml(self, features: UtilityFeatures) -> Optional[ActionUtility]:
        """Estimate utility using trained ML model."""
        try:
            # Convert features to model input
            feature_vector = np.array(features.to_feature_vector()).reshape(1, -1)
            
            # Get prediction with uncertainty
            prediction = self.model.predict(feature_vector)[0]
            
            # Estimate uncertainty (for now, use simple heuristic)
            # In production, could use prediction intervals or ensemble methods
            uncertainty = self._estimate_prediction_uncertainty(features, prediction)
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(uncertainty)
            
            return ActionUtility(
                expected_gain_ms=float(prediction),
                confidence_interval_ms=float(uncertainty),
                confidence_level=confidence_level,
                source="ml"
            )
            
        except Exception as e:
            self.logger.error(f"❌ ML utility estimation failed: {e}")
            return None
    
    def _estimate_with_heuristic(self, features: UtilityFeatures, conservative: bool = False) -> ActionUtility:
        """Estimate utility using fallback heuristic."""
        try:
            # Base gain from lookup table
            base_gain = self.heuristic_gains.get(features.candidate_type, {}).get(
                features.corner_type, 20  # default gain
            )
            
            # Apply intensity multiplier
            intensity_mult = self.intensity_multipliers.get(features.intensity, 1.0)
            raw_gain = base_gain * intensity_mult
            
            # Apply contextual adjustments
            adjusted_gain = self._apply_contextual_adjustments(raw_gain, features)
            
            # Conservative mode reduces estimates by 50%
            if conservative:
                adjusted_gain *= 0.5
            
            # Large confidence interval for heuristic
            confidence_interval = max(adjusted_gain * 0.8, 100)  # At least 100ms uncertainty
            
            return ActionUtility(
                expected_gain_ms=adjusted_gain,
                confidence_interval_ms=confidence_interval,
                confidence_level=ConfidenceLevel.LOW,
                source="heuristic"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Heuristic utility estimation failed: {e}")
            # Ultimate fallback - very conservative
            return ActionUtility(
                expected_gain_ms=10.0,
                confidence_interval_ms=200.0,
                confidence_level=ConfidenceLevel.LOW,
                source="heuristic"
            )
    
    def _apply_contextual_adjustments(self, base_gain: float, features: UtilityFeatures) -> float:
        """Apply contextual adjustments to base gain estimate."""
        adjusted = base_gain
        
        # Slip condition adjustment
        if features.slip_band == "red":
            adjusted *= 0.3  # Very reduced gain in red slip conditions
        elif features.slip_band == "yellow":
            adjusted *= 0.7  # Reduced gain in yellow slip conditions
        
        # Delta-based adjustment (if already close to reference, less gain)
        total_delta = abs(features.entry_delta_ms) + abs(features.rotation_delta_ms) + abs(features.exit_delta_ms)
        if total_delta < 50:  # Already close to reference
            adjusted *= 0.6
        elif total_delta > 200:  # Far from reference, more gain potential
            adjusted *= 1.3
        
        # Device adjustment
        if features.device_config == "controller":
            adjusted *= 0.8  # Slightly reduced expectations for controller
        
        # Assists adjustment
        if "advanced" in features.assists_config:
            adjusted *= 0.9  # Slightly reduced with assists
        
        return max(adjusted, 5.0)  # Minimum 5ms gain
    
    def _estimate_prediction_uncertainty(self, features: UtilityFeatures, prediction: float) -> float:
        """Estimate uncertainty in ML prediction."""
        # Simple heuristic for uncertainty estimation
        # In production, could use ensemble variance or calibrated prediction intervals
        
        base_uncertainty = abs(prediction) * 0.3  # 30% of prediction magnitude
        
        # Increase uncertainty for edge cases
        if features.slip_band == "red":
            base_uncertainty *= 2.0
        if abs(prediction) > 100:  # Large predictions are more uncertain
            base_uncertainty *= 1.5
        if len(self.training_data) < 100:  # Less data = more uncertainty
            base_uncertainty *= 1.8
        
        return max(base_uncertainty, 20.0)  # Minimum 20ms uncertainty
    
    def _determine_confidence_level(self, uncertainty: float) -> ConfidenceLevel:
        """Determine confidence level based on uncertainty."""
        if uncertainty <= 50:
            return ConfidenceLevel.HIGH
        elif uncertainty <= 100:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    async def update_model(self, evaluation: UtilityEvaluation, features: UtilityFeatures) -> bool:
        """
        Update the model with new evaluation data.
        
        Args:
            evaluation: Actual outcome evaluation
            features: Features that led to this outcome
            
        Returns:
            True if model was updated, False otherwise
        """
        try:
            # Only use valid evaluations for training
            if not evaluation.is_valid_evaluation():
                self.logger.debug(f"Skipping invalid evaluation for model update")
                return False
            
            # Add to training data
            self.training_data.append((features, evaluation))
            self.logger.debug(f"Added training sample, total: {len(self.training_data)}")
            
            # Retrain model if enough data and time has passed
            should_retrain = (
                len(self.training_data) >= self.min_training_samples and
                (self.last_model_update is None or 
                 datetime.utcnow() - self.last_model_update > self.model_update_interval)
            )
            
            if should_retrain:
                return await self._retrain_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating model: {e}")
            return False
    
    async def _retrain_model(self) -> bool:
        """Retrain the ML model with accumulated data."""
        try:
            self.logger.info(f"🔄 Retraining utility model with {len(self.training_data)} samples")
            
            # Prepare training data
            X = np.array([features.to_feature_vector() for features, _ in self.training_data])
            y = np.array([eval.realized_gain_ms for _, eval in self.training_data])
            
            # Import ML library
            try:
                from xgboost import XGBRegressor
                model_class = XGBRegressor
                model_params = {
                    'n_estimators': 100,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'random_state': 42
                }
            except ImportError:
                self.logger.warning("XGBoost not available, falling back to scikit-learn")
                from sklearn.ensemble import GradientBoostingRegressor
                model_class = GradientBoostingRegressor
                model_params = {
                    'n_estimators': 100,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'random_state': 42
                }
            
            # Train model
            self.model = model_class(**model_params)
            self.model.fit(X, y)
            
            self.is_model_trained = True
            self.last_model_update = datetime.utcnow()
            
            # Save model
            metadata = {
                "training_samples": len(self.training_data),
                "model_type": model_class.__name__,
                "feature_count": X.shape[1],
                "training_score": float(self.model.score(X, y)),
                "retrained_at": self.last_model_update.isoformat()
            }
            
            await self.model_persistence.save_utility_model(self.model, metadata)
            
            self.logger.info(f"✅ Model retrained successfully (R²: {metadata['training_score']:.3f})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Model retraining failed: {e}")
            return False
    
    def _initialize_model(self):
        """Initialize model on startup."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            self.model = loop.run_until_complete(self.model_persistence.load_utility_model())
            
            if self.model is not None:
                self.is_model_trained = True
                self.logger.info("✅ Utility estimation model loaded successfully")
            else:
                self.logger.info("ℹ️ No trained model found - using heuristic fallback")
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing model: {e}")
    
    def get_estimation_status(self) -> Dict[str, Any]:
        """Get status of utility estimation service."""
        return {
            "model_trained": self.is_model_trained,
            "training_samples": len(self.training_data),
            "min_samples_required": self.min_training_samples,
            "last_model_update": self.last_model_update.isoformat() if self.last_model_update else None,
            "model_type": type(self.model).__name__ if self.model else None,
            "fallback_mode": not self.is_model_trained
        }