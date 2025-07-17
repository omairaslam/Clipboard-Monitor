#!/usr/bin/env python3
"""
Unified Memory Dashboard - Combines Memory Visualizer and Monitoring Dashboard
Provides comprehensive real-time monitoring with multiple views and analytics.
"""

import json
import psutil
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
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_memory_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/current':
                # Current status including monitoring state (for Controls tab)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/memory':
                # Memory data for Memory tab charts
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_memory_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/data':
                # Comprehensive dashboard data for monitoring dashboard compatibility
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/processes':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_process_data())
                self.wfile.write(data.encode())
            elif self.path == '/api/system':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
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

                    print(f"Historical chart request: hours={hours_param}, resolution={resolution}")

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

                    print(f"Returning {len(chart_data['points'])} points for chart")

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
            height: 400px; /* Fixed height for chart wrapper */
            width: 100%;
            overflow: hidden; /* Prevent chart from expanding beyond container */
        }
        .chart-wrapper canvas {
            max-height: 400px !important;
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
            max-height: 300px;
            overflow-y: auto;
        }
        .process-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
            transition: background 0.2s ease;
        }
        .process-item:hover {
            background: rgba(52, 152, 219, 0.05);
        }
        .process-name {
            font-weight: 600;
            color: #2c3e50;
        }
        .process-memory {
            color: #e74c3c;
            font-weight: bold;
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
        <!-- Professional Dashboard Header with All Information -->
        <div class="header" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; padding: 15px; margin-bottom: 20px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <!-- Row 1: Title with Status Indicators -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h1 style="margin: 0; font-size: 20px; color: #333; font-weight: bold;">📊 Clipboard Monitor - Unified Memory Dashboard</h1>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="display: flex; align-items: center;">
                        <div id="dashboard-status-light" style="width: 10px; height: 10px; border-radius: 50%; background: #ccc; margin-right: 6px;"></div>
                        <span style="font-weight: bold; color: #666; font-size: 14px;" id="dashboard-status-text">Connecting...</span>
                    </div>
                    <div id="monitoring-status-indicator" style="display: none; align-items: center;">
                        <div class="pulse-dot" style="width: 8px; height: 8px; border-radius: 50%; background: #F44336; margin-right: 6px; animation: pulse 1.5s infinite;"></div>
                        <span style="font-weight: bold; color: #F44336; font-size: 14px;">Advanced Monitoring</span>
                    </div>
                </div>
            </div>

            <!-- Row 2: Separator Line -->
            <div style="height: 1px; background: linear-gradient(90deg, #dee2e6 0%, #adb5bd 50%, #dee2e6 100%); margin-bottom: 10px;"></div>

            <!-- Row 3: Memory Metrics -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 13px; color: #555; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: bold; color: #333; margin-right: 10px;">💾 Memory:</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">📱 Menu Bar</span>
                    <span id="header-menubar-memory" style="color: #2196F3; font-weight: bold; width: 50px; display: inline-block; text-align: right;">--</span>
                    <span style="color: #666; font-size: 11px; margin-left: 3px;">(↑</span>
                    <span id="header-menubar-peak" style="color: #FF5722; font-weight: bold; font-size: 11px; width: 45px; display: inline-block; text-align: right; margin-left: 2px;">--</span>
                    <span style="color: #666; font-size: 11px;">)</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">⚙️ Service</span>
                    <span id="header-service-memory" style="color: #4CAF50; font-weight: bold; width: 50px; display: inline-block; text-align: right;">--</span>
                    <span style="color: #666; font-size: 11px; margin-left: 3px;">(↑</span>
                    <span id="header-service-peak" style="color: #FF5722; font-weight: bold; font-size: 11px; width: 45px; display: inline-block; text-align: right; margin-left: 2px;">--</span>
                    <span style="color: #666; font-size: 11px;">)</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">📊 Total</span>
                    <span id="header-total-memory" style="color: #FF9800; font-weight: bold; width: 55px; display: inline-block; text-align: right;">--</span>
                    <span style="color: #666; font-size: 11px; margin-left: 3px;">(↑</span>
                    <span id="header-total-peak" style="color: #FF5722; font-weight: bold; font-size: 11px; width: 50px; display: inline-block; text-align: right; margin-left: 2px;">--</span>
                    <span style="color: #666; font-size: 11px;">)</span>
                </div>
            </div>

            <!-- Row 4: System Metrics -->
            <div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 13px; color: #555; align-items: center;">
                <span style="font-weight: bold; color: #333; margin-right: 10px;">🖥️ System:</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">🧠 RAM</span>
                    <span id="header-system-memory" style="color: #9C27B0; font-weight: bold; width: 35px; display: inline-block; text-align: right;">--</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">⚡ CPU</span>
                    <span id="header-cpu-usage" style="color: #F44336; font-weight: bold; width: 35px; display: inline-block; text-align: right;">--</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">💽 Total</span>
                    <span id="header-total-ram" style="color: #607D8B; font-weight: bold; width: 35px; display: inline-block; text-align: right;">--</span>
                    <span style="color: #666; margin: 0 2px;">GB</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">✅ Available</span>
                    <span id="header-available-ram" style="color: #4CAF50; font-weight: bold; width: 35px; display: inline-block; text-align: right;">--</span>
                    <span style="color: #666; margin: 0 2px;">GB</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">⏰ Uptime</span>
                    <span id="header-uptime" style="color: #795548; font-weight: bold; width: 60px; display: inline-block; text-align: right;">--</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">📈 Data Points</span>
                    <span id="header-data-points" style="color: #607D8B; font-weight: bold; width: 40px; display: inline-block; text-align: right;">--</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">🕐 Session</span>
                    <span id="header-session-time" style="color: #795548; font-weight: bold; width: 50px; display: inline-block; text-align: right;">--</span>
                </div>
                <span style="color: #ddd;">•</span>
                <div style="display: flex; align-items: center;">
                    <span style="font-weight: bold; color: #666; margin-right: 4px;">🔄 Updated</span>
                    <span id="header-last-update" style="color: #666; font-size: 12px; width: 70px; display: inline-block; text-align: right;">--</span>
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
            <div class="chart-container" style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h3 style="font-size: 16px; margin: 0; color: #333;">📈 <span id="chart-title">Real-time Memory Usage</span></h3>
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
                <div id="process-list" class="process-list">
                    <div class="process-item">
                        <span>Loading processes...</span>
                    </div>
                </div>
            </div>
        </div>
        


        <!-- Controls Tab (Removed - Merged with Analysis Tab) -->
    </div>
    
    <script>
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

            // Resize charts when switching to dashboard tab to fix any sizing issues
            if (tabName === 'dashboard') {
                setTimeout(() => {
                    if (typeof chart !== 'undefined') {
                        chart.resize();
                    }

                }, 100);
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
                        radius: 3,
                        hoverRadius: 6
                    }
                }
            }
        });
        
        // Polling for real-time updates (simpler than WebSockets)
        let isConnected = false;

        async function fetchMemoryData() {
            try {
                console.log('Fetching memory data from /api/memory...');
                const response = await fetch('/api/memory');  // Use /api/memory for memory tab data
                console.log('Response status:', response.status, response.statusText);

                if (response.ok) {
                    const data = await response.json();
                    console.log('Memory data received:', data);

                    if (!isConnected) {
                        // Update banner status
                        const statusLight = document.getElementById('dashboard-status-light');
                        const statusText = document.getElementById('dashboard-status-text');
                        if (statusLight && statusText) {
                            statusLight.style.background = '#4CAF50';
                            statusText.textContent = 'Connected';
                            statusText.style.color = '#4CAF50';
                            console.log('Connection status updated to Connected');
                        }
                        isConnected = true;
                    }

                    // Update dashboard with current data
                    if (data.clipboard) {
                        // Use process_type for accurate identification
                        const menubarProcess = data.clipboard.processes.find(p => p.process_type === 'menu_bar');

                        // For main service, if there are multiple, pick the one with highest memory (most active)
                        const serviceProcesses = data.clipboard.processes.filter(p => p.process_type === 'main_service');
                        const serviceProcess = serviceProcesses.length > 0 ?
                            serviceProcesses.reduce((prev, current) => (prev.memory_mb > current.memory_mb) ? prev : current) :
                            null;

                        const menubarMemory = menubarProcess ? menubarProcess.memory_mb : 0;
                        const serviceMemory = serviceProcess ? serviceProcess.memory_mb : 0;

                        // Optional debug output (can be enabled for troubleshooting)
                        // console.log('Process detection:', {
                        //     menubarProcess: menubarProcess ? `PID ${menubarProcess.pid}: ${menubarProcess.memory_mb} MB` : 'Not found',
                        //     serviceProcess: serviceProcess ? `PID ${serviceProcess.pid}: ${serviceProcess.memory_mb} MB` : 'Not found'
                        // });

                        updateDashboard({
                            timestamp: data.timestamp,
                            menubar_memory: menubarMemory,
                            service_memory: serviceMemory,
                            total_memory: menubarMemory + serviceMemory
                        });
                    }
                } else {
                    throw new Error('Failed to fetch data');
                }
            } catch (error) {
                console.error('Error fetching memory data:', error);
                console.error('Error details:', error.message, error.stack);

                if (isConnected) {
                    // Update banner status
                    const statusLight = document.getElementById('dashboard-status-light');
                    const statusText = document.getElementById('dashboard-status-text');
                    if (statusLight && statusText) {
                        statusLight.style.background = '#f44336';
                        statusText.textContent = 'Disconnected';
                        statusText.style.color = '#f44336';
                        console.log('Connection status updated to Disconnected');
                    }
                    isConnected = false;
                }
            }
        }
        
        function updateDashboard(data) {
            // Use server-provided peak values
            const peakMenubarMemory = data.peak_menubar_memory || 0;
            const peakServiceMemory = data.peak_service_memory || 0;
            const peakTotalMemory = data.peak_total_memory || 0;
            const sessionStartTime = data.session_start_time ? new Date(data.session_start_time) : new Date();

            // Update header metrics (moved to header)
            document.getElementById('header-menubar-memory').textContent = data.menubar_memory.toFixed(1) + 'MB';
            document.getElementById('header-menubar-peak').textContent = (peakMenubarMemory || data.menubar_memory || 0).toFixed(1) + 'MB';
            document.getElementById('header-service-memory').textContent = data.service_memory.toFixed(1) + 'MB';
            document.getElementById('header-service-peak').textContent = (peakServiceMemory || data.service_memory || 0).toFixed(1) + 'MB';
            document.getElementById('header-total-memory').textContent = data.total_memory.toFixed(1) + 'MB';
            document.getElementById('header-total-peak').textContent = (peakTotalMemory || data.total_memory || 0).toFixed(1) + 'MB';

            // Update session time - use persistent session start time
            if (!globalSessionStartTime && data.session_start_time) {
                globalSessionStartTime = new Date(data.session_start_time);
            }

            if (globalSessionStartTime) {
                const sessionDuration = new Date() - globalSessionStartTime;
                const hours = Math.floor(sessionDuration / (1000 * 60 * 60));
                const minutes = Math.floor((sessionDuration % (1000 * 60 * 60)) / (1000 * 60));
                document.getElementById('header-session-time').textContent = `${hours}h ${minutes}m`;
            } else {
                document.getElementById('header-session-time').textContent = '0h 0m';
            }

            // Update last update time in header
            document.getElementById('header-last-update').textContent = new Date(data.timestamp).toLocaleTimeString();

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
                        const item = document.createElement('div');
                        item.className = 'process-item';
                        item.innerHTML = `
                            <div>
                                <div class="process-name">${proc.name} (PID: ${proc.pid})</div>
                                <div style="font-size: 0.9em; color: #7f8c8d;">CPU: ${proc.cpu_percent}%</div>
                            </div>
                            <div class="process-memory">${proc.memory_mb.toFixed(1)} MB</div>
                        `;
                        processList.appendChild(item);
                    });
                } else {
                    processList.innerHTML = '<div class="process-item"><span>No Clipboard Monitor processes found</span></div>';
                }
            } catch (error) {
                console.error('Error fetching process data:', error);
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
                console.log('🔄 Refreshing memory data...');
                await fetchMemoryData();

                console.log('🔄 Refreshing system data...');
                await fetchSystemData();

                console.log('🔄 Refreshing process data...');
                await fetchProcessData();

                console.log('🔄 Refreshing analysis data...');
                await loadAnalysisData();

                console.log('🔄 Refreshing monitoring status...');
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

                    console.log(`Loading historical data: range=${timeRange}, resolution=${resolution}`);

                    const response = await fetch(`/api/historical-chart?hours=${timeRange}&resolution=${resolution}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();
                    console.log(`Loaded ${data.points?.length || 0} historical points`);

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
                    console.log(`🔄 Auto-refreshing historical data: range=${this.currentTimeRange}, resolution=${this.currentResolution}`);

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
                    console.log(`📊 Refreshed ${data.points?.length || 0} historical points`);

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

            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent', 'create_time']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()

                        # Enhanced detection for clipboard processes
                        is_clipboard_process = any(keyword in cmdline_str for keyword in [
                            'clipboard', 'menu_bar_app', 'main.py'
                        ]) or (
                            'python' in proc.info['name'].lower() and
                            any(path_part in cmdline_str for path_part in [
                                'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ])
                        )

                        if is_clipboard_process:
                            memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                            total_clipboard_memory += memory_mb

                            # Determine process type for better identification (consistent with collect_memory_data)
                            process_type = "unknown"
                            if ('clipboardmonitormenubar' in cmdline_str.lower() or
                                'menu_bar_app.py' in cmdline_str):
                                process_type = "menu_bar"
                            elif (('clipboardmonitor.app/contents/macos/clipboardmonitor' in cmdline_str.lower() and
                                   'menubar' not in cmdline_str.lower()) or
                                  ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                      'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                                  ]))):
                                process_type = "main_service"
                            elif 'unified_memory_dashboard.py' in cmdline_str:
                                process_type = "dashboard"

                            clipboard_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'memory_mb': round(memory_mb, 2),
                                'cpu_percent': proc.info['cpu_percent'],
                                'create_time': datetime.fromtimestamp(proc.info['create_time']).isoformat(),
                                'process_type': process_type,
                                'cmdline_snippet': cmdline_str[:100] + "..." if len(cmdline_str) > 100 else cmdline_str
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return {
                'system': {
                    'total_gb': round(system_memory.total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(system_memory.available / 1024 / 1024 / 1024, 2),
                    'used_gb': round((system_memory.total - system_memory.available) / 1024 / 1024 / 1024, 2),
                    'percent': system_memory.percent
                },
                'clipboard': {
                    'processes': clipboard_processes,
                    'total_memory_mb': round(total_clipboard_memory, 2),
                    'process_count': len(clipboard_processes)
                },
                'timestamp': datetime.now().isoformat()
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
        """Collect current memory usage data for WebSocket updates."""
        try:
            menubar_memory = 0
            service_memory = 0

            # Debug: collect all clipboard-related processes
            clipboard_processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()

                        # Check if this is a clipboard-related process
                        is_clipboard_process = any(keyword in cmdline_str for keyword in [
                            'clipboard', 'menu_bar_app', 'main.py'
                        ])

                        if is_clipboard_process:
                            memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                            clipboard_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline_str,
                                'memory_mb': memory_mb
                            })

                            # Improved detection logic - support both PyInstaller and Python execution
                            if ('clipboardmonitormenubar' in cmdline_str.lower() or
                                'menu_bar_app.py' in cmdline_str):
                                menubar_memory = memory_mb
                            elif (('clipboardmonitor.app/contents/macos/clipboardmonitor' in cmdline_str.lower() and
                                   'menubar' not in cmdline_str.lower()) or
                                  ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                      'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                                  ]))):
                                # Only use this if we haven't found a main service yet, or if this one has more memory (likely the active one)
                                if service_memory == 0 or memory_mb > service_memory:
                                    service_memory = memory_mb

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

            # Track peak total memory
            total_memory = menubar_memory + service_memory
            if total_memory > self.peak_total_memory:
                self.peak_total_memory = total_memory

            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': round(menubar_memory, 2),
                'service_memory': round(service_memory, 2),
                'total_memory': round(total_memory, 2),
                'peak_menubar_memory': round(self.peak_menubar_memory, 2),
                'peak_service_memory': round(self.peak_service_memory, 2),
                'peak_total_memory': round(self.peak_total_memory, 2),
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

        print(f"Resolution filter: {len(data)} -> {len(filtered)} points (interval: {interval}s)")
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
                print(f"Collected data: menubar={memory_data.get('menubar_memory', 0):.1f}MB, service={memory_data.get('service_memory', 0):.1f}MB")

                # Add to advanced monitoring history (separate from basic data collection)
                self.advanced_data_history.append(memory_data)
                print(f"Advanced data history now has {len(self.advanced_data_history)} points")

                # Limit advanced history size
                if len(self.advanced_data_history) > self.max_history:
                    self.advanced_data_history = self.advanced_data_history[-self.max_history:]
                    print(f"Trimmed advanced history to {len(self.advanced_data_history)} points")

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

                            if menubar_growth > 5.0:  # More than 5MB growth
                                print(f"⚠️  Menu Bar memory growth detected: +{menubar_growth:.1f}MB")

                            if service_growth > 5.0:  # More than 5MB growth
                                print(f"⚠️  Service memory growth detected: +{service_growth:.1f}MB")

                    except Exception as e:
                        print(f"Error in leak analysis: {e}")

                # Wait for the specified interval
                print(f"Waiting {self.monitor_interval} seconds until next collection...")
                time.sleep(self.monitor_interval)

            except Exception as e:
                print(f"Error in background monitoring: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)  # Wait before retrying

        print("Background monitoring loop stopped")

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
                    print(f"Auto-timeout: Advanced monitoring active, keeping server alive")
                    continue

                # Check if we've exceeded the timeout
                if minutes_inactive >= self.auto_timeout_minutes:
                    print(f"Auto-timeout: {minutes_inactive:.1f} minutes inactive, shutting down server")

                    # Graceful shutdown
                    if self.server:
                        print("Auto-timeout: Stopping server...")
                        threading.Thread(target=self.server.shutdown).start()
                    break
                else:
                    print(f"Auto-timeout: {minutes_inactive:.1f} minutes inactive (timeout at {self.auto_timeout_minutes})")

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
