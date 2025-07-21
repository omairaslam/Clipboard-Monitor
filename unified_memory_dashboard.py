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
        self.peak_total_memory = 0.0
        self.peak_menubar_cpu = 0.0
        self.peak_service_cpu = 0.0
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
            # Update activity time for any request
            self._update_activity()

            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.dashboard.render_dashboard_html().encode())
            elif self.path == '/api/memory':
                # Memory data for Memory tab charts - use the more comprehensive method
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_memory_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/current':
                # Current status including monitoring state (for Controls tab)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/data':
                # Comprehensive dashboard data for monitoring dashboard compatibility
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/processes':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_process_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/system':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_system_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/history':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.data_history[-200:])
                self.wfile.write(data.encode())
            elif self.path.startswith('/api/historical'):
                # Parse query parameters for time range
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                hours = int(params.get('hours', [24])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_historical_data(hours))
                self.wfile.write(data.encode())
            elif self.path.startswith('/api/analysis'):
                # Parse query parameters for time range
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                hours = int(params.get('hours', [24])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_analysis_data(hours))
                self.wfile.write(data.encode())
            elif self.path.startswith('/api/historical-chart'):
                # Enhanced historical data for chart
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    hours_param = params.get('hours', ['1'])[0]
                    resolution = params.get('resolution', ['full'])[0]

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
                        'time_range': 'error'
                    })
                    self.wfile.write(error_data.encode())
            elif self.path.startswith('/api/start_monitoring'):
                # Parse query parameters for interval
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                interval = int(params.get('interval', [30])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.start_advanced_monitoring(interval)
                self.wfile.write(json.dumps(result).encode())
            elif self.path == '/api/stop_monitoring':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.stop_advanced_monitoring()
                self.wfile.write(json.dumps(result).encode())
            elif self.path == '/api/force_gc':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.force_garbage_collection()
                self.wfile.write(json.dumps(result).encode())
            elif self.path == '/api/leak_analysis':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_leak_analysis())
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
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card h3 { 
            color: #2c3e50; 
            margin-bottom: 15px;
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
            margin-bottom: 20px;
            position: relative;
            height: 450px; /* Fixed height to prevent expansion */
        }
        .chart-wrapper {
            position: relative;
            height: 280px; /* Reduced height for more compact layout */
            width: 100%;
            overflow: hidden; /* Prevent chart from expanding beyond container */
        }
        .chart-wrapper canvas {
            max-height: 280px !important;
            max-width: 100% !important;
        }

        /* Button animations */
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
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        .tab {
            flex: 1;
            padding: 12px 20px;
            text-align: center;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .tab.active {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }
        .tab:not(.active):hover {
            background: rgba(52, 152, 219, 0.1);
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
        }
        .process-table {
            width: 100%;
            border-collapse: collapse;
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
        .process-table tr:hover {
            background: rgba(52, 152, 219, 0.05);
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
            gap: 15px;
        }
        .info-item {
            text-align: center;
            padding: 15px;
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
    </style>
</head>
<body>
    <div class="container">
        <!-- New 4-Box Dashboard Header -->
        <div class="header" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; padding: 12px; margin-bottom: 15px; border: 1px solid #dee2e6; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <!-- Compact Title and Status -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e0e0e0;">
                <h1 style="margin: 0; font-size: 16px; color: #333; font-weight: bold;">📊 Clipboard Monitor Dashboard</h1>
                <div style="display: flex; gap: 8px; align-items: center; font-size: 11px;">
                    <span style="background: #4CAF50; color: white; padding: 2px 6px; border-radius: 8px; font-weight: bold; display: flex; align-items: center; gap: 3px;">
                        <span>●</span> Connected
                    </span>
                    <span id="advanced-status" style="background: #999; color: white; padding: 2px 6px; border-radius: 8px; font-weight: bold; display: flex; align-items: center; gap: 3px;">
                        ⚫ Advanced
                    </span>
                </div>
            </div>

            <!-- Clean 4-Box Horizontal Layout -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; width: 100%;">

                <!-- Box 1: Menu Bar + Service -->
                <div style="background: white; border-radius: 6px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #2196F3;">
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
                <div style="background: white; border-radius: 6px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #FF9800;">
                    <div style="font-weight: bold; color: #FF9800; margin-bottom: 6px; font-size: 11px; text-align: center;">📊 Analytics</div>
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
                <div style="background: white; border-radius: 6px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #9C27B0;">
                    <div style="font-weight: bold; color: #9C27B0; margin-bottom: 6px; font-size: 11px; text-align: center;">💻 System</div>
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
                <div style="background: white; border-radius: 6px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #795548;">
                    <div style="font-weight: bold; color: #795548; margin-bottom: 6px; font-size: 11px; text-align: center;">📊 Session</div>
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
            <div class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</div>
            <div class="tab" onclick="switchTab('analysis')">🔍 Analysis & Controls</div>
            <div class="tab" onclick="switchTab('processes')">⚙️ Processes</div>
        </div>
        
        <!-- Consolidated Dashboard Tab -->
        <div id="dashboard-tab" class="tab-content active">




            <!-- Charts Section with Hybrid Controls -->
            <div class="chart-container" style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <h3 style="font-size: 16px; margin: 0; color: #333;">📈 <span id="chart-title">Real-time Memory Usage</span></h3>
                        <span style="font-size: 11px; color: #666; font-style: italic;" id="data-collection-info">Data collected every 2 seconds</span>
                    </div>
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <!-- Mode Toggle -->
                        <div style="display: flex; gap: 5px;">
                            <button id="realtime-btn" class="chart-mode-btn" onclick="chartManager.switchToRealtimeMode()"
                                    style="padding: 4px 8px; font-size: 11px; border: 1px solid #ddd; background: #4CAF50; color: white; border-radius: 4px; cursor: pointer;">
                                Real-time
                            </button>
                            <button id="historical-btn" class="chart-mode-btn" onclick="toggleHistoricalOptions()"
                                    style="padding: 4px 8px; font-size: 11px; border: 1px solid #ddd; background: #f5f5f5; color: #333; border-radius: 4px; cursor: pointer;">
                                Historical
                            </button>
                        </div>

                        <!-- Historical Range Options (hidden by default) -->
                        <div id="historical-options" style="display: none; gap: 5px;">
                            <select id="historical-range" onchange="handleRangeChange(this)"
                                    style="padding: 4px 6px; font-size: 11px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="1">Last Hour</option>
                                <option value="6">Last 6 Hours</option>
                                <option value="24">Last 24 Hours</option>
                                <option value="168">Last 7 Days</option>
                                <option value="all">Since Start ⚠️</option>
                            </select>
                            <select id="resolution-select" onchange="chartManager.changeResolution(this.value)"
                                    style="padding: 4px 6px; font-size: 11px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="full">Full Resolution</option>
                                <option value="10sec">10 Second Avg</option>
                                <option value="minute">1 Minute Avg</option>
                                <option value="hour">1 Hour Avg</option>
                            </select>
                        </div>

                        <!-- Chart Status -->
                        <div id="chart-status" style="font-size: 11px; color: #666;">
                            <span id="chart-mode-indicator">Real-time</span> •
                            <span id="chart-points-count">-- pts</span>
                        </div>

                        <!-- Legend -->
                        <div id="chart-legend" style="display: flex; gap: 15px; font-size: 12px;">
                            <div style="display: flex; align-items: center;">
                                <div style="width: 12px; height: 12px; background: #2196F3; margin-right: 4px; border-radius: 2px;"></div>
                                <span>Menu Bar App</span>
                            </div>
                            <div style="display: flex; align-items: center;">
                                <div style="width: 12px; height: 12px; background: #4CAF50; margin-right: 4px; border-radius: 2px;"></div>
                                <span>Main Service</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="chart-wrapper" style="height: 300px;">
                    <canvas id="memoryChart"></canvas>
                </div>
            </div>

            <!-- CPU Usage Chart -->
            <div class="chart-container" style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <h3 style="font-size: 16px; margin: 0; color: #333;">⚡ <span id="cpu-chart-title">Real-time CPU Usage</span></h3>
                        <span style="font-size: 11px; color: #666; font-style: italic;">Data collected every 2 seconds</span>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center;">
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



                        <!-- Chart Status -->
                        <div id="cpu-chart-status" style="font-size: 10px; color: #666;">
                            <span id="cpu-chart-mode-indicator">Real-time</span> •
                            <span id="cpu-chart-points-count">-- pts</span>
                        </div>

                        <!-- Legend -->
                        <div id="cpu-chart-legend" style="display: flex; gap: 15px; font-size: 12px;">
                            <div style="display: flex; align-items: center;">
                                <div style="width: 12px; height: 12px; background: #2196F3; margin-right: 4px; border-radius: 2px;"></div>
                                <span>Menu Bar App</span>
                            </div>
                            <div style="display: flex; align-items: center;">
                                <div style="width: 12px; height: 12px; background: #4CAF50; margin-right: 4px; border-radius: 2px;"></div>
                                <span>Main Service</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="chart-wrapper" style="height: 300px;">
                    <canvas id="cpuChart"></canvas>
                </div>
            </div>


        </div>

        <!-- Analysis Tab (Combined with Controls) -->
        <div id="analysis-tab" class="tab-content">
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4CAF50;">
                <h4 style="margin: 0 0 10px 0; color: #2e7d32;">🔍 Memory Analysis & Monitoring Dashboard</h4>
                <p style="margin: 0 0 10px 0;">This tab provides comprehensive memory leak detection, monitoring controls, and growth pattern analysis.</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
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

            <!-- Monitoring Controls Section (Moved from Controls Tab) -->
            <div class="card">
                <h3>⚙️ Advanced Monitoring Controls</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px;">
                    <div>
                        <label for="monitorInterval" style="display: block; margin-bottom: 5px;">Monitoring Interval:</label>
                        <select id="monitorInterval" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 15px;">
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
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <strong>Advanced Data Points:</strong> <span id="advanced-data-points">0</span><br>
                                    <strong>Advanced Collection Rate:</strong> <span id="collection-rate">Stopped</span><br>
                                    <small style="color: #666;">Leak detection & analysis data</small>
                                </div>
                                <div>
                                    <strong>Basic Data Points:</strong> <span id="basic-data-points">0</span><br>
                                    <strong>Basic Collection Rate:</strong> <span style="color: #4CAF50;">Every 1s</span><br>
                                    <small style="color: #666;">Real-time dashboard data</small>
                                </div>
                            </div>
                            <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
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
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px;">
                <div class="card">
                    <h3>⏱️ Analysis Time Range</h3>
                    <div style="margin-bottom: 15px;">
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
            <div class="card">
                <h3>🔍 Memory Leak Detection Results</h3>
                <div id="leak-analysis">
                    <div class="loading">Analyzing memory trends...</div>
                </div>
            </div>

            <div class="card">
                <h3>📈 Growth Trend Analysis</h3>
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
        </div>
        
        <!-- Processes Tab -->
        <div id="processes-tab" class="tab-content">
            <div class="card">
                <h3>🔍 Clipboard Monitor Processes</h3>
                <div class="process-list">
                    <table class="process-table">
                        <thead>
                            <tr>
                                <th>Process Name</th>
                                <th>Memory</th>
                                <th>CPU</th>
                            </tr>
                        </thead>
                        <tbody id="process-list">
                            <tr>
                                <td colspan="3" style="text-align: center; padding: 20px;">Loading processes...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        


        <!-- Controls Tab (Removed - Merged with Analysis Tab) -->
    </div>
    
    <script>
        // Global variables
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
        function switchTab(tabName) {
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

            // Add active class to clicked tab
            event.target.classList.add('active');

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
                processRefreshInterval = setInterval(fetchProcessData, 2000); // Refresh every 2 seconds
            }
        }
        
        // Initialize memory chart
        const ctx = document.getElementById('memoryChart').getContext('2d');
        const chart = new Chart(ctx, {
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
                const response = await fetch('/api/memory');
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
            }
        }
        
        function updateDashboard(data) {
            try {
                // Use the pre-processed data passed from fetchMemoryData
                const menubarMemory = data.menubar_memory || 0;
                const serviceMemory = data.service_memory || 0;
                const menubarCpu = data.menubar_cpu || 0;
                const serviceCpu = data.service_cpu || 0;
                const totalMemory = data.total_memory || 0;

                // Use server-provided peak values
                const peakMenubarMemory = data.peak_menubar_memory || 0;
                const peakServiceMemory = data.peak_service_memory || 0;
                const peakTotalMemory = data.peak_total_memory || 0;
                const peakMenubarCpu = data.peak_menubar_cpu || 0;
                const peakServiceCpu = data.peak_service_cpu || 0;
                const peakTotalCpu = data.peak_total_cpu || 0;
                const sessionStartTime = data.session_start_time ? new Date(data.session_start_time) : new Date();

                // Helper function to safely update element
                function safeUpdateElement(id, value) {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = value;
                    } else {
                        console.warn('Element not found:', id);
                    }
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

                // Update detailed process metrics from API data
                const processes = (data.clipboard && data.clipboard.processes) ? data.clipboard.processes : [];
                const menubarProcess = processes.find(p => p.process_type === 'menu_bar');
                const serviceProcess = processes.find(p => p.process_type === 'main_service');

                // Update Menu Bar detailed metrics
                if (menubarProcess) {
                    safeUpdateElement('header-menubar-threads', menubarProcess.threads || '--');
                    safeUpdateElement('header-menubar-handles', menubarProcess.handles || '--');
                    safeUpdateElement('header-menubar-uptime', menubarProcess.uptime || '--');
                    safeUpdateElement('header-menubar-restarts', menubarProcess.restarts || '0');
                }

                // Update Service detailed metrics
                if (serviceProcess) {
                    safeUpdateElement('header-service-threads', serviceProcess.threads || '--');
                    safeUpdateElement('header-service-handles', serviceProcess.handles || '--');
                    safeUpdateElement('header-service-uptime', serviceProcess.uptime || '--');
                    safeUpdateElement('header-service-restarts', serviceProcess.restarts || '0');
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
            } else {
                // Fallback to old method if chart manager not ready
                const time = new Date(data.timestamp).toLocaleTimeString();

                chart.data.labels.push(time);
                chart.data.datasets[0].data.push(data.menubar_memory);
                chart.data.datasets[1].data.push(data.service_memory);

                // Keep only last 50 data points for performance
                if (chart.data.labels.length > 50) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                }

                chart.update('none');
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
                
                chart.data.labels = recentHistory.map(d => new Date(d.timestamp).toLocaleTimeString());
                chart.data.datasets[0].data = recentHistory.map(d => d.menubar_memory);
                chart.data.datasets[1].data = recentHistory.map(d => d.service_memory);
                
                chart.update();
                
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

                // Update data points counter in header
                const headerDataPointsElement = document.getElementById('header-data-points');
                if (headerDataPointsElement && chart && chart.data && chart.data.labels) {
                    headerDataPointsElement.textContent = chart.data.labels.length + ' pts';
                }
            } catch (error) {
                console.error('Error fetching system data:', error);
            }
        }
        
        async function fetchProcessData() {
            try {
                const response = await fetch('/api/processes');
                const data = await response.json();

                const processList = document.getElementById('process-list');
                processList.innerHTML = '';

                if (data.clipboard_processes && data.clipboard_processes.length > 0) {
                    data.clipboard_processes.forEach(proc => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td class="process-name">${proc.display_name || proc.name} (${proc.pid})</td>
                            <td class="process-memory">${proc.memory_mb.toFixed(1)} MB</td>
                            <td class="process-cpu">${proc.cpu_percent.toFixed(1)}%</td>
                        `;
                        processList.appendChild(row);
                    });
                } else {
                    processList.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px;">No Clipboard Monitor processes found</td></tr>';
                }
            } catch (error) {
                console.error('Error fetching process data:', error);
                const processList = document.getElementById('process-list');
                processList.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px; color: #e74c3c;">Error loading processes</td></tr>';
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

                        // Show success message
                        const message = `✅ ${result.message}\\n\\n📊 Background collection: ${result.background_collection}\\n⏱️ Interval: ${result.interval} seconds\\n\\n💡 Data will be collected automatically and status will update every 5 seconds.`;
                        alert(message);

                        updateMonitoringStatus();
                    }
                } catch (error) {
                    alert('❌ Error starting monitoring: ' + error);
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

                        const message = `✅ ${result.message}\\n\\n📊 Session Summary:\\n• Duration: ${durationText}\\n• Advanced Data Points: ${dataPoints}\\n• Background collection: ${result.background_collection}\\n\\n💾 What happens next:\\n• Advanced monitoring data is preserved for analysis\\n• Basic data collection continues for real-time charts\\n• Leak detection analysis is available in Analysis tab\\n• You can restart advanced monitoring anytime`;
                        alert(message);

                        updateMonitoringStatus();
                    }
                } catch (error) {
                    alert('❌ Error stopping monitoring: ' + error);
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
                alert(message);

                // Refresh memory data to show the effect
                await fetchMemoryData();

            } catch (error) {
                // Error feedback
                gcBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    gcBtn.innerHTML = originalText;
                }, 2000);

                alert('❌ Error during garbage collection: ' + error);
            } finally {
                gcBtn.disabled = false;
            }
        }

        async function updateTimeRange() {
            await loadAnalysisData();
        }

        async function updateAnalysisTimeRange() {
            await loadAnalysisData();
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
                // Get time range from either selector (fallback to 24 hours)
                const timeRangeElement = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
                const hours = timeRangeElement ? timeRangeElement.value : 24;

                console.log(`Loading analysis data for ${hours} hours`);

                // Fetch analysis data
                const response = await fetch(`/api/analysis?hours=${hours}`);
                const data = await response.json();
                updateAnalysisDisplay(data);

                // Fetch leak analysis
                const leakResponse = await fetch('/api/leak_analysis');
                const leakData = await leakResponse.json();
                updateLeakAnalysisDisplay(leakData);

                // Update analysis summary
                updateAnalysisSummary(data, hours);

                // Update monitoring history
                updateMonitoringHistory();

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

            let leakHtml = '<div style="display: grid; gap: 15px;">';
            let trendHtml = '<div style="display: grid; gap: 15px;">';

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
            trendAnalysis.innerHTML = trendHtml;
        }

        function updateLeakAnalysisDisplay(leakData) {
            const leakAnalysis = document.getElementById('leak-analysis');
            if (!leakAnalysis) return;

            if (!leakData || Object.keys(leakData).length === 0) {
                leakAnalysis.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No leak analysis data available. Start advanced monitoring to collect data.</div>';
                return;
            }

            let html = '<div style="display: grid; gap: 15px;">';
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
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
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

                const status = data.dashboard_status || 'inactive';
                const advancedDataPoints = data.long_term_monitoring?.data_points || 0;
                const basicDataPoints = data.data_history_length || 0;
                const duration = data.long_term_monitoring?.monitoring_duration_hours || 0;
                const isActive = status === 'active';

                // Update status indicator and text
                if (statusIndicator && statusText) {
                    statusIndicator.className = isActive ? 'status-active' : 'status-inactive';
                    statusText.textContent = status.toUpperCase();
                    statusText.style.color = isActive ? '#4CAF50' : '#666';
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
                        const interval = data.long_term_monitoring?.interval || 30;
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
                const message = `✅ Dashboard Data Refreshed Successfully!\\n\\n📊 Updated Components:\\n• Memory usage charts and statistics\\n• System resource information\\n• Process monitoring data\\n• Memory leak analysis\\n• Advanced monitoring status\\n\\n💡 All data is now current as of ${new Date().toLocaleTimeString()}`;
                alert(message);

            } catch (error) {
                // Error feedback
                refreshBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

                alert('Error refreshing data: ' + error);
            } finally {
                refreshBtn.disabled = false;
            }
        }

        // Hybrid Memory Chart Manager Class
        class HybridMemoryChart {
            constructor() {
                this.mode = 'realtime'; // 'realtime' or 'historical'
                this.realtimeData = [];
                this.historicalData = null;
                this.maxRealtimePoints = 300; // 5 minutes at 1-second intervals
                this.currentTimeRange = '1';
                this.currentResolution = 'full';
                this.isInitialized = false;
            }

            async initialize() {
                if (this.isInitialized) return;

                // Load recent historical data for context (last hour)
                await this.loadRecentHistory();
                this.updateUI();
                this.isInitialized = true;
            }

            async loadRecentHistory() {
                try {
                    const response = await fetch('/api/historical-chart?hours=1&resolution=full');
                    const data = await response.json();

                    // Populate chart with recent data
                    this.realtimeData = data.points || [];

                    // Limit to max points for performance
                    if (this.realtimeData.length > this.maxRealtimePoints) {
                        this.realtimeData = this.realtimeData.slice(-this.maxRealtimePoints);
                    }

                    this.updateChart();
                } catch (error) {
                    console.error('Error loading recent history:', error);
                    this.realtimeData = [];
                }
            }

            addRealtimePoint(newPoint) {
                // Always collect real-time data for the buffer
                this.realtimeData.push(newPoint);

                // Keep only recent points for performance
                if (this.realtimeData.length > this.maxRealtimePoints) {
                    this.realtimeData.shift();
                }

                // Update chart only in real-time mode
                // Historical mode updates are handled by the periodic timer
                if (this.mode === 'realtime') {
                    this.updateChart();
                }
            }

            async switchToHistoricalMode(timeRange) {
                this.mode = 'historical';
                this.currentTimeRange = timeRange;

                try {
                    // Auto-adjust resolution for large datasets
                    let resolution = this.currentResolution;
                    if (timeRange === 'all' && resolution === 'full') {
                        resolution = 'minute'; // Default to 1-minute for "since start"
                        this.currentResolution = 'minute';
                        document.getElementById('resolution-select').value = 'minute';
                    } else if (timeRange === '168' && resolution === 'full') {
                        resolution = '10sec'; // 10-second for 7 days
                        this.currentResolution = '10sec';
                        document.getElementById('resolution-select').value = '10sec';
                    }

                    const response = await fetch(`/api/historical-chart?hours=${timeRange}&resolution=${resolution}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();

                    this.historicalData = data.points || [];

                    // Check if dataset is too large for browser performance
                    if (this.historicalData.length > 10000) {
                        console.warn(`Large dataset (${this.historicalData.length} points), consider using lower resolution`);
                        // Could auto-reduce resolution here if needed
                    }

                    this.updateChart();
                    this.updateUI();
                } catch (error) {
                    console.error('Error loading historical data:', error);
                    alert(`Failed to load historical data: ${error.message}\\nTrying real-time mode instead.`);
                    this.switchToRealtimeMode();
                }
            }

            switchToRealtimeMode() {
                this.mode = 'realtime';
                this.updateChart();
                this.updateUI();
            }

            async refreshHistoricalData() {
                if (this.mode !== 'historical') return;

                try {
                    // Show subtle loading indicator
                    const chartTitle = document.getElementById('chart-title');
                    const originalTitle = chartTitle ? chartTitle.textContent : '';
                    if (chartTitle && !originalTitle.includes('🔄')) {
                        chartTitle.textContent = originalTitle + ' 🔄';
                    }

                    const response = await fetch(`/api/historical?range=${this.currentTimeRange}&resolution=${this.currentResolution}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();

                    this.historicalData = data.points || [];
                    this.updateChart();

                    // Remove loading indicator
                    if (chartTitle && chartTitle.textContent.includes('🔄')) {
                        chartTitle.textContent = originalTitle;
                    }
                } catch (error) {
                    console.error('Error refreshing historical data:', error);
                    // Remove loading indicator on error
                    const chartTitle = document.getElementById('chart-title');
                    if (chartTitle && chartTitle.textContent.includes('🔄')) {
                        chartTitle.textContent = chartTitle.textContent.replace(' 🔄', '');
                    }
                    // Don't show alert for auto-refresh errors, just log them
                }
            }

            async changeResolution(resolution) {
                if (this.mode !== 'historical') return;

                console.log(`Changing resolution to: ${resolution}`);
                this.currentResolution = resolution;

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

            updateChart() {
                const data = this.mode === 'realtime' ? this.realtimeData : this.historicalData;

                if (!data || data.length === 0) {
                    chart.data.labels = [];
                    chart.data.datasets[0].data = [];
                    chart.data.datasets[1].data = [];
                } else {
                    chart.data.labels = data.map(d => {
                        const date = new Date(d.timestamp);
                        return this.mode === 'realtime' ?
                            date.toLocaleTimeString() :
                            this.formatHistoricalTime(date);
                    });
                    chart.data.datasets[0].data = data.map(d => d.menubar_memory || 0);
                    chart.data.datasets[1].data = data.map(d => d.service_memory || 0);
                }

                chart.update('none');

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
            }

            formatHistoricalTime(date) {
                if (this.currentTimeRange === 'all' || parseInt(this.currentTimeRange) > 24) {
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                } else {
                    return date.toLocaleTimeString();
                }
            }

            updateUI() {
                const realtimeBtn = document.getElementById('realtime-btn');
                const historicalBtn = document.getElementById('historical-btn');
                const historicalOptions = document.getElementById('historical-options');
                const chartTitle = document.getElementById('chart-title');
                const chartModeIndicator = document.getElementById('chart-mode-indicator');

                if (this.mode === 'realtime') {
                    realtimeBtn.style.background = '#4CAF50';
                    realtimeBtn.style.color = 'white';
                    historicalBtn.style.background = '#f5f5f5';
                    historicalBtn.style.color = '#333';
                    historicalOptions.style.display = 'none';

                    if (chartTitle) chartTitle.textContent = 'Real-time Memory Usage';
                    if (chartModeIndicator) chartModeIndicator.textContent = 'Real-time';
                } else {
                    realtimeBtn.style.background = '#f5f5f5';
                    realtimeBtn.style.color = '#333';
                    historicalBtn.style.background = '#2196F3';
                    historicalBtn.style.color = 'white';
                    historicalOptions.style.display = 'flex';

                    const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                     this.currentTimeRange === '1' ? 'Last Hour' :
                                     this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                     this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                     this.currentTimeRange === '168' ? 'Last 7 Days' :
                                     `Last ${this.currentTimeRange} Hours`;

                    if (chartTitle) chartTitle.textContent = `Historical Memory Usage (${rangeText})`;
                    if (chartModeIndicator) chartModeIndicator.textContent = `Historical (${rangeText})`;
                }
            }
        }

        // Helper function for historical options toggle
        function toggleHistoricalOptions() {
            const historicalOptions = document.getElementById('historical-options');
            const isVisible = historicalOptions.style.display !== 'none';

            if (isVisible) {
                chartManager.switchToRealtimeMode();
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
                            // Reset to real-time mode
                            chartManager.switchToRealtimeMode();
                            return;
                        }
                    } else {
                        chartManager.switchToHistoricalMode(selectedRange);
                    }
                }
            }
        }

        // Helper function to handle range selection changes
        function handleRangeChange(selectElement) {
            const selectedRange = selectElement.value;
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

        // Initialize Hybrid Chart Manager
        const chartManager = new HybridMemoryChart();

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

        // Start memory data polling every 2 seconds
        setInterval(fetchMemoryData, 2000);

        // Fetch additional data every 10 seconds
        setInterval(() => {
            fetchSystemData();
            fetchProcessData();
            loadAnalysisData();
        }, 10000);

        // Auto-refresh historical data every 10 seconds when in historical mode
        setInterval(() => {
            if (chartManager && chartManager.mode === 'historical') {
                chartManager.refreshHistoricalData();
            }
        }, 10000);

        // Initialize chart manager after chart is ready
        setTimeout(async () => {
            await chartManager.initialize();
        }, 1000);

        // Initial fetch
        fetchMemoryData();
        fetchSystemData();
        fetchProcessData();
        loadAnalysisData();
        updateMonitoringStatus();

        // Update monitoring status every 5 seconds
        setInterval(updateMonitoringStatus, 5000);
    </script>
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
        return {
            'clipboard_processes': memory_data.get('clipboard', {}).get('processes', []),
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
            menubar_cpu = 0
            service_cpu = 0

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

            # Track peak CPU values
            if menubar_cpu > self.peak_menubar_cpu:
                self.peak_menubar_cpu = menubar_cpu

            if service_cpu > self.peak_service_cpu:
                self.peak_service_cpu = service_cpu

            # Track peak totals
            total_memory = menubar_memory + service_memory
            total_cpu = menubar_cpu + service_cpu

            if total_memory > self.peak_total_memory:
                self.peak_total_memory = total_memory

            if total_cpu > self.peak_total_cpu:
                self.peak_total_cpu = total_cpu

            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': round(menubar_memory, 2),
                'service_memory': round(service_memory, 2),
                'total_memory': round(total_memory, 2),
                'menubar_cpu': round(menubar_cpu, 2),
                'service_cpu': round(service_cpu, 2),
                'total_cpu': round(total_cpu, 2),
                'peak_menubar_memory': round(self.peak_menubar_memory, 2),
                'peak_service_memory': round(self.peak_service_memory, 2),
                'peak_total_memory': round(self.peak_total_memory, 2),
                'peak_menubar_cpu': round(self.peak_menubar_cpu, 2),
                'peak_service_cpu': round(self.peak_service_cpu, 2),
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
                    if len(self.data_history) > self.max_history:
                        self.data_history = self.data_history[-self.max_history:]

                    time.sleep(1)  # Collect data every second
                except Exception as e:
                    print(f"Error collecting data: {e}")
                    time.sleep(5)

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
