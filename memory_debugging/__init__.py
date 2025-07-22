"""
Memory Debugging Package for Clipboard Monitor

This package provides comprehensive memory leak detection and debugging tools
for the Clipboard Monitor menu bar application.

Components:
- memory_leak_debugger: Core debugging engine with monitoring and profiling
- menu_bar_memory_integration: Seamless integration with the menu bar app
- memory_leak_analyzer: Analysis tools and visualization
- integrate_memory_debugging: Automated integration script

Usage:
    from memory_debugging import activate_memory_debugging, memory_profile
    
    # Activate debugging
    activate_memory_debugging()
    
    # Profile a function
    @memory_profile
    def my_function():
        pass
"""

# Import main functions for easy access
try:
    from .memory_leak_debugger import (
        memory_profile,
        log_memory,
        start_memory_debugging,
        stop_memory_debugging,
        generate_memory_report
    )
    
    from .menu_bar_memory_integration import (
        activate_memory_debugging,
        deactivate_memory_debugging,
        debug_memory_usage,
        debug_timer_memory,
        monitor_history,
        add_checkpoint,
        check_increase,
        get_memory_summary
    )
    
    __all__ = [
        'memory_profile',
        'log_memory', 
        'start_memory_debugging',
        'stop_memory_debugging',
        'generate_memory_report',
        'activate_memory_debugging',
        'deactivate_memory_debugging',
        'debug_memory_usage',
        'debug_timer_memory',
        'monitor_history',
        'add_checkpoint',
        'check_increase',
        'get_memory_summary'
    ]
    
except ImportError as e:
    print(f"Warning: Some memory debugging components not available: {e}")
    __all__ = []
