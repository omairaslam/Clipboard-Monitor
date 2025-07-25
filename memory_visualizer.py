#!/usr/bin/env python3
"""
Enhanced Memory Visualizer for Clipboard Monitor
Provides real-time and historical memory usage visualization with advanced leak detection.
"""

import os
import sys
import json
import time
import psutil
import threading
import webbrowser
import gc
import tracemalloc
import weakref
import resource
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict, deque
import subprocess
import fcntl
import tempfile
import atexit

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, get_app_paths, log_event, log_error


class MemoryLeakDetector:
    """Advanced memory leak detection and analysis"""

    def __init__(self):
        self.baseline_memory = {}
        self.memory_snapshots = deque(maxlen=100)  # Keep last 100 snapshots
        self.object_counts = defaultdict(int)
        self.leak_alerts = []
        self.growth_threshold = 10.0  # MB growth threshold for leak alert
        self.consecutive_growth_limit = 5  # Consecutive growth periods before alert
        self.tracemalloc_enabled = False

        # Initialize tracemalloc for detailed memory tracking
        try:
            tracemalloc.start(10)  # Keep 10 frames in traceback
            self.tracemalloc_enabled = True
            log_event("Tracemalloc enabled for detailed memory tracking", level="INFO")
        except Exception as e:
            log_error(f"Failed to enable tracemalloc: {e}")

    def take_memory_snapshot(self, process_info):
        """Take a detailed memory snapshot"""
        timestamp = time.time()
        snapshot = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "process_info": process_info,
            "gc_stats": self._get_gc_stats(),
            "object_counts": self._get_object_counts(),
            "resource_usage": self._get_resource_usage(),
        }

        # Add tracemalloc data if available
        if self.tracemalloc_enabled:
            try:
                snapshot["tracemalloc"] = self._get_tracemalloc_stats()
            except Exception as e:
                log_error(f"Failed to get tracemalloc stats: {e}")

        self.memory_snapshots.append(snapshot)
        return snapshot

    def _get_gc_stats(self):
        """Get garbage collection statistics"""
        try:
            return {
                "collections": gc.get_stats(),
                "count": gc.get_count(),
                "threshold": gc.get_threshold(),
                "objects": len(gc.get_objects())
            }
        except Exception as e:
            log_error(f"Failed to get GC stats: {e}")
            return {}

    def _get_object_counts(self):
        """Get count of objects by type"""
        try:
            objects = gc.get_objects()
            counts = defaultdict(int)
            for obj in objects:
                counts[type(obj).__name__] += 1
            return dict(counts)
        except Exception as e:
            log_error(f"Failed to get object counts: {e}")
            return {}

    def _get_resource_usage(self):
        """Get system resource usage"""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                "max_rss": usage.ru_maxrss,  # Maximum resident set size
                "user_time": usage.ru_utime,
                "system_time": usage.ru_stime,
                "page_faults": usage.ru_majflt,
                "voluntary_context_switches": usage.ru_nvcsw,
                "involuntary_context_switches": usage.ru_nivcsw
            }
        except Exception as e:
            log_error(f"Failed to get resource usage: {e}")
            return {}

    def _get_tracemalloc_stats(self):
        """Get tracemalloc memory statistics"""
        if not self.tracemalloc_enabled:
            return {}

        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')

            # Get top 10 memory allocations
            top_allocations = []
            for stat in top_stats[:10]:
                top_allocations.append({
                    "filename": stat.traceback.format()[0] if stat.traceback.format() else "unknown",
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                })

            return {
                "current_size_mb": tracemalloc.get_traced_memory()[0] / 1024 / 1024,
                "peak_size_mb": tracemalloc.get_traced_memory()[1] / 1024 / 1024,
                "top_allocations": top_allocations
            }
        except Exception as e:
            log_error(f"Failed to get tracemalloc stats: {e}")
            return {}

    def analyze_memory_trends(self):
        """Analyze memory trends and detect potential leaks"""
        if len(self.memory_snapshots) < 3:
            return {"status": "insufficient_data", "message": "Need at least 3 snapshots for analysis"}

        recent_snapshots = list(self.memory_snapshots)[-10:]  # Analyze last 10 snapshots
        analysis = {
            "leak_detected": False,
            "growth_rate_mb_per_hour": 0,
            "consecutive_growth_periods": 0,
            "memory_trend": "stable",
            "alerts": [],
            "recommendations": []
        }

        # Calculate memory growth rate
        memory_values = []
        timestamps = []

        for snapshot in recent_snapshots:
            if "process_info" in snapshot:
                for process_type, info in snapshot["process_info"].items():
                    if info and "memory_mb" in info:
                        memory_values.append(info["memory_mb"])
                        timestamps.append(snapshot["timestamp"])
                        break

        if len(memory_values) >= 2:
            # Calculate growth rate
            time_diff_hours = (timestamps[-1] - timestamps[0]) / 3600
            memory_diff = memory_values[-1] - memory_values[0]

            if time_diff_hours > 0:
                analysis["growth_rate_mb_per_hour"] = memory_diff / time_diff_hours

            # Check for consistent growth
            consecutive_growth = 0
            for i in range(1, len(memory_values)):
                if memory_values[i] > memory_values[i-1]:
                    consecutive_growth += 1
                else:
                    consecutive_growth = 0

            analysis["consecutive_growth_periods"] = consecutive_growth

            # Determine trend
            if analysis["growth_rate_mb_per_hour"] > self.growth_threshold:
                analysis["memory_trend"] = "growing_rapidly"
                analysis["leak_detected"] = True
                analysis["alerts"].append(f"Rapid memory growth detected: {analysis['growth_rate_mb_per_hour']:.2f} MB/hour")
            elif consecutive_growth >= self.consecutive_growth_limit:
                analysis["memory_trend"] = "growing_consistently"
                analysis["leak_detected"] = True
                analysis["alerts"].append(f"Consistent memory growth over {consecutive_growth} periods")
            elif analysis["growth_rate_mb_per_hour"] > 1:
                analysis["memory_trend"] = "growing_slowly"
                analysis["alerts"].append("Slow memory growth detected")

        # Add recommendations based on analysis
        if analysis["leak_detected"]:
            analysis["recommendations"].extend([
                "Enable detailed object tracking",
                "Check for unbounded data structures",
                "Review timer and event handler cleanup",
                "Monitor garbage collection effectiveness"
            ])

        return analysis


class MemoryMonitor:
    """Enhanced memory monitor with leak detection for Clipboard Monitor processes"""

    def __init__(self):
        self.data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/memory_data.json")
        self.leak_data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/leak_analysis.json")
        self.monitoring = False
        self.monitor_thread = None
        self.data_lock = threading.Lock()
        self.max_data_points = 1000  # Keep last 1000 data points

        # Initialize leak detector
        self.leak_detector = MemoryLeakDetector()

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        # Enhanced data structure with leak detection
        self.memory_data = {
            "main_service": [],
            "menu_bar": [],
            "system": [],
            "leak_analysis": [],
            "object_tracking": [],
            "last_updated": None,
            "leak_alerts": []
        }

        # Load existing data
        self.load_data()

    def load_data(self):
        """Load existing memory data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure all required keys exist
                    self.memory_data.update(loaded_data)
                log_event("Memory data loaded successfully", level="INFO")
            else:
                log_event("No existing memory data found, starting fresh", level="INFO")
        except Exception as e:
            log_error(f"Failed to load memory data: {e}")
            # Keep default structure on error
            pass

    def save_data(self):
        """Save memory data to file"""
        try:
            with self.data_lock:
                with open(self.data_file, 'w') as f:
                    json.dump(self.memory_data, f, indent=2)
        except Exception as e:
            log_error(f"Failed to save memory data: {e}")

    def find_processes(self):
        """Find Clipboard Monitor processes"""
        processes = {
            "main_service": None,
            "menu_bar": None
        }

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline)

                        # Look for main service (main.py)
                        if 'main.py' in cmdline_str and 'clipboard' in cmdline_str.lower():
                            processes["main_service"] = proc

                        # Look for menu bar app (menu_bar_app.py)
                        elif 'menu_bar_app.py' in cmdline_str:
                            processes["menu_bar"] = proc

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            log_error(f"Error finding processes: {e}")

        return processes

    def get_memory_info(self, process):
        """Get detailed memory information for a process"""
        try:
            if process is None:
                return None

            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            return {
                "rss": memory_info.rss,  # Resident Set Size (physical memory)
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": memory_percent,
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "memory_mb": round(memory_info.rss / 1024 / 1024, 2)  # Alias for compatibility
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def get_system_memory(self):
        """Get system-wide memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "used_gb": round(memory.used / 1024 / 1024 / 1024, 2)
            }
        except Exception as e:
            log_error(f"Error getting system memory: {e}")
            return None

    def collect_data_point(self):
        """Collect a single data point for all processes with enhanced leak detection"""
        timestamp = datetime.now().isoformat()
        processes = self.find_processes()

        # Collect data for each process
        main_memory = self.get_memory_info(processes["main_service"])
        menu_memory = self.get_memory_info(processes["menu_bar"])
        system_memory = self.get_system_memory()

        # Enhanced process information for leak detection
        process_info = {}
        if main_memory:
            process_info["main_service"] = main_memory
        if menu_memory:
            process_info["menu_bar"] = menu_memory

        # Take detailed memory snapshot for leak analysis
        leak_snapshot = self.leak_detector.take_memory_snapshot(process_info)

        with self.data_lock:
            # Add data points
            if main_memory:
                self.memory_data["main_service"].append({
                    "timestamp": timestamp,
                    **main_memory
                })

            if menu_memory:
                self.memory_data["menu_bar"].append({
                    "timestamp": timestamp,
                    **menu_memory
                })

            if system_memory:
                self.memory_data["system"].append({
                    "timestamp": timestamp,
                    **system_memory
                })

            # Add leak analysis data
            self.memory_data["leak_analysis"].append({
                "timestamp": timestamp,
                "snapshot": leak_snapshot
            })

            # Perform leak analysis every 10 data points
            if len(self.memory_data["leak_analysis"]) % 10 == 0:
                analysis = self.leak_detector.analyze_memory_trends()
                if analysis["leak_detected"]:
                    alert = {
                        "timestamp": timestamp,
                        "severity": "high" if analysis["memory_trend"] == "growing_rapidly" else "medium",
                        "analysis": analysis
                    }
                    self.memory_data["leak_alerts"].append(alert)
                    log_event(f"Memory leak detected: {analysis['alerts']}", level="WARNING")

            # Trim data to max points
            for key in ["main_service", "menu_bar", "system", "leak_analysis"]:
                if len(self.memory_data[key]) > self.max_data_points:
                    self.memory_data[key] = self.memory_data[key][-self.max_data_points:]

            # Keep only recent leak alerts (last 100)
            if len(self.memory_data["leak_alerts"]) > 100:
                self.memory_data["leak_alerts"] = self.memory_data["leak_alerts"][-100:]

            self.memory_data["last_updated"] = timestamp

        # Save data periodically
        self.save_data()

        return {
            "main_service": main_memory,
            "menu_bar": menu_memory,
            "system": system_memory,
            "leak_analysis": analysis if 'analysis' in locals() else None,
            "timestamp": timestamp
        }

    def start_monitoring(self, interval=30):
        """Start continuous memory monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        log_event(f"Memory monitoring started with {interval}s interval", level="INFO")

    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        log_event("Memory monitoring stopped", level="INFO")

    def _monitor_loop(self, interval):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self.collect_data_point()
                time.sleep(interval)
            except Exception as e:
                log_error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

    def get_current_status(self):
        """Get current memory status for all processes"""
        return self.collect_data_point()

    def get_leak_analysis(self):
        """Get current leak analysis and recommendations"""
        analysis = self.leak_detector.analyze_memory_trends()

        # Add recent alerts
        with self.data_lock:
            recent_alerts = self.memory_data.get("leak_alerts", [])[-10:] if self.memory_data.get("leak_alerts") else []

        return {
            "current_analysis": analysis,
            "recent_alerts": recent_alerts,
            "total_snapshots": len(self.leak_detector.memory_snapshots),
            "tracemalloc_enabled": self.leak_detector.tracemalloc_enabled
        }

    def get_object_tracking_data(self):
        """Get detailed object tracking information"""
        if not self.leak_detector.memory_snapshots:
            return {"error": "No snapshots available"}

        latest_snapshot = self.leak_detector.memory_snapshots[-1]

        # Compare with baseline if available
        comparison = {}
        if len(self.leak_detector.memory_snapshots) > 1:
            baseline = self.leak_detector.memory_snapshots[0]
            if "object_counts" in latest_snapshot and "object_counts" in baseline:
                for obj_type, current_count in latest_snapshot["object_counts"].items():
                    baseline_count = baseline["object_counts"].get(obj_type, 0)
                    if current_count > baseline_count:
                        comparison[obj_type] = {
                            "current": current_count,
                            "baseline": baseline_count,
                            "growth": current_count - baseline_count
                        }

        return {
            "latest_snapshot": latest_snapshot,
            "object_growth": comparison,
            "gc_stats": latest_snapshot.get("gc_stats", {}),
            "tracemalloc": latest_snapshot.get("tracemalloc", {})
        }

    def force_garbage_collection(self):
        """Force garbage collection and return statistics"""
        try:
            # Get stats before GC
            before_objects = len(gc.get_objects())
            before_count = gc.get_count()

            # Force collection
            collected = gc.collect()

            # Get stats after GC
            after_objects = len(gc.get_objects())
            after_count = gc.get_count()

            result = {
                "objects_before": before_objects,
                "objects_after": after_objects,
                "objects_freed": before_objects - after_objects,
                "collected_objects": collected,
                "count_before": before_count,
                "count_after": after_count,
                "timestamp": datetime.now().isoformat()
            }

            log_event(f"Forced GC: freed {result['objects_freed']} objects, collected {collected}", level="INFO")
            return result

        except Exception as e:
            log_error(f"Error during forced garbage collection: {e}")
            return {"error": str(e)}

    def get_historical_data(self, hours=24):
        """Get historical data for the specified number of hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()

        filtered_data = {}
        with self.data_lock:
            for key in ["main_service", "menu_bar", "system"]:
                filtered_data[key] = [
                    point for point in self.memory_data[key]
                    if point["timestamp"] >= cutoff_str
                ]

        return filtered_data

    def analyze_trends(self, hours=24):
        """Analyze memory trends to detect potential leaks"""
        data = self.get_historical_data(hours)
        analysis = {}

        for process_name, points in data.items():
            if len(points) < 2:
                analysis[process_name] = {"status": "insufficient_data"}
                continue

            # Calculate memory growth rate
            first_point = points[0]
            last_point = points[-1]

            if "rss_mb" in first_point and "rss_mb" in last_point:
                memory_growth = last_point["rss_mb"] - first_point["rss_mb"]
                time_diff = (datetime.fromisoformat(last_point["timestamp"]) -
                           datetime.fromisoformat(first_point["timestamp"])).total_seconds() / 3600

                growth_rate = memory_growth / time_diff if time_diff > 0 else 0

                # Calculate average memory usage
                avg_memory = sum(point["rss_mb"] for point in points) / len(points)

                # Determine status
                status = "normal"
                if growth_rate > 5:  # More than 5MB/hour growth
                    status = "potential_leak"
                elif growth_rate > 2:  # More than 2MB/hour growth
                    status = "monitoring_needed"

                analysis[process_name] = {
                    "status": status,
                    "growth_rate_mb_per_hour": round(growth_rate, 2),
                    "total_growth_mb": round(memory_growth, 2),
                    "average_memory_mb": round(avg_memory, 2),
                    "current_memory_mb": last_point["rss_mb"],
                    "data_points": len(points)
                }
            else:
                analysis[process_name] = {"status": "no_memory_data"}

        return analysis

class MemoryVisualizerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for memory visualizer web interface"""

    def __init__(self, *args, memory_monitor=None, **kwargs):
        self.memory_monitor = memory_monitor
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        if path == '/':
            self.serve_main_page()
        elif path == '/api/current':
            self.serve_current_data()
        elif path == '/api/historical':
            hours = int(query_params.get('hours', [24])[0])
            self.serve_historical_data(hours)
        elif path == '/api/analysis':
            hours = int(query_params.get('hours', [24])[0])
            self.serve_analysis_data(hours)
        elif path == '/api/start_monitoring':
            interval = int(query_params.get('interval', [30])[0])
            self.start_monitoring(interval)
        elif path == '/api/stop_monitoring':
            self.stop_monitoring()
        else:
            self.send_error(404)

    def serve_main_page(self):
        """Serve the main HTML page"""
        html_content = self.get_html_content()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

    def serve_current_data(self):
        """Serve current memory data as JSON"""
        try:
            data = self.memory_monitor.get_current_status()
            self.send_json_response(data)
        except Exception as e:
            self.send_error(500, f"Error getting current data: {e}")

    def serve_historical_data(self, hours):
        """Serve historical memory data as JSON"""
        try:
            data = self.memory_monitor.get_historical_data(hours)
            self.send_json_response(data)
        except Exception as e:
            self.send_error(500, f"Error getting historical data: {e}")

    def serve_analysis_data(self, hours):
        """Serve memory analysis data as JSON"""
        try:
            data = self.memory_monitor.analyze_trends(hours)
            self.send_json_response(data)
        except Exception as e:
            self.send_error(500, f"Error getting analysis data: {e}")

    def start_monitoring(self, interval):
        """Start memory monitoring"""
        try:
            self.memory_monitor.start_monitoring(interval)
            self.send_json_response({"status": "started", "interval": interval})
        except Exception as e:
            self.send_error(500, f"Error starting monitoring: {e}")

    def stop_monitoring(self):
        """Stop memory monitoring"""
        try:
            self.memory_monitor.stop_monitoring()
            self.send_json_response({"status": "stopped"})
        except Exception as e:
            self.send_error(500, f"Error stopping monitoring: {e}")

    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format, *args):
        """Override to suppress default logging"""
        pass

    def get_html_content(self):
        """Generate the HTML content for the memory visualizer"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Clipboard Monitor - Memory Visualizer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .controls {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .control-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn.danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        }

        select, input {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
        }

        .status-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .status-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .status-card:hover {
            transform: translateY(-5px);
        }

        .status-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-weight: 600;
            color: #666;
        }

        .metric-value {
            font-weight: 700;
            color: #333;
        }

        .charts-container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
        }

        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .chart-card h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.4rem;
            text-align: center;
        }

        .chart-container {
            position: relative;
            height: 400px;
        }

        .analysis-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .analysis-item {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }

        .analysis-item.warning {
            background: #fff3cd;
            border-left-color: #ffc107;
        }

        .analysis-item.danger {
            background: #f8d7da;
            border-left-color: #dc3545;
        }

        .analysis-item.success {
            background: #d4edda;
            border-left-color: #28a745;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }

        @media (max-width: 768px) {
            .controls {
                flex-direction: column;
                align-items: stretch;
            }

            .control-group {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Memory Visualizer</h1>
            <p>Real-time and historical memory monitoring for Clipboard Monitor</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label for="timeRange">Time Range:</label>
                <select id="timeRange">
                    <option value="1">Last 1 Hour</option>
                    <option value="6">Last 6 Hours</option>
                    <option value="24" selected>Last 24 Hours</option>
                    <option value="72">Last 3 Days</option>
                    <option value="168">Last Week</option>
                </select>
            </div>

            <div class="control-group">
                <label for="monitorInterval">Monitor Interval:</label>
                <select id="monitorInterval">
                    <option value="10">10 seconds</option>
                    <option value="30" selected>30 seconds</option>
                    <option value="60">1 minute</option>
                    <option value="300">5 minutes</option>
                </select>
            </div>

            <div class="control-group">
                <button id="startMonitoring" class="btn">Start Monitoring</button>
                <button id="stopMonitoring" class="btn danger">Stop Monitoring</button>
                <button id="refreshData" class="btn">Refresh Data</button>
            </div>
        </div>

        <div id="statusCards" class="status-cards">
            <div class="loading">Loading current status...</div>
        </div>

        <div class="charts-container">
            <div class="chart-card">
                <h3>📈 Memory Usage Over Time</h3>
                <div class="chart-container">
                    <canvas id="memoryChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3>📊 Memory Usage Comparison</h3>
                <div class="chart-container">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>
        </div>

        <div class="analysis-card">
            <h3>🔍 Memory Leak Analysis</h3>
            <div id="analysisResults">
                <div class="loading">Analyzing memory trends...</div>
            </div>
        </div>
    </div>

    <script>
        let memoryChart = null;
        let comparisonChart = null;
        let autoRefreshInterval = null;

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
            loadCurrentStatus();
            loadHistoricalData();
            loadAnalysis();

            // Set up event listeners
            document.getElementById('timeRange').addEventListener('change', function() {
                loadHistoricalData();
                loadAnalysis();
            });

            document.getElementById('startMonitoring').addEventListener('click', startMonitoring);
            document.getElementById('stopMonitoring').addEventListener('click', stopMonitoring);
            document.getElementById('refreshData').addEventListener('click', refreshAllData);

            // Auto-refresh every 30 seconds
            autoRefreshInterval = setInterval(refreshAllData, 30000);
        });

        function initializeCharts() {
            // Memory usage over time chart
            const memoryCtx = document.getElementById('memoryChart').getContext('2d');
            memoryChart = new Chart(memoryCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Main Service (MB)',
                            data: [],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Menu Bar App (MB)',
                            data: [],
                            borderColor: '#764ba2',
                            backgroundColor: 'rgba(118, 75, 162, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Memory Usage (MB)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    }
                }
            });

            // Comparison chart
            const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
            comparisonChart = new Chart(comparisonCtx, {
                type: 'bar',
                data: {
                    labels: ['Main Service', 'Menu Bar App'],
                    datasets: [
                        {
                            label: 'Current Memory (MB)',
                            data: [0, 0],
                            backgroundColor: ['rgba(102, 126, 234, 0.8)', 'rgba(118, 75, 162, 0.8)'],
                            borderColor: ['#667eea', '#764ba2'],
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Memory Usage (MB)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        async function loadCurrentStatus() {
            try {
                const response = await fetch('/api/current');
                const data = await response.json();
                updateStatusCards(data);
                updateComparisonChart(data);
            } catch (error) {
                console.error('Error loading current status:', error);
                showError('Failed to load current status');
            }
        }

        async function loadHistoricalData() {
            try {
                const hours = document.getElementById('timeRange').value;
                const response = await fetch(`/api/historical?hours=${hours}`);
                const data = await response.json();
                updateMemoryChart(data);
            } catch (error) {
                console.error('Error loading historical data:', error);
                showError('Failed to load historical data');
            }
        }

        async function loadAnalysis() {
            try {
                const hours = document.getElementById('timeRange').value;
                const response = await fetch(`/api/analysis?hours=${hours}`);
                const data = await response.json();
                updateAnalysisResults(data);
            } catch (error) {
                console.error('Error loading analysis:', error);
                showError('Failed to load analysis data');
            }
        }

        function updateStatusCards(data) {
            const container = document.getElementById('statusCards');
            let html = '';

            // Main Service Card
            if (data.main_service) {
                html += createStatusCard('🖥️ Main Service', data.main_service, true);
            } else {
                html += createStatusCard('🖥️ Main Service', null, false);
            }

            // Menu Bar App Card
            if (data.menu_bar) {
                html += createStatusCard('📋 Menu Bar App', data.menu_bar, true);
            } else {
                html += createStatusCard('📋 Menu Bar App', null, false);
            }

            // System Memory Card
            if (data.system) {
                html += createSystemCard('💻 System Memory', data.system);
            }

            container.innerHTML = html;
        }

        function createStatusCard(title, data, isRunning) {
            if (!isRunning) {
                return `
                    <div class="status-card">
                        <h3>${title}</h3>
                        <div class="metric">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value" style="color: #dc3545;">Not Running</span>
                        </div>
                    </div>
                `;
            }

            return `
                <div class="status-card">
                    <h3>${title}</h3>
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span class="metric-value" style="color: #28a745;">Running</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Physical Memory:</span>
                        <span class="metric-value">${data.rss_mb} MB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Virtual Memory:</span>
                        <span class="metric-value">${data.vms_mb} MB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Memory %:</span>
                        <span class="metric-value">${data.percent.toFixed(2)}%</span>
                    </div>
                </div>
            `;
        }

        function createSystemCard(title, data) {
            return `
                <div class="status-card">
                    <h3>${title}</h3>
                    <div class="metric">
                        <span class="metric-label">Total:</span>
                        <span class="metric-value">${data.total_gb} GB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Used:</span>
                        <span class="metric-value">${data.used_gb} GB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Available:</span>
                        <span class="metric-value">${data.available_gb} GB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Usage %:</span>
                        <span class="metric-value">${data.percent.toFixed(1)}%</span>
                    </div>
                </div>
            `;
        }

        function updateMemoryChart(data) {
            const labels = [];
            const mainServiceData = [];
            const menuBarData = [];

            // Process main service data
            if (data.main_service) {
                data.main_service.forEach(point => {
                    const time = new Date(point.timestamp).toLocaleTimeString();
                    if (!labels.includes(time)) {
                        labels.push(time);
                    }
                    mainServiceData.push({
                        x: time,
                        y: point.rss_mb
                    });
                });
            }

            // Process menu bar data
            if (data.menu_bar) {
                data.menu_bar.forEach(point => {
                    const time = new Date(point.timestamp).toLocaleTimeString();
                    if (!labels.includes(time)) {
                        labels.push(time);
                    }
                    menuBarData.push({
                        x: time,
                        y: point.rss_mb
                    });
                });
            }

            // Update chart
            memoryChart.data.labels = labels.slice(-50); // Show last 50 points
            memoryChart.data.datasets[0].data = mainServiceData.slice(-50);
            memoryChart.data.datasets[1].data = menuBarData.slice(-50);
            memoryChart.update();
        }

        function updateComparisonChart(data) {
            const values = [
                data.main_service ? data.main_service.rss_mb : 0,
                data.menu_bar ? data.menu_bar.rss_mb : 0
            ];

            comparisonChart.data.datasets[0].data = values;
            comparisonChart.update();
        }

        function updateAnalysisResults(data) {
            const container = document.getElementById('analysisResults');
            let html = '';

            for (const [processName, analysis] of Object.entries(data)) {
                const displayName = processName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

                if (analysis.status === 'insufficient_data') {
                    html += `
                        <div class="analysis-item">
                            <h4>${displayName}</h4>
                            <p>Insufficient data for analysis. Need more monitoring time.</p>
                        </div>
                    `;
                } else if (analysis.status === 'no_memory_data') {
                    html += `
                        <div class="analysis-item">
                            <h4>${displayName}</h4>
                            <p>No memory data available. Process may not be running.</p>
                        </div>
                    `;
                } else {
                    let cardClass = 'success';
                    let statusText = 'Normal';
                    let statusColor = '#28a745';

                    if (analysis.status === 'potential_leak') {
                        cardClass = 'danger';
                        statusText = 'Potential Memory Leak Detected!';
                        statusColor = '#dc3545';
                    } else if (analysis.status === 'monitoring_needed') {
                        cardClass = 'warning';
                        statusText = 'Elevated Memory Growth';
                        statusColor = '#ffc107';
                    }

                    html += `
                        <div class="analysis-item ${cardClass}">
                            <h4>${displayName}</h4>
                            <p><strong>Status:</strong> <span style="color: ${statusColor};">${statusText}</span></p>
                            <p><strong>Growth Rate:</strong> ${analysis.growth_rate_mb_per_hour} MB/hour</p>
                            <p><strong>Total Growth:</strong> ${analysis.total_growth_mb} MB</p>
                            <p><strong>Average Memory:</strong> ${analysis.average_memory_mb} MB</p>
                            <p><strong>Current Memory:</strong> ${analysis.current_memory_mb} MB</p>
                            <p><strong>Data Points:</strong> ${analysis.data_points}</p>
                        </div>
                    `;
                }
            }

            container.innerHTML = html || '<div class="loading">No analysis data available</div>';
        }

        async function startMonitoring() {
            try {
                const interval = document.getElementById('monitorInterval').value;
                const response = await fetch(`/api/start_monitoring?interval=${interval}`);
                const result = await response.json();
                showSuccess(`Monitoring started with ${interval}s interval`);
            } catch (error) {
                console.error('Error starting monitoring:', error);
                showError('Failed to start monitoring');
            }
        }

        async function stopMonitoring() {
            try {
                const response = await fetch('/api/stop_monitoring');
                const result = await response.json();
                showSuccess('Monitoring stopped');
            } catch (error) {
                console.error('Error stopping monitoring:', error);
                showError('Failed to stop monitoring');
            }
        }

        function refreshAllData() {
            loadCurrentStatus();
            loadHistoricalData();
            loadAnalysis();
        }

        function showError(message) {
            // You could implement a toast notification system here
            console.error(message);
        }

        function showSuccess(message) {
            // You could implement a toast notification system here
            console.log(message);
        }
    </script>
</body>
</html>'''


def create_handler_with_monitor(memory_monitor):
    """Create a request handler with the memory monitor instance"""
    class Handler(MemoryVisualizerHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, memory_monitor=memory_monitor, **kwargs)
    return Handler


def ensure_single_instance():
    """Ensure only one instance of memory visualizer runs"""
    try:
        # Create lock file in temp directory
        lock_file_path = os.path.join(tempfile.gettempdir(), 'clipboard_monitor_visualizer.lock')
        lock_file = open(lock_file_path, 'w')

        # Try to acquire exclusive lock
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        # Write PID to lock file
        lock_file.write(str(os.getpid()))
        lock_file.flush()

        # Register cleanup function
        def cleanup_lock():
            try:
                lock_file.close()
                if os.path.exists(lock_file_path):
                    os.unlink(lock_file_path)
            except Exception:
                pass

        atexit.register(cleanup_lock)
        print(f"✅ Memory Visualizer singleton lock acquired (PID: {os.getpid()})")
        return True

    except (IOError, OSError):
        print("❌ Another instance of Memory Visualizer is already running!")
        print("   Opening existing dashboard at http://localhost:8001")
        try:
            webbrowser.open('http://localhost:8001')
        except Exception:
            pass
        return False


def main():
    """Main function to start the memory visualizer server"""
    # Ensure only one instance runs
    if not ensure_single_instance():
        sys.exit(0)

    print("🚀 Starting Clipboard Monitor Memory Visualizer...")

    # Create memory monitor
    memory_monitor = MemoryMonitor()

    # Start monitoring automatically
    memory_monitor.start_monitoring(interval=30)

    # Create HTTP server
    port = 8001  # Use different port from web history viewer
    handler_class = create_handler_with_monitor(memory_monitor)

    try:
        server = HTTPServer(('localhost', port), handler_class)
        url = f"http://localhost:{port}"

        print(f"📊 Memory Visualizer running at: {url}")
        print("🔍 Monitoring both main service and menu bar app...")
        print("📈 Real-time charts and memory leak detection available")
        print("⏹️  Press Ctrl+C to stop")

        # Open browser
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please open {url} manually")

        # Start server
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 Stopping memory visualizer...")
        memory_monitor.stop_monitoring()
        print("✅ Memory visualizer stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        memory_monitor.stop_monitoring()


if __name__ == "__main__":
    main()