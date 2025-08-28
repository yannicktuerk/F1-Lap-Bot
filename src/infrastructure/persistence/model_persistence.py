"""Model persistence for utility estimation and bandit state."""
import pickle
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime


class ModelPersistence:
    """Handles saving and loading of ML models and bandit state."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize model persistence.
        
        Args:
            base_path: Base directory for model storage (auto-detected if None)
        """
        self.logger = logging.getLogger(__name__)
        
        if base_path is None:
            # Auto-detect models directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..", "..", "..")
            self.base_path = os.path.join(project_root, "models")
        else:
            self.base_path = base_path
        
        # Ensure models directory exists
        os.makedirs(self.base_path, exist_ok=True)
        
        # Model file paths
        self.utility_model_path = os.path.join(self.base_path, "utility_estimator.pkl")
        self.bandit_state_path = os.path.join(self.base_path, "bandit_state.json")
        self.model_metadata_path = os.path.join(self.base_path, "model_metadata.json")
    
    async def save_utility_model(self, model: Any, metadata: Dict[str, Any]) -> bool:
        """
        Save utility estimation model.
        
        Args:
            model: Trained model object (scikit-learn or XGBoost)
            metadata: Model metadata (training info, features, etc.)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Save model binary
            with open(self.utility_model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Update metadata
            full_metadata = {
                "utility_model": {
                    **metadata,
                    "saved_at": datetime.utcnow().isoformat(),
                    "model_file": "utility_estimator.pkl"
                }
            }
            
            # Load existing metadata if it exists
            existing_metadata = await self.load_model_metadata()
            if existing_metadata:
                existing_metadata.update(full_metadata)
                full_metadata = existing_metadata
            
            # Save metadata
            with open(self.model_metadata_path, 'w') as f:
                json.dump(full_metadata, f, indent=2)
            
            self.logger.info(f"✅ Utility model saved successfully: {self.utility_model_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save utility model: {e}")
            return False
    
    async def load_utility_model(self) -> Optional[Any]:
        """
        Load utility estimation model.
        
        Returns:
            Loaded model object or None if not found/invalid
        """
        try:
            if not os.path.exists(self.utility_model_path):
                self.logger.info("ℹ️ No utility model found - will use heuristic fallback")
                return None
            
            with open(self.utility_model_path, 'rb') as f:
                model = pickle.load(f)
            
            self.logger.info(f"✅ Utility model loaded: {self.utility_model_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load utility model: {e}")
            return None
    
    async def save_bandit_state(self, bandit_state: Dict[str, Any]) -> bool:
        """
        Save bandit algorithm state.
        
        Args:
            bandit_state: Complete bandit state including arms, priors, etc.
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Add timestamp
            state_with_timestamp = {
                **bandit_state,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.bandit_state_path, 'w') as f:
                json.dump(state_with_timestamp, f, indent=2)
            
            self.logger.info(f"✅ Bandit state saved: {self.bandit_state_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save bandit state: {e}")
            return False
    
    async def load_bandit_state(self) -> Optional[Dict[str, Any]]:
        """
        Load bandit algorithm state.
        
        Returns:
            Bandit state dictionary or None if not found/invalid
        """
        try:
            if not os.path.exists(self.bandit_state_path):
                self.logger.info("ℹ️ No bandit state found - will initialize with defaults")
                return None
            
            with open(self.bandit_state_path, 'r') as f:
                bandit_state = json.load(f)
            
            self.logger.info(f"✅ Bandit state loaded: {self.bandit_state_path}")
            return bandit_state
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load bandit state: {e}")
            return None
    
    async def load_model_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Load model metadata.
        
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            if not os.path.exists(self.model_metadata_path):
                return None
            
            with open(self.model_metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load model metadata: {e}")
            return None
    
    async def clear_all_models(self) -> bool:
        """
        Clear all saved models and state.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            files_to_remove = [
                self.utility_model_path,
                self.bandit_state_path,
                self.model_metadata_path
            ]
            
            removed_count = 0
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed_count += 1
            
            self.logger.info(f"✅ Cleared {removed_count} model files")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to clear models: {e}")
            return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status of all models and state files.
        
        Returns:
            Status dictionary with file existence and metadata
        """
        status = {
            "utility_model": {
                "exists": os.path.exists(self.utility_model_path),
                "path": self.utility_model_path,
                "size_bytes": 0
            },
            "bandit_state": {
                "exists": os.path.exists(self.bandit_state_path),
                "path": self.bandit_state_path,
                "size_bytes": 0
            },
            "metadata": {
                "exists": os.path.exists(self.model_metadata_path),
                "path": self.model_metadata_path,
                "size_bytes": 0
            }
        }
        
        # Get file sizes if they exist
        for key, info in status.items():
            if info["exists"]:
                try:
                    info["size_bytes"] = os.path.getsize(info["path"])
                    info["modified_at"] = datetime.fromtimestamp(
                        os.path.getmtime(info["path"])
                    ).isoformat()
                except Exception:
                    pass
        
        return status