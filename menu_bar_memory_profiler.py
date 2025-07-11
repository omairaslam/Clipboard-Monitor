#!/usr/bin/env python3
"""
Menu Bar Memory Profiler
Specialized memory profiling for the menu bar app to detect leaks in real-time.
"""

import os
import sys
import gc
import time
import json
import threading
import tracemalloc
import weakref
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error


class MenuBarMemoryProfiler:
    """Real-time memory profiler for menu bar app"""
    
    def __init__(self):
        self.profile_data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/menubar_profile.json")
        self.profiling_active = False
        self.profile_lock = threading.Lock()
        
        # Memory tracking
        self.memory_snapshots = deque(maxlen=50)
        self.object_refs = weakref.WeakSet()
        self.allocation_tracker = defaultdict(list)
        
        # Leak detection thresholds
        self.memory_growth_threshold = 5.0  # MB
        self.object_growth_threshold = 1000  # objects
        
        # Initialize tracemalloc
        self.tracemalloc_enabled = False
        try:
            if not tracemalloc.is_tracing():
                tracemalloc.start(10)
            self.tracemalloc_enabled = True
            log_event("MenuBar memory profiler initialized with tracemalloc", level="INFO")
        except Exception as e:
            log_error(f"Failed to initialize tracemalloc in menu bar profiler: {e}")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.profile_data_file), exist_ok=True)
    
    def start_profiling(self, interval=30):
        """Start continuous memory profiling"""
        if self.profiling_active:
            return
        
        self.profiling_active = True
        self.profile_thread = threading.Thread(target=self._profile_loop, args=(interval,))
        self.profile_thread.daemon = True
        self.profile_thread.start()
        log_event(f"Menu bar memory profiling started with {interval}s interval", level="INFO")
    
    def stop_profiling(self):
        """Stop memory profiling"""
        self.profiling_active = False
        log_event("Menu bar memory profiling stopped", level="INFO")
    
    def _profile_loop(self, interval):
        """Main profiling loop"""
        while self.profiling_active:
            try:
                self.take_memory_snapshot()
                time.sleep(interval)
            except Exception as e:
                log_error(f"Error in menu bar profiling loop: {e}")
                time.sleep(interval)
    
    def take_memory_snapshot(self):
        """Take a detailed memory snapshot"""
        try:
            import psutil
            process = psutil.Process()
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "memory_info": {
                    "rss_mb": process.memory_info().rss / 1024 / 1024,
                    "vms_mb": process.memory_info().vms / 1024 / 1024,
                    "percent": process.memory_percent()
                },
                "gc_stats": {
                    "objects": len(gc.get_objects()),
                    "count": gc.get_count(),
                    "collections": gc.get_stats()
                },
                "thread_count": threading.active_count(),
                "tracked_objects": len(self.object_refs)
            }
            
            # Add tracemalloc data if available
            if self.tracemalloc_enabled:
                try:
                    current, peak = tracemalloc.get_traced_memory()
                    snapshot["tracemalloc"] = {
                        "current_mb": current / 1024 / 1024,
                        "peak_mb": peak / 1024 / 1024
                    }
                    
                    # Get top allocations
                    snapshot_tm = tracemalloc.take_snapshot()
                    top_stats = snapshot_tm.statistics('lineno')
                    snapshot["top_allocations"] = [
                        {
                            "file": stat.traceback.format()[0] if stat.traceback.format() else "unknown",
                            "size_mb": stat.size / 1024 / 1024,
                            "count": stat.count
                        }
                        for stat in top_stats[:5]
                    ]
                except Exception as e:
                    log_error(f"Error getting tracemalloc data: {e}")
            
            with self.profile_lock:
                self.memory_snapshots.append(snapshot)
                
                # Analyze for leaks
                if len(self.memory_snapshots) >= 3:
                    leak_analysis = self._analyze_for_leaks()
                    if leak_analysis["leak_detected"]:
                        snapshot["leak_alert"] = leak_analysis
                        log_event(f"Menu bar memory leak detected: {leak_analysis['description']}", level="WARNING")
            
            # Save snapshot data
            self._save_profile_data()
            
            return snapshot
            
        except Exception as e:
            log_error(f"Error taking menu bar memory snapshot: {e}")
            return None
    
    def _analyze_for_leaks(self):
        """Analyze recent snapshots for memory leaks"""
        if len(self.memory_snapshots) < 3:
            return {"leak_detected": False}
        
        recent = list(self.memory_snapshots)[-3:]
        
        # Check memory growth
        memory_values = [s["memory_info"]["rss_mb"] for s in recent]
        memory_growth = memory_values[-1] - memory_values[0]
        
        # Check object count growth
        object_values = [s["gc_stats"]["objects"] for s in recent]
        object_growth = object_values[-1] - object_values[0]
        
        leak_detected = False
        description = ""
        
        if memory_growth > self.memory_growth_threshold:
            leak_detected = True
            description += f"Memory grew by {memory_growth:.2f} MB. "
        
        if object_growth > self.object_growth_threshold:
            leak_detected = True
            description += f"Object count grew by {object_growth}. "
        
        # Check for consistent growth
        memory_growing = all(memory_values[i] <= memory_values[i+1] for i in range(len(memory_values)-1))
        objects_growing = all(object_values[i] <= object_values[i+1] for i in range(len(object_values)-1))
        
        if memory_growing and objects_growing:
            leak_detected = True
            description += "Consistent memory and object growth detected."
        
        return {
            "leak_detected": leak_detected,
            "description": description.strip(),
            "memory_growth_mb": memory_growth,
            "object_growth": object_growth,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _save_profile_data(self):
        """Save profiling data to file"""
        try:
            with self.profile_lock:
                data = {
                    "snapshots": list(self.memory_snapshots),
                    "profiling_active": self.profiling_active,
                    "last_updated": datetime.now().isoformat()
                }
            
            with open(self.profile_data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            log_error(f"Error saving menu bar profile data: {e}")
    
    def track_object(self, obj):
        """Track an object for leak detection"""
        try:
            self.object_refs.add(obj)
        except TypeError:
            # Object not weakly referenceable
            pass
    
    def get_current_status(self):
        """Get current profiling status"""
        if not self.memory_snapshots:
            return {"status": "no_data"}
        
        latest = self.memory_snapshots[-1]
        
        # Calculate trends if we have enough data
        trends = {}
        if len(self.memory_snapshots) >= 2:
            previous = self.memory_snapshots[-2]
            trends = {
                "memory_change_mb": latest["memory_info"]["rss_mb"] - previous["memory_info"]["rss_mb"],
                "object_change": latest["gc_stats"]["objects"] - previous["gc_stats"]["objects"],
                "thread_change": latest["thread_count"] - previous["thread_count"]
            }
        
        return {
            "status": "active" if self.profiling_active else "inactive",
            "latest_snapshot": latest,
            "trends": trends,
            "total_snapshots": len(self.memory_snapshots),
            "tracemalloc_enabled": self.tracemalloc_enabled
        }
    
    def force_gc_and_analyze(self):
        """Force garbage collection and analyze the impact"""
        try:
            # Take snapshot before GC
            before_snapshot = self.take_memory_snapshot()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Take snapshot after GC
            time.sleep(1)  # Brief pause
            after_snapshot = self.take_memory_snapshot()
            
            if before_snapshot and after_snapshot:
                memory_freed = before_snapshot["memory_info"]["rss_mb"] - after_snapshot["memory_info"]["rss_mb"]
                objects_freed = before_snapshot["gc_stats"]["objects"] - after_snapshot["gc_stats"]["objects"]
                
                result = {
                    "memory_freed_mb": memory_freed,
                    "objects_freed": objects_freed,
                    "collected_objects": collected,
                    "before_snapshot": before_snapshot,
                    "after_snapshot": after_snapshot,
                    "timestamp": datetime.now().isoformat()
                }
                
                log_event(f"Menu bar GC analysis: freed {memory_freed:.2f} MB, {objects_freed} objects", level="INFO")
                return result
            
        except Exception as e:
            log_error(f"Error in menu bar GC analysis: {e}")
            return {"error": str(e)}


# Global profiler instance
_menu_bar_profiler = None

def get_menu_bar_profiler():
    """Get or create the global menu bar profiler instance"""
    global _menu_bar_profiler
    if _menu_bar_profiler is None:
        _menu_bar_profiler = MenuBarMemoryProfiler()
    return _menu_bar_profiler

def start_menu_bar_profiling(interval=30):
    """Start menu bar memory profiling"""
    profiler = get_menu_bar_profiler()
    profiler.start_profiling(interval)
    return profiler

def stop_menu_bar_profiling():
    """Stop menu bar memory profiling"""
    global _menu_bar_profiler
    if _menu_bar_profiler:
        _menu_bar_profiler.stop_profiling()
