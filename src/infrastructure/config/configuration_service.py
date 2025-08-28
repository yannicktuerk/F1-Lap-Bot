"""Configuration management with YAML loading and hot-reload capability (Issue 14)."""
import os
import yaml
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigChangeEvent:
    """Event emitted when configuration changes."""
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    changed_keys: List[str]
    timestamp: float


class ConfigurationValidator:
    """Validates configuration structure and values."""
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """Validate configuration structure and values."""
        required_sections = [
            'phases_priority', 'intensity_words', 'slip_amps', 
            'bandit', 'reviewer', 'performance', 'observability',
            'database', 'telemetry', 'turn_catalog', 'language'
        ]
        
        # Check required sections
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate phases_priority
        valid_phases = {'entry', 'rotation', 'exit'}
        if not all(phase in valid_phases for phase in config['phases_priority']):
            raise ValueError("Invalid phases in phases_priority")
        
        # Validate slip_amps structure
        for phase in ['entry', 'rotation', 'exit']:
            if phase not in config['slip_amps']:
                raise ValueError(f"Missing slip_amps configuration for phase: {phase}")
            
            for color in ['green', 'yellow', 'red']:
                if color not in config['slip_amps'][phase]:
                    raise ValueError(f"Missing {color} threshold for {phase} phase")
                
                thresholds = config['slip_amps'][phase][color]
                if not isinstance(thresholds, list) or len(thresholds) != 2:
                    raise ValueError(f"Invalid threshold format for {phase}.{color}")
                
                if thresholds[0] >= thresholds[1]:
                    raise ValueError(f"Invalid threshold range for {phase}.{color}")
        
        # Validate performance requirements
        if config['performance']['max_report_generation_ms'] <= 0:
            raise ValueError("max_report_generation_ms must be positive")
        
        # Validate telemetry settings
        if not (1024 <= config['telemetry']['udp_port'] <= 65535):
            raise ValueError("UDP port must be between 1024 and 65535")
        
        return True


class ConfigurationLoader:
    """Loads and manages YAML configuration with hot-reload."""
    
    def __init__(self, config_path: str = "config/coaching_config.yaml"):
        """Initialize configuration loader."""
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.last_modified: float = 0
        self.change_callbacks: List[Callable[[ConfigChangeEvent], None]] = []
        self._lock = threading.Lock()
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_watching = threading.Event()
        
        # Load initial configuration
        self.reload()
    
    def reload(self) -> None:
        """Reload configuration from file."""
        with self._lock:
            try:
                if not self.config_path.exists():
                    raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
                
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    new_config = yaml.safe_load(f)
                
                # Validate configuration
                ConfigurationValidator.validate(new_config)
                
                # Check for changes
                old_config = self.config.copy()
                changed_keys = self._find_changed_keys(old_config, new_config)
                
                # Update configuration
                self.config = new_config
                self.last_modified = self.config_path.stat().st_mtime
                
                # Notify listeners of changes
                if changed_keys and old_config:
                    event = ConfigChangeEvent(
                        old_config=old_config,
                        new_config=new_config.copy(),
                        changed_keys=changed_keys,
                        timestamp=time.time()
                    )
                    self._notify_change_listeners(event)
                
                logger.info(f"Configuration reloaded from {self.config_path}")
                if changed_keys:
                    logger.info(f"Changed configuration keys: {changed_keys}")
                    
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
                if not self.config:  # No fallback configuration available
                    raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        with self._lock:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        with self._lock:
            return self.config.get(section, {}).copy()
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration."""
        with self._lock:
            return self.config.copy()
    
    def add_change_listener(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Add callback for configuration changes."""
        self.change_callbacks.append(callback)
    
    def remove_change_listener(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Remove change callback."""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    def start_watching(self) -> None:
        """Start watching configuration file for changes."""
        if self._watch_thread and self._watch_thread.is_alive():
            return
        
        self._stop_watching.clear()
        self._watch_thread = threading.Thread(target=self._watch_file, daemon=True)
        self._watch_thread.start()
        logger.info("Started configuration file watching")
    
    def stop_watching(self) -> None:
        """Stop watching configuration file for changes."""
        self._stop_watching.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=5.0)
        logger.info("Stopped configuration file watching")
    
    def _watch_file(self) -> None:
        """Watch configuration file for changes in separate thread."""
        while not self._stop_watching.is_set():
            try:
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    if current_mtime > self.last_modified:
                        logger.info("Configuration file changed, reloading...")
                        self.reload()
                
                self._stop_watching.wait(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Error watching configuration file: {e}")
                self._stop_watching.wait(5.0)  # Wait longer on error
    
    def _find_changed_keys(self, old: Dict[str, Any], new: Dict[str, Any], prefix: str = '') -> List[str]:
        """Find changed keys between old and new configuration."""
        changed = []
        
        # Check for changed/new keys
        for key, value in new.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if key not in old:
                changed.append(full_key)
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changed.extend(self._find_changed_keys(old[key], value, full_key))
            elif value != old[key]:
                changed.append(full_key)
        
        # Check for deleted keys
        for key in old:
            if key not in new:
                full_key = f"{prefix}.{key}" if prefix else key
                changed.append(full_key)
        
        return changed
    
    def _notify_change_listeners(self, event: ConfigChangeEvent) -> None:
        """Notify all change listeners."""
        for callback in self.change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in configuration change callback: {e}")


class ConfigurationService:
    """Central configuration service for the coaching system."""
    
    def __init__(self, config_path: str = "config/coaching_config.yaml"):
        """Initialize configuration service."""
        self.loader = ConfigurationLoader(config_path)
        self.loader.start_watching()
    
    def get_phases_priority(self) -> List[str]:
        """Get phase priority configuration."""
        return self.loader.get('phases_priority', ['entry', 'rotation', 'exit'])
    
    def get_intensity_words(self) -> Dict[str, List[str]]:
        """Get intensity words configuration."""
        return self.loader.get_section('intensity_words')
    
    def get_slip_thresholds(self, phase: str) -> Dict[str, List[float]]:
        """Get slip thresholds for a specific phase."""
        return self.loader.get(f'slip_amps.{phase}', {})
    
    def get_bandit_config(self) -> Dict[str, Any]:
        """Get bandit optimization configuration."""
        return self.loader.get_section('bandit')
    
    def get_reviewer_config(self) -> Dict[str, Any]:
        """Get reviewer service configuration."""
        return self.loader.get_section('reviewer')
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance requirements configuration."""
        return self.loader.get_section('performance')
    
    def get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration."""
        return self.loader.get_section('observability')
    
    def get_telemetry_config(self) -> Dict[str, Any]:
        """Get telemetry configuration."""
        return self.loader.get_section('telemetry')
    
    def get_turn_catalog_config(self) -> Dict[str, Any]:
        """Get turn catalog configuration."""
        return self.loader.get_section('turn_catalog')
    
    def add_change_listener(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Add configuration change listener."""
        self.loader.add_change_listener(callback)
    
    def close(self) -> None:
        """Close configuration service and stop watching."""
        self.loader.stop_watching()