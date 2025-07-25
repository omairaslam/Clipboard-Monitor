"""
ConfigManager class - Handles all configuration operations.
Extracted from main.py for better modularity and testability.
"""
import os
import json
import logging
from pathlib import Path

# Use the same config path as utils.py for consistency
CONFIG_PATH = str(Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json")

from constants import DEFAULT_CONFIG, DEFAULT_POLLING_INTERVAL, DEFAULT_ENHANCED_CHECK_INTERVAL, DEFAULT_MAX_CLIPBOARD_SIZE

logger = logging.getLogger("config_manager")


class ConfigManager:
    """
    Manages application configuration with defaults and validation.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # Use centralized default configuration
    # DEFAULT_CONFIG is imported from constants.py
    
    def __init__(self, config_path=None):
        """
        Initialize the config manager.
        Args:
            config_path (str, optional): Path to config file. If None, uses CONFIG_PATH.
        """
        if hasattr(self, 'config'):
            return

        if config_path is None:
            # Use the module-level CONFIG_PATH
            config_path = CONFIG_PATH
        self.config_path = str(config_path)
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Load configuration from config.json, merging with defaults.
        
        Returns:
            dict: Loaded configuration with defaults applied
        """
        # Start with a deep copy of the defaults to avoid modifying the original
        config = json.loads(json.dumps(DEFAULT_CONFIG))
        
        try:
            config_file = Path(self.config_path)

            # Ensure the directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)

            if config_file.exists():
                with config_file.open('r') as f:
                    user_config = json.load(f)
                
                # Deep merge user config over defaults
                for section, settings in user_config.items():
                    if section in config and isinstance(config[section], dict):
                        # Update existing section
                        config[section].update(settings)
                    else:
                        # Add new section if it doesn't exist in defaults
                        config[section] = settings
                
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.info("No config.json found, using defaults")
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
        
        return config
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def get_section(self, section, default=None):
        """
        Get an entire configuration section.
        
        Args:
            section (str): Section name
            default: Default value if section not found
            
        Returns:
            dict: Configuration section or default
        """
        return self.config.get(section, default or {})
    
    def get_config_value(self, section, key, default=None):
        """
        Get a specific configuration value from a section.
        
        Args:
            section (str): The configuration section (e.g., 'general').
            key (str): The key within the section.
            default: The default value to return if not found.
            
        Returns:
            The configuration value or the default.
        """
        return self.config.get(section, {}).get(key, default)

    def set(self, key, value):
        """
        Set a configuration value (in memory only).
        
        Args:
            key (str): Configuration key
            value: Value to set
        """
        self.config[key] = value
    
    def save(self):
        """
        Save current configuration to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            config_file = Path(self.config_path)
            with config_file.open('w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def reload(self):
        """
        Reload configuration from file.
        
        Returns:
            dict: Reloaded configuration
        """
        self.config = self._load_config()
        return self.config
    
    def is_debug_mode(self):
        """
        Check if debug mode is enabled.
        
        Returns:
            bool: True if debug mode enabled
        """
        return self.get_config_value('general', 'debug_mode', False)
    
    def get_polling_interval(self):
        """
        Get polling interval for clipboard monitoring.
        
        Returns:
            float: Polling interval in seconds
        """
        return self.get_config_value('general', 'polling_interval', DEFAULT_POLLING_INTERVAL)
    
    def get_enhanced_check_interval(self):
        """
        Get enhanced check interval for macOS monitoring.
        
        Returns:
            float: Check interval in seconds
        """
        return self.get_config_value('general', 'enhanced_check_interval', DEFAULT_ENHANCED_CHECK_INTERVAL)
    
    def get_max_clipboard_size(self):
        """
        Get maximum clipboard size to process.
        
        Returns:
            int: Maximum size in bytes
        """
        return self.get_config_value('security', 'max_clipboard_size', DEFAULT_MAX_CLIPBOARD_SIZE)
    
    def get_module_config(self, module_name=None):
        """
        Get module configuration.
        
        Args:
            module_name (str, optional): Specific module name. If None, returns all module config.
            
        Returns:
            dict: Module configuration
        """
        modules_config = self.get_section('modules', {})
        # Always return a dict, never an int or other type
        if module_name:
            value = modules_config.get(module_name, {})
            if isinstance(value, dict):
                return value
            else:
                return {}  # fallback to empty dict if misconfigured
        return modules_config if isinstance(modules_config, dict) else {}
    
    def is_module_enabled(self, module_name):
        """
        Check if a specific module is enabled.
        
        Args:
            module_name (str): Name of the module
            
        Returns:
            bool: True if enabled, False if disabled
        """
        module_config = self.get_module_config()
        module_enabled = module_config.get(module_name, True)
        return module_enabled not in [0, False]
