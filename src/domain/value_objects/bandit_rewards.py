"""Value objects for bandit algorithm and reward tracking."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class ActionClass(Enum):
    """Discrete action classes for bandit algorithm."""
    BRAKE_EARLIER = "brake_earlier"
    PRESSURE_FASTER = "pressure_faster"
    RELEASE_EARLIER = "release_earlier"
    THROTTLE_EARLIER = "throttle_earlier"
    REDUCE_STEERING = "reduce_steering"


@dataclass(frozen=True)
class CornerId:
    """Unique identifier for a corner."""
    track_id: int
    corner_number: int
    
    def __str__(self) -> str:
        return f"T{self.track_id}C{self.corner_number}"


@dataclass(frozen=True)
class Reward:
    """Reward from coaching action based on per-turn split of next valid lap."""
    
    corner_id: CornerId
    action_class: ActionClass
    reward_ms: float  # Negative = time loss, Positive = time gain
    confidence: float  # 0.0 to 1.0
    evaluation_type: str  # "split_comparison", "telemetry_analysis", "manual"
    
    # Context for reward validity
    laps_evaluated: int
    track_conditions: str  # "similar", "changed"
    driver_consistency: float  # std dev of recent lap times
    
    def __post_init__(self):
        """Validate reward values."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if self.laps_evaluated < 1:
            raise ValueError("Must evaluate at least 1 lap")
    
    @property
    def is_valid_reward(self) -> bool:
        """Check if this reward is suitable for bandit learning."""
        return (
            self.confidence >= 0.5 and
            self.laps_evaluated >= 2 and
            self.track_conditions == "similar" and
            self.driver_consistency < 2.0  # Less than 2s std dev
        )
    
    @property
    def is_positive(self) -> bool:
        """Check if this represents a positive outcome."""
        return self.reward_ms > 0
    
    @property
    def is_neutral(self) -> bool:
        """Check if this represents a neutral outcome (no clear benefit)."""
        return abs(self.reward_ms) <= 10.0  # Within 10ms considered neutral


@dataclass
class BanditArm:
    """Individual arm in the bandit algorithm for an action class on a corner."""
    
    corner_id: CornerId
    action_class: ActionClass
    
    # Thompson Sampling parameters (Beta distribution)
    alpha: float = 1.0  # Successes + 1
    beta: float = 1.0   # Failures + 1
    
    # Reward tracking
    total_rewards: float = 0.0
    reward_count: int = 0
    last_selected: Optional[datetime] = None
    
    # Cooldown tracking
    cooldown_until: Optional[datetime] = None
    consecutive_selections: int = 0
    
    def __post_init__(self):
        """Validate arm parameters."""
        if self.alpha <= 0 or self.beta <= 0:
            raise ValueError("Alpha and beta must be positive")
    
    @property
    def expected_reward(self) -> float:
        """Expected reward (mean of beta distribution)."""
        return self.alpha / (self.alpha + self.beta)
    
    @property
    def confidence_interval(self) -> float:
        """Width of 95% confidence interval."""
        import math
        # Approximation for beta distribution CI width
        mean = self.expected_reward
        variance = (self.alpha * self.beta) / ((self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1))
        return 1.96 * math.sqrt(variance)
    
    @property
    def is_in_cooldown(self) -> bool:
        """Check if this arm is currently in cooldown."""
        if self.cooldown_until is None:
            return False
        return datetime.utcnow() < self.cooldown_until
    
    def update_with_reward(self, reward: Reward) -> None:
        """Update arm parameters with new reward."""
        if not reward.is_valid_reward:
            return
        
        # Update reward tracking
        self.total_rewards += reward.reward_ms
        self.reward_count += 1
        
        # Update Beta distribution parameters
        # Convert reward to binary success/failure with confidence weighting
        normalized_reward = max(-1.0, min(1.0, reward.reward_ms / 100.0))  # Normalize to [-1, 1]
        success_weight = reward.confidence * max(0, normalized_reward)
        failure_weight = reward.confidence * max(0, -normalized_reward)
        
        self.alpha += success_weight
        self.beta += failure_weight
    
    def apply_cooldown(self, cooldown_minutes: int) -> None:
        """Apply cooldown to prevent over-coaching."""
        from datetime import timedelta
        self.cooldown_until = datetime.utcnow() + timedelta(minutes=cooldown_minutes)
        self.consecutive_selections += 1
    
    def reset_consecutive_selections(self) -> None:
        """Reset consecutive selection counter."""
        self.consecutive_selections = 0


@dataclass
class BanditState:
    """Complete state of the bandit algorithm."""
    
    arms: Dict[str, BanditArm]  # Key: f"{corner_id}_{action_class}"
    total_selections: int = 0
    total_rewards: float = 0.0
    
    # Configuration
    exploration_factor: float = 1.0
    cooldown_minutes: int = 15
    max_consecutive_selections: int = 3
    
    def get_arm_key(self, corner_id: CornerId, action_class: ActionClass) -> str:
        """Generate key for arm lookup."""
        return f"{corner_id}_{action_class.value}"
    
    def get_or_create_arm(self, corner_id: CornerId, action_class: ActionClass) -> BanditArm:
        """Get existing arm or create new one."""
        key = self.get_arm_key(corner_id, action_class)
        
        if key not in self.arms:
            self.arms[key] = BanditArm(corner_id, action_class)
        
        return self.arms[key]
    
    def get_available_arms(self, corner_id: CornerId) -> List[BanditArm]:
        """Get all available (non-cooldown) arms for a corner."""
        available = []
        
        for action_class in ActionClass:
            arm = self.get_or_create_arm(corner_id, action_class)
            if not arm.is_in_cooldown:
                available.append(arm)
        
        return available
    
    def update_global_stats(self, reward: Reward) -> None:
        """Update global bandit statistics."""
        if reward.is_valid_reward:
            self.total_selections += 1
            self.total_rewards += reward.reward_ms
    
    @property
    def average_reward(self) -> float:
        """Average reward across all selections."""
        if self.total_selections == 0:
            return 0.0
        return self.total_rewards / self.total_selections
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for persistence."""
        return {
            "arms": {
                key: {
                    "corner_id": {"track_id": arm.corner_id.track_id, "corner_number": arm.corner_id.corner_number},
                    "action_class": arm.action_class.value,
                    "alpha": arm.alpha,
                    "beta": arm.beta,
                    "total_rewards": arm.total_rewards,
                    "reward_count": arm.reward_count,
                    "last_selected": arm.last_selected.isoformat() if arm.last_selected else None,
                    "cooldown_until": arm.cooldown_until.isoformat() if arm.cooldown_until else None,
                    "consecutive_selections": arm.consecutive_selections
                }
                for key, arm in self.arms.items()
            },
            "total_selections": self.total_selections,
            "total_rewards": self.total_rewards,
            "exploration_factor": self.exploration_factor,
            "cooldown_minutes": self.cooldown_minutes,
            "max_consecutive_selections": self.max_consecutive_selections
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BanditState":
        """Create from dictionary (for loading from persistence)."""
        state = cls(
            arms={},
            total_selections=data.get("total_selections", 0),
            total_rewards=data.get("total_rewards", 0.0),
            exploration_factor=data.get("exploration_factor", 1.0),
            cooldown_minutes=data.get("cooldown_minutes", 15),
            max_consecutive_selections=data.get("max_consecutive_selections", 3)
        )
        
        # Restore arms
        for key, arm_data in data.get("arms", {}).items():
            corner_id = CornerId(
                track_id=arm_data["corner_id"]["track_id"],
                corner_number=arm_data["corner_id"]["corner_number"]
            )
            action_class = ActionClass(arm_data["action_class"])
            
            arm = BanditArm(
                corner_id=corner_id,
                action_class=action_class,
                alpha=arm_data.get("alpha", 1.0),
                beta=arm_data.get("beta", 1.0),
                total_rewards=arm_data.get("total_rewards", 0.0),
                reward_count=arm_data.get("reward_count", 0),
                consecutive_selections=arm_data.get("consecutive_selections", 0)
            )
            
            if arm_data.get("last_selected"):
                arm.last_selected = datetime.fromisoformat(arm_data["last_selected"])
            if arm_data.get("cooldown_until"):
                arm.cooldown_until = datetime.fromisoformat(arm_data["cooldown_until"])
            
            state.arms[key] = arm
        
        return state