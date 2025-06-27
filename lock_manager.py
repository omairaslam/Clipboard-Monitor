"""
Centralized Lock Manager
Provides thread-safe locks for clipboard processing operations.
"""

import threading
import logging

logger = logging.getLogger("lock_manager")


class LockManager:
    """Centralized manager for thread locks to prevent race conditions."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one lock manager exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the lock manager with shared locks."""
        if not hasattr(self, 'initialized'):
            self.clipboard_processing_lock = threading.Lock()
            self.config_access_lock = threading.Lock()
            self.history_access_lock = threading.Lock()
            self.module_execution_lock = threading.Lock()
            self.initialized = True
            logger.debug("LockManager initialized with shared locks")
    
    def get_clipboard_processing_lock(self):
        """Get the shared clipboard processing lock."""
        return self.clipboard_processing_lock
    
    def get_config_access_lock(self):
        """Get the shared configuration access lock."""
        return self.config_access_lock
    
    def get_history_access_lock(self):
        """Get the shared history access lock."""
        return self.history_access_lock
    
    def get_module_execution_lock(self):
        """Get the shared module execution lock."""
        return self.module_execution_lock
