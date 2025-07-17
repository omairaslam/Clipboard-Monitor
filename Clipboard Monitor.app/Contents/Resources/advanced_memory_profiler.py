#!/usr/bin/env python3
"""
Advanced Memory Profiler
Detailed object tracking and garbage collection analysis for leak detection.
"""

import gc
import sys
import time
import threading
import tracemalloc
import weakref
import psutil
import os
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error


class AdvancedMemoryProfiler:
    """Advanced memory profiler with detailed object and GC analysis"""
    
    def __init__(self):
        self.profiling_active = False
        self.profile_lock = threading.Lock()
        self.data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/advanced_profile.json")
        
        # Object tracking
        self.object_snapshots = []
        self.gc_snapshots = []
        self.memory_snapshots = []
        self.leak_patterns = []
        
        # Tracemalloc setup
        self.tracemalloc_enabled = False
        try:
            if not tracemalloc.is_tracing():
                tracemalloc.start(25)  # Keep 25 frames for detailed tracebacks
            self.tracemalloc_enabled = True
            log_event("Advanced memory profiler initialized with tracemalloc", level="INFO")
        except Exception as e:
            log_error(f"Failed to initialize tracemalloc: {e}")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def take_detailed_snapshot(self):
        """Take a comprehensive memory snapshot"""
        timestamp = datetime.now().isoformat()
        
        snapshot = {
            "timestamp": timestamp,
            "process_info": self._get_process_info(),
            "object_analysis": self._analyze_objects(),
            "gc_analysis": self._analyze_garbage_collection(),
            "memory_analysis": self._analyze_memory_usage(),
            "leak_indicators": self._detect_leak_indicators()
        }
        
        if self.tracemalloc_enabled:
            snapshot["tracemalloc_analysis"] = self._analyze_tracemalloc()
        
        with self.profile_lock:
            self.memory_snapshots.append(snapshot)
            
            # Keep only recent snapshots to prevent profiler from leaking memory
            if len(self.memory_snapshots) > 100:
                self.memory_snapshots = self.memory_snapshots[-100:]
        
        return snapshot
    
    def _get_process_info(self):
        """Get detailed process information"""
        try:
            process = psutil.Process()

            # Try to get full memory info, fall back to basic if not available
            try:
                memory_info = process.memory_full_info()
                memory_data = {
                    "memory_rss_mb": memory_info.rss / 1024 / 1024,
                    "memory_vms_mb": memory_info.vms / 1024 / 1024,
                    "memory_uss_mb": memory_info.uss / 1024 / 1024,
                    "memory_pss_mb": memory_info.pss / 1024 / 1024,
                }
            except (AttributeError, psutil.AccessDenied):
                # Fall back to basic memory info
                memory_info = process.memory_info()
                memory_data = {
                    "memory_rss_mb": memory_info.rss / 1024 / 1024,
                    "memory_vms_mb": memory_info.vms / 1024 / 1024,
                    "memory_uss_mb": memory_info.rss / 1024 / 1024,  # Use RSS as fallback
                    "memory_pss_mb": memory_info.rss / 1024 / 1024,  # Use RSS as fallback
                }

            result = {
                "pid": process.pid,
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "cpu_percent": process.cpu_percent()
            }
            result.update(memory_data)

            # Add file descriptors if available
            if hasattr(process, 'num_fds'):
                try:
                    result["num_fds"] = process.num_fds()
                except (psutil.AccessDenied, AttributeError):
                    result["num_fds"] = 0
            else:
                result["num_fds"] = 0

            return result

        except Exception as e:
            log_error(f"Error getting process info: {e}")
            return {
                "pid": 0,
                "memory_rss_mb": 0,
                "memory_vms_mb": 0,
                "memory_uss_mb": 0,
                "memory_pss_mb": 0,
                "memory_percent": 0,
                "num_threads": 0,
                "num_fds": 0,
                "cpu_percent": 0
            }
    
    def _analyze_objects(self):
        """Analyze Python objects in memory"""
        try:
            # Get all objects
            all_objects = gc.get_objects()
            
            # Count objects by type
            type_counts = Counter(type(obj).__name__ for obj in all_objects)
            
            # Find large objects
            large_objects = []
            for obj in all_objects:
                try:
                    size = sys.getsizeof(obj)
                    if size > 1024 * 1024:  # > 1MB
                        large_objects.append({
                            "type": type(obj).__name__,
                            "size_mb": size / 1024 / 1024,
                            "id": id(obj)
                        })
                except (TypeError, AttributeError):
                    continue
            
            # Sort large objects by size
            large_objects.sort(key=lambda x: x["size_mb"], reverse=True)
            
            # Look for specific leak-prone objects
            leak_prone_types = ['list', 'dict', 'tuple', 'str', 'MenuItem', 'Timer']
            leak_prone_counts = {obj_type: type_counts.get(obj_type, 0) for obj_type in leak_prone_types}
            
            return {
                "total_objects": len(all_objects),
                "type_counts": dict(type_counts.most_common(20)),
                "large_objects": large_objects[:10],  # Top 10 largest
                "leak_prone_counts": leak_prone_counts
            }
        except Exception as e:
            log_error(f"Error analyzing objects: {e}")
            return {}
    
    def _analyze_garbage_collection(self):
        """Analyze garbage collection statistics"""
        try:
            # Get GC stats
            gc_stats = gc.get_stats()
            gc_counts = gc.get_count()
            gc_threshold = gc.get_threshold()
            
            # Force a collection and measure impact
            before_objects = len(gc.get_objects())
            collected = gc.collect()
            after_objects = len(gc.get_objects())
            
            # Check for uncollectable objects
            uncollectable = gc.garbage
            
            return {
                "gc_stats": gc_stats,
                "gc_counts": gc_counts,
                "gc_threshold": gc_threshold,
                "objects_before_gc": before_objects,
                "objects_after_gc": after_objects,
                "objects_collected": collected,
                "objects_freed": before_objects - after_objects,
                "uncollectable_count": len(uncollectable),
                "gc_effectiveness": (before_objects - after_objects) / before_objects if before_objects > 0 else 0
            }
        except Exception as e:
            log_error(f"Error analyzing GC: {e}")
            return {}
    
    def _analyze_memory_usage(self):
        """Analyze detailed memory usage patterns"""
        try:
            # Get memory info from different sources
            import resource
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            
            return {
                "max_rss_mb": rusage.ru_maxrss / 1024 / 1024,
                "user_time": rusage.ru_utime,
                "system_time": rusage.ru_stime,
                "page_faults": rusage.ru_majflt,
                "voluntary_context_switches": rusage.ru_nvcsw,
                "involuntary_context_switches": rusage.ru_nivcsw,
                "block_input_ops": rusage.ru_inblock,
                "block_output_ops": rusage.ru_oublock
            }
        except Exception as e:
            log_error(f"Error analyzing memory usage: {e}")
            return {}
    
    def _analyze_tracemalloc(self):
        """Analyze tracemalloc data for detailed allocation tracking"""
        if not self.tracemalloc_enabled:
            return {}
        
        try:
            # Take snapshot
            snapshot = tracemalloc.take_snapshot()
            
            # Get top allocations by line
            top_stats_by_line = snapshot.statistics('lineno')
            
            # Get top allocations by file
            top_stats_by_file = snapshot.statistics('filename')
            
            # Get current and peak memory
            current, peak = tracemalloc.get_traced_memory()
            
            # Format top allocations
            top_allocations = []
            for stat in top_stats_by_line[:10]:
                top_allocations.append({
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count,
                    "traceback": stat.traceback.format()[:3] if stat.traceback else []
                })
            
            top_files = []
            for stat in top_stats_by_file[:5]:
                top_files.append({
                    "filename": stat.traceback.format()[0] if stat.traceback else "unknown",
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                })
            
            return {
                "current_memory_mb": current / 1024 / 1024,
                "peak_memory_mb": peak / 1024 / 1024,
                "top_allocations": top_allocations,
                "top_files": top_files
            }
        except Exception as e:
            log_error(f"Error analyzing tracemalloc: {e}")
            return {}
    
    def _detect_leak_indicators(self):
        """Detect potential memory leak indicators"""
        indicators = []
        
        try:
            # Check for common leak patterns
            all_objects = gc.get_objects()
            
            # Count specific object types that commonly leak
            list_count = sum(1 for obj in all_objects if isinstance(obj, list))
            dict_count = sum(1 for obj in all_objects if isinstance(obj, dict))
            
            # Check for large collections
            large_lists = []
            large_dicts = []
            
            for obj in all_objects:
                try:
                    if isinstance(obj, list) and len(obj) > 1000:
                        large_lists.append(len(obj))
                    elif isinstance(obj, dict) and len(obj) > 1000:
                        large_dicts.append(len(obj))
                except (TypeError, AttributeError):
                    continue
            
            if large_lists:
                indicators.append({
                    "type": "large_lists",
                    "count": len(large_lists),
                    "max_size": max(large_lists),
                    "total_items": sum(large_lists)
                })
            
            if large_dicts:
                indicators.append({
                    "type": "large_dicts", 
                    "count": len(large_dicts),
                    "max_size": max(large_dicts),
                    "total_items": sum(large_dicts)
                })
            
            # Check for excessive object counts
            if list_count > 10000:
                indicators.append({
                    "type": "excessive_lists",
                    "count": list_count,
                    "threshold": 10000
                })
            
            if dict_count > 5000:
                indicators.append({
                    "type": "excessive_dicts",
                    "count": dict_count,
                    "threshold": 5000
                })
            
        except Exception as e:
            log_error(f"Error detecting leak indicators: {e}")
        
        return indicators
    
    def analyze_memory_trends(self):
        """Analyze memory trends across snapshots"""
        if len(self.memory_snapshots) < 2:
            return {"status": "insufficient_data"}
        
        with self.profile_lock:
            snapshots = self.memory_snapshots[-10:]  # Last 10 snapshots
        
        # Extract memory values
        memory_values = []
        object_counts = []
        timestamps = []
        
        for snapshot in snapshots:
            if "process_info" in snapshot and "object_analysis" in snapshot:
                memory_values.append(snapshot["process_info"].get("memory_rss_mb", 0))
                object_counts.append(snapshot["object_analysis"].get("total_objects", 0))
                timestamps.append(snapshot["timestamp"])
        
        if len(memory_values) < 2:
            return {"status": "insufficient_data"}
        
        # Calculate trends
        memory_trend = "stable"
        object_trend = "stable"
        
        # Check for consistent growth
        memory_growing = all(memory_values[i] <= memory_values[i+1] for i in range(len(memory_values)-1))
        objects_growing = all(object_counts[i] <= object_counts[i+1] for i in range(len(object_counts)-1))
        
        memory_growth = memory_values[-1] - memory_values[0]
        object_growth = object_counts[-1] - object_counts[0]
        
        if memory_growing and memory_growth > 10:  # > 10 MB growth
            memory_trend = "growing"
        if objects_growing and object_growth > 1000:  # > 1000 objects growth
            object_trend = "growing"
        
        return {
            "status": "analyzed",
            "memory_trend": memory_trend,
            "object_trend": object_trend,
            "memory_growth_mb": memory_growth,
            "object_growth": object_growth,
            "snapshots_analyzed": len(snapshots),
            "time_span": f"{timestamps[0]} to {timestamps[-1]}"
        }
    
    def get_leak_recommendations(self):
        """Get specific recommendations based on analysis"""
        recommendations = []
        
        if not self.memory_snapshots:
            return ["Take memory snapshots first to get recommendations"]
        
        latest = self.memory_snapshots[-1]
        
        # Check process memory
        if "process_info" in latest:
            memory_mb = latest["process_info"].get("memory_rss_mb", 0)
            if memory_mb > 100:
                recommendations.append(f"High memory usage ({memory_mb:.1f} MB) - investigate large objects")
        
        # Check object counts
        if "object_analysis" in latest:
            total_objects = latest["object_analysis"].get("total_objects", 0)
            if total_objects > 50000:
                recommendations.append(f"High object count ({total_objects}) - check for object accumulation")
            
            # Check for large objects
            large_objects = latest["object_analysis"].get("large_objects", [])
            if large_objects:
                recommendations.append(f"Found {len(large_objects)} large objects - review memory usage patterns")
        
        # Check GC effectiveness
        if "gc_analysis" in latest:
            effectiveness = latest["gc_analysis"].get("gc_effectiveness", 1.0)
            if effectiveness < 0.1:  # Less than 10% of objects freed
                recommendations.append("Low garbage collection effectiveness - possible reference cycles")
        
        # Check leak indicators
        if "leak_indicators" in latest:
            indicators = latest["leak_indicators"]
            if indicators:
                recommendations.append(f"Found {len(indicators)} leak indicators - review data structures")
        
        if not recommendations:
            recommendations.append("Memory usage appears normal - continue monitoring")
        
        return recommendations
    
    def start_profiling(self, interval=60):
        """Start continuous advanced profiling"""
        if self.profiling_active:
            return
        
        self.profiling_active = True
        self.profile_thread = threading.Thread(target=self._profile_loop, args=(interval,))
        self.profile_thread.daemon = True
        self.profile_thread.start()
        log_event(f"Advanced memory profiling started with {interval}s interval", level="INFO")
    
    def stop_profiling(self):
        """Stop profiling"""
        self.profiling_active = False
        log_event("Advanced memory profiling stopped", level="INFO")
    
    def _profile_loop(self, interval):
        """Main profiling loop"""
        while self.profiling_active:
            try:
                self.take_detailed_snapshot()
                time.sleep(interval)
            except Exception as e:
                log_error(f"Error in advanced profiling loop: {e}")
                time.sleep(interval)
    
    def get_summary_report(self):
        """Get a comprehensive summary report"""
        if not self.memory_snapshots:
            return {"status": "no_data", "message": "No profiling data available"}
        
        latest = self.memory_snapshots[-1]
        trends = self.analyze_memory_trends()
        recommendations = self.get_leak_recommendations()
        
        return {
            "status": "active",
            "latest_snapshot": latest,
            "trends": trends,
            "recommendations": recommendations,
            "total_snapshots": len(self.memory_snapshots),
            "profiling_active": self.profiling_active,
            "tracemalloc_enabled": self.tracemalloc_enabled
        }


# Global profiler instance
_advanced_profiler = None

def get_advanced_profiler():
    """Get or create the global advanced profiler instance"""
    global _advanced_profiler
    if _advanced_profiler is None:
        _advanced_profiler = AdvancedMemoryProfiler()
    return _advanced_profiler

def start_advanced_profiling(interval=60):
    """Start advanced memory profiling"""
    profiler = get_advanced_profiler()
    profiler.start_profiling(interval)
    return profiler

def stop_advanced_profiling():
    """Stop advanced memory profiling"""
    global _advanced_profiler
    if _advanced_profiler:
        _advanced_profiler.stop_profiling()


if __name__ == "__main__":
    # Demo the advanced profiler
    profiler = get_advanced_profiler()
    print("Taking detailed memory snapshot...")
    snapshot = profiler.take_detailed_snapshot()
    
    print(f"Process Memory: {snapshot['process_info']['memory_rss_mb']:.1f} MB")
    print(f"Total Objects: {snapshot['object_analysis']['total_objects']}")
    print(f"GC Effectiveness: {snapshot['gc_analysis']['gc_effectiveness']:.2%}")
    
    recommendations = profiler.get_leak_recommendations()
    print("\nRecommendations:")
    for rec in recommendations:
        print(f"  • {rec}")
