"""
ModuleManager class - Handles loading and execution of processing modules.
Extracted from main.py for better modularity and testability.
"""

import os
import importlib
import importlib.util
import logging
import threading
import hashlib
from pathlib import Path
from config_manager import ConfigManager
from lock_manager import LockManager
from constants import DEFAULT_MAX_CLIPBOARD_SIZE

logger = logging.getLogger("module_manager")


class ModuleManager:
    """
    Manages the loading and execution of processing modules.
    """
    
    def __init__(self):
        """Initialize the module manager."""
        self.modules = []
        self.module_specs = []
        self.lock_manager = LockManager()
        self.last_processed_hash = None
    
    def load_modules(self, modules_dir):
        """
        Load all enabled modules from the specified directory with lazy initialization.
        
        Args:
            modules_dir (str): Path to the modules directory
        """
        self.modules = []
        self.module_specs = []
        
        # Load module configuration
        module_config = self._load_module_config()
        
        modules_path = Path(modules_dir)
        if not modules_path.exists() or not modules_path.is_dir():
            logger.error(f"Module directory issue: {modules_dir}")
            return
        
        # First pass: collect module specs without importing
        for module_file in modules_path.iterdir():
            if module_file.name.endswith('_module.py'):
                module_name = module_file.stem  # Remove .py
                
                # Check if module is enabled
                module_enabled = module_config.get(module_name, True)
                if module_enabled not in [0, False]:
                    # Store module spec for lazy loading
                    spec = importlib.util.spec_from_file_location(module_name, str(module_file))
                    self.module_specs.append((module_name, spec))
                    logger.info(f"Found module: {module_name} (enabled: {module_enabled})")
                else:
                    logger.info(f"Module disabled in config: {module_name} (value: {module_enabled})")
    
    def _load_module_config(self):
        """Load module configuration from config.json."""
        try:
            config_manager = ConfigManager()
            config = config_manager.get_section('modules', {})
            return config
        except Exception as e:
            logger.error(f"Error loading module config: {e}")
            return {}
    
    def _load_module_if_needed(self, module_name, spec):
        """
        Lazy load a module only when needed.
        
        Args:
            module_name (str): Name of the module
            spec: Module specification
            
        Returns:
            module: Loaded module
            
        Raises:
            AttributeError: If module doesn't have required 'process' function
        """
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Validate module has process function
        if not hasattr(module, 'process') or not callable(module.process):
            raise AttributeError(f"Module {module_name} missing required 'process' function")
        
        return module
    
    def _validate_module(self, module):
        """
        Validate that a module has the required interface.
        
        Args:
            module: Module to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not hasattr(module, 'process'):
            logger.error(f"Module {getattr(module, '__name__', 'unknown')} missing 'process' function")
            return False
        
        if not callable(getattr(module, 'process')):
            logger.error(f"Module {getattr(module, '__name__', 'unknown')} 'process' is not callable")
            return False
        
        return True
    
    def _get_content_hash(self, content):
        """
        Generate a hash of the content to detect processing loops.
        
        Args:
            content: Content to hash
            
        Returns:
            str: MD5 hash of the content
        """
        if content is None:
            return "none"
        return hashlib.md5(str(content).encode()).hexdigest()
    
    def process_content(self, clipboard_content, max_size=DEFAULT_MAX_CLIPBOARD_SIZE):
        """
        Process clipboard content with all loaded modules.
        
        Args:
            clipboard_content (str): Content to process
            max_size (int): Maximum content size to process
            
        Returns:
            bool: True if any module processed the content, False otherwise
        """
        # Prevent processing extremely large content
        if clipboard_content and len(clipboard_content) > max_size:
            logger.warning(f"Skipping oversized clipboard content ({len(clipboard_content)} bytes)")
            return False
        
        with self.lock_manager.get_module_execution_lock():
            content_hash = self._get_content_hash(clipboard_content)
            if content_hash == self.last_processed_hash:
                logger.debug("Skipping processing - content hash matches last processed")
                return False
            
            self.last_processed_hash = content_hash
            processed = False
            
            # Lazy load modules if not already loaded
            if not self.modules and self.module_specs:
                for module_name, spec in self.module_specs:
                    try:
                        module = self._load_module_if_needed(module_name, spec)
                        self.modules.append(module)
                    except (ImportError, AttributeError) as e:
                        logger.error(f"Error loading module {module_name}: {e}")
            
            # Process with loaded modules
            for module in self.modules:
                try:
                    # Pass the relevant module config to the module's process function
                    module_specific_config = self._load_module_config().get(module.__name__, {})
                    if module.process(clipboard_content, module_specific_config):
                        processed = True
                        logger.info(f"Processed with module: {getattr(module, '__name__', 'unknown')}")
                except Exception as e:
                    logger.error(f"Error processing with module: {e}")
            
            return processed
    
    def get_enabled_modules(self):
        """
        Get list of enabled module names.
        
        Returns:
            list: List of enabled module names
        """
        return [name for name, spec in self.module_specs]
    
    def get_loaded_modules_count(self):
        """
        Get count of currently loaded modules.
        
        Returns:
            int: Number of loaded modules
        """
        return len(self.modules)
