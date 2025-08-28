"""Thompson Sampling bandit policy for personalized coaching action selection."""
import logging
import random
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ...domain.value_objects.bandit_rewards import (
    ActionClass, CornerId, Reward, BanditArm, BanditState
)
from ...domain.value_objects.slip_indicators import AmpelColor
from ...infrastructure.persistence.model_persistence import ModelPersistence


class BanditPolicy:
    """
    Thompson Sampling bandit for personalized coaching action selection.
    
    Uses Thompson Sampling to balance exploration and exploitation, with cooldown
    mechanisms to prevent over-coaching and safety constraints for slip conditions.
    """
    
    def __init__(self, model_persistence: Optional[ModelPersistence] = None):
        """
        Initialize bandit policy.
        
        Args:
            model_persistence: Model persistence handler (auto-created if None)
        """
        self.logger = logging.getLogger(__name__)
        self.model_persistence = model_persistence or ModelPersistence()
        
        # Load or initialize bandit state
        self.state = self._load_bandit_state()
        
        # Safety constraints
        self.red_slip_blocked_actions = {
            "entry": [ActionClass.PRESSURE_FASTER],  # No aggressive pressure in red slip
            "exit": [ActionClass.THROTTLE_EARLIER]   # No early throttle in red slip
        }
        
        # Configuration
        self.default_cooldown_minutes = 15
        self.success_threshold_ms = 20.0  # Minimum gain to consider success
        self.max_consecutive_selections = 3
        
        # Auto-save interval
        self.last_save = datetime.utcnow()
        self.save_interval = timedelta(minutes=5)
    
    async def select_action(self, 
                          corner_id: CornerId, 
                          available_actions: List[ActionClass],
                          slip_color: AmpelColor,
                          phase: str) -> Optional[ActionClass]:
        """
        Select coaching action using Thompson Sampling with safety constraints.
        
        Args:
            corner_id: Corner identifier
            available_actions: List of candidate action classes
            slip_color: Current slip/ampel color for safety
            phase: Turn phase ("entry", "rotation", "exit")
            
        Returns:
            Selected action class or None if no safe actions available
        """
        try:
            # Filter actions by safety constraints
            safe_actions = self._filter_by_safety_constraints(
                available_actions, slip_color, phase
            )
            
            if not safe_actions:
                self.logger.debug(f"No safe actions available for {corner_id} in {slip_color} slip")
                return None
            
            # Get available arms (not in cooldown)
            available_arms = []
            for action_class in safe_actions:
                arm = self.state.get_or_create_arm(corner_id, action_class)
                if not arm.is_in_cooldown:
                    available_arms.append(arm)
            
            if not available_arms:
                self.logger.debug(f"All safe actions in cooldown for {corner_id}")
                return None
            
            # Thompson Sampling selection
            selected_arm = self._thompson_sampling_selection(available_arms)
            
            if selected_arm is None:
                return None
            
            # Apply selection and cooldown
            selected_arm.last_selected = datetime.utcnow()
            
            # Apply cooldown based on consecutive selections
            cooldown_minutes = self._calculate_cooldown(selected_arm)
            if cooldown_minutes > 0:
                selected_arm.apply_cooldown(cooldown_minutes)
            
            # Auto-save state periodically
            await self._auto_save_state()
            
            self.logger.info(f"🎯 Selected action {selected_arm.action_class.value} for {corner_id}")
            return selected_arm.action_class
            
        except Exception as e:
            self.logger.error(f"❌ Error in bandit action selection: {e}")
            return None
    
    def _filter_by_safety_constraints(self, 
                                    actions: List[ActionClass], 
                                    slip_color: AmpelColor, 
                                    phase: str) -> List[ActionClass]:
        """Filter actions by safety constraints based on slip conditions."""
        if slip_color != AmpelColor.RED:
            return actions  # No filtering needed for green/yellow
        
        # Block specific actions in red slip conditions
        blocked_actions = self.red_slip_blocked_actions.get(phase, [])
        safe_actions = [action for action in actions if action not in blocked_actions]
        
        self.logger.debug(f"Filtered {len(actions)} → {len(safe_actions)} actions for {slip_color} slip")
        return safe_actions
    
    def _thompson_sampling_selection(self, arms: List[BanditArm]) -> Optional[BanditArm]:
        """Select arm using Thompson Sampling."""
        try:
            # Sample from each arm's posterior distribution
            samples = []
            for arm in arms:
                # Sample from Beta(alpha, beta) distribution
                sample = np.random.beta(arm.alpha, arm.beta)
                samples.append((sample, arm))
            
            # Select arm with highest sample
            if samples:
                best_sample, best_arm = max(samples, key=lambda x: x[0])
                return best_arm
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Thompson sampling failed: {e}")
            # Fallback to random selection
            return random.choice(arms) if arms else None
    
    def _calculate_cooldown(self, arm: BanditArm) -> int:
        """Calculate cooldown minutes based on arm's selection history."""
        # Increase cooldown for consecutive selections of same action
        base_cooldown = self.default_cooldown_minutes
        
        if arm.consecutive_selections >= self.max_consecutive_selections:
            # Long cooldown for over-selection
            return base_cooldown * 3
        elif arm.consecutive_selections >= 2:
            # Moderate cooldown
            return base_cooldown * 2
        elif arm.expected_reward < 0.3:  # Poor performing action
            # Shorter cooldown for poor performers to allow more exploration
            return base_cooldown // 2
        else:
            # Standard cooldown
            return base_cooldown
    
    async def update_with_reward(self, 
                               corner_id: CornerId, 
                               action_class: ActionClass, 
                               reward: Reward) -> bool:
        """
        Update bandit with reward from coaching outcome.
        
        Args:
            corner_id: Corner where action was taken
            action_class: Action that was selected
            reward: Observed reward from action
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get the arm that was selected
            arm = self.state.get_or_create_arm(corner_id, action_class)
            
            # Update arm with reward
            arm.update_with_reward(reward)
            
            # Update global statistics
            self.state.update_global_stats(reward)
            
            # Reset consecutive selections if this was a clear success
            if reward.reward_ms > self.success_threshold_ms:
                arm.reset_consecutive_selections()
            
            # Log the update
            self.logger.info(f"📈 Updated {action_class.value} for {corner_id}: "
                           f"reward={reward.reward_ms:.1f}ms, "
                           f"expected={arm.expected_reward:.3f}")
            
            # Save state
            await self._save_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating bandit with reward: {e}")
            return False
    
    async def get_corner_recommendations(self, corner_id: CornerId) -> Dict[str, Any]:
        """
        Get recommendations and statistics for a specific corner.
        
        Args:
            corner_id: Corner to analyze
            
        Returns:
            Dictionary with recommendations and arm statistics
        """
        try:
            recommendations = {
                "corner_id": str(corner_id),
                "arms": {},
                "best_action": None,
                "exploration_opportunities": []
            }
            
            best_expected_reward = -float('inf')
            best_action = None
            
            for action_class in ActionClass:
                arm = self.state.get_or_create_arm(corner_id, action_class)
                
                arm_info = {
                    "expected_reward": arm.expected_reward,
                    "confidence_interval": arm.confidence_interval,
                    "total_selections": arm.reward_count,
                    "is_in_cooldown": arm.is_in_cooldown,
                    "consecutive_selections": arm.consecutive_selections
                }
                
                recommendations["arms"][action_class.value] = arm_info
                
                # Track best action
                if arm.expected_reward > best_expected_reward:
                    best_expected_reward = arm.expected_reward
                    best_action = action_class.value
                
                # Identify exploration opportunities (high uncertainty)
                if arm.confidence_interval > 0.3 and arm.reward_count < 5:
                    recommendations["exploration_opportunities"].append({
                        "action": action_class.value,
                        "reason": "insufficient_data",
                        "selections": arm.reward_count
                    })
            
            recommendations["best_action"] = best_action
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ Error getting corner recommendations: {e}")
            return {}
    
    def _load_bandit_state(self) -> BanditState:
        """Load bandit state from persistence or create new."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            saved_state = loop.run_until_complete(self.model_persistence.load_bandit_state())
            
            if saved_state:
                state = BanditState.from_dict(saved_state)
                self.logger.info(f"✅ Loaded bandit state with {len(state.arms)} arms")
                return state
            else:
                self.logger.info("ℹ️ No saved bandit state found - initializing new state")
                return BanditState(arms={})
                
        except Exception as e:
            self.logger.error(f"❌ Error loading bandit state: {e}")
            return BanditState(arms={})
    
    async def _save_state(self) -> bool:
        """Save current bandit state."""
        try:
            state_dict = self.state.to_dict()
            success = await self.model_persistence.save_bandit_state(state_dict)
            
            if success:
                self.last_save = datetime.utcnow()
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error saving bandit state: {e}")
            return False
    
    async def _auto_save_state(self) -> None:
        """Auto-save state if enough time has passed."""
        if datetime.utcnow() - self.last_save > self.save_interval:
            await self._save_state()
    
    async def reset_bandit_state(self) -> bool:
        """Reset all bandit state (for testing or fresh start)."""
        try:
            self.state = BanditState(arms={})
            success = await self._save_state()
            
            if success:
                self.logger.info("🔄 Bandit state reset successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error resetting bandit state: {e}")
            return False
    
    def get_bandit_status(self) -> Dict[str, Any]:
        """Get comprehensive bandit status and statistics."""
        return {
            "total_arms": len(self.state.arms),
            "total_selections": self.state.total_selections,
            "average_reward": self.state.average_reward,
            "exploration_factor": self.state.exploration_factor,
            "cooldown_minutes": self.state.cooldown_minutes,
            "arms_in_cooldown": sum(1 for arm in self.state.arms.values() if arm.is_in_cooldown),
            "last_save": self.last_save.isoformat(),
            "config": {
                "default_cooldown_minutes": self.default_cooldown_minutes,
                "success_threshold_ms": self.success_threshold_ms,
                "max_consecutive_selections": self.max_consecutive_selections
            }
        }