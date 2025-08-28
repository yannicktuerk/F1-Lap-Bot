"""Repository interface for coaching actions persistence (Port)."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from ..entities.corner_analysis import SelectedAction, ActionResult


class CoachingRepository(ABC):
    """Abstract repository interface for coaching actions persistence."""
    
    @abstractmethod
    async def save_action(self, action: SelectedAction) -> str:
        """
        Save a coaching action and return the generated ID.
        
        Args:
            action: The coaching action to save
            
        Returns:
            The generated unique ID for the saved action
        """
        pass
    
    @abstractmethod
    async def save_action_result(self, result: ActionResult) -> str:
        """
        Save an action result and return the generated ID.
        
        Args:
            result: The action result to save
            
        Returns:
            The generated unique ID for the saved result
        """
        pass
    
    @abstractmethod
    async def find_action_by_id(self, action_id: str) -> Optional[SelectedAction]:
        """
        Find a coaching action by its ID.
        
        Args:
            action_id: The unique identifier of the action
            
        Returns:
            The coaching action if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_result_by_action_id(self, action_id: str) -> Optional[ActionResult]:
        """
        Find an action result by the action ID.
        
        Args:
            action_id: The unique identifier of the action
            
        Returns:
            The action result if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_recent_actions_by_corner(
        self, 
        corner_id: int, 
        days_back: int = 7,
        limit: int = 10
    ) -> List[SelectedAction]:
        """
        Find recent coaching actions for a specific corner.
        
        Args:
            corner_id: The corner identifier
            days_back: Number of days to look back
            limit: Maximum number of actions to return
            
        Returns:
            List of recent coaching actions for the corner
        """
        pass
    
    @abstractmethod
    async def get_action_success_rate(
        self,
        action_type: str,
        phase: str,
        days_back: int = 30
    ) -> Dict[str, float]:
        """
        Get success rate statistics for a specific action type and phase.
        
        Args:
            action_type: The action type to analyze
            phase: The turn phase
            days_back: Number of days to analyze
            
        Returns:
            Dictionary containing success rate statistics
        """
        pass
    
    @abstractmethod
    async def find_pending_evaluations(self, max_age_hours: int = 24) -> List[SelectedAction]:
        """
        Find coaching actions that need evaluation (no result yet).
        
        Args:
            max_age_hours: Maximum age in hours for pending evaluations
            
        Returns:
            List of actions awaiting evaluation
        """
        pass
    
    @abstractmethod
    async def get_coaching_statistics(self) -> Dict[str, any]:
        """
        Get overall coaching statistics.
        
        Returns:
            Dictionary containing coaching statistics
        """
        pass