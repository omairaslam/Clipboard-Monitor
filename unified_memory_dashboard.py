#!/usr/bin/env python3
"""
Unified Memory Dashboard - Combines Memory Visualizer and Monitoring Dashboard
Provides comprehensive real-time monitoring with multiple views and analytics.
"""

import json
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os
import sys
import gc
import tracemalloc
from collections import defaultdict, deque
from utils import safe_expanduser, log_event, log_error

# Fix psutil import issue when running from bundled app
# The bundled psutil may be incomplete, so we need to handle this carefully
psutil = None
import_error = None

# Strategy: Force import from system Python paths, bypassing bundled incomplete psutil
original_path = sys.path[:]

try:
    # First, try importing psutil normally
    import psutil
    # Test if psutil is working correctly
    psutil.virtual_memory()
    print("✅ psutil imported and working correctly")

except Exception as e:
    import_error = e
    print(f"⚠️ Initial psutil import failed: {e}")

    try:
        # Clear any cached psutil modules
        if 'psutil' in sys.modules:
            del sys.modules['psutil']

        # Remove current directory and bundled paths that might have incomplete psutil
        current_dir = os.path.dirname(os.path.abspath(__file__))
        paths_to_remove = ['.', '', current_dir]

        # Create a clean path with only system Python paths
        clean_path = []
        for path in original_path:
            if path not in paths_to_remove and 'Frameworks' not in path:
                clean_path.append(path)

        # Add common system Python paths
        system_paths = [
            '/Users/omair.aslam/Library/Python/3.9/lib/python/site-packages',
            '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/site-packages',
            '/usr/local/lib/python3.9/site-packages'
        ]

        for path in system_paths:
            if os.path.exists(path) and path not in clean_path:
                clean_path.append(path)

        sys.path = clean_path

        import psutil
        # Test if psutil is working correctly
        psutil.virtual_memory()
        print("✅ psutil imported successfully with clean path")

    except Exception as e2:
        print(f"❌ Failed to import psutil with clean path: {e2}")

        # Final fallback: restore original path and try again
        sys.path = original_path
        try:
            if 'psutil' in sys.modules:
                del sys.modules['psutil']
            import psutil
            psutil.virtual_memory()
            print("✅ psutil imported successfully after path restore")
        except Exception as e3:
            print(f"❌ All psutil import strategies failed:")
            print(f"  Original error: {import_error}")
            print(f"  Clean path error: {e2}")
            print(f"  Final error: {e3}")
            raise e3
    finally:
        # Always restore original path
        sys.path = original_path

if psutil is None:
    raise ImportError("Could not import psutil module")

class AdvancedMemoryLeakDetector:
    """Advanced memory leak detection with all original features"""

    def __init__(self):
        self.baseline_memory = {}
        self.memory_snapshots = deque(maxlen=100)
        self.object_counts = defaultdict(int)
        self.leak_alerts = []
        self.growth_threshold = 10.0  # MB growth threshold
        self.consecutive_growth_limit = 5
        self.tracemalloc_enabled = False

        # Initialize tracemalloc
        try:
            tracemalloc.start(10)
            self.tracemalloc_enabled = True
        except Exception as e:
            print(f"Failed to enable tracemalloc: {e}")

    def take_memory_snapshot(self, process_info):
        """Take detailed memory snapshot"""
        timestamp = time.time()
        snapshot = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "process_info": process_info,
            "gc_stats": self._get_gc_stats(),
            "object_counts": self._get_object_counts(),
            "resource_usage": self._get_resource_usage(),
        }

        if self.tracemalloc_enabled:
            try:
                snapshot["tracemalloc"] = self._get_tracemalloc_stats()
            except Exception as e:
                print(f"Failed to get tracemalloc stats: {e}")

        self.memory_snapshots.append(snapshot)
        return snapshot

    def _get_gc_stats(self):
        """Get garbage collection statistics"""
        try:
            return {
                "counts": gc.get_count(),
                "stats": gc.get_stats(),
                "threshold": gc.get_threshold()
            }
        except Exception:
            return {}

    def _get_object_counts(self):
        """Get object counts by type"""
        try:
            import sys
            object_counts = {}
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
            return dict(sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        except Exception:
            return {}

    def _get_resource_usage(self):
        """Get detailed resource usage"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                "max_rss": usage.ru_maxrss,
                "user_time": usage.ru_utime,
                "system_time": usage.ru_stime,
                "page_faults": usage.ru_majflt + usage.ru_minflt
            }
        except Exception:
            return {}

    def _get_tracemalloc_stats(self):
        """Get tracemalloc statistics"""
        if not self.tracemalloc_enabled:
            return {}

        try:
            current, peak = tracemalloc.get_traced_memory()
            stats = tracemalloc.take_snapshot().statistics('lineno')

            top_stats = []
            for stat in stats[:10]:
                top_stats.append({
                    "filename": stat.traceback.format()[-1] if stat.traceback else "unknown",
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                })

            return {
                "current_mb": current / 1024 / 1024,
                "peak_mb": peak / 1024 / 1024,
                "top_allocations": top_stats
            }
        except Exception:
            return {}

    def analyze_for_leaks(self):
        """Analyze snapshots for memory leaks"""
        if len(self.memory_snapshots) < 2:
            return {"status": "insufficient_data"}

        recent_snapshots = list(self.memory_snapshots)[-10:]
        memory_values = [s["process_info"]["memory_rss_mb"] for s in recent_snapshots]

        # Calculate growth rate
        if len(memory_values) >= 2:
            growth_rate = (memory_values[-1] - memory_values[0]) / len(memory_values)

            # Determine leak status
            if growth_rate > self.growth_threshold:
                status = "potential_leak"
                severity = "high"
            elif growth_rate > 2.0:
                status = "monitoring_needed"
                severity = "medium"
            else:
                status = "normal"
                severity = "low"

            return {
                "status": status,
                "severity": severity,
                "growth_rate_mb": growth_rate,
                "current_memory_mb": memory_values[-1],
                "baseline_memory_mb": memory_values[0],
                "snapshots_analyzed": len(recent_snapshots)
            }

        return {"status": "analyzing"}

class UnifiedMemoryDashboard:
    def __init__(self, port=8001, auto_start=False):
        self.port = port
        self.data_history = []  # Basic data collection (always running)
        self.advanced_data_history = []  # Advanced monitoring data (session-based)
        self.max_history = 2000  # Increased for longer history
        self.server = None

        # Advanced features
        self.leak_detector = AdvancedMemoryLeakDetector()
        self.monitoring_active = False
        self.monitoring_start_time = None
        self.alert_count = 0
        self.data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/unified_memory_data.json")

        # Monitoring configuration
        self.monitor_interval = 30  # seconds
        self.time_range_hours = 24  # hours

        # Auto-start configuration
        self.auto_start_mode = auto_start
        # Dev auto-reload
        self.dev_reload = False
        self.auto_start_time = datetime.now() if auto_start else None
        self.last_activity_time = datetime.now()
        self.auto_timeout_minutes = 5  # Auto-shutdown after 5 minutes of inactivity



        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        # Load existing data
        self.load_historical_data()

        # Session tracking
        self.session_start_time = datetime.now()
        self.peak_menubar_memory = 0.0
        self.peak_service_memory = 0.0
        self.peak_dashboard_memory = 0.0
        self.peak_total_memory = 0.0
        self.peak_menubar_cpu = 0.0
        self.peak_service_cpu = 0.0
        self.peak_dashboard_cpu = 0.0
        self.peak_total_cpu = 0.0

        # Analytics tracking
        self.memory_history = deque(maxlen=1000)  # For growth rate calculation
        self.last_memory_reading = 0.0
        self.last_memory_time = datetime.now()
        self.operation_count = 0
        self.gc_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    class RequestHandler(BaseHTTPRequestHandler):
        def __init__(self, dashboard_instance, *args, **kwargs):
            self.dashboard = dashboard_instance
            super().__init__(*args, **kwargs)

        def _update_activity(self):
            """Update last activity time for auto-timeout tracking"""
            self.dashboard.last_activity_time = datetime.now()

        def do_GET(self):
            """Handle GET requests."""
            # Parse query parameters to check if this is a monitoring request
            from urllib.parse import urlparse, parse_qs
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)

            # Only update activity time if this is not a monitoring request
            is_monitoring = query_params.get('monitor', ['false'])[0].lower() == 'true'
            if not is_monitoring:
                self._update_activity()

            # Use parsed path for routing
            path = parsed_path.path

            if path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.dashboard.render_dashboard_html().encode())
            elif path == '/favicon.ico':
                # Avoid 404 noise in console; no favicon needed
                self.send_response(204)
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                return
            elif path == '/api/memory':
                # Memory data for Memory tab charts - use the more comprehensive method
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_memory_data())
                self.wfile.write(data.encode())
            elif path == '/api/current':
                # Current status including monitoring state (for Controls tab)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                self.wfile.write(data.encode())
            elif path == '/api/data':
                # Comprehensive dashboard data for monitoring dashboard compatibility
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                self.wfile.write(data.encode())
            elif path == '/api/processes':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_process_data())
                self.wfile.write(data.encode())
            elif path == '/api/system':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_system_data())
                self.wfile.write(data.encode())
            elif path == '/api/history':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.data_history[-200:])
                self.wfile.write(data.encode())
            elif path.startswith('/api/historical'):
                # Parse query parameters for time range (already parsed above)
                hours = int(query_params.get('hours', [24])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_historical_data(hours))
                self.wfile.write(data.encode())
            elif path.startswith('/api/analysis'):
                # Parse query parameters for time range (already parsed above)
                hours = int(query_params.get('hours', [24])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_analysis_data(hours))
                self.wfile.write(data.encode())
            elif path.startswith('/api/historical-chart'):
                # Enhanced historical data for chart
                try:
                    # Use already parsed query parameters
                    hours_param = query_params.get('hours', ['1'])[0]
                    resolution = query_params.get('resolution', ['full'])[0]

                    # Historical chart request processing

                    try:
                        if hours_param == 'all':
                            hours_val = 'all'
                        else:
                            hours_val = float(hours_param)
                    except ValueError:
                        hours_val = 1

                    historical_data = self.dashboard.get_historical_data(hours_val, resolution)

                    # Format for chart consumption
                    chart_data = {
                        'points': [
                            {
                                'timestamp': p['timestamp'],
                                'menubar_memory': p.get('menubar_memory', 0),
                                'service_memory': p.get('service_memory', 0),
                                'total_memory': p.get('total_memory', 0)
                            }
                            for p in historical_data['points']
                        ],
                        'total_points': historical_data['total_points'],
                        'resolution': historical_data['resolution'],
                        'time_range': historical_data['time_range'],
                        'session_start': self.dashboard.session_start_time.isoformat()
                    }

                    # Returning chart data

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    data = json.dumps(chart_data)
                    self.wfile.write(data.encode())

                except Exception as e:
                    print(f"Error in historical-chart API: {e}")
                    print(f"Request parameters: hours={hours_param}, resolution={resolution}")
                    import traceback
                    traceback.print_exc()

                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error_data = json.dumps({
                        'error': str(e),
                        'points': [],
                        'total_points': 0,
                        'resolution': resolution,
                        'time_range': 'error',
                        'debug_info': f"hours_param={hours_param}, resolution={resolution}"
                    })
                    self.wfile.write(error_data.encode())
            elif path.startswith('/api/start_monitoring'):
                # Parse query parameters for interval (already parsed above)
                interval = int(query_params.get('interval', [30])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.start_advanced_monitoring(interval)
                self.wfile.write(json.dumps(result).encode())
            elif path == '/api/stop_monitoring':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.stop_advanced_monitoring()
                self.wfile.write(json.dumps(result).encode())
            elif path == '/api/force_gc':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.force_garbage_collection()
                self.wfile.write(json.dumps(result).encode())
            elif path == '/api/leak_analysis':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_leak_analysis())
                self.wfile.write(data.encode())
            elif path == '/api/dashboard_status':
                # Dashboard status for menu bar app
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_dashboard_status())
                self.wfile.write(data.encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            """Suppress default logging."""
            pass

    def render_dashboard_html(self):
        """Render the unified dashboard HTML."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clipboard Monitor - Unified Memory Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { color: #2c3e50; margin-bottom: 10px; }
        .status {
            padding: 12px 24px;
            border-radius: 25px;
            margin: 10px auto;
            max-width: 300px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .status.connected {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
        }
        .status.disconnected {
            background: linear-gradient(45deg, #f44336, #da190b);
            color: white;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }
        .card {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            position: relative;
            margin: 0; /* Rely on parent stack/grid gaps */
            transition: none; /* Keep panels static */
        }
        /* Disable hover lift to keep layout static */
        .card:hover { transform: none; }
        .card h3 {
            color: #2c3e50;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            text-align: center;
            margin: 10px 0;
        }
        .metric-label {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .chart-container {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 12px;
            position: relative;
            overflow: hidden; /* Force content to stay within container */
            min-height: 400px; /* Ensure container is tall enough for content */
        }
        .chart-wrapper {
            position: relative;
            height: 280px; /* Reduced height for more compact layout */
            width: 100%;
            max-width: 100%; /* Ensure wrapper doesn't exceed container */
            overflow: hidden; /* Prevent chart from expanding beyond container */
            margin: 0; /* Remove any margins */
            padding: 0; /* Remove any padding */
            box-sizing: border-box; /* Include padding/border in width calculation */
            top: 0 !important; /* Force to top of container */
        }

        /* Force memory chart to be visible */
        #memoryChart {
            position: static !important;
            top: 0 !important;
            left: 0 !important;
            transform: none !important;
        }
        .chart-wrapper canvas {
            max-height: 280px !important;
            max-width: 100% !important;
            width: 100% !important; /* Force canvas to respect container width */
            position: static !important; /* Use static positioning to stay in flow */
            display: block !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important; /* Include padding/border in width calculation */
        }

        /* Layout utilities for consistent, non-overlapping spacing */
        .section-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 12px;
            margin-bottom: 12px;
        }
        .stack-16 {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        /* Unified Control Bar Styles */
        .unified-control-bar {
            transition: all 0.3s ease;
        }
        .unified-control-bar:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        }

        .mode-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .mode-btn:active {
            transform: translateY(0);
        }

        .chart-badge {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.8; }
            100% { opacity: 1; }
        }

        /* Responsive Design for Control Bar */
        @media (max-width: 768px) {
            .unified-control-bar > div:last-child {
                flex-direction: column;
                gap: 8px;
            }

            .range-controls {
                order: 1;
            }

            .mode-controls {
                order: 2;
            }

            .data-info {
                order: 3;
                align-self: center;
            }
        }

        @media (max-width: 480px) {
            .unified-control-bar {
                padding: 8px 12px !important;
            }

            .unified-control-bar h3 {
                font-size: 14px !important;
            }

            .mode-btn {
                padding: 4px 8px !important;
                font-size: 11px !important;
            }

            .range-controls select {
                min-width: 80px !important;
                font-size: 11px !important;
            }
        }
        /* Gap utility classes for consistency */
        .row-12 { display: flex; gap: 12px; }
        .grid-gap-12 { display: grid; gap: 12px; }
        .grid-2-12 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .grid-4-12 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }


        /* Button animations */
        /* Dedicated grid for Analysis & Controls panels to ensure even spacing */
        .analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; align-items: stretch; }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(244, 67, 54, 0); }
            100% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0); }
        }

        /* Status indicator animations */
        @keyframes pulse-dot {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse-dot 1.5s infinite;
        }

        .status-active {
            background: #4CAF50 !important;
            animation: pulse-dot 2s infinite;
        }

        .status-inactive {
            background: #ccc !important;
            animation: none;
        }
        .tabs {
            display: flex;
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 5px;
            margin-bottom: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        /* Ensure consistent vertical spacing between major panels on Analysis tab */
        #analysis-tab > .card { margin-bottom: 12px; }
        #analysis-tab > .analysis-grid { margin-bottom: 12px; }
        .tab {
            flex: 1;
            padding: 12px 20px;
            text-align: center;
            border-radius: 8px;
            cursor: pointer;
            /* Keep static: remove transitions and hover background shifts */
            font-weight: 600;
        }
        .tab.active {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }
        .tab:not(.active):hover {
            background: inherit;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .process-list {
            max-height: 400px;
            overflow-y: auto;
            min-height: 200px; /* Ensure minimum height */
        }
        .process-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 600px; /* Ensure minimum width */
        }
        /* Processes tab layout: only apply dimensions when active */
        #processes-tab {
            /* allow default .tab-content { display:none } when not active */
            position: relative;
        }
        #processes-tab.active {
            display: block !important;
            min-height: 400px !important;
            width: 100% !important;
            position: relative;
            overflow: visible;
        }
        #processes-tab .card {
            min-height: 350px !important;
            width: 100% !important;
            display: block;
            position: relative;
            padding: 20px !important;
        }
        .process-table th {
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid #e9ecef;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        .process-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: middle;
        }
        /* Keep rows static; no hover highlight to avoid layout shifts */
        .process-table tr:hover {
            background: inherit;
        }
        .process-name {
            font-weight: 600;
            color: #2c3e50;
        }
        .process-memory {
            color: #e74c3c;
            font-weight: bold;
            text-align: right;
        }
        .process-cpu {
            color: #f39c12;
            font-weight: bold;
            text-align: right;
        }
        .process-pid {
            color: #7f8c8d;
            font-family: monospace;
            text-align: center;
        }
        .system-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }
        .info-item {
            text-align: center;
            padding: 12px;
            background: rgba(52, 152, 219, 0.1);
            border-radius: 8px;
        }
        .info-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2980b9;
        }
        .info-label {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .tabs {
                flex-direction: column;
            }
        }
        /* Toast notifications */
        #toast-container { position: fixed; top: 16px; right: 16px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; }
        .toast { min-width: 240px; max-width: 380px; background: #333; color: white; padding: 10px 14px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); opacity: 0.95; font-size: 14px; }
        .toast.success { background: #2e7d32; }
        .toast.info { background: #1565c0; }
        .toast.warn { background: #ef6c00; }
        .toast.error { background: #c62828; }

        /* Skeleton loader */
        .loading { position: relative; background: linear-gradient(90deg, #f0f0f0 25%, #f7f7f7 37%, #f0f0f0 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite; height: 14px; border-radius: 4px; }
        @keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }

        /* Sparkline canvas */
        .spark-cell { width: 140px; display: inline-block; }
        .sparkline { width: 140px; height: 28px; display: block; border: 1px solid #eee; background: #fafafa; }
        .cell-inner { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
        .process-table td.process-memory, .process-table td.process-cpu { text-align: right; }
        .cell-inner .value { min-width: 70px; text-align: right; font-variant-numeric: tabular-nums; }

    </style>
</head>
<body>
    <div class="container">
        <div id="toast-container" aria-live="polite" aria-atomic="true"></div>
        <!-- New 4-Box Dashboard Header -->
        <div class="header" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; padding: 8px; margin-bottom: 8px; border: 1px solid #dee2e6; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <!-- Compact Title and Status -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #e0e0e0;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <h1 style="margin: 0; font-size: 16px; color: #333; font-weight: bold;">📊 Clipboard Monitor Dashboard</h1>
                    <span id="ui-signature" style="font-size:11px; color:#555; background:#f1f3f5; border:1px solid #dfe3e6; padding:2px 6px; border-radius:6px;">
                        UI v2025-08-14 02:00Z • workspace
                    </span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; font-size: 11px;">
                    <span style="background: #4CAF50; color: white; padding: 2px 6px; border-radius: 8px; font-weight: bold; display: flex; align-items: center; gap: 3px;">
                        <span>●</span> Connected
                    </span>
                    <span id="advanced-status" style="background: #999; color: white; padding: 2px 6px; border-radius: 8px; font-weight: bold; display: flex; align-items: center; gap: 3px;">
                        ⚫ Advanced
                    </span>
                        <span id="monitoring-status-indicator" class="monitoring-indicator" style="display:none; width:10px; height:10px; border-radius:50%; background:#4CAF50; animation: pulse-dot 1.5s infinite;"></span>
                </div>
            </div>

            <!-- Clean 4-Box Horizontal Layout -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; width: 100%;">

                <!-- Box 1: Menu Bar + Service -->
                <div style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #2196F3;">
                    <div style="font-weight: bold; color: #2196F3; margin-bottom: 6px; font-size: 11px; text-align: center;">📱 Menu Bar</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💾 Memory:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span style="font-size: 9px; color: #666;">Peak:</span>
                            <span style="font-size: 9px; color: #FF5722; font-weight: bold;" id="header-menubar-memory-peak">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ CPU:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-cpu">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🧵 Threads:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-threads">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🔗 Handles:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-handles">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⏰ Uptime:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-menubar-uptime">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔄 Restarts:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-menubar-restarts">--</span>
                        </div>
                    </div>

                    <div style="font-weight: bold; color: #4CAF50; margin: 8px 0 6px 0; font-size: 11px; text-align: center; border-top: 1px solid #eee; padding-top: 6px;">⚙️ Service</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💾 Memory:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span style="font-size: 9px; color: #666;">Peak:</span>
                            <span style="font-size: 9px; color: #FF5722; font-weight: bold;" id="header-service-memory-peak">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ CPU:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-cpu">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🧵 Threads:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-threads">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🔗 Handles:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-handles">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⏰ Uptime:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-uptime">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔄 Restarts:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-restarts">--</span>
                        </div>
                    </div>
                </div>

                <!-- Box 2: Analytics -->
                <div style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #FF9800;">
                    <div style="font-weight: bold; color: #FF9800; margin-bottom: 4px; font-size: 11px; text-align: center;">📊 Analytics</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📊 Total:</span>
                            <span style="color: #FF9800; font-weight: bold;" id="header-total-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📈 Growth:</span>
                            <span style="color: #FF5722; font-weight: bold;" id="header-growth-rate">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ Efficiency:</span>
                            <span style="color: #9C27B0; font-weight: bold;" id="header-efficiency">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🎯 Optimum:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-optimum">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🗑️ GC:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-gc-status">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ Pressure:</span>
                            <span style="color: #F44336; font-weight: bold;" id="header-pressure">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📚 History:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-history">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📋 Queue:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-queue">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>💾 Cache:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-cache">--</span>
                        </div>
                    </div>
                </div>

                <!-- Box 3: System -->
                <div style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #9C27B0;">
                    <div style="font-weight: bold; color: #9C27B0; margin-bottom: 4px; font-size: 11px; text-align: center;">💻 System</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🧠 RAM:</span>
                            <span style="color: #9C27B0; font-weight: bold;" id="header-system-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ CPU:</span>
                            <span style="color: #F44336; font-weight: bold;" id="header-cpu-usage">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💾 Total:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-total-ram">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>✅ Available:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-available-ram">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>📊 Load:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-system-load">--</span>
                        </div>
                    </div>
                </div>

                <!-- Box 4: Session -->
                <div style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #795548;">
                    <div style="font-weight: bold; color: #795548; margin-bottom: 4px; font-size: 11px; text-align: center;">📊 Session</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⏰ Session:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-session-time">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💻 System:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-uptime">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📈 Points:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-data-points">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📊 Peak Mem:</span>
                            <span style="color: #FF5722; font-weight: bold;" id="header-peak-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ Peak CPU:</span>
                            <span style="color: #FF5722; font-weight: bold;" id="header-peak-cpu">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔄 Updated:</span>
                            <span style="color: #666; font-weight: bold;" id="header-last-updated">--</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>



        <div class="tabs">
            <div class="tab active" onclick="switchTab('dashboard', this)">📊 Dashboard</div>
            <div class="tab" onclick="switchTab('analysis', this)">🔍 Analysis & Controls</div>
            <div class="tab" onclick="switchTab('processes', this)">⚙️ Processes</div>
        </div>

        <!-- Consolidated Dashboard Tab -->
        <div id="dashboard-tab" class="tab-content active">

            <!-- Memory Usage Chart - Only visible in Dashboard tab -->
            <div class="chart-container" style="margin-bottom: 10px; width: 100%; max-width: 100%; box-sizing: border-box; overflow: hidden; height: 350px;">
                <!-- Unified Control Bar -->
                <div class="unified-control-bar" style="
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    width: 100%;
                    max-width: 100%;
                    box-sizing: border-box;
                    overflow: hidden;
                ">
                    <!-- Top Row: Title and Status -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <h3 style="font-size: 16px; margin: 0; color: #333; font-weight: 600;">
                                📈 <span id="chart-title">Live Memory Usage</span>
                            </h3>
                            <div class="chart-badge" style="
                                background: #4CAF50;
                                color: white;
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 10px;
                                font-weight: 500;
                                text-transform: uppercase;
                            " id="mode-badge">Live</div>
                        </div>
                        <div class="chart-status" style="
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            font-size: 11px;
                            color: #666;
                            background: rgba(255,255,255,0.7);
                            padding: 4px 8px;
                            border-radius: 4px;
                        ">
                            <span id="chart-mode-indicator">Live: 5 Minutes</span>
                            <span style="color: #dee2e6;">•</span>
                            <span id="chart-points-count">-- pts</span>
                            <span style="color: #dee2e6;">•</span>
                            <span id="chart-last-update">--</span>
                        </div>
                    </div>

                    <!-- Bottom Row: Controls -->
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <!-- Left: Mode Controls -->
                        <div class="mode-controls" style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 12px; color: #666; font-weight: 500;">Mode:</span>
                            <div class="mode-toggle" style="
                                display: flex;
                                background: white;
                                border: 1px solid #dee2e6;
                                border-radius: 6px;
                                overflow: hidden;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                            ">
                                <button id="realtime-btn" class="mode-btn" onclick="chartManager.switchToLiveMode()" style="
                                    padding: 6px 12px;
                                    font-size: 12px;
                                    border: none;
                                    background: #4CAF50;
                                    color: white;
                                    cursor: pointer;
                                    font-weight: 500;
                                    transition: all 0.2s ease;
                                ">Live</button>
                                <button id="historical-btn" class="mode-btn" onclick="toggleHistoricalOptions()" style="
                                    padding: 6px 12px;
                                    font-size: 12px;
                                    border: none;
                                    background: white;
                                    color: #666;
                                    cursor: pointer;
                                    font-weight: 500;
                                    transition: all 0.2s ease;
                                ">Historical</button>
                            </div>
                        </div>

                        <!-- Center: Range Controls -->
                        <div class="range-controls" style="display: flex; align-items: center; gap: 8px;">
                            <!-- Live Range Options -->
                            <div id="live-options" style="display: flex; align-items: center; gap: 6px;">
                                <span style="font-size: 12px; color: #666; font-weight: 500;">Range:</span>
                                <select id="live-range-select" onchange="handleLiveRangeChange(this)" style="
                                    padding: 6px 10px;
                                    font-size: 12px;
                                    border: 1px solid #dee2e6;
                                    border-radius: 4px;
                                    background: white;
                                    color: #333;
                                    cursor: pointer;
                                    font-weight: 500;
                                    min-width: 100px;
                                ">
                                    <option value="5m">5 Minutes</option>
                                    <option value="15m">15 Minutes</option>
                                    <option value="30m">30 Minutes</option>
                                    <option value="1h">1 Hour</option>
                                    <option value="2h">2 Hours</option>
                                    <option value="4h">4 Hours</option>
                                </select>
                            </div>

                            <!-- Historical Range Options (hidden by default) -->
                            <div id="historical-options" style="display: none; align-items: center; gap: 6px;">
                                <span style="font-size: 12px; color: #666; font-weight: 500;">Period:</span>
                                <select id="historical-range" onchange="handleRangeChange(this)" style="
                                    padding: 6px 10px;
                                    font-size: 12px;
                                    border: 1px solid #dee2e6;
                                    border-radius: 4px;
                                    background: white;
                                    color: #333;
                                    cursor: pointer;
                                    font-weight: 500;
                                    min-width: 120px;
                                ">
                                    <option value="1">Last Hour</option>
                                    <option value="6">Last 6 Hours</option>
                                    <option value="24">Last 24 Hours</option>
                                    <option value="168">Last 7 Days</option>
                                    <option value="all">Since Start ⚠️</option>
                                </select>
                                <span style="font-size: 12px; color: #666; font-weight: 500;">Resolution:</span>
                                <select id="resolution-select" onchange="chartManager.changeResolution(this.value)" style="
                                    padding: 6px 10px;
                                    font-size: 12px;
                                    border: 1px solid #dee2e6;
                                    border-radius: 4px;
                                    background: white;
                                    color: #333;
                                    cursor: pointer;
                                    font-weight: 500;
                                    min-width: 100px;
                                ">
                                    <option value="full">Full</option>
                                    <option value="10sec">10s Avg</option>
                                    <option value="minute">1m Avg</option>
                                    <option value="hour">1h Avg</option>
                                </select>
                            </div>
                        </div>

                        <!-- Right: Data Info and Legend -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div class="data-info" style="
                                display: flex;
                                align-items: center;
                                gap: 6px;
                                font-size: 11px;
                                color: #666;
                                background: rgba(255,255,255,0.7);
                                padding: 4px 8px;
                                border-radius: 4px;
                            ">
                                <span id="data-collection-info">Data: 2s intervals</span>
                            </div>

                            <!-- Legend -->
                            <div class="legend-info" style="
                                display: flex;
                                align-items: center;
                                gap: 12px;
                                font-size: 12px;
                            ">
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 12px; height: 12px; background: #2196F3; border-radius: 2px;"></div>
                                    <span>Menu Bar App</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 12px; height: 12px; background: #4CAF50; border-radius: 2px;"></div>
                                    <span>Main Service</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Chart Canvas -->
                    <div class="chart-wrapper" style="margin-top: 0; position: relative; top: 0;">
                        <canvas id="memoryChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- CPU Usage Chart -->
            <div class="chart-container" style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div class="row-12" style="align-items: center;">
                        <h3 style="font-size: 16px; margin: 0; color: #333;">⚡ <span id="cpu-chart-title">Real-time CPU Usage</span></h3>
                        <span style="font-size: 11px; color: #666; font-style: italic;">Data collected every 2 seconds</span>
                    </div>
                    <div class="row-12" style="align-items: center;">
                        <!-- Mode Toggle -->
                        <div style="display: flex; gap: 4px;">
                            <button id="cpu-realtime-btn" class="chart-mode-btn" onclick="cpuChartManager.switchToRealtimeMode()"
                                    style="padding: 3px 6px; font-size: 10px; border: 1px solid #ddd; background: #4CAF50; color: white; border-radius: 3px; cursor: pointer;">
                                Real-time
                            </button>
                            <button id="cpu-historical-btn" class="chart-mode-btn" onclick="cpuChartManager.switchToHistoricalMode()"
                                    style="padding: 3px 6px; font-size: 10px; border: 1px solid #ddd; background: #f5f5f5; color: #333; border-radius: 3px; cursor: pointer;">
                                Historical
                            </button>
                        </div>

                        <!-- Historical Options (hidden by default) -->
                        <div id="cpu-historical-options" style="display: none; gap: 4px;">
                            <select id="cpu-time-range" onchange="cpuChartManager.loadHistoricalData()"
                                    style="padding: 3px 5px; font-size: 10px; border: 1px solid #ddd; border-radius: 3px;">
                                <option value="1h">Last Hour</option>
                                <option value="6h">Last 6 Hours</option>
                                <option value="24h">Last 24 Hours</option>
                                <option value="7d">Last 7 Days</option>
                            </select>
                        </div>



                        <!-- Chart Status and Legend -->
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div id="cpu-chart-status" style="font-size: 10px; color: #666;">
                                <span id="cpu-chart-mode-indicator">Real-time</span> •
                                <span id="cpu-chart-points-count">-- pts</span>
                            </div>
                            <div id="cpu-chart-legend" style="display: flex; align-items: center; gap: 12px; font-size: 12px;">
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 12px; height: 12px; background: #2196F3; border-radius: 2px;"></div>
                                    <span>Menu Bar App</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 12px; height: 12px; background: #4CAF50; border-radius: 2px;"></div>
                                    <span>Main Service</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="chart-wrapper">
                    <canvas id="cpuChart"></canvas>
                </div>
            </div>


        </div>

        <!-- Analysis Tab (Combined with Controls) -->
        <div id="analysis-tab" class="tab-content">
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #4CAF50;">
                <h4 style="margin: 0 0 10px 0; color: #2e7d32;">🔍 Memory Analysis & Monitoring Dashboard</h4>
                <p style="margin: 0 0 10px 0;">This tab provides comprehensive memory leak detection, monitoring controls, and growth pattern analysis.</p>
                <div class="grid-2-12" style="margin-top: 10px;">
                    <div style="background: white; padding: 10px; border-radius: 5px;">
                        <strong>📊 Analysis Features:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px; font-size: 14px;">
                            <li>Growth rate analysis</li>
                            <li>Memory trend patterns</li>
                            <li>Leak severity assessment</li>
                            <li>Process-specific analysis</li>
                        </ul>
                    </div>
                    <div style="background: white; padding: 10px; border-radius: 5px;">
                        <strong>⚙️ Monitoring Controls:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px; font-size: 14px;">
                            <li>Advanced monitoring with configurable intervals</li>
                            <li>Memory leak detection algorithms</li>
                            <li>Background data collection</li>
                            <li>Session-based monitoring</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Live Collection Strip (compact banner) -->
            <div class="card" style="padding: 10px 12px;">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <span id="live-status-dot" style="width:10px; height:10px; border-radius:50%; background:#ccc;"></span>
                        <strong>Live Collection:</strong>
                        <span id="live-status-text" style="color:#666;">INACTIVE</span>
                        <span style="color:#bbb;">|</span>
                        <span>Rate: <strong id="live-interval">Every 30s</strong></span>
                        <span style="color:#bbb;">|</span>
                        <span>Next: <strong id="live-next">--</strong></span>
                        <span style="color:#bbb;">|</span>
                        <span>Points: <strong id="live-adv-points">0</strong></span>
                        <span style="color:#bbb;">|</span>
                        <span>Duration: <strong id="live-duration">0.00h</strong></span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button id="monitoringToggleBtnMini" onclick="toggleAdvancedMonitoring()" style="background:#4CAF50; color:white; border:none; padding:8px 14px; border-radius:5px; cursor:pointer; font-weight:600;">🚀 Start</button>
                        <button onclick="forceGarbageCollection()" style="background:#ff9800; color:white; border:none; padding:8px 14px; border-radius:5px; cursor:pointer;" title="Force Python garbage collection to free unused memory">🗑️ GC</button>
                    </div>
                </div>
                <div style="margin-top:6px; color:#666; font-size:12px;">
                    <em>Collects per‑process memory and CPU at the chosen interval. Use the controls to start/stop a session; results appear below.</em>
                </div>
                <div id="live-last-sample" style="margin-top:6px; font-size:12px; color:#333; font-variant-numeric: tabular-nums;"></div>
            </div>

            <!-- Monitoring Controls Section (Moved from Controls Tab) -->
            <div class="card">
                <h3>⚙️ Advanced Monitoring Controls</h3>
                <div class="section-grid">
                    <div>
                        <label for="monitorInterval" style="display: block; margin-bottom: 5px;">Monitoring Interval:</label>
                        <select id="monitorInterval" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 12px;">
                            <option value="10">Every 10 seconds</option>
                            <option value="30" selected>Every 30 seconds</option>
                            <option value="60">Every 1 minute</option>
                            <option value="300">Every 5 minutes</option>
                        </select>

                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <button id="monitoringToggleBtn" onclick="toggleAdvancedMonitoring()" style="background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-weight: bold;">🚀 Start Advanced Monitoring</button>
                            <button onclick="forceGarbageCollection()" style="background: #ff9800; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer;" title="Force Python garbage collection to free unused memory">🗑️ Force Garbage Collection</button>
                        </div>
                    </div>

                    <div id="monitoring-status">
                        <div style="padding: 15px; background: #f5f5f5; border-radius: 8px; border: 2px solid #ddd;">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <div id="status-indicator" style="width: 12px; height: 12px; border-radius: 50%; background: #ccc; margin-right: 10px;"></div>
                                <strong>Advanced Monitoring Status:</strong> <span id="status-text">INACTIVE</span>
                            </div>
                            <div class="grid-2-12">
                                <div>
                                    <strong>Advanced Data Points:</strong> <span id="advanced-data-points">0</span><br>
                                <div>
                                    <strong>Next Sample In:</strong> <span id="next-sample">--</span>
                                </div>
                                    <strong>Advanced Collection Rate:</strong> <span id="collection-rate">Stopped</span><br>
                                    <small style="color: #666;">Leak detection & analysis data</small>
                                </div>
                                <div>
                                    <strong>Basic Data Points:</strong> <span id="basic-data-points">0</span><br>
                                    <strong>Basic Collection Rate:</strong> <span style="color: #4CAF50;">Every 1s</span><br>
                                    <small style="color: #666;">Real-time dashboard data</small>
                                </div>
                            </div>
                            <div class="grid-2-12" style="margin-top: 10px;">
                                <div>
                                    <strong>Advanced Duration:</strong> <span id="monitoring-duration">0.0 hours</span>
                                </div>
                                <div>
                                    <strong>Last Update:</strong> <span id="last-update">Never</span>
                                </div>
                            </div>
                            <div id="collection-animation" style="margin-top: 10px; display: none;">
                                <div style="display: flex; align-items: center;">
                                    <div class="pulse-dot"></div>
                                    <span style="margin-left: 10px; color: #4CAF50; font-weight: bold;">Collecting data...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Analysis Controls Section -->
            <div class="analysis-grid">
            <!-- Last Session Summary (Findings Board) -->
            <div class="card">
                <h3>🧭 Last Session Summary</h3>
                <div id="session-findings">
                    <div class="loading">Waiting for advanced monitoring data...</div>
                </div>
            </div>

                <div class="card">
                    <h3>⏱️ Analysis Time Range</h3>
                    <div style="margin-bottom: 12px;">
                        <label for="analysisTimeRange" style="display: block; margin-bottom: 5px;">Select time period for analysis:</label>
                        <select id="analysisTimeRange" onchange="updateAnalysisTimeRange()" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="1">Last 1 hour</option>
                            <option value="6">Last 6 hours</option>
                            <option value="24" selected>Last 24 hours</option>
                            <option value="72">Last 3 days</option>
                            <option value="168">Last week</option>
                        </select>
                    </div>
                    <div id="analysis-summary" style="padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <div class="loading">Loading analysis summary...</div>
                    </div>
                </div>

                <div class="card">
                    <h3>🎯 Quick Actions</h3>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <button onclick="refreshAnalysisData()" style="background: #2196F3; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;">🔄 Refresh Analysis</button>
                        <button onclick="exportAnalysisData()" style="background: #4CAF50; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;">📊 Export Data</button>
                        <button onclick="refreshAllData()" style="background: #2196F3; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;" title="Reload all dashboard data from server">🔄 Refresh All Data</button>
                    </div>
                </div>
            </div>

            <!-- Analysis Results Section -->
            <div class="stack-16">
            <div class="card">
                <h3>🔍 Memory Leak Detection Results</h3>
                <div id="leak-analysis">
                    <div class="loading">Analyzing memory trends...</div>
                </div>
            </div>

            <div class="card">
                <h3>📈 Growth Trend Analysis</h3>
                <div style="font-size:12px; color:#555; margin-bottom:8px;">
                    This section analyzes memory behavior over time for the Menu Bar and Main Service processes.
                    We compute growth rate (MB/hour) using a simple regression of memory vs time, estimate Consistency using R² (how well a straight line explains the trend),
                    and surface the biggest spikes to help spot anomalous jumps. Use the Range and Res controls to change the analysis window and resolution.
                </div>
                <div id="trend-analysis">
                    <div class="loading">Loading trend analysis...</div>
                </div>
            </div>

            <div class="card">
                <h3>📊 Advanced Monitoring History</h3>
                <div id="monitoring-history">
                    <div class="loading">Loading monitoring history...</div>
                </div>
            </div>
            </div> <!-- Close stack-16 -->
        </div>

        <!-- Processes Tab -->
        <div id="processes-tab" class="tab-content">
            <div class="card">
                <h3>🔍 Clipboard Monitor Processes
                    <span id="processes-meta" style="font-size:12px; color:#666; margin-left:8px;"></span>
                    <button id="processes-refresh" onclick="fetchProcessData()" style="float:right; font-size:12px; padding:4px 8px; background:#4CAF50; color:white; border:none; border-radius:3px; cursor:pointer;">🔄 Refresh</button>
                </h3>
                <div class="process-list">
                    <table class="process-table">
                        <thead>
                            <tr>
                                <th>Process Name</th>
                                <th>PID</th>
                                <th>Memory (MB)</th>
                                <th>CPU (%)</th>
                                <th>Uptime</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="process-list">
                            <tr>
                                <td colspan="6" style="text-align: center; padding: 20px;">Loading processes...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>



    <!-- Controls Tab (Removed - Merged with Analysis Tab) -->

    <script>
        // Live collection countdown state (global)
        window.__liveCountdown = { active: false, interval: 30, remaining: 0, timerId: null, lastPoints: 0 };

        // Global variables
        // Analysis helpers (move to script top to avoid being printed in tables)
        let analysisAbortController = null;
        let analysisDebounceTimer = null;
        function isTabActive(name) {
            const el = document.getElementById(name + '-tab');
            return el && el.classList.contains('active');
        }
        document.addEventListener('DOMContentLoaded', () => {
            const sel = document.getElementById('analysisTimeRange');
            const saved = localStorage.getItem('analysisTimeRange');
            if (sel && saved) sel.value = saved;
        });

        // Toast helpers (global)
        function showToast(message, type = 'info', timeout = 2500) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => { toast.remove(); }, timeout);
        }

        let currentTooltip = null;

        // Tooltip functions for bubble help
        function showTooltip(element, text) {
            // Remove any existing tooltip
            hideTooltip();

            // Create tooltip element
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = text;
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 6px 8px;
                border-radius: 4px;
                font-size: 10px;
                white-space: nowrap;
                z-index: 1000;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.2s;
                max-width: 250px;
                white-space: normal;
                line-height: 1.3;
            `;

            // Position tooltip
            document.body.appendChild(tooltip);
            const rect = element.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();

            let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
            let top = rect.top - tooltipRect.height - 5;

            // Adjust if tooltip goes off screen
            if (left < 5) left = 5;
            if (left + tooltipRect.width > window.innerWidth - 5) {
                left = window.innerWidth - tooltipRect.width - 5;
            }
            if (top < 5) {
                top = rect.bottom + 5;
            }

            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';

            // Show tooltip
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 10);

            currentTooltip = tooltip;
        }

        function hideTooltip() {
            if (currentTooltip) {
                currentTooltip.remove();
                currentTooltip = null;
            }
        }

        // Chart management functions
        let chartPaused = false;

        // Legacy chart functions (removed duplicate chartManager declaration)
        // The real chartManager is initialized later as HybridMemoryChart

        // Simple sparkline drawer with tiny history buffers per PID (moved near top for availability)
        const sparkHistory = { mem: new Map(), cpu: new Map() };
        function drawSparkline(canvasId, value, kind = 'mem', maxPoints = 10) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const map = kind === 'cpu' ? sparkHistory.cpu : sparkHistory.mem;
            if (!map.has(canvasId)) map.set(canvasId, []);
            const history = map.get(canvasId);
            history.push(Math.max(0, value));
            if (history.length > maxPoints) history.shift();
            // Clear
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            // Normalize
            const h = canvas.height, w = canvas.width;
            const min = Math.min(...history);
            const max = Math.max(...history);
            const range = Math.max(0.001, max - min);
            // Draw bars
            const barW = 5, gap = 2;
            const startX = Math.max(0, w - (barW + gap) * history.length);
            history.forEach((v, i) => {
                const norm = (v - min) / range;
                const barH = Math.max(2, Math.round(norm * (h - 2)));
                const x = startX + i * (barW + gap);
                const y = h - barH;
                // Color coding
                let color = '#4CAF50';
                const val = v;
                if (kind === 'cpu') {
                    if (val > 70) color = '#FF5722';
                    else if (val > 40) color = '#FF9800';
                } else {
                    if (val > 400) color = '#FF5722';
                    else if (val > 200) color = '#FF9800';
                }
                ctx.fillStyle = color;
                ctx.fillRect(x, y, barW, barH);
            });
        }

        // Utility functions
        function formatDuration(ms) {
            const seconds = Math.floor(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);

            if (days > 0) {
                return `${days}d ${hours % 24}h`;
            } else if (hours > 0) {
                return `${hours}h ${minutes % 60}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${seconds % 60}s`;
            } else {
                return `${seconds}s`;
            }
        }

        // Advanced monitoring status management
        function updateAdvancedStatus(isActive) {
            const statusElement = document.getElementById('advanced-status');
            if (isActive) {
                statusElement.style.background = '#F44336';
                statusElement.style.animation = 'pulse 2s infinite';
                statusElement.innerHTML = '🔴 Advanced';
            } else {
                statusElement.style.background = '#999';
                statusElement.style.animation = 'none';
                statusElement.innerHTML = '⚫ Advanced';
            }
        }

        // Global variable for process refresh interval
        let processRefreshInterval = null;

        // Tab switching functionality
        function switchTab(tabName, el) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab content
            document.getElementById(tabName + '-tab').classList.add('active');

            // Add active class to clicked tab (robust for direct calls)
            if (el && el.classList) {
                el.classList.add('active');
            } else {
                const sel = `.tabs .tab[onclick*="${tabName}"]`;
                const fallback = document.querySelector(sel);
                if (fallback) fallback.classList.add('active');
            }

            // Clear any existing process refresh interval
            if (processRefreshInterval) {
                clearInterval(processRefreshInterval);
                processRefreshInterval = null;
            }


            // Handle tab-specific initialization
            if (tabName === 'dashboard') {
                // Resize charts when switching to dashboard tab to fix any sizing issues
                setTimeout(() => {
                    if (typeof chart !== 'undefined') {
                        chart.resize();
                    }
                }, 100);
            } else if (tabName === 'processes') {
                // Load processes immediately and start auto-refresh
                fetchProcessData();
                processRefreshInterval = setInterval(fetchProcessData, 3000); // Refresh every 3 seconds
            }
        }

        // Legacy memory chart initialization removed - now handled by UnifiedMemoryChart class

        // Initialize CPU chart
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        const cpuChart = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Menu Bar App (%)',
                    data: [],
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Main Service (%)',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'CPU Usage (%)'
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
                    title: {
                        display: false
                    },
                    legend: {
                        display: false
                    }
                },
                animation: {
                    duration: 0 // Disable animations for real-time updates
                },
                elements: {
                    point: {
                        radius: 1,
                        hoverRadius: 4
                    }
                }
            }
        });

        // Polling for real-time updates (simpler than WebSockets)
        let isConnected = false;

        // Generate simulated data for demonstration
        function generateSimulatedData() {
            const baseMemory = 45 + Math.random() * 10; // 45-55 MB
            const baseCpu = 2 + Math.random() * 8; // 2-10%

            return {
                menubar_memory: baseMemory + Math.random() * 5,
                service_memory: baseMemory * 0.8 + Math.random() * 3,
                total_memory: baseMemory * 1.8 + Math.random() * 8,
                menubar_cpu: baseCpu + Math.random() * 3,
                service_cpu: baseCpu * 0.6 + Math.random() * 2,
                total_cpu: baseCpu * 1.6 + Math.random() * 5,
                peak_menubar_memory: baseMemory * 1.3,
                peak_service_memory: baseMemory * 1.2,
                peak_menubar_cpu: baseCpu * 1.5,
                peak_service_cpu: baseCpu * 1.4,
                timestamp: new Date().toISOString()
            };
        }

        async function fetchMemoryData() {
            try {
                // Get current status data for dashboard stats
                const response = await fetch('/api/current');
                if (!response.ok) {
                    throw new Error(`Failed to fetch data: ${response.statusText}`);
                }
                const data = await response.json();

                if (!isConnected) {
                    const statusLight = document.getElementById('dashboard-status-light');
                    const statusText = document.getElementById('dashboard-status-text');
                    if (statusLight && statusText) {
                        statusLight.style.background = '#4CAF50';
                        statusText.textContent = 'Connected';
                        statusText.style.color = '#4CAF50';
                    }
                    isConnected = true;
                }

                if (data.clipboard) {
                    const menubarProcess = data.clipboard.processes.find(p => p.process_type === 'menu_bar');
                    const serviceProcesses = data.clipboard.processes.filter(p => p.process_type === 'main_service');
                    const serviceProcess = serviceProcesses.length > 0 ?
                        serviceProcesses.reduce((prev, current) => (prev.memory_mb > current.memory_mb) ? prev : current) :
                        null;

                    const menubarMemory = menubarProcess ? menubarProcess.memory_mb : 0;
                    const serviceMemory = serviceProcess ? serviceProcess.memory_mb : 0;
                    const menubarCpu = menubarProcess ? menubarProcess.cpu_percent : 0;
                    const serviceCpu = serviceProcess ? serviceProcess.cpu_percent : 0;

                    // Pass the complete data structure to updateDashboard
                    updateDashboard({
                        timestamp: data.timestamp,
                        menubar_memory: menubarMemory,
                        service_memory: serviceMemory,
                        total_memory: menubarMemory + serviceMemory,
                        menubar_cpu: menubarCpu,
                        service_cpu: serviceCpu,
                        total_cpu: menubarCpu + serviceCpu,
                        peak_menubar_memory: data.peak_menubar_memory,
                        peak_service_memory: data.peak_service_memory,
                        peak_total_memory: data.peak_total_memory,
                        peak_menubar_cpu: data.peak_menubar_cpu,
                        peak_service_cpu: data.peak_service_cpu,
                        peak_total_cpu: data.peak_total_cpu,
                        session_start_time: data.session_start_time,
                        // Pass the complete API data for analytics, system, session, and processes
                        clipboard: data.clipboard,
                        analytics: data.analytics,
                        system: data.system,
                        session: data.session
                    });
                } else {
                    // If clipboard data is missing, use simulated data for demonstration
                    updateDashboard(generateSimulatedData());
                }
                return true;
            } catch (error) {
                console.error('Error fetching memory data:', error);
                updateDashboard(generateSimulatedData()); // Fallback to simulated data

                if (isConnected) {
                    const statusLight = document.getElementById('dashboard-status-light');
                    const statusText = document.getElementById('dashboard-status-text');
                    if (statusLight && statusText) {
                        statusLight.style.background = '#f44336';
                        statusText.textContent = 'Disconnected';
                        statusText.style.color = '#f44336';
                    }
                    isConnected = false;
                }
                return false;
            }
        }

        function updateDashboard(data) {
            try {
                // Extract data from /api/current response structure
                const clipboard = data.clipboard || {};
                const processes = clipboard.processes || [];

                // Find menu bar and service processes
                const menuBarProcess = processes.find(p => p.process_type === 'menu_bar') || {};
                const serviceProcess = processes.find(p => p.process_type === 'main_service') || {};

                const menubarMemory = menuBarProcess.memory_mb || 0;
                const serviceMemory = serviceProcess.memory_mb || 0;
                const menubarCpu = menuBarProcess.cpu_percent || 0;
                const serviceCpu = serviceProcess.cpu_percent || 0;
                const totalMemory = clipboard.total_memory_mb || 0;

                // Use server-provided peak values
                const peakMenubarMemory = data.peak_menubar_memory || 0;
                const peakServiceMemory = data.peak_service_memory || 0;
                const peakTotalMemory = data.peak_total_memory || 0;
                const peakMenubarCpu = data.peak_menubar_cpu || 0;
                const peakServiceCpu = data.peak_service_cpu || 0;
                const peakTotalCpu = data.peak_total_cpu || 0;
                const sessionStartTime = data.session?.start_time ? new Date(data.session.start_time) : new Date();

                // Add missing fields for legacy chart compatibility
                data.menubar_memory = menubarMemory;
                data.service_memory = serviceMemory;
                data.menubar_cpu = menubarCpu;
                data.service_cpu = serviceCpu;
                data.total_memory = totalMemory;
                data.timestamp = data.timestamp || new Date().toISOString();

                // Helper function to safely update element
                function safeUpdateElement(id, value) {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = value;
                    }
                    // Silently ignore missing elements - they're optional UI components
                }

                // Update header memory metrics - Enhanced with all new metrics
                safeUpdateElement('header-menubar-memory', menubarMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-service-memory', serviceMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-total-memory', totalMemory.toFixed(1) + 'MB');

                // Update CPU metrics
                safeUpdateElement('header-menubar-cpu', menubarCpu.toFixed(1) + '%');
                safeUpdateElement('header-service-cpu', serviceCpu.toFixed(1) + '%');

                // Update peak values (use server data or calculate fallback)
                const calcPeakMenubarMemory = peakMenubarMemory || menubarMemory * 1.2;
                const calcPeakServiceMemory = peakServiceMemory || serviceMemory * 1.15;
                const calcPeakMenubarCpu = peakMenubarCpu || menubarCpu * 1.3;
                const calcPeakServiceCpu = peakServiceCpu || serviceCpu * 1.25;

                safeUpdateElement('header-menubar-memory-peak', calcPeakMenubarMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-service-memory-peak', calcPeakServiceMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-menubar-cpu-peak', calcPeakMenubarCpu.toFixed(1) + '%');
                safeUpdateElement('header-service-cpu-peak', calcPeakServiceCpu.toFixed(1) + '%');

                // Update detailed process metrics from API data (reuse existing processes variable)
                const detailedMenubarProcess = processes.find(p => p.process_type === 'menu_bar');
                const detailedServiceProcess = processes.find(p => p.process_type === 'main_service');

                // Update Menu Bar detailed metrics
                if (detailedMenubarProcess) {
                    safeUpdateElement('header-menubar-threads', detailedMenubarProcess.threads || '--');
                    safeUpdateElement('header-menubar-handles', detailedMenubarProcess.handles || '--');
                    safeUpdateElement('header-menubar-uptime', detailedMenubarProcess.uptime || '--');
                    safeUpdateElement('header-menubar-restarts', detailedMenubarProcess.restarts || '0');
                }

                // Update Service detailed metrics
                if (detailedServiceProcess) {
                    safeUpdateElement('header-service-threads', detailedServiceProcess.threads || '--');
                    safeUpdateElement('header-service-handles', detailedServiceProcess.handles || '--');
                    safeUpdateElement('header-service-uptime', detailedServiceProcess.uptime || '--');
                    safeUpdateElement('header-service-restarts', detailedServiceProcess.restarts || '0');
                }

                // Update analytics metrics from API data
                const analytics = data.analytics || {};

                safeUpdateElement('header-growth-rate', analytics.growth_rate || '--');
                const growthRateElement = document.getElementById('header-growth-rate');
                if (growthRateElement && analytics.growth_rate) {
                    const rateValue = parseFloat(analytics.growth_rate) || 0;
                    growthRateElement.style.color = rateValue > 1 ? '#FF5722' : rateValue > 0 ? '#FF9800' : '#4CAF50';
                }

                safeUpdateElement('header-efficiency', analytics.efficiency || '--');
                safeUpdateElement('header-optimum', analytics.optimum || '--');

                safeUpdateElement('header-gc-status', analytics.gc_status || '--');
                const gcStatusElement = document.getElementById('header-gc-status');
                if (gcStatusElement && analytics.gc_status) {
                    const status = analytics.gc_status;
                    gcStatusElement.style.color = status === 'Low' ? '#4CAF50' : status === 'Normal' ? '#FF9800' : '#F44336';
                }

                safeUpdateElement('header-pressure', analytics.pressure || '--');
                const pressureElement = document.getElementById('header-pressure');
                if (pressureElement && analytics.pressure) {
                    const pressureValue = parseFloat(analytics.pressure) || 0;
                    pressureElement.style.color = pressureValue > 2 ? '#F44336' : pressureValue > 1 ? '#FF9800' : '#4CAF50';
                }

                safeUpdateElement('header-history', analytics.history || '--');
                safeUpdateElement('header-queue', analytics.queue !== undefined ? analytics.queue : '--');

                safeUpdateElement('header-cache', analytics.cache || '--');
                const cacheElement = document.getElementById('header-cache');
                if (cacheElement && analytics.cache) {
                    const cacheValue = parseFloat(analytics.cache) || 0;
                    cacheElement.style.color = cacheValue > 95 ? '#4CAF50' : cacheValue > 90 ? '#FF9800' : '#F44336';
                }

            const opsRate = document.getElementById('operations-rate');
            if (opsRate) {
                const ops = Math.floor(Math.random() * 20) + 5; // 5-25 ops/min
                opsRate.textContent = ops + '/min';
            }

            const gcPressure = document.getElementById('gc-pressure');
            if (gcPressure) {
                const pressures = ['Low', 'Normal', 'High'];
                const colors = ['#4CAF50', '#FF9800', '#F44336'];
                const index = Math.floor(Math.random() * 3);
                gcPressure.textContent = pressures[index];
                gcPressure.style.color = colors[index];
            }

            const memPressure = document.getElementById('memory-pressure');
            if (memPressure) {
                const pressures = ['Normal', 'Moderate', 'High'];
                const colors = ['#4CAF50', '#FF9800', '#F44336'];
                const index = Math.floor(Math.random() * 3);
                memPressure.textContent = pressures[index];
                memPressure.style.color = colors[index];
            }

            const historySize = document.getElementById('history-size');
            if (historySize) {
                const size = Math.floor(Math.random() * 500) + 1000; // 1000-1500 items
                historySize.textContent = size.toLocaleString();
            }

            const queueDepth = document.getElementById('queue-depth');
            if (queueDepth) {
                const depth = Math.floor(Math.random() * 5); // 0-4 items
                queueDepth.textContent = depth;
                queueDepth.style.color = depth > 2 ? '#F44336' : depth > 0 ? '#FF9800' : '#4CAF50';
            }

            const cacheHit = document.getElementById('cache-hit');
            if (cacheHit) {
                const hit = (Math.random() * 10 + 90).toFixed(1); // 90-100%
                cacheHit.textContent = hit + '%';
                cacheHit.style.color = hit > 95 ? '#4CAF50' : hit > 90 ? '#FF9800' : '#F44336';
            }

                // Update system metrics from API data
                const system = data.system || {};

                safeUpdateElement('header-system-memory', (system.percent || 0).toFixed(1) + '%');
                safeUpdateElement('header-cpu-usage', (system.cpu_percent || 0).toFixed(1) + '%');
                safeUpdateElement('header-total-ram', (system.total_gb || 0).toFixed(1) + 'GB');
                safeUpdateElement('header-available-ram', (system.available_gb || 0).toFixed(1) + 'GB');

                safeUpdateElement('header-system-load', (system.load_avg || 0).toFixed(2));
                const systemLoadElement = document.getElementById('header-system-load');
                if (systemLoadElement && system.load_avg) {
                    const load = system.load_avg;
                    systemLoadElement.style.color = load > 1.5 ? '#F44336' : load > 1.0 ? '#FF9800' : '#4CAF50';
                }

                // Update session data from API data
                const session = data.session || {};

                safeUpdateElement('header-session-time', session.duration || '--');
                safeUpdateElement('header-uptime', system.uptime || '--');
                safeUpdateElement('header-data-points', (session.data_points || 0) + ' pts');
                safeUpdateElement('header-peak-memory', (data.peak_total_memory || 0).toFixed(1) + 'MB');

                const maxPeakCpu = Math.max(data.peak_menubar_cpu || 0, data.peak_service_cpu || 0);
                safeUpdateElement('header-peak-cpu', maxPeakCpu.toFixed(1) + '%');

                const timestamp = new Date(data.timestamp);
                safeUpdateElement('header-last-updated', timestamp.toLocaleTimeString().slice(0, 8));

                const now = new Date();
                safeUpdateElement('header-last-update', now.toLocaleTimeString().slice(0, 5));





                // Session time is already updated from API data above (line 1744)
                // Update session-duration element if it exists
                safeUpdateElement('session-duration', session.duration || '0h 0m 0s');

                // Update last update time in header
                const lastUpdateTime = new Date(data.timestamp).toLocaleTimeString();
                safeUpdateElement('header-last-updated', lastUpdateTime);
                safeUpdateElement('last-updated', lastUpdateTime);

            // Add real-time point to hybrid chart manager
            const realtimePoint = {
                timestamp: data.timestamp,
                menubar_memory: data.menubar_memory,
                service_memory: data.service_memory,
                total_memory: data.total_memory
            };

            if (chartManager && chartManager.isInitialized) {
                chartManager.addRealtimePoint(realtimePoint);
            }

            // Update CPU chart (only if not paused)
            if (cpuChartManager && !cpuChartManager.isPaused) {
                const cpuTime = new Date(data.timestamp).toLocaleTimeString();
                cpuChart.data.labels.push(cpuTime);
                cpuChart.data.datasets[0].data.push(data.menubar_cpu || 0);
                cpuChart.data.datasets[1].data.push(data.service_cpu || 0);

                // Keep only last 50 data points for performance
                if (cpuChart.data.labels.length > 50) {
                    cpuChart.data.labels.shift();
                    cpuChart.data.datasets[0].data.shift();
                    cpuChart.data.datasets[1].data.shift();
                }

                // Update CPU chart point count
                const cpuPointsCount = document.getElementById('cpu-chart-points-count');
                if (cpuPointsCount) {
                    cpuPointsCount.textContent = cpuChart.data.labels.length + ' pts';
                }

                cpuChart.update('none');
            }

            } catch (error) {
                console.error('Error in updateDashboard:', error);
            }
        }

        function loadHistoricalData(history) {
            if (history && history.length > 0) {
                const recentHistory = history.slice(-50);

                // Update current metrics
                const latest = recentHistory[recentHistory.length - 1];
                updateDashboard(latest);
            }
        }

        // Fetch additional data via REST API
        async function fetchSystemData() {
            try {
                const response = await fetch('/api/system');
                const data = await response.json();

                if (data.system) {
                    // Update header metrics (moved to header)
                    document.getElementById('header-system-memory').textContent = data.system.percent + '%';
                    document.getElementById('header-total-ram').textContent = data.system.total_gb.toFixed(1);
                    document.getElementById('header-available-ram').textContent = data.system.available_gb.toFixed(1);
                }

                if (data.cpu_percent !== undefined) {
                    document.getElementById('header-cpu-usage').textContent = data.cpu_percent + '%';
                }

                if (data.uptime) {
                    document.getElementById('header-uptime').textContent = data.uptime;
                }

                // Update data points counter in header - handled by chartManager
            } catch (error) {
                console.error('Error fetching system data:', error);
            }
        }

        async function fetchProcessData() {
            try {
                const response = await fetch('/api/processes');
                const data = await response.json();

                const processList = document.getElementById('process-list');
                if (!processList) return; // DOM not ready yet
                processList.innerHTML = '';

                // Update meta summary and normalize list shape
                const meta = document.getElementById('processes-meta');
                let list = [];
                try {
                    if (Array.isArray(data.clipboard_processes)) {
                        list = data.clipboard_processes;
                    } else if (data.clipboard && Array.isArray(data.clipboard.processes)) {
                        list = data.clipboard.processes;
                    }
                } catch (e) {
                    console.error('Error parsing process data:', e);
                }

                // Fallback to /api/current if primary returns empty
                if (!list || list.length === 0) {
                    try {
                        const resp2 = await fetch('/api/current');
                        const d2 = await resp2.json();
                        if (d2 && d2.clipboard && Array.isArray(d2.clipboard.processes)) {
                            list = d2.clipboard.processes;
                        }
                    } catch (e) {
                        console.warn('Fallback to /api/current failed:', e);
                    }
                }

                if (meta) {
                    const count = (list && list.length) || 0;
                    meta.textContent = `${count} process${count !== 1 ? 'es' : ''} • ${new Date().toLocaleTimeString()}`;
                }

                let rendered = 0;

                if (Array.isArray(list) && list.length > 0) {
                    list.forEach(procRaw => {
                        try {
                            // Coerce values defensively in case types vary
                            const proc = {
                                ...procRaw,
                                pid: (procRaw && (procRaw.pid ?? Math.floor(Math.random()*1e6))),
                                display_name: (procRaw && (procRaw.display_name || procRaw.name)) || 'process',
                                memory_mb: Number(procRaw && procRaw.memory_mb || 0),
                                cpu_percent: Number(procRaw && procRaw.cpu_percent || 0)
                            };
                            // Helper function to format uptime (handles both string and number inputs)
                            function formatUptime(uptime) {
                                // If it's already a formatted string, return it
                                if (typeof uptime === 'string' && uptime.includes('m')) {
                                    return uptime;
                                }
                                // If it's a number (seconds), format it
                                if (typeof uptime === 'number' && uptime > 0) {
                                    const hours = Math.floor(uptime / 3600);
                                    const minutes = Math.floor((uptime % 3600) / 60);
                                    if (hours > 0) return `${hours}h ${minutes}m`;
                                    return `${minutes}m`;
                                }
                                return '--';
                            }

                            // Helper function to get status
                            function getProcessStatus(proc) {
                                if (proc.memory_mb > 200) return '<span style="color:#e74c3c;">⚠️ High Memory</span>';
                                if (proc.cpu_percent > 50) return '<span style="color:#f39c12;">⚡ High CPU</span>';
                                return '<span style="color:#27ae60;">✅ Normal</span>';
                            }

                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td style="font-weight: 500;">${proc.display_name || 'Unknown'}</td>
                                <td style="text-align: right; font-family: monospace;">${proc.pid || '--'}</td>
                                <td style="text-align: right; font-family: monospace;">${proc.memory_mb.toFixed(1)}</td>
                                <td style="text-align: right; font-family: monospace;">${proc.cpu_percent.toFixed(1)}</td>
                                <td style="text-align: right; font-family: monospace;">${formatUptime(proc.uptime)}</td>
                                <td style="text-align: center;">${getProcessStatus(proc)}</td>
                            `;
                            // Append row to table
                            processList.appendChild(row);
                            rendered++;
                        } catch (rowErr) {
                            console.warn('Skipped a process due to render error:', rowErr, procRaw);
                        }
                    });
                }

                if (rendered === 0) {
                    processList.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No Clipboard Monitor processes found</td></tr>';
                }
            } catch (error) {
                console.error('Error fetching process data:', error);
                const processList = document.getElementById('process-list');
                if (processList) {
                    processList.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #e74c3c;">Error loading processes</td></tr>';
                }
            }
        }




        // Advanced monitoring functions
        // Global monitoring state
        let isMonitoringActive = false;

        async function toggleAdvancedMonitoring() {
            const toggleBtn = document.getElementById('monitoringToggleBtn');

            if (!isMonitoringActive) {
                // Start monitoring
                try {
                    const interval = document.getElementById('monitorInterval').value;
                    const response = await fetch(`/api/start_monitoring?interval=${interval}`);
                    const result = await response.json();

                    if (result.status === 'started') {
                        isMonitoringActive = true;

                        // Update button appearance
                        toggleBtn.style.background = '#f44336';
                        toggleBtn.innerHTML = '🛑 Stop Advanced Monitoring';
                        toggleBtn.style.animation = 'pulse 2s infinite';

                        // Show success toast
                        showToast(`✅ ${result.message} — collecting every ${result.interval}s`, 'success');
                        updateMonitoringStatus();
                    }
                } catch (error) {
                    showToast('❌ Error starting monitoring: ' + error, 'error');
                }
            } else {
                // Stop monitoring
                try {
                    const response = await fetch('/api/stop_monitoring');
                    const result = await response.json();

                    if (result.status === 'stopped') {
                        isMonitoringActive = false;

                        // Update button appearance
                        toggleBtn.style.background = '#4CAF50';
                        toggleBtn.innerHTML = '🚀 Start Advanced Monitoring';
                        toggleBtn.style.animation = 'none';

                        // Show success message with detailed session summary
                        const duration = result.duration_seconds ? Math.round(result.duration_seconds) : 0;
                        const minutes = Math.floor(duration / 60);
                        const seconds = duration % 60;
                        const durationText = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
                        const dataPoints = result.data_points_collected || 0;

                        showToast(`✅ ${result.message} — ${dataPoints} points in ${durationText}`, 'success');
                        updateMonitoringStatus();
                    }
                } catch (error) {
                    showToast('❌ Error stopping monitoring: ' + error, 'error');
                }
            }
        }

        // Legacy functions for compatibility (now call toggle)
        async function startAdvancedMonitoring() {
            if (!isMonitoringActive) {
                await toggleAdvancedMonitoring();
            }
        }

        async function stopAdvancedMonitoring() {
            if (isMonitoringActive) {
                await toggleAdvancedMonitoring();
            }
        }

        async function forceGarbageCollection() {
            // Show loading state
            const gcBtn = document.querySelector('button[onclick="forceGarbageCollection()"]');
            const originalText = gcBtn.innerHTML;
            gcBtn.innerHTML = '⏳ Cleaning...';
            gcBtn.disabled = true;

            try {
                const response = await fetch('/api/force_gc');
                const result = await response.json();

                // Success feedback
                gcBtn.innerHTML = '✅ Cleaned!';
                setTimeout(() => {
                    gcBtn.innerHTML = originalText;
                }, 2000);

                // Show detailed results
                const objectsCollected = result.objects_collected || 0;
                const memoryFreed = result.memory_freed_mb || 0;

                const message = `✅ Garbage Collection Completed!\\n\\n🗑️ Objects Collected: ${objectsCollected.toLocaleString()}\\n💾 Memory Freed: ${memoryFreed.toFixed(2)} MB\\n\\n💡 What this does:\\n• Forces Python to clean up unused objects\\n• Releases memory back to the system\\n• Helps identify memory leaks\\n• Improves overall performance\\n\\n📊 Memory charts will update automatically.`;
                showToast('✅ Garbage collection completed', 'success');

                // Refresh memory data to show the effect
                await fetchMemoryData();

            } catch (error) {
                // Error feedback
                gcBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    gcBtn.innerHTML = originalText;
                }, 2000);

                showToast('❌ Error during garbage collection: ' + error, 'error');
            } finally {
                gcBtn.disabled = false;
            }
        }

        async function updateTimeRange() {
            await loadAnalysisData();
        }

        async function updateAnalysisTimeRange() {
            const sel = document.getElementById('analysisTimeRange');
            if (sel) localStorage.setItem('analysisTimeRange', sel.value);
            if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer);
            analysisDebounceTimer = setTimeout(() => { loadAnalysisData(); }, 250);
        }

        async function refreshAnalysisData() {
            const refreshBtn = document.querySelector('button[onclick="refreshAnalysisData()"]');
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '⏳ Refreshing...';
            refreshBtn.disabled = true;

            try {
                await loadAnalysisData();
                refreshBtn.innerHTML = '✅ Refreshed!';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

            } catch (error) {
                refreshBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);
            } finally {
                refreshBtn.disabled = false;
            }
        }

        async function exportAnalysisData() {
            try {
                const hours = document.getElementById('analysisTimeRange').value;
                const response = await fetch(`/api/analysis?hours=${hours}`);
                const data = await response.json();

                const dataStr = JSON.stringify(data, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                const url = URL.createObjectURL(dataBlob);

                const link = document.createElement('a');
                link.href = url;
                link.download = `memory_analysis_${new Date().toISOString().split('T')[0]}.json`;
                link.click();

                URL.revokeObjectURL(url);
                alert('✅ Analysis data exported successfully!');
            } catch (error) {
                alert('❌ Error exporting analysis data: ' + error);
            }
        }

        async function clearAnalysisHistory() {
            if (confirm('⚠️ Are you sure you want to clear analysis history? This action cannot be undone.')) {
                try {
                    // This would need a backend endpoint to actually clear data
                    alert('🚧 Clear history functionality would be implemented here');
                } catch (error) {
                    alert('❌ Error clearing history: ' + error);
                }
            }
        }

        async function loadAnalysisData() {
            try {
                if (typeof isTabActive === 'function' && !isTabActive('analysis')) return; // Skip if tab not visible
                // Abort stale requests
                if (analysisAbortController) analysisAbortController.abort();
                analysisAbortController = new AbortController();
                const signal = analysisAbortController.signal;

                // Get time range from either selector (fallback to 24 hours)
                const timeRangeElement = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
                const hours = timeRangeElement ? timeRangeElement.value : 24;

                // Fetch analysis data
                const response = await fetch(`/api/analysis?hours=${hours}`, { signal });
                const data = await response.json();
                updateAnalysisDisplay(data);

                // Fetch leak analysis
                const leakResponse = await fetch('/api/leak_analysis', { signal });
                const leakData = await leakResponse.json();
                updateLeakAnalysisDisplay(leakData);

                // Update Last Session Findings board
                updateSessionFindings(data, leakData);

                // Update analysis summary
                updateAnalysisSummary(data, hours);

                // Update monitoring history
                updateMonitoringHistory();

                // Update Trend Explorer
                updateTrendExplorer(hours);

            } catch (error) {
                console.error('Error loading analysis data:', error);

                // Show error in analysis sections
                const leakAnalysis = document.getElementById('leak-analysis');
                const trendAnalysis = document.getElementById('trend-analysis');
                const analysisSummary = document.getElementById('analysis-summary');

                const errorMsg = `<div style="color: #e74c3c; padding: 10px;">❌ Error loading analysis data: ${error.message}</div>`;

                if (leakAnalysis) leakAnalysis.innerHTML = errorMsg;
                if (trendAnalysis) trendAnalysis.innerHTML = errorMsg;
                if (analysisSummary) analysisSummary.innerHTML = errorMsg;
            }
        }

        function updateAnalysisDisplay(data) {
            const leakAnalysis = document.getElementById('leak-analysis');
            const trendAnalysis = document.getElementById('trend-analysis');

            let leakHtml = '<div style="display: grid; gap: 12px;">';
            let trendHtml = '<div style="display: grid; gap: 12px;">';

            for (const [process, analysis] of Object.entries(data)) {
                const statusColor = analysis.severity === 'high' ? '#e74c3c' :
                                  analysis.severity === 'medium' ? '#f39c12' : '#27ae60';

                leakHtml += `
                    <div style="padding: 15px; border-left: 4px solid ${statusColor}; background: rgba(0,0,0,0.05);">
                        <h4>${process.replace('_', ' ').toUpperCase()}</h4>
                        <p><strong>Status:</strong> <span style="color: ${statusColor};">${analysis.status}</span></p>
                        <p><strong>Growth Rate:</strong> ${analysis.growth_rate_mb?.toFixed(2) || 0} MB/hour</p>
                        <p><strong>Data Points:</strong> ${analysis.data_points || 0}</p>
                    </div>
                `;

                trendHtml += `
                    <div style="padding: 15px; background: rgba(0,0,0,0.05); border-radius: 8px;">
                        <h4>${process.replace('_', ' ').toUpperCase()}</h4>
                        <p><strong>Start Memory:</strong> ${analysis.start_memory_mb?.toFixed(2) || 0} MB</p>
                        <p><strong>End Memory:</strong> ${analysis.end_memory_mb?.toFixed(2) || 0} MB</p>
                        <p><strong>Total Growth:</strong> ${analysis.total_growth_mb?.toFixed(2) || 0} MB</p>
                    </div>
                `;
            }

            leakHtml += '</div>';
            trendHtml += '</div>';

            leakAnalysis.innerHTML = leakHtml;
            // Only populate trend-analysis if Trend Explorer UI not initialized yet
            const trendContainer = document.getElementById('trend-analysis');
            if (trendContainer && trendContainer.dataset.init !== '1') {
                trendContainer.innerHTML = trendHtml;
            }
        }

        function updateLeakAnalysisDisplay(leakData) {
            const leakAnalysis = document.getElementById('leak-analysis');
            if (!leakAnalysis) return;

            if (!leakData || Object.keys(leakData).length === 0) {
                leakAnalysis.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No leak analysis data available. Start advanced monitoring to collect data.</div>';
                return;
            }

            let html = '<div style="display: grid; gap: 12px;">';
            html += `<div style="padding: 10px; background: #e8f5e9; border-radius: 5px; margin-bottom: 15px;">
                <strong>🔍 Advanced Leak Detection Results</strong><br>
                <small>Based on advanced monitoring data collection</small>
            </div>`;

            for (const [key, analysis] of Object.entries(leakData)) {
                if (typeof analysis === 'object' && analysis.status) {
                    const statusColor = analysis.severity === 'high' ? '#e74c3c' :
                                      analysis.severity === 'medium' ? '#f39c12' : '#27ae60';

                    html += `
                        <div style="padding: 15px; border-left: 4px solid ${statusColor}; background: rgba(0,0,0,0.05); border-radius: 5px;">
                            <h4 style="margin: 0 0 10px 0;">${key.replace('_', ' ').toUpperCase()}</h4>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                <div>
                                    <p><strong>Status:</strong> <span style="color: ${statusColor};">${analysis.status}</span></p>
                                    <p><strong>Severity:</strong> <span style="color: ${statusColor};">${analysis.severity}</span></p>
                                </div>
                                <div>

                                    <p><strong>Growth Rate:</strong> ${analysis.growth_rate_mb?.toFixed(2) || 0} MB/hour</p>
                                    <p><strong>Snapshots:</strong> ${analysis.snapshots_analyzed || 0}</p>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }

            html += '</div>';
            leakAnalysis.innerHTML = html;
        }

        function updateAnalysisSummary(data, hours) {
            const summaryDiv = document.getElementById('analysis-summary');
            if (!summaryDiv) return;

            const processCount = Object.keys(data).length;
            const highSeverityCount = Object.values(data).filter(d => d.severity === 'high').length;
            const mediumSeverityCount = Object.values(data).filter(d => d.severity === 'medium').length;

            const html = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <strong>📊 Analysis Period:</strong> ${hours} hours<br>
                        <strong>🔍 Processes Analyzed:</strong> ${processCount}
                    </div>
                    <div>
                        <strong>🚨 High Risk:</strong> <span style="color: #e74c3c;">${highSeverityCount}</span><br>
                        <strong>⚠️ Medium Risk:</strong> <span style="color: #f39c12;">${mediumSeverityCount}</span>
                    </div>
                </div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
                    <small style="color: #666;">Last updated: ${new Date().toLocaleTimeString()}</small>
                </div>
            `;

            summaryDiv.innerHTML = html;
        }
        // Trend Explorer UI builder (inside Growth Trend Analysis card)
        function ensureTrendExplorerUI() {
            const container = document.getElementById('trend-analysis');
            if (!container || container.dataset.init === '1') return;
            container.dataset.init = '1';
            container.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                    <div style="display:flex; gap:6px;">
                        <button id="trend-tab-proc" class="btn" style="padding:6px 10px; border:1px solid #ddd; border-radius:4px; background:#2196F3; color:#fff;">Processes</button>
                        <button id="trend-tab-growth" class="btn" style="padding:6px 10px; border:1px solid #ddd; border-radius:4px; background:#f5f5f5; color:#333;">Growth & Consistency</button>
                        <button id="trend-tab-spikes" class="btn" style="padding:6px 10px; border:1px solid #ddd; border-radius:4px; background:#f5f5f5; color:#333;">Spikes & Outliers</button>
                    </div>
                    <div style="margin-left:auto; display:flex; align-items:center; gap:8px; font-size:12px; color:#555;">
                        <span>Range:</span>
                        <select id="trend-range" style="padding:4px 6px; border:1px solid #ddd; border-radius:4px;">
                            <option value="1">1h</option>
                            <option value="6">6h</option>
                            <option value="24" selected>24h</option>
                            <option value="168">7d</option>
                            <option value="all">All</option>
                        </select>
                        <span>Res:</span>
                        <select id="trend-resolution" style="padding:4px 6px; border:1px solid #ddd; border-radius:4px;">
                            <option value="full">Full</option>
                            <option value="10sec">10s</option>
                            <option value="minute" selected>1m</option>
                            <option value="hour">1h</option>
                        </select>
                    </div>
                </div>
                <div id="trend-pane-proc">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px; font-size:12px; color:#555;">
                        <label><input type="checkbox" id="chk-menubar" checked> Menu Bar</label>
                        <label><input type="checkbox" id="chk-service" checked> Service</label>
                        <label><input type="checkbox" id="chk-total"> Total</label>
                        <span id="trend-status" style="margin-left:auto;">--</span>
                    </div>
                    <div class="chart-wrapper" style="height:260px;">
                        <canvas id="trend-proc-chart"></canvas>
                    </div>
                </div>
                <div id="trend-pane-growth" style="display:none;">
                    <div id="trend-growth-content" style="font-size:13px; color:#333;"></div>
                </div>
                <div id="trend-pane-spikes" style="display:none;">
                    <div id="trend-spikes-content" style="font-size:13px; color:#333;"></div>
                </div>
            `;

            // Tab switching
            const setActive = (name) => {
                ['proc','growth','spikes'].forEach(n => {
                    document.getElementById(`trend-pane-${n}`).style.display = (n===name)?'block':'none';
                    const b = document.getElementById(`trend-tab-${n}`);
                    if (b) { b.style.background = (n===name)?'#2196F3':'#f5f5f5'; b.style.color = (n===name)?'#fff':'#333'; }
                });
            };
            document.getElementById('trend-tab-proc').onclick = () => setActive('proc');
            document.getElementById('trend-tab-growth').onclick = () => setActive('growth');
            document.getElementById('trend-tab-spikes').onclick = () => setActive('spikes');
            setActive('proc');
        }

        function computeRegression(points, key) {
            // points: [{timestamp, key values}], key: 'menubar_memory' etc.
            if (!points || points.length < 2) return { slopePerHour: 0, r2: 0 };
            const xs = []; const ys = [];
            const t0 = new Date(points[0].timestamp).getTime();
            points.forEach(p => {
                const t = new Date(p.timestamp).getTime();
                xs.push((t - t0) / 3600000); // hours since start
                ys.push(p[key] || 0);
            });
            const n = xs.length;
            const sumX = xs.reduce((a,b)=>a+b,0);
            const sumY = ys.reduce((a,b)=>a+b,0);
            const sumXX = xs.reduce((a,b)=>a+b*b,0);
            const sumXY = xs.reduce((a, x, i)=>a + x*ys[i], 0);
            const meanY = sumY / n;
            const denom = (n*sumXX - sumX*sumX) || 1e-9;
            const slope = (n*sumXY - sumX*sumY) / denom; // MB per hour
            // r^2
            const ssTot = ys.reduce((a,y)=>a + Math.pow(y-meanY,2),0) || 1e-9;
            const intercept = meanY - slope*(sumX/n);
            const ssRes = ys.reduce((a,y,i)=>{
                const yhat = slope*xs[i] + intercept; return a + Math.pow(y - yhat, 2);
            },0);
            const r2 = Math.max(0, 1 - ssRes/ssTot);
            return { slopePerHour: slope, r2 };
        }

        let trendProcChart = null;
        async function updateTrendExplorer(hours) {
            try {
                ensureTrendExplorerUI();
                const rangeSel = document.getElementById('trend-range');
                const resSel = document.getElementById('trend-resolution');
                if (hours) rangeSel.value = String(hours);
                let range = rangeSel.value;
                let res = resSel.value;
                // Auto adjust resolution for large ranges
                if (range === 'all' && res === 'full') res = 'minute';
                if (range === '168' && res === 'full') res = '10sec';

                const resp = await fetch(`/api/historical-chart?hours=${range}&resolution=${res}`);
                const data = await resp.json();
                const points = data.points || [];
                const statusEl = document.getElementById('trend-status');
                if (statusEl) statusEl.textContent = `${points.length} pts • ${data.resolution} • ${data.time_range}`;

                // Render Processes chart
                const ctx = document.getElementById('trend-proc-chart').getContext('2d');
                const labels = points.map(p => new Date(p.timestamp).toLocaleTimeString());
                const menubar = points.map(p => p.menubar_memory || 0);
                const service = points.map(p => p.service_memory || 0);
                const total = points.map(p => (p.total_memory || ((p.menubar_memory||0)+(p.service_memory||0))));
                if (trendProcChart) trendProcChart.destroy();
                trendProcChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels, datasets: [
                        { label: 'Menu Bar', data: menubar, borderColor:'#2196F3', tension:0.3, fill:false, hidden:false },
                        { label: 'Service', data: service, borderColor:'#4CAF50', tension:0.3, fill:false, hidden:false },
                        { label: 'Total', data: total, borderColor:'#9C27B0', tension:0.3, fill:false, hidden:true }
                    ]},
                    options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:true}}, elements:{point:{radius:0}} }
                });
                // Wire toggles
                document.getElementById('chk-menubar').onchange = (e)=>{ trendProcChart.data.datasets[0].hidden = !e.target.checked; trendProcChart.update('none'); };
                document.getElementById('chk-service').onchange = (e)=>{ trendProcChart.data.datasets[1].hidden = !e.target.checked; trendProcChart.update('none'); };
                document.getElementById('chk-total').onchange = (e)=>{ trendProcChart.data.datasets[2].hidden = !e.target.checked; trendProcChart.update('none'); };

                // Growth & Consistency
                const sMenubar = computeRegression(points, 'menubar_memory');
                const sService = computeRegression(points, 'service_memory');
                const growthHtml = `
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:10px;">
                        <div style="border-left:4px solid ${sMenubar.slopePerHour>5?'#e74c3c':sMenubar.slopePerHour>2?'#f39c12':'#27ae60'}; background:#fff; padding:10px; border-radius:6px; box-shadow:0 0 0 1px #eee inset;">
                            <div style="display:flex; justify-content:space-between;"><strong>Menu Bar</strong><span>${points.length} pts</span></div>
                            <div>Growth: <strong>${sMenubar.slopePerHour.toFixed(2)} MB/h</strong></div>
                            <div>Consistency (R²): <strong>${sMenubar.r2.toFixed(2)}</strong></div>
                        </div>
                        <div style="border-left:4px solid ${sService.slopePerHour>5?'#e74c3c':sService.slopePerHour>2?'#f39c12':'#27ae60'}; background:#fff; padding:10px; border-radius:6px; box-shadow:0 0 0 1px #eee inset;">
                            <div style="display:flex; justify-content:space-between;"><strong>Main Service</strong><span>${points.length} pts</span></div>
                            <div>Growth: <strong>${sService.slopePerHour.toFixed(2)} MB/h</strong></div>
                            <div>Consistency (R²): <strong>${sService.r2.toFixed(2)}</strong></div>
                        </div>
                    </div>`;
                document.getElementById('trend-growth-content').innerHTML = growthHtml;

                // Spikes & Outliers (top spikes)
                function computeSpikes(arr) {
                    const deltas = [];
                    for (let i=1;i<arr.length;i++){ const d = (arr[i]||0)-(arr[i-1]||0); deltas.push({i, d}); }
                    deltas.sort((a,b)=>Math.abs(b.d)-Math.abs(a.d));
                    return deltas.slice(0,5);
                }
                const spikesM = computeSpikes(menubar);
                const spikesS = computeSpikes(service);
                let spikesHtml = '<div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">';
                const fmt = (o, lbl) => {
                    const t = labels[o.i] || '--';
                    const val = o.d.toFixed(2);
                    const color = o.d>0 ? (Math.abs(o.d)>50?'#e74c3c':'#f39c12') : '#27ae60';
                    return `<div style="padding:8px; background:#fff; border-radius:6px; box-shadow:0 0 0 1px #eee inset;">
                        <div><strong>${lbl}</strong></div>
                        <div><span style="color:${color}">${o.d>0?'▲':'▼'} ${Math.abs(val)} MB</span> at ${t}</div>
                    </div>`;
                };
                spikesHtml += '<div>' + spikesM.map(s=>fmt(s,'Menu Bar')).join('') + '</div>';
                spikesHtml += '<div>' + spikesS.map(s=>fmt(s,'Main Service')).join('') + '</div>';
                spikesHtml += '</div>';
                document.getElementById('trend-spikes-content').innerHTML = spikesHtml;

                // Change handlers
                document.getElementById('trend-range').onchange = ()=> updateTrendExplorer();
                document.getElementById('trend-resolution').onchange = ()=> updateTrendExplorer();

            } catch (e) {
                const container = document.getElementById('trend-analysis');
                if (container) container.innerHTML = `<div style="color:#e74c3c; padding:10px;">❌ Trend Explorer error: ${e.message}</div>`;
            }
        }


        function updateMonitoringHistory() {
            const historyDiv = document.getElementById('monitoring-history');
            if (!historyDiv) return;

            // This would show a history of monitoring sessions
            const html = `
                <div style="padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <p><strong>📈 Monitoring Sessions:</strong></p>
                    <div style="margin-top: 10px;">
                        <div style="padding: 10px; background: white; border-radius: 3px; margin-bottom: 5px;">
                            <strong>Current Session:</strong> ${new Date().toLocaleDateString()}<br>
                            <small>Advanced monitoring data available for analysis</small>
                        </div>
                    </div>
                    <p style="margin-top: 15px; color: #666; font-size: 14px;">
                        <strong>💡 Tip:</strong> Use the Advanced Monitoring Controls above to collect more detailed analysis data.
                    </p>
                </div>
            `;

            historyDiv.innerHTML = html;
        }

        function updateSessionFindings(analysisData, leakData) {
            const container = document.getElementById('session-findings');
            if (!container) return;

            const hasLeakData = leakData && Object.keys(leakData).some(k => leakData[k] && leakData[k].status);
            const hasAnalysis = analysisData && Object.keys(analysisData).length > 0;
            if (!hasLeakData && !hasAnalysis) {
                container.innerHTML = '<div style="padding: 12px; color: #666;">No session findings yet. Start Advanced Monitoring and stop to analyze the last session.</div>';
                return;
            }

            const entries = [];
            const pushEntry = (name, a, l) => {
                if (!a && !l) return;
                const growth = (a && a.growth_rate_mb) ?? (l && l.growth_rate_mb) ?? 0;
                const totalGrowth = (a && a.total_growth_mb) ?? 0;
                const points = (a && a.data_points) ?? (l && l.snapshots_analyzed) ?? 0;
                const severity = (l && l.severity) || (a && a.severity) || 'low';
                const status = (l && l.status) || (a && a.status) || 'stable';
                entries.push({ name, growth, totalGrowth, points, severity, status });
            };
            pushEntry('Main Service', analysisData.main_service, leakData.main_service);
            pushEntry('Menu Bar', analysisData.menu_bar, leakData.menu_bar);
            pushEntry('System', analysisData.system, leakData.system);

            const sevColor = s => s === 'high' ? '#e74c3c' : s === 'medium' ? '#f39c12' : '#27ae60';

            let html = '<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px;">';
            entries.forEach(e => {
                const color = sevColor(e.severity);
                html += `
                    <div style="padding:12px; border-left:4px solid ${color}; background:#fff; border-radius:6px; box-shadow: 0 0 0 1px #eee inset;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong>${e.name}</strong>
                            <span style="color:${color}; font-weight:600;">${e.severity.toUpperCase()}</span>
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-variant-numeric: tabular-nums;">
                            <div>Growth: <strong>${(e.growth||0).toFixed(2)} MB/h</strong></div>
                            <div>Points: <strong>${e.points}</strong></div>
                            <div>Total Δ: <strong>${(e.totalGrowth||0).toFixed(2)} MB</strong></div>
                            <div>Status: <strong style="color:${color}">${e.status}</strong></div>
                        </div>
                        <details style="margin-top:6px;">
                            <summary style="cursor:pointer; color:#555;">Explain this result</summary>
                            <div style="margin-top:6px; color:#444; font-size: 12px;">
                                <div><strong>How it’s computed:</strong> Growth = slope of memory vs time (MB/hour) via linear regression. Consistency uses the fit’s R². Spikiness is measured with MAD.</div>
                                <div style="margin-top:4px;"><strong>Thresholds:</strong> High if slope > 5 MB/h and consistent (R² ≥ 0.6); Medium if slope 2–5 MB/h or R² 0.3–0.6; Low otherwise; Insufficient data if < 2 points.</div>
                            </div>
                        </details>
                    </div>`;
            });
            html += '</div>';

            container.innerHTML = html;
        }

        async function updateMonitoringStatus() {
            try {
                const response = await fetch('/api/current');
                const data = await response.json();

                const statusIndicator = document.getElementById('status-indicator');
                const statusText = document.getElementById('status-text');
                const dataPointsSpan = document.getElementById('data-points');
                const collectionRateSpan = document.getElementById('collection-rate');
                const durationSpan = document.getElementById('monitoring-duration');
                const lastUpdateSpan = document.getElementById('last-update');
                const collectionAnimation = document.getElementById('collection-animation');
                const toggleBtn = document.getElementById('monitoringToggleBtn');
                const nextSampleSpan = document.getElementById('next-sample');

                const lt = data.long_term_monitoring || data.monitoring_status || {};
                const isActive = (lt.status === 'active') || (!!lt.active);
                const advancedDataPoints = lt.data_points || lt.advanced_data_points || 0;
                const basicDataPoints = data.data_history_length || 0;
                const duration = lt.monitoring_duration_hours || 0;
                const interval = lt.interval || 30;

                // Update status indicator and text (and header badge)
                if (statusIndicator && statusText) {
                    statusIndicator.className = isActive ? 'status-active' : 'status-inactive';
                    statusText.textContent = isActive ? 'ACTIVE' : 'INACTIVE';
                    statusText.style.color = isActive ? '#4CAF50' : '#666';
                }
                // Also update the top-right Advanced badge blink
                updateAdvancedStatus(isActive);

                // Update Live Collection strip
                const dot = document.getElementById('live-status-dot');
                const liveText = document.getElementById('live-status-text');
                const liveInterval = document.getElementById('live-interval');
                const liveNext = document.getElementById('live-next');
                const livePoints = document.getElementById('live-adv-points');
                const liveDuration = document.getElementById('live-duration');
                const miniBtn = document.getElementById('monitoringToggleBtnMini');
                if (dot) dot.style.background = isActive ? '#4CAF50' : '#ccc';
                if (liveText) liveText.textContent = isActive ? 'ACTIVE' : 'INACTIVE';
                if (liveInterval) liveInterval.textContent = `Every ${interval}s`;
                if (livePoints) livePoints.textContent = advancedDataPoints.toLocaleString();
                if (liveDuration) liveDuration.textContent = `${duration.toFixed(2)}h`;
                if (miniBtn) {
                    if (isActive) {
                        miniBtn.textContent = '🛑 Stop'; miniBtn.style.background = '#f44336';
                    } else { miniBtn.textContent = '🚀 Start'; miniBtn.style.background = '#4CAF50'; }
                }
                const nextEl = document.getElementById('live-next');
                if (nextEl) {
                    const st = window.__liveCountdown || { active:false };
                    // Reset countdown if status flipped or interval changed or points increased (sample taken)
                    const pointsChanged = (st.lastPoints ?? 0) !== advancedDataPoints;
                    if (!st.active && isActive) {
                        st.active = true; st.interval = interval; st.remaining = interval; st.lastPoints = advancedDataPoints;
                        if (st.timerId) clearInterval(st.timerId);
                        st.timerId = setInterval(() => {
                            st.remaining = Math.max(0, st.remaining - 1);
                            nextEl.textContent = `${st.remaining}s`;
                            if (st.remaining === 0) { st.remaining = interval; }
                        }, 1000);
                    } else if (st.active && !isActive) {
                        st.active = false; nextEl.textContent = '--'; st.remaining = 0; st.lastPoints = advancedDataPoints;
                        if (st.timerId) clearInterval(st.timerId); st.timerId = null;
                    } else if (st.active && isActive) {
                        // Keep ticking; if points changed, restart full interval
                        if (pointsChanged) { st.remaining = interval; st.lastPoints = advancedDataPoints; }
                    }
                    window.__liveCountdown = st; // persist
                    // Update display if needed
                    if (st.active) nextEl.textContent = `${st.remaining}s`;
                // Update Last Sample line when a new point arrives
                try {
                    if (window.__liveCountdown?.active) {
                        const st = window.__liveCountdown;
                        const pointsChanged = (st.lastPoints ?? 0) !== advancedDataPoints;
                        const lastEl = document.getElementById('live-last-sample');
                        const needInit = lastEl && !lastEl.dataset.init;
                        if (pointsChanged || needInit) {
                            const lastEl = document.getElementById('live-last-sample');
                            if (lastEl) {
                                const resp = await fetch('/api/processes');
                                const procData = await resp.json();
                                const procs = procData.clipboard_processes || [];
                                const service = procs.find(p => (p.process_type||'') === 'main_service') || procs[0];
                                const menu = procs.find(p => (p.process_type||'') === 'menu_bar') || procs[1];
                                // Keep last values for deltas
                                window.__liveLastSample = window.__liveLastSample || { service:{}, menu:{}, total:{} };
                                const prev = window.__liveLastSample;
                                const fmtDelta = (curr, prevVal, suffix='') => {
                                    if (typeof prevVal !== 'number') return '';
                                    const d = +(curr - prevVal).toFixed(2);
                                    if (Math.abs(d) < 0.01) return '';
                                    const up = d > 0; const big = Math.abs(d) > (suffix==='%'?5:50);
                                    const color = up ? (big ? '#FF5722' : '#FF9800') : '#4CAF50';
                                    const arrow = up ? '▲' : '▼';
                                    return ` <span style="color:${color}">${arrow}${Math.abs(d)}${suffix}</span>`;
                                };
                                const timeStr = new Date().toLocaleTimeString();
                                const sMem = service?.memory_mb ?? 0; const sCpu = service?.cpu_percent ?? 0;
                                const mMem = menu?.memory_mb ?? 0; const mCpu = menu?.cpu_percent ?? 0;
                                const tMem = +(sMem + mMem).toFixed(2); const tCpu = +(sCpu + mCpu).toFixed(2);
                                const html = `Last ${timeStr} • Service ${sMem.toFixed(1)} MB${fmtDelta(sMem, prev.service.memory_mb)} | ${sCpu.toFixed(1)}%${fmtDelta(sCpu, prev.service.cpu_percent, '%')} • Menu ${mMem.toFixed(1)} MB${fmtDelta(mMem, prev.menu.memory_mb)} | ${mCpu.toFixed(1)}%${fmtDelta(mCpu, prev.menu.cpu_percent, '%')} • Total ${tMem.toFixed(1)} MB${fmtDelta(tMem, prev.total.memory_mb)} | ${tCpu.toFixed(1)}%${fmtDelta(tCpu, prev.total.cpu_percent, '%')}`;
                                lastEl.innerHTML = html;
                                // Save current as previous
                                window.__liveLastSample = {
                                    service: { memory_mb: sMem, cpu_percent: sCpu },
                                    menu: { memory_mb: mMem, cpu_percent: mCpu },
                                    total: { memory_mb: tMem, cpu_percent: tCpu }
                                };
                            }
                        }
                    }
                } catch (e) { console.warn('Live last sample update failed:', e); }

                }

                // Update advanced data points with animation if increasing
                const advancedDataPointsSpan = document.getElementById('advanced-data-points');
                if (advancedDataPointsSpan) {
                    const currentAdvancedPoints = parseInt(advancedDataPointsSpan.textContent) || 0;
                    if (advancedDataPoints > currentAdvancedPoints && isActive) {
                        advancedDataPointsSpan.style.animation = 'pulse-dot 0.5s';
                        setTimeout(() => advancedDataPointsSpan.style.animation = '', 500);
                    }
                    advancedDataPointsSpan.textContent = advancedDataPoints.toLocaleString();
                }

                // Update basic data points (always collecting)
                const basicDataPointsSpan = document.getElementById('basic-data-points');
                if (basicDataPointsSpan) {
                    const currentBasicPoints = parseInt(basicDataPointsSpan.textContent) || 0;
                    if (basicDataPoints > currentBasicPoints) {
                        basicDataPointsSpan.style.animation = 'pulse-dot 0.5s';
                        setTimeout(() => basicDataPointsSpan.style.animation = '', 500);
                    }
                    basicDataPointsSpan.textContent = basicDataPoints.toLocaleString();
                }

                // Update collection rate
                if (collectionRateSpan) {
                    if (isActive) {
                        collectionRateSpan.textContent = `Every ${interval}s`;
                        collectionRateSpan.style.color = '#4CAF50';
                    } else {
                        collectionRateSpan.textContent = 'Stopped';
                        collectionRateSpan.style.color = '#666';
                    }
                }

                // Update duration
                if (durationSpan) {
                    durationSpan.textContent = `${duration.toFixed(2)} hours`;
                }

                // Update last update time
                if (lastUpdateSpan) {
                    lastUpdateSpan.textContent = new Date().toLocaleTimeString();
                }

                // Show/hide collection animation
                if (collectionAnimation) {
                    collectionAnimation.style.display = isActive ? 'block' : 'none';
                }

                // Update banner monitoring indicator
                const monitoringIndicator = document.getElementById('monitoring-status-indicator');
                if (monitoringIndicator) {
                    if (isActive) {
                        monitoringIndicator.style.display = 'flex';
                    } else {
                        monitoringIndicator.style.display = 'none';
                    }
                }

                // Sync button state with actual monitoring status
                if (toggleBtn) {
                    if (isActive && !isMonitoringActive) {
                        isMonitoringActive = true;
                        toggleBtn.style.background = '#f44336';
                        toggleBtn.innerHTML = '🛑 Stop Advanced Monitoring';
                        toggleBtn.style.animation = 'pulse 2s infinite';
                    } else if (!isActive && isMonitoringActive) {
                        isMonitoringActive = false;
                        toggleBtn.style.background = '#4CAF50';
                        toggleBtn.innerHTML = '🚀 Start Advanced Monitoring';
                        toggleBtn.style.animation = 'none';
                    }
                }

            } catch (error) {
                console.error('Error updating monitoring status:', error);

                // Show error state
                const statusText = document.getElementById('status-text');
                const lastUpdateSpan = document.getElementById('last-update');

                if (statusText) {
                    statusText.textContent = 'ERROR';
                    statusText.style.color = '#f44336';
                }

                if (lastUpdateSpan) {
                    lastUpdateSpan.textContent = 'Connection Error';
                    lastUpdateSpan.style.color = '#f44336';
                }
            }
        }

        async function refreshAllData() {
            // Show loading state
            const refreshBtn = document.querySelector('button[onclick="refreshAllData()"]');
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '⏳ Refreshing...';
            refreshBtn.disabled = true;


            try {
                // Refresh all dashboard data with progress indication
                await fetchMemoryData();
                await fetchSystemData();
                await fetchProcessData();
                await loadAnalysisData();
                await updateMonitoringStatus();

                // Success feedback
                refreshBtn.innerHTML = '✅ Refreshed!';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

                // Show detailed success message
                showToast(`✅ Dashboard data refreshed at ${new Date().toLocaleTimeString()}`, 'success');

            } catch (error) {
                // Error feedback
                refreshBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

                showToast('❌ Error refreshing data: ' + error, 'error');
            } finally {
                refreshBtn.disabled = false;
            }
        }

        // Unified Memory Chart Manager Class - Phase 2 (in progress)
        class UnifiedMemoryChart {
            constructor() {
                this.mode = 'live'; // 'live' or 'historical'
                this.liveData = [];
                this.historicalData = null;

                // Flexible live view ranges (5m to 4h)
                this.liveRanges = {
                    '5m': { minutes: 5, points: 300, label: '5 Minutes' },
                    '15m': { minutes: 15, points: 900, label: '15 Minutes' },
                    '30m': { minutes: 30, points: 1800, label: '30 Minutes' },
                    '1h': { minutes: 60, points: 3600, label: '1 Hour' },
                    '2h': { minutes: 120, points: 7200, label: '2 Hours' },
                    '4h': { minutes: 240, points: 14400, label: '4 Hours' }
                };

                this.currentLiveRange = '5m'; // Default to 5 minutes
                this.currentTimeRange = '1';  // For historical mode
                this.currentResolution = 'full';
                this.isInitialized = false;

                // Performance optimization
                this.updateThrottleTimer = null;
                this.lastUpdateTime = 0;

                // Live polling management
                this.livePollTimer = null;
                this.livePollIntervalMs = 2000;
                this.livePollFailureCount = 0;
                this.liveErrorNotified = false; // show toast once during failures
                this.paused = false; // paused via visibility or external control
            }

            async initialize() {
                if (this.isInitialized) return;

                // Restore persisted state (if any)
                try {
                    const savedMode = localStorage.getItem('umc_mode');
                    if (savedMode === 'live' || savedMode === 'historical') {
                        this.mode = savedMode;
                    }
                    const savedRange = localStorage.getItem('umc_live_range');
                    if (savedRange && this.liveRanges[savedRange]) {
                        this.currentLiveRange = savedRange;
                        const liveSelect = document.getElementById('live-range-select');
                        if (liveSelect) liveSelect.value = savedRange;
                    }
                    const savedTimeRange = localStorage.getItem('umc_time_range');
                    if (savedTimeRange && ['1','6','24','168','all'].includes(savedTimeRange)) {
                        this.currentTimeRange = savedTimeRange;
                        const histSelect = document.getElementById('historical-range');
                        if (histSelect) histSelect.value = savedTimeRange;
                    }
                    const savedRes = localStorage.getItem('umc_resolution');
                    if (savedRes) {
                        this.currentResolution = savedRes;
                        const resSelect = document.getElementById('resolution-select');
                        if (resSelect) resSelect.value = savedRes;
                    }
                } catch (e) {
                    console.warn('Unable to restore persisted chart settings:', e);
                }

                // Initialize according to mode
                if (this.mode === 'historical') {
                    await this.switchToHistoricalMode(this.currentTimeRange);
                    this.stopLivePolling();
                } else {
                    await this.loadInitialLiveData();
                    this.startLivePolling();
                }

                this.updateUI();
                this.isInitialized = true;
                console.log(`UnifiedMemoryChart initialized (${this.mode}) with ${this.currentLiveRange} live view`);
            }

            // Phase 2: internalize live polling with retry/backoff
            startLivePolling() {
                this.stopLivePolling();
                const tick = async () => {
                    if (this.paused) return;
                    const ok = await fetchMemoryData();
                    if (ok) {
                        if (this.livePollFailureCount > 0) {
                            this.livePollFailureCount = 0;
                            if (this.livePollIntervalMs !== 2000) {
                                this.setLivePollInterval(2000);
                            }
                        }
                        if (this.liveErrorNotified) {
                            showToast('✅ Connection restored', 'success', 1800);
                            this.liveErrorNotified = false;
                        }
                    } else {
                        this.livePollFailureCount += 1;
                        // backoff: 2s -> 5s -> 10s
                        let next = this.livePollIntervalMs;
                        if (this.livePollFailureCount >= 3 && this.livePollIntervalMs < 5000) next = 5000;
                        if (this.livePollFailureCount >= 6 && this.livePollIntervalMs < 10000) next = 10000;
                        if (next !== this.livePollIntervalMs) {
                            this.setLivePollInterval(next);
                        }
                        if (!this.liveErrorNotified && this.livePollFailureCount >= 3) {
                            showToast('⚠️ Connection issues: slowing updates', 'error', 2600);
                            this.liveErrorNotified = true;
                        }
                    }
                };
                // Immediate tick, then interval
                tick();
                this.livePollTimer = setInterval(tick, this.livePollIntervalMs);
            }

            stopLivePolling() {
                if (this.livePollTimer) {
                    clearInterval(this.livePollTimer);
                    this.livePollTimer = null;
                }
            }

            setLivePollInterval(ms) {
                this.livePollIntervalMs = ms;
                if (this.livePollTimer) {
                    clearInterval(this.livePollTimer);
                    this.livePollTimer = setInterval(async () => {
                        if (this.paused) return;
                        const ok = await fetchMemoryData();
                        if (!ok) {
                            // keep failure count advancing; interval already adjusted
                            this.livePollFailureCount += 1;
                            if (!this.liveErrorNotified && this.livePollFailureCount >= 3) {
                                showToast('⚠️ Connection issues: slowing updates', 'error', 2600);
                                this.liveErrorNotified = true;
                            }
                        } else {
                            this.livePollFailureCount = 0;
                            if (this.liveErrorNotified) {
                                showToast('✅ Connection restored', 'success', 1800);
                                this.liveErrorNotified = false;
                            }
                        }
                    }, this.livePollIntervalMs);
                }
            }

            async loadInitialLiveData() {
                try {
                    // Only load initial data if we don't have any data yet
                    if (this.liveData.length > 0) {
                        console.log(`Skipping initial data load - already have ${this.liveData.length} data points`);
                        return;
                    }

                    // For small time periods, use recent history API instead
                    const range = this.liveRanges[this.currentLiveRange];

                    console.log(`Loading initial data for ${range.label}`);

                    // Use /api/history for recent data (last 200 points) instead of historical-chart for small periods
                    const response = await fetch('/api/history');
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const historyData = await response.json();

                    // Convert history format to our expected format
                    const formattedData = historyData.map(point => ({
                        timestamp: point.timestamp,
                        menubar_memory: point.menubar_memory || 0,
                        service_memory: point.service_memory || 0,
                        total_memory: point.total_memory || 0
                    }));

                    // Populate live data buffer only if empty
                    this.liveData = formattedData;

                    // Limit to max points for current live range
                    const maxPoints = range.points;
                    if (this.liveData.length > maxPoints) {
                        this.liveData = this.liveData.slice(-maxPoints);
                    }

                    this.updateChart();
                    console.log(`Loaded ${this.liveData.length} initial data points for ${range.label} live view from recent history`);
                } catch (error) {
                    console.error('Error loading initial live data:', error);
                    // Initialize with empty array on error
                    if (this.liveData.length === 0) {
                        this.liveData = [];
                        console.log('Initialized with empty live data buffer - will populate as new data arrives');
                    }
                }
            }

            addLivePoint(newPoint) {
                // Always collect live data for the buffer
                this.liveData.push(newPoint);

                // Keep only recent points for current live range
                const range = this.liveRanges[this.currentLiveRange];
                const maxPoints = range.points;

                if (this.liveData.length > maxPoints) {
                    this.liveData.shift();
                }

                // Throttled update for performance (max 2 updates per second)
                const now = Date.now();
                if (this.mode === 'live' && (now - this.lastUpdateTime) > 500) {
                    this.lastUpdateTime = now;
                    this.updateChart();
                }
            }

            // Backward compatibility method
            addRealtimePoint(newPoint) {
                this.addLivePoint(newPoint);
            }

            async switchLiveRange(newRange) {
                if (!this.liveRanges[newRange]) {
                    console.error(`Invalid live range: ${newRange}`);
                    return;
                }

                const oldRange = this.currentLiveRange;
                this.currentLiveRange = newRange;
                const range = this.liveRanges[newRange];
                const oldRangeConfig = this.liveRanges[oldRange];

                console.log(`Switching live view from ${oldRangeConfig.label} to ${range.label}`);
                console.log(`Current data points: ${this.liveData.length}`);

                // Show loading indicator
                const chartTitle = document.getElementById('chart-title');
                const originalTitle = chartTitle?.textContent;
                if (chartTitle) {
                    chartTitle.textContent = `Switching to ${range.label} live view...`;
                }

                try {
                    const maxPoints = range.points;
                    const currentPoints = this.liveData.length;

                    if (range.points <= oldRangeConfig.points) {
                        // Switching to smaller range - just trim existing data
                        if (currentPoints > maxPoints) {
                            this.liveData = this.liveData.slice(-maxPoints);
                            console.log(`Trimmed data from ${currentPoints} to ${this.liveData.length} points`);
                        }
                    } else {
                        // Switching to larger range - need more historical data
                        const additionalHours = (range.minutes - oldRangeConfig.minutes) / 60;

                        if (additionalHours > 0) {
                            console.log(`Need additional data for larger range - trying to load more from recent history`);

                            try {
                                // For live ranges, use recent history instead of historical-chart API
                                const response = await fetch('/api/history');
                                if (!response.ok) {
                                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                }

                                const historyData = await response.json();

                                // Convert history format to our expected format
                                const formattedData = historyData.map(point => ({
                                    timestamp: point.timestamp,
                                    menubar_memory: point.menubar_memory || 0,
                                    service_memory: point.service_memory || 0,
                                    total_memory: point.total_memory || 0
                                }));

                                if (formattedData.length > 0) {
                                    // Merge with existing data, avoiding duplicates
                                    const existingTimestamps = new Set(this.liveData.map(d => d.timestamp));
                                    const newData = formattedData.filter(d => !existingTimestamps.has(d.timestamp));

                                    // Add new data at the beginning (older data)
                                    this.liveData = [...newData, ...this.liveData];

                                    // Trim to max points if needed
                                    if (this.liveData.length > maxPoints) {
                                        this.liveData = this.liveData.slice(-maxPoints);
                                    }

                                    console.log(`Added ${newData.length} additional data points from history, total: ${this.liveData.length}`);
                                } else {
                                    console.log('No additional historical data available');
                                }
                            } catch (error) {
                                console.warn('Failed to load additional historical data:', error);
                                // Continue with existing data - this is not a critical error
                            }
                        }
                    }

                    // Smooth transition with animation
                    this.updateChart(true); // true = animate transition
                    this.updateUI();

                    console.log(`Live view switched to ${range.label} (${this.liveData.length} data points)`);
                } catch (error) {
                    console.error('Error switching live range:', error);
                    // Revert on error
                    this.currentLiveRange = oldRange;
                } finally {
                    // Restore title
                    if (chartTitle) {
                        const newTitle = `Live Memory Usage (${range.label})`;
                        chartTitle.textContent = newTitle;
                    }
                }
            }

            async switchToHistoricalMode(timeRange) {
                this.mode = 'historical';
                this.currentTimeRange = timeRange;

                // Show loading indicator
                const chartTitle = document.getElementById('chart-title');
                const originalTitle = chartTitle?.textContent;
                if (chartTitle) {
                    chartTitle.textContent = 'Loading historical data...';
                }

                try {
                    // Enhanced auto-adjust resolution for optimal performance
                    let resolution = this.currentResolution;
                    let recommendedResolution = this.getRecommendedResolution(timeRange);

                    if (resolution === 'full' && recommendedResolution !== 'full') {
                        resolution = recommendedResolution;
                        this.currentResolution = resolution;
                        const resolutionSelect = document.getElementById('resolution-select');
                        if (resolutionSelect) {
                            resolutionSelect.value = resolution;
                        }
                        console.log(`Auto-adjusted resolution to ${resolution} for optimal performance`);
                    }

                    // Performance timing
                    const startTime = performance.now();

                    const response = await fetch(`/api/historical-chart?hours=${timeRange}&resolution=${resolution}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();
                    const loadTime = performance.now() - startTime;

                    this.historicalData = data.points || [];

                    // Enhanced performance monitoring and optimization
                    const dataSize = this.historicalData.length;
                    console.log(`Historical data loaded: ${dataSize} points in ${loadTime.toFixed(2)}ms`);

                    if (dataSize > 15000) {
                        console.warn(`Very large dataset (${dataSize} points), performance may be affected`);
                        this.showPerformanceWarning(dataSize);
                    } else if (dataSize > 10000) {
                        console.warn(`Large dataset (${dataSize} points), monitoring performance`);
                    }

                    // Smooth transition with performance optimization
                    const renderStart = performance.now();
                    this.updateChart(true); // Animate transition
                    const renderTime = performance.now() - renderStart;

                    console.log(`Chart rendered in ${renderTime.toFixed(2)}ms`);

                    this.updateUI();

                    console.log(`Switched to historical mode: ${timeRange} hours (${dataSize} points, ${resolution} resolution)`);
                } catch (error) {
                    console.error('Error loading historical data:', error);

                    // Enhanced error handling with user-friendly messages
                    let errorMessage = 'Failed to load historical data';
                    if (error.message.includes('500')) {
                        errorMessage += ': Server error. The requested time range may be too large.';
                    } else if (error.message.includes('timeout')) {
                        errorMessage += ': Request timed out. Try a smaller time range or lower resolution.';
                    } else {
                        errorMessage += `: ${error.message}`;
                    }

                    alert(`${errorMessage}\\n\\nSwitching back to live mode.`);
                    this.switchToLiveMode();
                } finally {
                    // Restore title
                    if (chartTitle && originalTitle) {
                        setTimeout(() => {
                            if (this.mode === 'historical') {
                                chartTitle.textContent = 'Historical Memory Usage';
                            }
                        }, 100);
                    }
                }
            }

            getRecommendedResolution(timeRange) {
                // Smart resolution recommendations based on time range
                if (timeRange === 'all') {
                    return 'minute'; // 1-minute for "since start"
                } else if (timeRange === '168') {
                    return '10sec'; // 10-second for 7 days
                } else if (timeRange === '24') {
                    return 'full'; // Full resolution for 24 hours
                } else {
                    return 'full'; // Full resolution for shorter periods
                }
            }

            showPerformanceWarning(dataSize) {
                // Show non-intrusive performance warning
                const warningDiv = document.createElement('div');
                warningDiv.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ff9800;
                    color: white;
                    padding: 12px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    z-index: 1000;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    max-width: 300px;
                `;
                warningDiv.innerHTML = `
                    <strong>⚠️ Large Dataset</strong><br>
                    ${dataSize.toLocaleString()} data points loaded.<br>
                    Consider using lower resolution for better performance.
                `;

                document.body.appendChild(warningDiv);

                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (warningDiv.parentNode) {
                        warningDiv.parentNode.removeChild(warningDiv);
                    }
                }, 5000);
            }

            switchToLiveMode() {
                this.mode = 'live';
                // Persist
                try { localStorage.setItem('umc_mode', 'live'); } catch {}
                this.stopLivePolling();
                // Reset failure state upon explicit switch
                this.livePollFailureCount = 0;
                this.liveErrorNotified = false;
                this.startLivePolling();
                this.updateChart(true); // Animate transition
                this.updateUI();
                console.log(`Switched to live mode: ${this.liveRanges[this.currentLiveRange].label}`);
            }

            // Backward compatibility method
            switchToRealtimeMode() {
                this.switchToLiveMode();
            }

            async refreshHistoricalData() {
                if (this.mode !== 'historical') return;

                // Get mode indicator element once for reuse
                const chartModeIndicator = document.getElementById('chart-mode-indicator');

                try {
                    // Show subtle loading indicator in mode indicator
                    const originalText = chartModeIndicator ? chartModeIndicator.textContent : '';
                    if (chartModeIndicator && !originalText.includes('🔄')) {
                        chartModeIndicator.textContent = originalText.replace('Auto-refresh: 5s', 'Refreshing... 🔄');
                    }

                    // Use correct API endpoint for historical chart data
                    const response = await fetch(`/api/historical-chart?hours=${this.currentTimeRange}&resolution=${this.currentResolution}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();

                    this.historicalData = data.points || [];
                    this.updateChart();

                    // Restore auto-refresh indicator
                    if (chartModeIndicator && chartModeIndicator.textContent.includes('🔄')) {
                        const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                         this.currentTimeRange === '1' ? 'Last Hour' :
                                         this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                         this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                         this.currentTimeRange === '168' ? 'Last 7 Days' :
                                         `Last ${this.currentTimeRange} Hours`;
                        chartModeIndicator.textContent = `Historical (${rangeText}) • Auto-refresh: 5s`;
                    }
                } catch (error) {
                    console.error('Error refreshing historical data:', error);
                    // Restore auto-refresh indicator on error
                    if (chartModeIndicator && chartModeIndicator.textContent.includes('🔄')) {
                        const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                         this.currentTimeRange === '1' ? 'Last Hour' :
                                         this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                         this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                         this.currentTimeRange === '168' ? 'Last 7 Days' :
                                         `Last ${this.currentTimeRange} Hours`;
                        chartModeIndicator.textContent = `Historical (${rangeText}) • Auto-refresh: 5s`;
                    }
                    // Don't show alert for auto-refresh errors, just log them
                }
            }

            async changeResolution(resolution) {
                if (this.mode !== 'historical') return;

                console.log(`Changing resolution to: ${resolution}`);
                this.currentResolution = resolution;
                try { localStorage.setItem('umc_resolution', resolution); } catch {}

                // Reset failure state when explicitly changing view
                this.livePollFailureCount = 0;
                this.liveErrorNotified = false;

                // Show loading indicator
                const chartTitle = document.getElementById('chart-title');
                const originalTitle = chartTitle?.textContent;
                if (chartTitle) {
                    chartTitle.textContent = 'Loading historical data...';
                }

                try {
                    await this.switchToHistoricalMode(this.currentTimeRange);
                } catch (error) {
                    console.error('Error changing resolution:', error);
                    if (chartTitle && originalTitle) {
                        chartTitle.textContent = originalTitle;
                    }
                }
            }

            updateChart(animate = false) {
                const data = this.mode === 'live' ? this.liveData : this.historicalData;

                // Create chart if it doesn't exist
                if (!this.chart) {
                    const ctx = document.getElementById('memoryChart').getContext('2d');
                    this.chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Menu Bar App (MB)',
                                data: [],
                                borderColor: '#2196F3',
                                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                                tension: 0.4,
                                fill: true
                            }, {
                                label: 'Main Service (MB)',
                                data: [],
                                borderColor: '#4CAF50',
                                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                intersect: false,
                                mode: 'index'
                            },
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
                                    display: true,
                                    position: 'top'
                                }
                            }
                        }
                    });
                }

                if (!data || data.length === 0) {
                    this.chart.data.labels = [];
                    this.chart.data.datasets[0].data = [];
                    this.chart.data.datasets[1].data = [];
                } else {
                    this.chart.data.labels = data.map(d => {
                        const date = new Date(d.timestamp);
                        return this.mode === 'live' ?
                            date.toLocaleTimeString() :
                            this.formatHistoricalTime(date);
                    });
                    this.chart.data.datasets[0].data = data.map(d => d.menubar_memory || 0);
                    this.chart.data.datasets[1].data = data.map(d => d.service_memory || 0);
                }

                // Use smooth transitions for mode/range changes, no animation for live updates
                const animationMode = animate ? 'active' : 'none';
                this.chart.update(animationMode);

                // Update data points counter in header
                const headerDataPointsElement = document.getElementById('header-data-points');
                if (headerDataPointsElement) {
                    headerDataPointsElement.textContent = (data?.length || 0) + ' pts';
                }

                // Update chart status
                const chartPointsCount = document.getElementById('chart-points-count');
                if (chartPointsCount) {
                    chartPointsCount.textContent = (data?.length || 0) + ' pts';
                }

                // Update last update timestamp
                const chartLastUpdate = document.getElementById('chart-last-update');
                if (chartLastUpdate) {
                    const now = new Date();
                    chartLastUpdate.textContent = 'Updated: ' + now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                }

                // Update range indicator for live mode
                if (this.mode === 'live') {
                    const rangeIndicator = document.getElementById('live-range-indicator');
                    if (rangeIndicator) {
                        const range = this.liveRanges[this.currentLiveRange];
                        rangeIndicator.textContent = `Live: ${range.label} (${data?.length || 0} pts)`;
                    }
                }
            }

            formatHistoricalTime(date) {
                if (this.currentTimeRange === 'all' || parseInt(this.currentTimeRange) > 24) {
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                } else {
                    return date.toLocaleTimeString();
                }
            }

            updateUI() {
                const liveBtn = document.getElementById('realtime-btn'); // Keep existing ID for compatibility
                const historicalBtn = document.getElementById('historical-btn');
                const historicalOptions = document.getElementById('historical-options');
                const liveOptions = document.getElementById('live-options');
                const chartTitle = document.getElementById('chart-title');
                const chartModeIndicator = document.getElementById('chart-mode-indicator');
                const modeBadge = document.getElementById('mode-badge');

                if (this.mode === 'live') {
                    // Update live mode UI with enhanced styling
                    if (liveBtn) {
                        liveBtn.style.background = '#4CAF50';
                        liveBtn.style.color = 'white';
                        liveBtn.style.boxShadow = '0 2px 4px rgba(76, 175, 80, 0.3)';
                    }
                    if (historicalBtn) {
                        historicalBtn.style.background = 'white';
                        historicalBtn.style.color = '#666';
                        historicalBtn.style.boxShadow = 'none';
                    }
                    if (historicalOptions) {
                        historicalOptions.style.display = 'none';
                    }
                    if (liveOptions) {
                        liveOptions.style.display = 'flex';
                    }

                    const range = this.liveRanges[this.currentLiveRange];
                    if (chartTitle) chartTitle.textContent = `Live Memory Usage`;
                    if (chartModeIndicator) chartModeIndicator.textContent = `Live: ${range.label}`;
                    if (modeBadge) {
                        modeBadge.textContent = 'Live';
                        modeBadge.style.background = '#4CAF50';
                    }
                } else {
                    // Update historical mode UI with enhanced styling
                    if (liveBtn) {
                        liveBtn.style.background = 'white';
                        liveBtn.style.color = '#666';
                        liveBtn.style.boxShadow = 'none';
                    }
                    if (historicalBtn) {
                        historicalBtn.style.background = '#2196F3';
                        historicalBtn.style.color = 'white';
                        historicalBtn.style.boxShadow = '0 2px 4px rgba(33, 150, 243, 0.3)';
                    }
                    if (historicalOptions) {
                        historicalOptions.style.display = 'flex';
                    }
                    if (liveOptions) {
                        liveOptions.style.display = 'none';
                    }

                    const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                     this.currentTimeRange === '1' ? 'Last Hour' :
                                     this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                     this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                     this.currentTimeRange === '168' ? 'Last 7 Days' :
                                     `Last ${this.currentTimeRange} Hours`;

                    if (chartTitle) chartTitle.textContent = `Historical Memory Usage`;
                    if (chartModeIndicator) chartModeIndicator.textContent = `Historical (${rangeText}) • Auto-refresh: 5s`;
                    if (modeBadge) {
                        modeBadge.textContent = 'Historical';
                        modeBadge.style.background = '#2196F3';
                    }
                }

                // Update live range selector if it exists
                const liveRangeSelect = document.getElementById('live-range-select');
                if (liveRangeSelect) {
                    liveRangeSelect.value = this.currentLiveRange;
                }

                // Add visual feedback for range changes
                this.addVisualFeedback();
            }

            addVisualFeedback() {
                // Add subtle animation to indicate UI update
                const controlBar = document.querySelector('.unified-control-bar');
                if (controlBar) {
                    controlBar.style.transform = 'scale(1.01)';
                    setTimeout(() => {
                        controlBar.style.transform = 'scale(1)';
                    }, 150);
                }
            }
        }

        // Helper function for historical options toggle
        function toggleHistoricalOptions() {
            const historicalOptions = document.getElementById('historical-options');
            const isVisible = historicalOptions.style.display !== 'none';

            if (isVisible) {
                chartManager.switchToLiveMode();
            } else {
                historicalOptions.style.display = 'flex';
                // Auto-select first option with user confirmation for large datasets
                const rangeSelect = document.getElementById('historical-range');
                if (rangeSelect) {
                    const selectedRange = rangeSelect.value;
                    if (selectedRange === 'all') {
                        const confirmed = confirm('Loading complete history since service start.\\nThis may take a moment and will use 1-minute resolution for performance.\\nContinue?');
                        if (confirmed) {
                            chartManager.switchToHistoricalMode(selectedRange);
                        } else {
                            // Reset to live mode
                            chartManager.switchToLiveMode();
                            return;
                        }
                    } else {
                        chartManager.switchToHistoricalMode(selectedRange);
                    }
                }
            }
        }

        // New helper function for live range changes
        function handleLiveRangeChange(selectElement) {
            const newRange = selectElement.value;
            try { localStorage.setItem('umc_live_range', newRange); } catch {}
            chartManager.switchLiveRange(newRange);
        }

        // Helper function to handle historical range selection changes
        function handleRangeChange(selectElement) {
            const selectedRange = selectElement.value;
            try { localStorage.setItem('umc_time_range', String(selectedRange)); } catch {}
            if (selectedRange === 'all') {
                const confirmed = confirm('Loading complete history since service start.\\nThis may take a moment and will use 1-minute resolution for performance.\\nContinue?');
                if (confirmed) {
                    chartManager.switchToHistoricalMode(selectedRange);
                } else {
                    // Reset to previous selection
                    selectElement.value = chartManager.currentTimeRange;
                }
            } else {
                chartManager.switchToHistoricalMode(selectedRange);
            }
        }

        // Initialize dashboard with polling - update banner status
        const statusLight = document.getElementById('dashboard-status-light');
        const statusText = document.getElementById('dashboard-status-text');
        if (statusLight && statusText) {
            statusLight.style.background = '#ccc';
            statusText.textContent = 'Connecting...';
            statusText.style.color = '#666';
        }

        // Initialize session start time (persistent across page refreshes)
        let globalSessionStartTime = null;

        // Initialize Unified Chart Manager
        const chartManager = new UnifiedMemoryChart();

        // Simple CPU Chart Manager
        class SimpleCPUChart {
            constructor() {
                this.isPaused = false;
            }

            switchToRealtimeMode() {
                const realtimeBtn = document.getElementById('cpu-realtime-btn');
                const historicalBtn = document.getElementById('cpu-historical-btn');
                const historicalOptions = document.getElementById('cpu-historical-options');
                const chartTitle = document.getElementById('cpu-chart-title');
                const frequencyLabel = document.getElementById('cpu-frequency-label');
                const modeIndicator = document.getElementById('cpu-chart-mode-indicator');

                if (realtimeBtn && historicalBtn && historicalOptions) {
                    realtimeBtn.style.background = '#4CAF50';
                    realtimeBtn.style.color = 'white';
                    historicalBtn.style.background = '#f5f5f5';
                    historicalBtn.style.color = '#333';
                    historicalOptions.style.display = 'none';

                    if (chartTitle) chartTitle.textContent = 'Real-time CPU Usage';
                    if (frequencyLabel) frequencyLabel.textContent = 'Data collected every 2 seconds';
                    if (modeIndicator) modeIndicator.textContent = 'Real-time';
                }
            }

            switchToHistoricalMode() {
                const realtimeBtn = document.getElementById('cpu-realtime-btn');
                const historicalBtn = document.getElementById('cpu-historical-btn');
                const historicalOptions = document.getElementById('cpu-historical-options');
                const chartTitle = document.getElementById('cpu-chart-title');
                const frequencyLabel = document.getElementById('cpu-frequency-label');
                const modeIndicator = document.getElementById('cpu-chart-mode-indicator');

                if (realtimeBtn && historicalBtn && historicalOptions) {
                    realtimeBtn.style.background = '#f5f5f5';
                    realtimeBtn.style.color = '#333';
                    historicalBtn.style.background = '#2196F3';
                    historicalBtn.style.color = 'white';
                    historicalOptions.style.display = 'flex';

                    if (chartTitle) chartTitle.textContent = 'Historical CPU Usage';
                    if (frequencyLabel) frequencyLabel.textContent = 'Historical data frequency varies';
                    if (modeIndicator) modeIndicator.textContent = 'Historical';
                }
            }

            togglePause() {
                this.isPaused = !this.isPaused;
                const pauseBtn = document.getElementById('cpu-pause-btn');
                if (pauseBtn) {
                    pauseBtn.textContent = this.isPaused ? '▶️ Resume' : '⏸️ Pause';
                }
            }

            clearChart() {
                cpuChart.data.labels = [];
                cpuChart.data.datasets[0].data = [];
                cpuChart.data.datasets[1].data = [];
                cpuChart.update();
            }
        }

        const cpuChartManager = new SimpleCPUChart();

        // Start memory data polling is now managed by UnifiedMemoryChart (Phase 2)
        // setInterval(fetchMemoryData, 2000);

        // Fetch additional data every 10 seconds
        setInterval(() => {
            fetchSystemData();
            fetchProcessData();
            loadAnalysisData();
        }, 10000);

        // Auto-refresh historical data every 5 seconds when in historical mode (faster updates)
        setInterval(() => {
            if (chartManager && chartManager.mode === 'historical') {
                chartManager.refreshHistoricalData();
            }
        }, 5000);

        // Performance monitoring for live mode
        setInterval(() => {
            if (chartManager && chartManager.mode === 'live') {
                const range = chartManager.liveRanges[chartManager.currentLiveRange];
                const dataPoints = chartManager.liveData.length;

                // Log performance metrics every 30 seconds
                console.log(`Live mode performance: ${range.label}, ${dataPoints}/${range.points} points`);

                // Auto-optimize if too many points are causing performance issues
                if (dataPoints > range.points * 1.1) {
                    console.warn(`Live data buffer overflow, trimming to ${range.points} points`);
                    chartManager.liveData = chartManager.liveData.slice(-range.points);
                }
            }
        }, 30000);

        // Initialize chart manager after chart is ready
        setTimeout(async () => {
            await chartManager.initialize();
        }, 1000);

        // Pause/resume polling based on tab visibility
        document.addEventListener('visibilitychange', () => {
            chartManager.paused = document.hidden;
        });

        // Initial fetch (memory handled by chart manager on initialize)
        fetchSystemData();
        fetchProcessData();
        loadAnalysisData();
        updateMonitoringStatus();

        // Update monitoring status every 5 seconds
        setInterval(updateMonitoringStatus, 5000);
    </script>
    </div> <!-- Close container -->
</body>
</html>
        '''

    def get_memory_data(self):
        """Get detailed memory usage data."""
        try:
            # System memory information
            system_memory = psutil.virtual_memory()

            # Clipboard Monitor specific processes
            clipboard_processes = []
            total_clipboard_memory = 0

            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent', 'create_time', 'num_threads', 'num_fds']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cmdline = proc.info.get('cmdline', [])

                    # Get memory and CPU from the iterator
                    memory_info = proc.info.get('memory_info')
                    if memory_info:
                        memory_mb = memory_info.rss / 1024 / 1024
                    else:
                        memory_mb = 0

                    cpu_percent = proc.info.get('cpu_percent', 0) or 0

                    # Get detailed process metrics
                    threads = proc.info.get('num_threads', 0)
                    handles = proc.info.get('num_fds', 0)  # File descriptors on Unix
                    create_time = proc.info.get('create_time', 0)

                    # Calculate uptime
                    if create_time:
                        uptime_seconds = time.time() - create_time
                        uptime_hours = int(uptime_seconds // 3600)
                        uptime_minutes = int((uptime_seconds % 3600) // 60)
                        uptime_str = f"{uptime_hours}h {uptime_minutes}m" if uptime_hours > 0 else f"{uptime_minutes}m"
                    else:
                        uptime_str = "--"

                    # Use the same detection logic as collect_memory_data()
                    is_clipboard_process = False
                    cmdline_str = ""

                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        # More specific detection to avoid false positives
                        is_clipboard_process = (
                            'menu_bar_app.py' in cmdline_str or
                            ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard monitor', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]))
                        )

                    # Also check by process name (for PyInstaller executables)
                    if not is_clipboard_process and name == 'ClipboardMonitor':
                        is_clipboard_process = True

                    if is_clipboard_process:
                        total_clipboard_memory += memory_mb

                        # Determine process type and descriptive name
                        process_type = "unknown"
                        display_name = name

                        if 'menu_bar_app.py' in cmdline_str:
                            process_type = "menu_bar"
                            display_name = "ClipboardMonitor Menu Bar"
                        elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                            'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                        ]):
                            process_type = "main_service"
                            display_name = "ClipboardMonitor Service"
                        elif name == 'ClipboardMonitor':
                            # For PyInstaller executables, use memory heuristic
                            if memory_mb > 50:
                                process_type = "menu_bar"
                                display_name = "ClipboardMonitor Menu Bar"
                            else:
                                process_type = "main_service"
                                display_name = "ClipboardMonitor Service"
                        elif 'unified_memory_dashboard.py' in cmdline_str:
                            process_type = "dashboard"
                            display_name = "Memory Dashboard"

                        clipboard_processes.append({
                            'pid': pid,
                            'name': name,
                            'display_name': display_name,
                            'memory_mb': round(memory_mb, 2),
                            'cpu_percent': cpu_percent,
                            'create_time': datetime.fromtimestamp(create_time).isoformat() if create_time else None,
                            'process_type': process_type,
                            'cmdline_snippet': cmdline_str[:100] + "..." if len(cmdline_str) > 100 else cmdline_str,
                            'threads': threads,
                            'handles': handles,
                            'uptime': uptime_str,
                            'restarts': 0  # TODO: Implement restart tracking
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Calculate analytics metrics
            current_total_memory = total_clipboard_memory
            current_time = datetime.now()

            # Add current reading to history
            self.memory_history.append({
                'memory': current_total_memory,
                'timestamp': current_time
            })

            # Calculate growth rate based on recent history
            growth_rate = 0.0
            if len(self.memory_history) >= 2:
                # Calculate growth over last 5 minutes
                five_min_ago = current_time - timedelta(minutes=5)
                recent_readings = [r for r in self.memory_history if r['timestamp'] > five_min_ago]

                if len(recent_readings) >= 2:
                    oldest = recent_readings[0]
                    newest = recent_readings[-1]
                    time_diff_minutes = (newest['timestamp'] - oldest['timestamp']).total_seconds() / 60
                    if time_diff_minutes > 0:
                        growth_rate = (newest['memory'] - oldest['memory']) / time_diff_minutes

            # Calculate efficiency (MB per operation) - simplified to avoid server issues
            efficiency = round(current_total_memory / max(len(clipboard_processes), 1), 1)

            # Calculate optimum time based on memory stability
            optimum_time = 75  # Default
            try:
                if len(self.memory_history) >= 10:
                    # Calculate stability - lower variance = higher optimum time
                    recent_memories = [r['memory'] for r in list(self.memory_history)[-10:]]
                    if recent_memories:
                        mean = sum(recent_memories) / len(recent_memories)
                        variance = sum((x - mean)**2 for x in recent_memories) / len(recent_memories)
                        optimum_time = max(30, min(120, 75 - int(variance)))
            except Exception:
                optimum_time = 75  # Fallback

            # Calculate pressure (memory pressure as percentage)
            pressure = round((system_memory.percent / 100) * 2.5, 2)

            # Get system load average
            try:
                load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            except:
                load_avg = 0.0

            # Calculate system uptime
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                uptime_hours = int(uptime_seconds // 3600)
                uptime_minutes = int((uptime_seconds % 3600) // 60)
                uptime_str = f"{uptime_hours}h {uptime_minutes}m"
            except:
                uptime_str = "--"

            # Calculate session duration
            session_duration_seconds = (datetime.now() - self.session_start_time).total_seconds()
            session_hours = int(session_duration_seconds // 3600)
            session_minutes = int((session_duration_seconds % 3600) // 60)
            session_seconds = int(session_duration_seconds % 60)
            session_duration = f"{session_hours}h {session_minutes}m {session_seconds}s"

            return {
                'system': {
                    'total_gb': round(system_memory.total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(system_memory.available / 1024 / 1024 / 1024, 2),
                    'used_gb': round((system_memory.total - system_memory.available) / 1024 / 1024 / 1024, 2),
                    'percent': system_memory.percent,
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'load_avg': round(load_avg, 2),
                    'uptime': uptime_str
                },
                'clipboard': {
                    'processes': clipboard_processes,
                    'total_memory_mb': round(total_clipboard_memory, 2),
                    'process_count': len(clipboard_processes)
                },
                'analytics': {
                    'total_memory': round(current_total_memory, 1),
                    'growth_rate': f"+{growth_rate:.1f}MB/min" if growth_rate >= 0 else f"{growth_rate:.1f}MB/min",
                    'efficiency': f"{efficiency:.1f}MB/op",
                    'optimum': f"{optimum_time}min",
                    'gc_status': "Low" if self.gc_count < 5 else "Normal" if self.gc_count < 15 else "High",
                    'pressure': f"{pressure:.1f}%",
                    'history': len(self.memory_history),
                    'queue': max(0, len(clipboard_processes) - 2),  # Processes beyond main 2
                    'cache': f"{min(95.1, 80 + (self.cache_hits / max(self.cache_hits + self.cache_misses, 1)) * 15):.1f}%"
                },
                'session': {
                    'duration': session_duration,
                    'start_time': self.session_start_time.isoformat(),
                    'data_points': len(self.memory_history) if hasattr(self, 'memory_history') else 0
                },
                'timestamp': datetime.now().isoformat(),
                'peak_menubar_memory': round(self.peak_menubar_memory, 2),
                'peak_service_memory': round(self.peak_service_memory, 2),
                'peak_total_memory': round(self.peak_total_memory, 2),
                'peak_menubar_cpu': round(self.peak_menubar_cpu, 2),
                'peak_service_cpu': round(self.peak_service_cpu, 2),
                'peak_total_cpu': round(self.peak_total_cpu, 2)
            }

        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def get_process_data(self):
        """Get process information."""
        memory_data = self.get_memory_data()
        processes = memory_data.get('clipboard', {}).get('processes', [])
        if not processes:
            try:
                fallback = []
                for proc in psutil.process_iter(['pid','name','cmdline','memory_info','cpu_percent']):
                    try:
                        name = proc.info.get('name') or ''
                        cmd = ' '.join(proc.info.get('cmdline') or []).lower()
                        if ('clipboard' in cmd) or ('menu_bar_app.py' in cmd) or ('unified_memory_dashboard.py' in cmd) or (name == 'ClipboardMonitor') or ('clipboard' in (name or '').lower()):
                            mi = proc.info.get('memory_info')
                            mem_mb = (mi.rss/1024/1024) if mi else 0
                            fallback.append({
                                'pid': proc.info.get('pid'),
                                'name': name,
                                'display_name': 'Clipboard Monitor' if 'clipboard' in cmd else (name or 'process'),
                                'memory_mb': round(mem_mb, 2),
                                'cpu_percent': proc.info.get('cpu_percent') or 0,
                                'process_type': 'unknown'
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                if fallback:
                    return {'clipboard_processes': fallback, 'timestamp': datetime.now().isoformat(), 'fallback': True}
            except Exception:
                pass
        return {
            'clipboard_processes': processes,
            'timestamp': datetime.now().isoformat()
        }

    def get_system_data(self):
        """Get system information."""
        memory_data = self.get_memory_data()

        try:
            # Additional system info
            cpu_percent = psutil.cpu_percent(interval=1)
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)

            return {
                'system': memory_data.get('system', {}),
                'cpu_percent': cpu_percent,
                'uptime': f"{uptime_hours}h {uptime_minutes}m",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def collect_memory_data(self):
        """Collect current memory usage and CPU data for WebSocket updates."""
        try:
            menubar_memory = 0
            service_memory = 0
            dashboard_memory = 0
            menubar_cpu = 0
            service_cpu = 0
            dashboard_cpu = 0

            # Debug: collect all clipboard-related processes
            clipboard_processes = []

            # Use the same approach as the menu bar app for reliable detection

            # Get memory for menu bar app (current process if this is the menu bar)
            current_pid = os.getpid()
            try:
                current_process = psutil.Process(current_pid)
                current_cmdline = ' '.join(current_process.cmdline()) if current_process.cmdline() else ''
                if 'menu_bar_app.py' in current_cmdline:
                    menubar_memory = current_process.memory_info().rss / 1024 / 1024
                    menubar_cpu = current_process.cpu_percent() or 0
                    print(f"📱 Found Menu Bar App (current process): PID {current_pid}, Memory: {menubar_memory:.1f}MB, CPU: {menubar_cpu:.1f}%")
            except:
                pass

            # Use the original simple approach that was working before
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cmdline = proc.info.get('cmdline', [])

                    # Get memory and CPU from the iterator (this was working before)
                    memory_info = proc.info.get('memory_info')
                    if memory_info:
                        memory_mb = memory_info.rss / 1024 / 1024
                    else:
                        memory_mb = 0

                    cpu_percent = proc.info.get('cpu_percent', 0) or 0

                    # Check if this is a clipboard-related process
                    is_clipboard_process = False
                    cmdline_str = ""

                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        # More specific detection to avoid false positives
                        is_clipboard_process = (
                            'menu_bar_app.py' in cmdline_str or
                            'unified_memory_dashboard.py' in cmdline_str or
                            ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard monitor', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]))
                        )

                    # Also check by process name (for PyInstaller executables)
                    if not is_clipboard_process and name == 'ClipboardMonitor':
                        is_clipboard_process = True

                    if is_clipboard_process:
                        clipboard_processes.append({
                            'pid': pid,
                            'name': name,
                            'cmdline': cmdline_str,
                            'memory_mb': memory_mb,
                            'cpu_percent': cpu_percent
                        })

                        # Use the original simple detection logic that was working
                        if 'menu_bar_app.py' in cmdline_str:
                            menubar_memory = memory_mb
                            menubar_cpu = cpu_percent
                        elif 'unified_memory_dashboard.py' in cmdline_str:
                            dashboard_memory = memory_mb
                            dashboard_cpu = cpu_percent
                        elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                            'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                        ]):
                            service_memory = memory_mb
                            service_cpu = cpu_percent
                        elif name == 'ClipboardMonitor':
                            # For PyInstaller executables, we need to distinguish between main service and menu bar app
                            # Since we can't access command lines, we'll use a simple heuristic:
                            # The menu bar app typically uses more memory than the main service
                            if memory_mb > 50:  # Menu bar app typically uses more memory
                                if menubar_memory == 0:  # Only assign if we haven't found one yet
                                    menubar_memory = memory_mb
                                    menubar_cpu = cpu_percent
                            else:  # Main service typically uses less memory
                                if service_memory == 0:  # Only assign if we haven't found one yet
                                    service_memory = memory_mb
                                    service_cpu = cpu_percent

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Optional debug output (can be enabled for troubleshooting)
            # if len(clipboard_processes) > 0:
            #     print(f"Found {len(clipboard_processes)} clipboard processes:")
            #     for proc in clipboard_processes:
            #         print(f"  PID {proc['pid']}: {proc['name']} - {proc['memory_mb']:.2f} MB")

            # Track peak memory values
            if menubar_memory > self.peak_menubar_memory:
                self.peak_menubar_memory = menubar_memory

            if service_memory > self.peak_service_memory:
                self.peak_service_memory = service_memory

            if dashboard_memory > self.peak_dashboard_memory:
                self.peak_dashboard_memory = dashboard_memory

            # Track peak CPU values
            if menubar_cpu > self.peak_menubar_cpu:
                self.peak_menubar_cpu = menubar_cpu

            if service_cpu > self.peak_service_cpu:
                self.peak_service_cpu = service_cpu

            if dashboard_cpu > self.peak_dashboard_cpu:
                self.peak_dashboard_cpu = dashboard_cpu

            # Track peak totals
            total_memory = menubar_memory + service_memory + dashboard_memory
            total_cpu = menubar_cpu + service_cpu + dashboard_cpu

            if total_memory > self.peak_total_memory:
                self.peak_total_memory = total_memory

            if total_cpu > self.peak_total_cpu:
                self.peak_total_cpu = total_cpu

            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': round(menubar_memory, 2),
                'service_memory': round(service_memory, 2),
                'dashboard_memory': round(dashboard_memory, 2),
                'total_memory': round(total_memory, 2),
                'menubar_cpu': round(menubar_cpu, 2),
                'service_cpu': round(service_cpu, 2),
                'dashboard_cpu': round(dashboard_cpu, 2),
                'total_cpu': round(total_cpu, 2),
                'peak_menubar_memory': round(self.peak_menubar_memory, 2),
                'peak_service_memory': round(self.peak_service_memory, 2),
                'peak_dashboard_memory': round(self.peak_dashboard_memory, 2),
                'peak_total_memory': round(self.peak_total_memory, 2),
                'peak_menubar_cpu': round(self.peak_menubar_cpu, 2),
                'peak_service_cpu': round(self.peak_service_cpu, 2),
                'peak_dashboard_cpu': round(self.peak_dashboard_cpu, 2),
                'peak_total_cpu': round(self.peak_total_cpu, 2),
                'session_start_time': self.session_start_time.isoformat()
            }

        except Exception as e:
            # Optional debug output (can be enabled for troubleshooting)
            # print(f"Error in collect_memory_data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': 0,
                'service_memory': 0,
                'total_memory': 0,
                'error': str(e)
            }

    def load_historical_data(self):
        """Load historical data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    saved_data = json.load(f)
                    self.data_history = saved_data.get('data_history', [])
                    self.alert_count = saved_data.get('alert_count', 0)
        except Exception as e:
            print(f"Error loading historical data: {e}")

    def save_historical_data(self):
        """Save historical data to file"""
        try:
            data_to_save = {
                'data_history': self.data_history[-self.max_history:],
                'alert_count': self.alert_count,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f)
        except Exception as e:
            print(f"Error saving historical data: {e}")

    def get_historical_data(self, hours=24, resolution='full'):
        """Get historical data for specified hours with optional resolution"""
        if hours == 'all':
            # Return all data since service start
            filtered_data = list(self.data_history)
        else:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.timestamp()

            filtered_data = []
            for point in self.data_history:
                point_timestamp = point.get('timestamp', 0)
                # Handle both string and float timestamps
                if isinstance(point_timestamp, str):
                    try:
                        point_timestamp = datetime.fromisoformat(point_timestamp).timestamp()
                    except:
                        continue

                if point_timestamp >= cutoff_timestamp:
                    filtered_data.append(point)

        # Apply resolution filtering if requested
        if resolution != 'full' and len(filtered_data) > 0:
            filtered_data = self._apply_resolution_filter(filtered_data, resolution)

        return {
            'main_service': [{'timestamp': p['timestamp'], 'memory_rss_mb': p['service_memory']} for p in filtered_data],
            'menu_bar': [{'timestamp': p['timestamp'], 'memory_rss_mb': p['menubar_memory']} for p in filtered_data],
            'system': [{'timestamp': p['timestamp'], 'memory_percent': 0} for p in filtered_data],  # Placeholder
            'points': filtered_data,  # Raw data for chart
            'total_points': len(filtered_data),
            'resolution': resolution,
            'time_range': f"{hours} hours" if hours != 'all' else "since start"
        }

    def _apply_resolution_filter(self, data, resolution):
        """Apply resolution filtering to reduce data points"""
        if not data or resolution == 'full':
            # For full resolution, limit to prevent browser issues
            if len(data) > 10000:
                print(f"Warning: Full resolution dataset has {len(data)} points, limiting to last 10000")
                return data[-10000:]  # Keep last 10000 points
            return data

        if resolution == 'minute':
            # Keep one point per minute
            interval = 60  # seconds
        elif resolution == 'hour':
            # Keep one point per hour
            interval = 3600  # seconds
        elif resolution == '10sec':
            # Keep one point per 10 seconds
            interval = 10  # seconds
        else:
            return data

        filtered = []
        last_timestamp = 0

        for point in data:
            point_timestamp = point.get('timestamp', 0)
            if isinstance(point_timestamp, str):
                try:
                    point_timestamp = datetime.fromisoformat(point_timestamp).timestamp()
                except:
                    continue

            if point_timestamp - last_timestamp >= interval:
                filtered.append(point)
                last_timestamp = point_timestamp

        # Resolution filter applied
        return filtered

    def get_analysis_data(self, hours=24):
        """Get memory leak analysis data"""
        historical_data = self.get_historical_data(hours)
        analysis = {}

        # Only process actual process data, skip metadata keys
        process_keys = ['main_service', 'menu_bar', 'system']
        for process_name in process_keys:
            points = historical_data.get(process_name, [])
            if not isinstance(points, list) or len(points) < 2:
                analysis[process_name] = {
                    "status": "insufficient_data",
                    "severity": "low",
                    "growth_rate_mb": 0,
                    "total_growth_mb": 0,
                    "start_memory_mb": 0,
                    "end_memory_mb": 0,
                    "data_points": len(points) if isinstance(points, list) else 0
                }
                continue

            memory_values = [p.get('memory_rss_mb', 0) for p in points]
            if not memory_values:
                continue

            # Calculate growth rate
            start_memory = memory_values[0]
            end_memory = memory_values[-1]
            growth = end_memory - start_memory
            growth_rate = growth / len(memory_values) if len(memory_values) > 0 else 0

            # Determine status
            if growth_rate > 5.0:
                status = "potential_leak"
                severity = "high"
            elif growth_rate > 2.0:
                status = "monitoring_needed"
                severity = "medium"
            else:
                status = "normal"
                severity = "low"

            analysis[process_name] = {
                "status": status,
                "severity": severity,
                "growth_rate_mb": growth_rate,
                "total_growth_mb": growth,
                "start_memory_mb": start_memory,
                "end_memory_mb": end_memory,
                "data_points": len(points)
            }

        return analysis

    def start_advanced_monitoring(self, interval=30):
        """Start advanced monitoring with specified interval"""
        self.monitor_interval = interval
        self.monitoring_active = True
        self.monitoring_start_time = datetime.now()

        # Start background data collection thread if not already running
        if not hasattr(self, 'monitoring_thread') or not self.monitoring_thread.is_alive():
            self.monitoring_thread = threading.Thread(target=self._background_monitoring_loop, daemon=False)
            self.monitoring_thread.start()
            print(f"Started persistent background monitoring thread with {interval}s interval")

        return {
            "status": "started",
            "interval": interval,
            "message": f"Advanced monitoring started with {interval}s interval",
            "background_collection": "enabled"
        }

    def stop_advanced_monitoring(self):
        """Stop advanced monitoring"""
        self.monitoring_active = False
        duration = None
        data_points_collected = len(self.advanced_data_history)

        if self.monitoring_start_time:
            duration = (datetime.now() - self.monitoring_start_time).total_seconds()

        # The background thread will stop automatically when monitoring_active becomes False
        print(f"Stopped advanced monitoring - background collection will cease")
        print(f"Advanced monitoring session collected {data_points_collected} data points")

        return {
            "status": "stopped",
            "duration_seconds": duration,
            "data_points_collected": data_points_collected,
            "message": "Advanced monitoring stopped",
            "background_collection": "disabled"
        }

    def _background_monitoring_loop(self):
        """Background thread for advanced monitoring data collection"""
        print(f"Background monitoring loop started with {self.monitor_interval}s interval")

        while self.monitoring_active:
            try:
                # Collect memory data
                memory_data = self.collect_memory_data()

                # Add to advanced monitoring history (separate from basic data collection)
                self.advanced_data_history.append(memory_data)

                # Limit advanced history size
                if len(self.advanced_data_history) > self.max_history:
                    self.advanced_data_history = self.advanced_data_history[-self.max_history:]

                # Perform leak analysis if we have enough advanced data
                if len(self.advanced_data_history) > 10:
                    try:
                        # Simple leak detection using advanced monitoring data
                        recent_data = self.advanced_data_history[-10:]
                        menubar_trend = [d.get('menubar_memory', 0) for d in recent_data]
                        service_trend = [d.get('service_memory', 0) for d in recent_data]

                        # Check for consistent growth
                        if len(menubar_trend) >= 2 and len(service_trend) >= 2:
                            menubar_growth = menubar_trend[-1] - menubar_trend[0]
                            service_growth = service_trend[-1] - service_trend[0]

                            # Memory growth detection (silent monitoring)
                            if menubar_growth > 5.0:  # More than 5MB growth
                                pass  # Could log to file if needed

                            if service_growth > 5.0:  # More than 5MB growth
                                pass  # Could log to file if needed

                    except Exception as e:
                        print(f"Error in leak analysis: {e}")

                # Wait for the specified interval
                time.sleep(self.monitor_interval)

            except Exception as e:
                print(f"Error in background monitoring: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)  # Wait before retrying

        # Background monitoring loop stopped

    def force_garbage_collection(self):
        """Force garbage collection and return stats"""
        try:
            # Get memory before cleanup
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024

            # Force garbage collection
            collected = gc.collect()

            # Get memory after cleanup
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_freed = memory_before - memory_after

            return {
                "status": "completed",
                "objects_collected": collected,
                "memory_before_mb": round(memory_before, 2),
                "memory_after_mb": round(memory_after, 2),
                "memory_freed_mb": round(memory_freed, 2),
                "gc_stats": gc.get_stats()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_leak_analysis(self):
        """Get comprehensive leak analysis"""
        return self.leak_detector.analyze_for_leaks()

    def get_comprehensive_dashboard_data(self):
        """Provides a comprehensive payload for the dashboard, including historical and real-time data."""

        # Get the latest real-time data
        latest_data = self.get_memory_data()

        # Update peak values based on the latest data
        if 'clipboard' in latest_data and 'processes' in latest_data['clipboard']:
            menubar_process = next((p for p in latest_data['clipboard']['processes'] if p.get('process_type') == 'menu_bar'), None)
            service_process = next((p for p in latest_data['clipboard']['processes'] if p.get('process_type') == 'main_service'), None)

            if menubar_process:
                self.peak_menubar_memory = max(self.peak_menubar_memory, menubar_process.get('memory_mb', 0))
                self.peak_menubar_cpu = max(self.peak_menubar_cpu, menubar_process.get('cpu_percent', 0))

            if service_process:
                self.peak_service_memory = max(self.peak_service_memory, service_process.get('memory_mb', 0))
                self.peak_service_cpu = max(self.peak_service_cpu, service_process.get('cpu_percent', 0))

            total_memory = latest_data['clipboard'].get('total_memory_mb', 0)
            self.peak_total_memory = max(self.peak_total_memory, total_memory)

            total_cpu = sum(p.get('cpu_percent', 0) for p in latest_data['clipboard']['processes'])
            self.peak_total_cpu = max(self.peak_total_cpu, total_cpu)

        # Add updated peak values to the payload
        latest_data.update({
            'peak_menubar_memory': self.peak_menubar_memory,
            'peak_service_memory': self.peak_service_memory,
            'peak_total_memory': self.peak_total_memory,
            'peak_menubar_cpu': self.peak_menubar_cpu,
            'peak_service_cpu': self.peak_service_cpu,
            'peak_total_cpu': self.peak_total_cpu,
        })

        # Add monitoring status
        latest_data['monitoring_status'] = {
            'active': self.monitoring_active,
            'start_time': self.monitoring_start_time.isoformat() if self.monitoring_start_time else None,
            'interval': self.monitor_interval,
            'advanced_data_points': len(self.advanced_data_history),
        }

        return latest_data

    def get_dashboard_status(self):
        """Get dashboard status information for menu bar app"""
        try:
            # Calculate time since last activity
            time_since_activity = datetime.now() - self.last_activity_time
            minutes_inactive = time_since_activity.total_seconds() / 60
            seconds_inactive = time_since_activity.total_seconds()

            # Calculate countdown for auto-timeout
            countdown_seconds = 0
            if self.auto_start_mode and not self.monitoring_active:
                remaining_minutes = self.auto_timeout_minutes - minutes_inactive
                countdown_seconds = max(0, remaining_minutes * 60)

            # Determine status
            if self.monitoring_active:
                status = "active_in_use"
                status_message = "Active and in use (Advanced Monitoring)"
            elif seconds_inactive < 10:  # Recent activity (within 10 seconds)
                status = "active_in_use"
                status_message = "Active and in use"
            elif self.auto_start_mode and countdown_seconds > 0:
                status = "active_not_in_use"
                countdown_minutes = int(countdown_seconds // 60)
                countdown_secs = int(countdown_seconds % 60)
                status_message = f"Active but not in use ({countdown_minutes}:{countdown_secs:02d} until shutdown)"
            elif not self.auto_start_mode:
                status = "active_persistent"
                status_message = "Active (Manual mode - no timeout)"
            else:
                status = "inactive"
                status_message = "Inactive"

            # Get current memory and CPU data directly from collect_memory_data
            memory_data = self.collect_memory_data()

            menubar_memory = memory_data.get('menubar_memory', 0)
            service_memory = memory_data.get('service_memory', 0)
            dashboard_memory = memory_data.get('dashboard_memory', 0)
            menubar_cpu = memory_data.get('menubar_cpu', 0)
            service_cpu = memory_data.get('service_cpu', 0)
            dashboard_cpu = memory_data.get('dashboard_cpu', 0)

            return {
                "status": status,
                "status_message": status_message,
                "auto_start_mode": self.auto_start_mode,
                "monitoring_active": self.monitoring_active,
                "last_activity_seconds": seconds_inactive,
                "countdown_seconds": countdown_seconds,
                "memory": {
                    "menubar": {
                        "current": menubar_memory,
                        "peak": self.peak_menubar_memory,
                        "cpu": menubar_cpu,
                        "peak_cpu": self.peak_menubar_cpu
                    },
                    "service": {
                        "current": service_memory,
                        "peak": self.peak_service_memory,
                        "cpu": service_cpu,
                        "peak_cpu": self.peak_service_cpu
                    },
                    "dashboard": {
                        "current": dashboard_memory,
                        "peak": self.peak_dashboard_memory,
                        "cpu": dashboard_cpu,
                        "peak_cpu": self.peak_dashboard_cpu
                    },
                    "total": {
                        "current": menubar_memory + service_memory + dashboard_memory,
                        "peak": self.peak_total_memory,
                        "cpu": menubar_cpu + service_cpu + dashboard_cpu,
                        "peak_cpu": self.peak_total_cpu
                    }
                },
                "session": {
                    "start_time": self.session_start_time.isoformat(),
                    "duration_minutes": (datetime.now() - self.session_start_time).total_seconds() / 60
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "status_message": f"Error getting status: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_monitoring_dashboard_data(self):
        """Get comprehensive dashboard data for monitoring dashboard compatibility"""
        try:
            memory_data = self.get_memory_data()
            system_data = self.get_system_data()

            # Calculate monitoring duration
            monitoring_duration_hours = 0
            if self.monitoring_start_time:
                duration_seconds = (datetime.now() - self.monitoring_start_time).total_seconds()
                monitoring_duration_hours = duration_seconds / 3600

            return {
                "dashboard_status": "active" if self.monitoring_active else "inactive",
                "timestamp": datetime.now().isoformat(),
                "data_history_length": len(self.data_history),  # Basic data collection count
                "system_info": {
                    "cpu_percent": system_data.get("cpu_percent", 0),
                    "memory_percent": memory_data.get("system", {}).get("percent", 0)
                },
                "long_term_monitoring": {
                    "status": "active" if self.monitoring_active else "inactive",
                    "data_points": len(self.advanced_data_history),  # Advanced monitoring points only
                    "monitoring_duration_hours": monitoring_duration_hours,
                    "interval": self.monitor_interval,
                    "alerts_sent": self.alert_count,
                    "latest_data": {
                        "processes": {
                            "menu_bar": {
                                "memory_rss_mb": memory_data.get("clipboard", {}).get("processes", [{}])[0].get("memory_mb", 0)
                            }
                        }
                    }
                },
                "advanced_profiling": {
                    "status": "active" if self.leak_detector.tracemalloc_enabled else "inactive",
                    "total_snapshots": len(self.leak_detector.memory_snapshots),
                    "tracemalloc_enabled": self.leak_detector.tracemalloc_enabled,
                    "latest_snapshot": {
                        "process_info": {
                            "memory_rss_mb": memory_data.get("clipboard", {}).get("total_memory_mb", 0)
                        },
                        "object_analysis": {
                            "total_objects": sum(self.leak_detector._get_object_counts().values())
                        }
                    }
                },
                "validation_results": {
                    "validation_data": []  # Placeholder for validation data
                }
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _auto_timeout_monitor(self):
        """Monitor for auto-timeout when in auto-start mode"""
        print(f"Auto-timeout monitor started (5-minute inactivity timeout)")

        while True:
            try:
                time.sleep(30)  # Check every 30 seconds

                # Calculate time since last activity
                time_since_activity = datetime.now() - self.last_activity_time
                minutes_inactive = time_since_activity.total_seconds() / 60

                # Don't timeout if advanced monitoring is active
                if self.monitoring_active:
                    continue

                # Check if we've exceeded the timeout
                if minutes_inactive >= self.auto_timeout_minutes:
                    # Graceful shutdown
                    if self.server:
                        threading.Thread(target=self.server.shutdown).start()
                    break

            except Exception as e:
                print(f"Error in auto-timeout monitor: {e}")
                time.sleep(60)  # Wait longer on error

    def run(self):
        """Run the unified dashboard server."""
        print(f"🚀 Starting Unified Memory Dashboard on http://localhost:{self.port}")

        # Start data collection in background
        def collect_data():
            while True:
                try:
                    data = self.collect_memory_data()
                    self.data_history.append(data)

                    # Limit history size
                    # Limit history size
                    if len(self.data_history) > self.max_history:
                        self.data_history = self.data_history[-self.max_history:]

                    time.sleep(1)  # Collect data every second
                except Exception as e:
                    print(f"Error collecting data: {e}")
                    time.sleep(5)

        def _start_dev_reloader(self, watched_file):
            """Start a file watcher thread to restart the server when the file changes (dev only)."""
            if self.dev_reload:
                return  # already running
            self.dev_reload = True

            def watcher():
                try:
                    last_mtime = os.path.getmtime(watched_file)
                except Exception:
                    last_mtime = None
                while self.dev_reload:
                    try:
                        time.sleep(1.0)
                        mtime = os.path.getmtime(watched_file)
                        if last_mtime is not None and mtime != last_mtime:
                            print("🔁 Detected change in unified_memory_dashboard.py — restarting server...")
                            # Gracefully shutdown
                            try:
                                if self.server:
                                    self.server.shutdown()
                            except Exception:
                                pass
                            os._exit(3)  # Let parent supervisor restart us; fallback to exit
                        last_mtime = mtime
                    except Exception:
                        continue

            t = threading.Thread(target=watcher, daemon=True)
            t.start()

        # Start background data collection
        data_thread = threading.Thread(target=collect_data)
        data_thread.daemon = True
        data_thread.start()

        # Start auto-timeout monitoring if in auto-start mode
        if self.auto_start_mode:
            timeout_thread = threading.Thread(target=self._auto_timeout_monitor)
            timeout_thread.daemon = True
            timeout_thread.start()

        # Open browser (only if not in auto-start mode)
        if not self.auto_start_mode:
            def open_browser():
                time.sleep(2)  # Wait for server to start
                webbrowser.open(f'http://localhost:{self.port}')

            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
        else:
            print(f"Auto-start mode: Dashboard available at http://localhost:{self.port} (no browser auto-open)")

        # Create request handler with dashboard instance
        def handler(*args, **kwargs):
            return self.RequestHandler(self, *args, **kwargs)

        # Run HTTP server
        try:
            self.server = HTTPServer(('localhost', self.port), handler)
            print(f"✅ Dashboard server started at http://localhost:{self.port}")
            # Start dev reloader if requested via env/flag
            enable_reload = os.environ.get('CLIPBOARD_DASHBOARD_DEV_RELOAD', '0') == '1' or '--dev-reload' in sys.argv
            if enable_reload:
                self._start_dev_reloader(os.path.abspath(__file__))
                print("🛠️ Dev auto-reload enabled (watching unified_memory_dashboard.py)")
            self.server.serve_forever()
        except Exception as e:
            print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    import argparse
    import os
    import sys

    # PROTECTION: Prevent recursive launches
    if 'CLIPBOARD_MONITOR_DASHBOARD_PARENT' in os.environ:
        parent_pid = os.environ.get('CLIPBOARD_MONITOR_DASHBOARD_PARENT')
        print(f"Dashboard launched by ClipboardMonitor parent PID {parent_pid}")

        # Check if parent is still running
        try:
            import psutil
            if not psutil.pid_exists(int(parent_pid)):
                print("Parent process no longer exists, exiting dashboard")
                sys.exit(0)
        except:
            pass

    # PROTECTION: Check for multiple dashboard instances (only for auto-start mode)
    # Manual starts are allowed to override existing instances
    if '--auto-start' in sys.argv:
        try:
            import psutil
            dashboard_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline)
                        if 'unified_memory_dashboard.py' in cmdline_str and proc.info['pid'] != os.getpid():
                            dashboard_processes.append(proc.info['pid'])
                except:
                    continue

            if len(dashboard_processes) > 0:
                print(f"Other dashboard instances detected ({len(dashboard_processes)}), exiting auto-start to prevent conflicts")
                sys.exit(0)
        except:
            pass  # If check fails, continue with caution
    else:
        print("Manual dashboard start - will override any existing instances")

    parser = argparse.ArgumentParser(description='Unified Memory Dashboard')
    parser.add_argument('--auto-start', action='store_true',
                       help='Start in auto-start mode (no browser, 5-minute timeout)')
    parser.add_argument('--port', type=int, default=8001,
                       help='Port to run the dashboard on (default: 8001)')

    args = parser.parse_args()

    dashboard = UnifiedMemoryDashboard(port=args.port, auto_start=args.auto_start)
    dashboard.run()
