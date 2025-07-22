#!/usr/bin/env python3
"""
Memory Leak Debugger for Clipboard Monitor Menu Bar App

This module provides comprehensive memory leak detection and debugging tools:
1. Memory profiling by function/module
2. Object tracking and lifecycle monitoring  
3. Memory usage checkpoints and trend analysis
4. Automated leak detection and reporting

Usage:
    from memory_leak_debugger import MemoryLeakDebugger
    debugger = MemoryLeakDebugger()
    debugger.start_monitoring()
"""

import psutil
import gc
import sys
import os
import time
import threading
import traceback
import weakref
from collections import defaultdict, deque
from datetime import datetime
import json
import functools

class MemoryLeakDebugger:
    def __init__(self, process_name="menu_bar_app", log_file="memory_leak_debug.log"):
        self.process_name = process_name
        self.log_file = log_file
        self.start_time = time.time()
        self.baseline_memory = None
        
        # Memory tracking data structures
        self.memory_snapshots = deque(maxlen=1000)  # Last 1000 snapshots
        self.function_memory_usage = defaultdict(list)
        self.object_counts = defaultdict(int)
        self.object_registry = weakref.WeakSet()
        
        # Configuration
        self.snapshot_interval = 30  # seconds
        self.leak_threshold = 50  # MB increase to trigger alert
        self.monitoring_active = False
        
        # Thread for continuous monitoring
        self.monitor_thread = None
        
        self.log("Memory Leak Debugger initialized")
    
    def log(self, message, level="INFO"):
        """Log message with timestamp and memory info."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_memory = self.get_current_memory()
        
        log_entry = f"[{timestamp}] [{level}] Memory: {current_memory:.1f}MB | {message}"
        
        # Write to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")
        
        # Also print to console if debug mode
        if os.getenv('DEBUG_MEMORY', '').lower() == 'true':
            print(log_entry)
    
    def get_current_memory(self):
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def take_memory_snapshot(self):
        """Take a comprehensive memory snapshot."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            snapshot = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'gc_objects': len(gc.get_objects()),
                'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else [],
                'object_counts': dict(self.object_counts),
                'thread_count': threading.active_count()
            }
            
            self.memory_snapshots.append(snapshot)
            
            # Set baseline if first snapshot
            if self.baseline_memory is None:
                self.baseline_memory = snapshot['rss_mb']
                self.log(f"Baseline memory set: {self.baseline_memory:.1f}MB")
            
            # Check for memory leak
            memory_increase = snapshot['rss_mb'] - self.baseline_memory
            if memory_increase > self.leak_threshold:
                self.log(f"MEMORY LEAK DETECTED! Increase: {memory_increase:.1f}MB", "WARNING")
                self.analyze_memory_leak()
            
            return snapshot
            
        except Exception as e:
            self.log(f"Error taking memory snapshot: {e}", "ERROR")
            return None
    
    def analyze_memory_leak(self):
        """Analyze recent memory snapshots to identify leak patterns."""
        if len(self.memory_snapshots) < 10:
            return
        
        recent_snapshots = list(self.memory_snapshots)[-10:]
        
        # Calculate memory growth rate
        time_span = recent_snapshots[-1]['timestamp'] - recent_snapshots[0]['timestamp']
        memory_growth = recent_snapshots[-1]['rss_mb'] - recent_snapshots[0]['rss_mb']
        growth_rate = memory_growth / (time_span / 3600)  # MB per hour
        
        self.log(f"Memory growth analysis: {memory_growth:.1f}MB over {time_span/60:.1f} minutes")
        self.log(f"Growth rate: {growth_rate:.2f}MB/hour")
        
        # Analyze object count changes
        if len(recent_snapshots) >= 2:
            old_objects = recent_snapshots[0]['gc_objects']
            new_objects = recent_snapshots[-1]['gc_objects']
            object_growth = new_objects - old_objects
            
            self.log(f"Object count growth: {object_growth} objects")
            
            # Check for specific object type increases
            old_counts = recent_snapshots[0].get('object_counts', {})
            new_counts = recent_snapshots[-1].get('object_counts', {})
            
            for obj_type, new_count in new_counts.items():
                old_count = old_counts.get(obj_type, 0)
                if new_count > old_count + 100:  # Significant increase
                    self.log(f"Object type '{obj_type}' increased by {new_count - old_count}", "WARNING")
    
    def memory_profiler(self, func):
        """Decorator to profile memory usage of functions."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Memory before function call
            memory_before = self.get_current_memory()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Memory after function call
                memory_after = self.get_current_memory()
                execution_time = time.time() - start_time
                memory_delta = memory_after - memory_before
                
                # Record function memory usage
                func_name = f"{func.__module__}.{func.__name__}"
                self.function_memory_usage[func_name].append({
                    'timestamp': time.time(),
                    'memory_delta': memory_delta,
                    'execution_time': execution_time,
                    'memory_before': memory_before,
                    'memory_after': memory_after
                })
                
                # Log significant memory increases
                if abs(memory_delta) > 1.0:  # More than 1MB change
                    self.log(f"Function {func_name}: {memory_delta:+.2f}MB change in {execution_time:.3f}s")
                
                return result
                
            except Exception as e:
                memory_after = self.get_current_memory()
                memory_delta = memory_after - memory_before
                self.log(f"Function {func_name} failed: {e}, Memory delta: {memory_delta:+.2f}MB", "ERROR")
                raise
        
        return wrapper
    
    def track_object_creation(self, obj, obj_type=None):
        """Track object creation for leak detection."""
        if obj_type is None:
            obj_type = type(obj).__name__
        
        self.object_counts[obj_type] += 1
        self.object_registry.add(obj)
        
        # Log significant object creation
        if self.object_counts[obj_type] % 100 == 0:
            self.log(f"Object type '{obj_type}' count reached {self.object_counts[obj_type]}")
    
    def start_monitoring(self):
        """Start continuous memory monitoring."""
        if self.monitoring_active:
            self.log("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.log("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous memory monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.log("Memory monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self.take_memory_snapshot()
                time.sleep(self.snapshot_interval)
            except Exception as e:
                self.log(f"Error in monitoring loop: {e}", "ERROR")
                time.sleep(self.snapshot_interval)
    
    def generate_report(self):
        """Generate comprehensive memory leak report."""
        if not self.memory_snapshots:
            return "No memory snapshots available"
        
        report = []
        report.append("=" * 60)
        report.append("MEMORY LEAK ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Basic statistics
        first_snapshot = self.memory_snapshots[0]
        last_snapshot = self.memory_snapshots[-1]
        
        total_time = (last_snapshot['timestamp'] - first_snapshot['timestamp']) / 3600
        memory_increase = last_snapshot['rss_mb'] - first_snapshot['rss_mb']
        
        report.append(f"Monitoring Duration: {total_time:.2f} hours")
        report.append(f"Memory Increase: {memory_increase:.1f}MB")
        report.append(f"Growth Rate: {memory_increase/total_time:.2f}MB/hour")
        report.append("")
        
        # Top memory-consuming functions
        report.append("TOP MEMORY-CONSUMING FUNCTIONS:")
        report.append("-" * 40)
        
        func_totals = {}
        for func_name, usages in self.function_memory_usage.items():
            total_delta = sum(usage['memory_delta'] for usage in usages)
            func_totals[func_name] = total_delta
        
        for func_name, total_delta in sorted(func_totals.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"{func_name}: {total_delta:+.2f}MB")
        
        report.append("")
        
        # Object count analysis
        report.append("OBJECT COUNT ANALYSIS:")
        report.append("-" * 40)
        
        if len(self.memory_snapshots) >= 2:
            first_objects = first_snapshot.get('object_counts', {})
            last_objects = last_snapshot.get('object_counts', {})
            
            for obj_type in set(list(first_objects.keys()) + list(last_objects.keys())):
                first_count = first_objects.get(obj_type, 0)
                last_count = last_objects.get(obj_type, 0)
                increase = last_count - first_count
                
                if increase > 0:
                    report.append(f"{obj_type}: +{increase} objects")
        
        return "\n".join(report)
    
    def force_garbage_collection(self):
        """Force garbage collection and log results."""
        before_memory = self.get_current_memory()
        before_objects = len(gc.get_objects())
        
        # Force garbage collection
        collected = gc.collect()
        
        after_memory = self.get_current_memory()
        after_objects = len(gc.get_objects())
        
        memory_freed = before_memory - after_memory
        objects_freed = before_objects - after_objects
        
        self.log(f"Garbage collection: {collected} cycles, {memory_freed:.2f}MB freed, {objects_freed} objects freed")
        
        return {
            'cycles_collected': collected,
            'memory_freed_mb': memory_freed,
            'objects_freed': objects_freed
        }

# Global instance for easy access
memory_debugger = MemoryLeakDebugger()

# Convenience functions
def start_memory_debugging():
    """Start memory debugging."""
    memory_debugger.start_monitoring()

def stop_memory_debugging():
    """Stop memory debugging."""
    memory_debugger.stop_monitoring()

def memory_profile(func):
    """Decorator for memory profiling."""
    return memory_debugger.memory_profiler(func)

def track_object(obj, obj_type=None):
    """Track object creation."""
    memory_debugger.track_object_creation(obj, obj_type)

def log_memory(message, level="INFO"):
    """Log message with memory info."""
    memory_debugger.log(message, level)

def generate_memory_report():
    """Generate memory leak report."""
    return memory_debugger.generate_report()

if __name__ == "__main__":
    # Test the memory debugger
    debugger = MemoryLeakDebugger()
    debugger.start_monitoring()
    
    print("Memory debugging started. Press Ctrl+C to stop and generate report.")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        debugger.stop_monitoring()
        print("\n" + debugger.generate_report())
