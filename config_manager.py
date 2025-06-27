"""
ConfigManager class - Handles all configuration operations.
Extracted from main.py for better modularity and testability.
"""

import os
import json
import logging
from pathlib import Path
from constants import DEFAULT_CONFIG, DEFAULT_POLLING_INTERVAL, DEFAULT_ENHANCED_CHECK_INTERVAL, DEFAULT_MAX_CLIPBOARD_SIZE

logger = logging.getLogger("config_manager")


class ConfigManager:
    """
    Manages application configuration with defaults and validation.
    """
    
    # Use centralized default configuration
    # DEFAULT_CONFIG is imported from constants.py
    
    def __init__(self, config_path=None):
        """
        Initialize the config manager.
        
        Args:
            config_path (str, optional): Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent / 'config.json'
        
        self.config_path = str(config_path)
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Load configuration from config.json if available.
        
        Returns:
            dict: Loaded configuration with defaults applied
        """
        config = DEFAULT_CONFIG.copy()
        
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with config_file.open('r') as f:
                    user_config = json.load(f)
                
                # Update general settings
                if 'general' in user_config:
                    for key, value in user_config['general'].items():
                        if key in config:
                            config[key] = value
                
                # Add support for performance, history, and security sections
                for section in ['performance', 'history', 'security', 'modules']:
                    if section in user_config:
                        config[section] = user_config[section]
                
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
        return self.config.get('debug_mode', False)
    
    def get_polling_interval(self):
        """
        Get polling interval for clipboard monitoring.
        
        Returns:
            float: Polling interval in seconds
        """
        return self.config.get('polling_interval', DEFAULT_POLLING_INTERVAL)
    
    def get_enhanced_check_interval(self):
        """
        Get enhanced check interval for macOS monitoring.
        
        Returns:
            float: Check interval in seconds
        """
        return self.config.get('enhanced_check_interval', DEFAULT_ENHANCED_CHECK_INTERVAL)
    
    def get_max_clipboard_size(self):
        """
        Get maximum clipboard size to process.
        
        Returns:
            int: Maximum size in bytes
        """
        security_config = self.get_section('security', {})
        return security_config.get('max_clipboard_size', DEFAULT_MAX_CLIPBOARD_SIZE)
    
    def get_module_config(self, module_name=None):
        """
        Get module configuration.
        
        Args:
            module_name (str, optional): Specific module name. If None, returns all module config.
            
        Returns:
            dict: Module configuration
        """
        modules_config = self.get_section('modules', {})
        
        if module_name:
            return modules_config.get(module_name, {})
        
        return modules_config
    
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
