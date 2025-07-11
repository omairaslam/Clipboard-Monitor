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
    def __init__(self, port=8001):
        self.port = port
        self.data_history = []
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

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        # Load existing data
        self.load_historical_data()

    class RequestHandler(BaseHTTPRequestHandler):
        def __init__(self, dashboard_instance, *args, **kwargs):
            self.dashboard = dashboard_instance
            super().__init__(*args, **kwargs)

        def do_GET(self):
            """Handle GET requests."""
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
                # Alias for /api/memory for compatibility
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
        <div class="header">
            <h1>📊 Clipboard Monitor - Unified Memory Dashboard</h1>
            <div id="status" class="status disconnected">Connecting...</div>
            <div id="last-update" style="color: #7f8c8d; margin-top: 10px;">Last updated: Never</div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('overview')">📊 Overview</div>
            <div class="tab" onclick="switchTab('memory')">🧠 Memory</div>
            <div class="tab" onclick="switchTab('analysis')">🔍 Analysis</div>
            <div class="tab" onclick="switchTab('processes')">⚙️ Processes</div>
            <div class="tab" onclick="switchTab('system')">💻 System</div>
            <div class="tab" onclick="switchTab('controls')">⚙️ Controls</div>
        </div>
        
        <!-- Overview Tab -->
        <div id="overview-tab" class="tab-content active">
            <div class="dashboard-grid">
                <div class="card">
                    <h3>📱 Menu Bar App</h3>
                    <div class="metric-value" id="menubar-memory">--</div>
                    <div class="metric-label">Memory Usage (MB)</div>
                </div>
                <div class="card">
                    <h3>⚙️ Main Service</h3>
                    <div class="metric-value" id="service-memory">--</div>
                    <div class="metric-label">Memory Usage (MB)</div>
                </div>
                <div class="card">
                    <h3>📊 Total Usage</h3>
                    <div class="metric-value" id="total-memory">--</div>
                    <div class="metric-label">Combined Memory (MB)</div>
                </div>
                <div class="card">
                    <h3>💾 System Memory</h3>
                    <div class="metric-value" id="system-memory-percent">--</div>
                    <div class="metric-label">Usage Percentage</div>
                </div>
            </div>
        </div>
        
        <!-- Memory Tab -->
        <div id="memory-tab" class="tab-content">
            <div class="chart-container">
                <h3>📈 Real-time Memory Usage</h3>
                <div class="chart-wrapper">
                    <canvas id="memoryChart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <h3>📊 Memory Usage Comparison</h3>
                <div class="chart-wrapper">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Analysis Tab -->
        <div id="analysis-tab" class="tab-content">
            <div class="card">
                <h3>🔍 Memory Leak Analysis</h3>
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
        
        <!-- System Tab -->
        <div id="system-tab" class="tab-content">
            <div class="card">
                <h3>💻 System Information</h3>
                <div id="system-info" class="system-info">
                    <div class="info-item">
                        <div class="info-value" id="total-ram">--</div>
                        <div class="info-label">Total RAM (GB)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-value" id="available-ram">--</div>
                        <div class="info-label">Available RAM (GB)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-value" id="cpu-usage">--</div>
                        <div class="info-label">CPU Usage (%)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-value" id="uptime">--</div>
                        <div class="info-label">System Uptime</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Controls Tab -->
        <div id="controls-tab" class="tab-content">
            <div class="card">
                <h3>⚙️ Monitoring Controls</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div>
                        <label for="timeRange">Time Range:</label>
                        <select id="timeRange" onchange="updateTimeRange()">
                            <option value="1">Last 1 Hour</option>
                            <option value="6">Last 6 Hours</option>
                            <option value="24" selected>Last 24 Hours</option>
                            <option value="72">Last 3 Days</option>
                            <option value="168">Last Week</option>
                        </select>
                    </div>
                    <div>
                        <label for="monitorInterval">Monitor Interval:</label>
                        <select id="monitorInterval">
                            <option value="10">10 seconds</option>
                            <option value="30" selected>30 seconds</option>
                            <option value="60">1 minute</option>
                            <option value="300">5 minutes</option>
                        </select>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="startAdvancedMonitoring()" style="background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Start Monitoring</button>
                    <button onclick="stopAdvancedMonitoring()" style="background: #f44336; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Stop Monitoring</button>
                    <button onclick="forceGarbageCollection()" style="background: #ff9800; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Force GC</button>
                    <button onclick="refreshAllData()" style="background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Refresh Data</button>
                </div>
            </div>
            <div class="card">
                <h3>📊 Monitoring Status</h3>
                <div id="monitoring-status">
                    <div class="loading">Loading monitoring status...</div>
                </div>
            </div>
        </div>
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

            // Resize charts when switching to memory tab to fix any sizing issues
            if (tabName === 'memory') {
                setTimeout(() => {
                    if (typeof chart !== 'undefined') {
                        chart.resize();
                    }
                    if (typeof comparisonChart !== 'undefined') {
                        comparisonChart.resize();
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
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Main Service (MB)',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
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
                        display: true,
                        text: 'Memory Usage Over Time'
                    },
                    legend: {
                        display: true,
                        position: 'top'
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
                const response = await fetch('/api/current');  // Use /api/current for compatibility
                if (response.ok) {
                    const data = await response.json();
                    if (!isConnected) {
                        document.getElementById('status').textContent = 'Connected - Receiving real-time data';
                        document.getElementById('status').className = 'status connected';
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
                if (isConnected) {
                    document.getElementById('status').textContent = 'Disconnected - Attempting to reconnect...';
                    document.getElementById('status').className = 'status disconnected';
                    isConnected = false;
                }
                console.error('Error fetching memory data:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update overview metrics
            document.getElementById('menubar-memory').textContent = data.menubar_memory + ' MB';
            document.getElementById('service-memory').textContent = data.service_memory + ' MB';
            document.getElementById('total-memory').textContent = data.total_memory + ' MB';
            document.getElementById('last-update').textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleTimeString();
            
            // Update memory chart
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

            // Update comparison chart
            comparisonChart.data.datasets[0].data = [data.menubar_memory, data.service_memory];
            comparisonChart.update('none');
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
                    document.getElementById('system-memory-percent').textContent = data.system.percent + '%';
                    document.getElementById('total-ram').textContent = data.system.total_gb.toFixed(1);
                    document.getElementById('available-ram').textContent = data.system.available_gb.toFixed(1);
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
        
        // Initialize comparison chart
        const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
        const comparisonChart = new Chart(comparisonCtx, {
            type: 'bar',
            data: {
                labels: ['Menu Bar App', 'Main Service'],
                datasets: [{
                    label: 'Current Memory Usage (MB)',
                    data: [0, 0],
                    backgroundColor: ['rgba(52, 152, 219, 0.8)', 'rgba(231, 76, 60, 0.8)'],
                    borderColor: ['#3498db', '#e74c3c'],
                    borderWidth: 2
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
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Current Memory Comparison'
                    },
                    legend: {
                        display: false
                    }
                },
                animation: {
                    duration: 300
                }
            }
        });

        // Advanced monitoring functions
        async function startAdvancedMonitoring() {
            try {
                const interval = document.getElementById('monitorInterval').value;
                const response = await fetch(`/api/start_monitoring?interval=${interval}`);
                const result = await response.json();
                alert(result.message);
                updateMonitoringStatus();
            } catch (error) {
                alert('Error starting monitoring: ' + error);
            }
        }

        async function stopAdvancedMonitoring() {
            try {
                const response = await fetch('/api/stop_monitoring');
                const result = await response.json();
                alert(result.message);
                updateMonitoringStatus();
            } catch (error) {
                alert('Error stopping monitoring: ' + error);
            }
        }

        async function forceGarbageCollection() {
            try {
                const response = await fetch('/api/force_gc');
                const result = await response.json();
                alert(`Garbage collection completed. Objects collected: ${result.objects_collected}, Memory freed: ${result.memory_freed_mb} MB`);
                fetchMemoryData(); // Refresh data
            } catch (error) {
                alert('Error forcing garbage collection: ' + error);
            }
        }

        async function updateTimeRange() {
            await loadAnalysisData();
        }

        async function loadAnalysisData() {
            try {
                const hours = document.getElementById('timeRange').value;
                const response = await fetch(`/api/analysis?hours=${hours}`);
                const data = await response.json();
                updateAnalysisDisplay(data);

                // Also fetch historical data for compatibility
                const historicalResponse = await fetch(`/api/historical?hours=${hours}`);
                const historicalData = await historicalResponse.json();

                // Fetch comprehensive dashboard data
                const dashboardResponse = await fetch('/api/data');
                const dashboardData = await dashboardResponse.json();

                // Fetch leak analysis
                const leakResponse = await fetch('/api/leak_analysis');
                const leakData = await leakResponse.json();

            } catch (error) {
                console.error('Error loading analysis data:', error);
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

        async function updateMonitoringStatus() {
            // This would show monitoring status - placeholder for now
            const statusDiv = document.getElementById('monitoring-status');
            statusDiv.innerHTML = '<p>Monitoring status updated</p>';
        }

        function refreshAllData() {
            fetchMemoryData();
            fetchSystemData();
            fetchProcessData();
            loadAnalysisData();
            updateMonitoringStatus();
        }

        // Initialize dashboard with polling
        document.getElementById('status').textContent = 'Connecting...';
        document.getElementById('status').className = 'status disconnected';

        // Start memory data polling every 2 seconds
        setInterval(fetchMemoryData, 2000);

        // Fetch additional data every 10 seconds
        setInterval(() => {
            fetchSystemData();
            fetchProcessData();
            loadAnalysisData();
        }, 10000);

        // Initial fetch
        fetchMemoryData();
        fetchSystemData();
        fetchProcessData();
        loadAnalysisData();
        updateMonitoringStatus();
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
                            if 'menu_bar_app.py' in cmdline_str:
                                process_type = "menu_bar"
                            elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]):
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

                            # Improved detection logic - prioritize exact matches
                            if 'menu_bar_app.py' in cmdline_str:
                                menubar_memory = memory_mb
                            elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]):
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

            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': round(menubar_memory, 2),
                'service_memory': round(service_memory, 2),
                'total_memory': round(menubar_memory + service_memory, 2)
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

    def get_historical_data(self, hours=24):
        """Get historical data for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()

        filtered_data = []
        for point in self.data_history:
            if point.get('timestamp', '') >= cutoff_str:
                filtered_data.append(point)

        return {
            'main_service': [{'timestamp': p['timestamp'], 'memory_rss_mb': p['service_memory']} for p in filtered_data],
            'menu_bar': [{'timestamp': p['timestamp'], 'memory_rss_mb': p['menubar_memory']} for p in filtered_data],
            'system': [{'timestamp': p['timestamp'], 'memory_percent': 0} for p in filtered_data]  # Placeholder
        }

    def get_analysis_data(self, hours=24):
        """Get memory leak analysis data"""
        historical_data = self.get_historical_data(hours)
        analysis = {}

        for process_name, points in historical_data.items():
            if len(points) < 2:
                analysis[process_name] = {"status": "insufficient_data"}
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

        return {
            "status": "started",
            "interval": interval,
            "message": f"Advanced monitoring started with {interval}s interval"
        }

    def stop_advanced_monitoring(self):
        """Stop advanced monitoring"""
        self.monitoring_active = False
        duration = None

        if self.monitoring_start_time:
            duration = (datetime.now() - self.monitoring_start_time).total_seconds()

        return {
            "status": "stopped",
            "duration_seconds": duration,
            "message": "Advanced monitoring stopped"
        }

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
                "system_info": {
                    "cpu_percent": system_data.get("cpu_percent", 0),
                    "memory_percent": memory_data.get("system", {}).get("percent", 0)
                },
                "long_term_monitoring": {
                    "status": "active" if self.monitoring_active else "inactive",
                    "data_points": len(self.data_history),
                    "monitoring_duration_hours": monitoring_duration_hours,
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

        # Open browser
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f'http://localhost:{self.port}')

        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

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
    dashboard = UnifiedMemoryDashboard()
    dashboard.run()
