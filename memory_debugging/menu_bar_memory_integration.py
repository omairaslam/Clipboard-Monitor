#!/usr/bin/env python3
"""
Memory Leak Detection Integration for Menu Bar App

This module integrates memory leak debugging into the menu bar application
by adding memory profiling decorators and checkpoints to key functions.

Usage:
    1. Import this module in menu_bar_app.py
    2. Apply @memory_profile decorators to suspect functions
    3. Add memory checkpoints at key locations
    4. Monitor memory usage through the unified dashboard
"""

import os
import sys
import functools
import threading
import time
from memory_leak_debugger import memory_debugger, memory_profile, log_memory, track_object

class MenuBarMemoryIntegration:
    def __init__(self):
        self.integration_active = False
        self.suspect_functions = [
            # Functions that might be causing memory leaks
            'update_status',
            'update_memory_status', 
            'update_recent_history',
            'copy_history_item',
            'take_memory_snapshot',
            '_monitoring_loop',
            'get_current_memory',
            'update_status_periodically',
            'initial_history_update'
        ]
        
        # Memory checkpoints for tracking
        self.checkpoints = {}
        
    def activate_integration(self):
        """Activate memory leak detection integration."""
        if self.integration_active:
            return
            
        self.integration_active = True
        
        # Start memory debugging
        memory_debugger.start_monitoring()
        log_memory("Menu Bar Memory Integration activated")
        
        # Set up periodic memory reports
        self.setup_periodic_reporting()
        
    def deactivate_integration(self):
        """Deactivate memory leak detection integration."""
        if not self.integration_active:
            return
            
        self.integration_active = False
        memory_debugger.stop_monitoring()
        log_memory("Menu Bar Memory Integration deactivated")
    
    def setup_periodic_reporting(self):
        """Set up periodic memory leak reporting."""
        def report_loop():
            while self.integration_active:
                try:
                    # Generate report every 30 minutes
                    time.sleep(30 * 60)
                    
                    if self.integration_active:
                        report = memory_debugger.generate_report()
                        log_memory("Periodic Memory Report Generated", "INFO")
                        
                        # Save report to file
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        report_file = f"memory_report_{timestamp}.txt"
                        
                        try:
                            with open(report_file, 'w') as f:
                                f.write(report)
                            log_memory(f"Memory report saved to {report_file}")
                        except Exception as e:
                            log_memory(f"Failed to save memory report: {e}", "ERROR")
                            
                except Exception as e:
                    log_memory(f"Error in periodic reporting: {e}", "ERROR")
        
        report_thread = threading.Thread(target=report_loop, daemon=True)
        report_thread.start()
    
    def add_memory_checkpoint(self, name, location="unknown"):
        """Add a memory checkpoint for tracking."""
        current_memory = memory_debugger.get_current_memory()
        timestamp = time.time()
        
        self.checkpoints[name] = {
            'memory_mb': current_memory,
            'timestamp': timestamp,
            'location': location
        }
        
        log_memory(f"Memory checkpoint '{name}' at {location}: {current_memory:.1f}MB")
    
    def check_memory_increase(self, checkpoint_name, threshold_mb=5.0):
        """Check if memory has increased significantly since checkpoint."""
        if checkpoint_name not in self.checkpoints:
            log_memory(f"Checkpoint '{checkpoint_name}' not found", "WARNING")
            return False
            
        checkpoint = self.checkpoints[checkpoint_name]
        current_memory = memory_debugger.get_current_memory()
        memory_increase = current_memory - checkpoint['memory_mb']
        
        if memory_increase > threshold_mb:
            log_memory(f"Memory increase detected since '{checkpoint_name}': {memory_increase:.1f}MB", "WARNING")
            return True
            
        return False
    
    def profile_suspect_functions(self, app_instance):
        """Apply memory profiling to suspect functions in the app."""
        for func_name in self.suspect_functions:
            if hasattr(app_instance, func_name):
                original_func = getattr(app_instance, func_name)
                profiled_func = memory_profile(original_func)
                setattr(app_instance, func_name, profiled_func)
                log_memory(f"Applied memory profiling to {func_name}")
    
    def track_rumps_objects(self, obj, obj_type="rumps_object"):
        """Track rumps-related objects that might be leaking."""
        track_object(obj, obj_type)
    
    def monitor_history_operations(self, operation_name):
        """Monitor memory usage during history operations."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Add checkpoint before operation
                checkpoint_name = f"before_{operation_name}"
                self.add_memory_checkpoint(checkpoint_name, f"{func.__name__}")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Check for memory increase after operation
                    self.check_memory_increase(checkpoint_name, threshold_mb=2.0)
                    
                    return result
                    
                except Exception as e:
                    log_memory(f"Error in {operation_name}: {e}", "ERROR")
                    raise
            
            return wrapper
        return decorator
    
    def monitor_timer_operations(self, timer_name):
        """Monitor memory usage during timer operations."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Track timer execution frequency
                checkpoint_name = f"timer_{timer_name}_{int(time.time())}"
                self.add_memory_checkpoint(checkpoint_name, f"timer_{timer_name}")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Force garbage collection periodically for timers
                    if int(time.time()) % 300 == 0:  # Every 5 minutes
                        gc_result = memory_debugger.force_garbage_collection()
                        log_memory(f"Timer {timer_name} triggered GC: {gc_result['memory_freed_mb']:.2f}MB freed")
                    
                    return result
                    
                except Exception as e:
                    log_memory(f"Error in timer {timer_name}: {e}", "ERROR")
                    raise
            
            return wrapper
        return decorator
    
    def get_memory_summary(self):
        """Get current memory summary for dashboard display."""
        current_memory = memory_debugger.get_current_memory()
        baseline = memory_debugger.baseline_memory or current_memory
        
        return {
            'current_memory_mb': current_memory,
            'baseline_memory_mb': baseline,
            'memory_increase_mb': current_memory - baseline,
            'monitoring_active': self.integration_active,
            'snapshots_count': len(memory_debugger.memory_snapshots),
            'checkpoints_count': len(self.checkpoints)
        }

# Global instance
menu_bar_memory_integration = MenuBarMemoryIntegration()

# Convenience functions for easy integration
def activate_memory_debugging():
    """Activate memory debugging for menu bar app."""
    menu_bar_memory_integration.activate_integration()

def deactivate_memory_debugging():
    """Deactivate memory debugging for menu bar app."""
    menu_bar_memory_integration.deactivate_integration()

def add_checkpoint(name, location="unknown"):
    """Add memory checkpoint."""
    menu_bar_memory_integration.add_memory_checkpoint(name, location)

def check_increase(checkpoint_name, threshold_mb=5.0):
    """Check memory increase since checkpoint."""
    return menu_bar_memory_integration.check_memory_increase(checkpoint_name, threshold_mb)

def profile_app_functions(app_instance):
    """Profile suspect functions in app."""
    menu_bar_memory_integration.profile_suspect_functions(app_instance)

def monitor_history(operation_name):
    """Decorator for monitoring history operations."""
    return menu_bar_memory_integration.monitor_history_operations(operation_name)

def monitor_timer(timer_name):
    """Decorator for monitoring timer operations."""
    return menu_bar_memory_integration.monitor_timer_operations(timer_name)

def track_rumps_object(obj, obj_type="rumps_object"):
    """Track rumps objects."""
    menu_bar_memory_integration.track_rumps_objects(obj, obj_type)

def get_memory_summary():
    """Get memory summary."""
    return menu_bar_memory_integration.get_memory_summary()

# Memory debugging decorators for specific use cases
def debug_memory_usage(func_name=None):
    """Decorator to debug memory usage of specific functions."""
    def decorator(func):
        name = func_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            add_checkpoint(f"before_{name}", f"function_{name}")
            
            try:
                result = func(*args, **kwargs)
                check_increase(f"before_{name}", threshold_mb=1.0)
                return result
            except Exception as e:
                log_memory(f"Error in {name}: {e}", "ERROR")
                raise
        
        return wrapper
    return decorator

def debug_timer_memory(timer_name):
    """Decorator specifically for timer functions that might leak memory."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Add checkpoint with unique timestamp
            checkpoint_name = f"timer_{timer_name}_{int(time.time())}"
            add_checkpoint(checkpoint_name, f"timer_{timer_name}")
            
            try:
                result = func(*args, **kwargs)
                
                # Check for memory increase
                if check_increase(checkpoint_name, threshold_mb=0.5):
                    log_memory(f"Timer {timer_name} caused memory increase", "WARNING")
                
                return result
            except Exception as e:
                log_memory(f"Timer {timer_name} error: {e}", "ERROR")
                raise
        
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the integration
    activate_memory_debugging()
    
    print("Memory debugging integration test started.")
    print("Memory summary:", get_memory_summary())
    
    # Simulate some operations
    for i in range(10):
        add_checkpoint(f"test_checkpoint_{i}", "test_location")
        time.sleep(1)
    
    print("Final memory summary:", get_memory_summary())
    deactivate_memory_debugging()
