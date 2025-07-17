#!/usr/bin/env python3
"""
Memory Monitoring Dashboard
Unified dashboard for all memory monitoring and leak detection tools.
"""

import os
import sys
import time
import json
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import fcntl
import tempfile
import atexit

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error
from long_term_memory_monitor import LongTermMemoryMonitor
from validate_leak_fixes import MemoryLeakFixValidator
from advanced_memory_profiler import get_advanced_profiler


class MemoryMonitoringDashboard:
    """Unified dashboard for memory monitoring"""
    
    def __init__(self, port=8002):
        self.port = port
        self.server = None
        self.server_thread = None
        
        # Initialize monitoring components
        self.long_term_monitor = LongTermMemoryMonitor()
        self.validator = MemoryLeakFixValidator()
        self.advanced_profiler = get_advanced_profiler()
        
        # Dashboard state
        self.dashboard_active = False
    
    def start_dashboard(self):
        """Start the monitoring dashboard"""
        if self.dashboard_active:
            return
        
        try:
            # Start monitoring components
            self.long_term_monitor.start_monitoring()
            
            # Start web server
            self.server = HTTPServer(('localhost', self.port), DashboardRequestHandler)
            self.server.dashboard = self  # Pass reference to handler
            
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.dashboard_active = True
            
            log_event(f"Memory monitoring dashboard started on port {self.port}", level="INFO")
            print(f"🚀 Memory Monitoring Dashboard started")
            print(f"   URL: http://localhost:{self.port}")
            print(f"   Long-term monitoring: Active")
            print(f"   Advanced profiling: Active")
            
            # Open browser
            webbrowser.open(f'http://localhost:{self.port}')
            
        except Exception as e:
            log_error(f"Failed to start dashboard: {e}")
            print(f"❌ Failed to start dashboard: {e}")
    
    def stop_dashboard(self):
        """Stop the monitoring dashboard"""
        if not self.dashboard_active:
            return
        
        try:
            # Stop monitoring components
            self.long_term_monitor.stop_monitoring()
            
            # Stop web server
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            if self.server_thread:
                self.server_thread.join(timeout=5)
            
            self.dashboard_active = False
            
            log_event("Memory monitoring dashboard stopped", level="INFO")
            print("🛑 Memory monitoring dashboard stopped")
            
        except Exception as e:
            log_error(f"Error stopping dashboard: {e}")
    
    def get_dashboard_data(self):
        """Get comprehensive dashboard data"""
        try:
            # Get data from all monitoring components
            long_term_status = self.long_term_monitor.get_status_report()
            advanced_report = self.advanced_profiler.get_summary_report()
            
            # Get validation data if available
            validation_data = {}
            if os.path.exists(self.validator.data_file):
                try:
                    with open(self.validator.data_file, 'r') as f:
                        validation_data = json.load(f)
                except Exception as e:
                    log_error(f"Error loading validation data: {e}")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "dashboard_status": "active" if self.dashboard_active else "inactive",
                "long_term_monitoring": long_term_status,
                "advanced_profiling": advanced_report,
                "validation_results": validation_data,
                "system_info": self._get_system_info()
            }
            
        except Exception as e:
            log_error(f"Error getting dashboard data: {e}")
            return {"error": str(e)}
    
    def _get_system_info(self):
        """Get system information"""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "boot_time": psutil.boot_time()
            }
        except Exception as e:
            return {"error": str(e)}


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/':
                self._serve_dashboard_html()
            elif path == '/api/data':
                self._serve_dashboard_data()
            elif path == '/api/start_validation':
                self._start_validation()
            elif path == '/api/stop_validation':
                self._stop_validation()
            else:
                self._serve_404()
                
        except Exception as e:
            self._serve_error(str(e))
    
    def _serve_dashboard_html(self):
        """Serve the main dashboard HTML"""
        html_content = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Memory Monitoring Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
                .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .card h3 { margin-top: 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                .metric { display: flex; justify-content: space-between; margin: 10px 0; padding: 8px; background: #f8f9fa; border-radius: 5px; }
                .metric-label { font-weight: bold; }
                .metric-value { color: #007bff; }
                .status-good { color: #28a745; }
                .status-warning { color: #ffc107; }
                .status-danger { color: #dc3545; }
                .button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
                .button:hover { background: #0056b3; }
                .button-danger { background: #dc3545; }
                .button-danger:hover { background: #c82333; }
                .log-container { max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; }
                .refresh-info { text-align: center; color: #666; margin: 20px 0; }
                .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
                .alert-danger { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
                .alert-success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔬 Memory Monitoring Dashboard</h1>
                <p>Real-time monitoring and validation of memory leak fixes</p>
            </div>
            
            <div id="dashboard-content">
                <div class="refresh-info">Loading dashboard data...</div>
            </div>
            
            <script>
                let dashboardData = {};
                
                function updateDashboard() {
                    fetch('/api/data')
                        .then(response => response.json())
                        .then(data => {
                            dashboardData = data;
                            renderDashboard(data);
                        })
                        .catch(error => {
                            console.error('Error fetching data:', error);
                            document.getElementById('dashboard-content').innerHTML = 
                                '<div class="alert alert-danger">Error loading dashboard data: ' + error + '</div>';
                        });
                }
                
                function renderDashboard(data) {
                    const content = document.getElementById('dashboard-content');
                    
                    let html = '<div class="dashboard-grid">';
                    
                    // System Status Card
                    html += '<div class="card">';
                    html += '<h3>📊 System Status</h3>';
                    html += '<div class="metric"><span class="metric-label">Dashboard Status:</span>';
                    html += '<span class="metric-value ' + (data.dashboard_status === 'active' ? 'status-good' : 'status-danger') + '">' + data.dashboard_status + '</span></div>';
                    html += '<div class="metric"><span class="metric-label">Last Updated:</span><span class="metric-value">' + new Date(data.timestamp).toLocaleString() + '</span></div>';
                    
                    if (data.system_info && !data.system_info.error) {
                        html += '<div class="metric"><span class="metric-label">CPU Usage:</span><span class="metric-value">' + data.system_info.cpu_percent + '%</span></div>';
                        html += '<div class="metric"><span class="metric-label">Memory Usage:</span><span class="metric-value">' + data.system_info.memory_percent + '%</span></div>';
                    }
                    html += '</div>';
                    
                    // Long-term Monitoring Card
                    html += '<div class="card">';
                    html += '<h3>📈 Long-term Monitoring</h3>';
                    const ltm = data.long_term_monitoring || {};
                    html += '<div class="metric"><span class="metric-label">Status:</span>';
                    html += '<span class="metric-value ' + (ltm.status === 'active' ? 'status-good' : 'status-warning') + '">' + (ltm.status || 'unknown') + '</span></div>';
                    html += '<div class="metric"><span class="metric-label">Data Points:</span><span class="metric-value">' + (ltm.data_points || 0) + '</span></div>';
                    html += '<div class="metric"><span class="metric-label">Monitoring Duration:</span><span class="metric-value">' + (ltm.monitoring_duration_hours || 0).toFixed(1) + ' hours</span></div>';
                    html += '<div class="metric"><span class="metric-label">Alerts Sent:</span><span class="metric-value">' + (ltm.alerts_sent || 0) + '</span></div>';
                    
                    if (ltm.latest_data && ltm.latest_data.processes && ltm.latest_data.processes.menu_bar) {
                        const menuBar = ltm.latest_data.processes.menu_bar;
                        html += '<div class="metric"><span class="metric-label">Menu Bar Memory:</span>';
                        const memoryClass = menuBar.memory_rss_mb > 100 ? 'status-danger' : (menuBar.memory_rss_mb > 50 ? 'status-warning' : 'status-good');
                        html += '<span class="metric-value ' + memoryClass + '">' + menuBar.memory_rss_mb.toFixed(1) + ' MB</span></div>';
                    }
                    html += '</div>';
                    
                    // Advanced Profiling Card
                    html += '<div class="card">';
                    html += '<h3>🔬 Advanced Profiling</h3>';
                    const ap = data.advanced_profiling || {};
                    html += '<div class="metric"><span class="metric-label">Status:</span>';
                    html += '<span class="metric-value ' + (ap.status === 'active' ? 'status-good' : 'status-warning') + '">' + (ap.status || 'unknown') + '</span></div>';
                    html += '<div class="metric"><span class="metric-label">Total Snapshots:</span><span class="metric-value">' + (ap.total_snapshots || 0) + '</span></div>';
                    html += '<div class="metric"><span class="metric-label">Tracemalloc:</span><span class="metric-value">' + (ap.tracemalloc_enabled ? 'Enabled' : 'Disabled') + '</span></div>';
                    
                    if (ap.latest_snapshot && ap.latest_snapshot.process_info) {
                        const procInfo = ap.latest_snapshot.process_info;
                        html += '<div class="metric"><span class="metric-label">Current Memory:</span><span class="metric-value">' + procInfo.memory_rss_mb.toFixed(1) + ' MB</span></div>';
                        html += '<div class="metric"><span class="metric-label">Objects:</span><span class="metric-value">' + (ap.latest_snapshot.object_analysis.total_objects || 0).toLocaleString() + '</span></div>';
                    }
                    html += '</div>';
                    
                    // Validation Results Card
                    html += '<div class="card">';
                    html += '<h3>🧪 Fix Validation</h3>';
                    const validation = data.validation_results || {};
                    
                    if (validation.validation_data && validation.validation_data.length > 0) {
                        const latest = validation.validation_data[validation.validation_data.length - 1];
                        html += '<div class="metric"><span class="metric-label">Test Duration:</span><span class="metric-value">' + (latest.elapsed_minutes || 0).toFixed(1) + ' minutes</span></div>';
                        html += '<div class="metric"><span class="metric-label">Data Points:</span><span class="metric-value">' + validation.validation_data.length + '</span></div>';
                        
                        if (latest.fix_validation) {
                            const fixValidation = latest.fix_validation;
                            const passedFixes = Object.values(fixValidation).filter(status => status === 'PASS').length;
                            const totalFixes = Object.keys(fixValidation).length;
                            html += '<div class="metric"><span class="metric-label">Fixes Passing:</span><span class="metric-value">' + passedFixes + '/' + totalFixes + '</span></div>';
                        }
                    } else {
                        html += '<div class="alert alert-warning">No validation data available</div>';
                    }
                    
                    html += '<button class="button" onclick="startValidation()">Start Validation</button>';
                    html += '<button class="button button-danger" onclick="stopValidation()">Stop Validation</button>';
                    html += '</div>';
                    
                    // Recommendations Card
                    html += '<div class="card">';
                    html += '<h3>💡 Recommendations</h3>';
                    
                    if (ap.recommendations && ap.recommendations.length > 0) {
                        html += '<ul>';
                        ap.recommendations.forEach(rec => {
                            html += '<li>' + rec + '</li>';
                        });
                        html += '</ul>';
                    } else {
                        html += '<div class="alert alert-success">No specific recommendations - system appears stable</div>';
                    }
                    html += '</div>';
                    
                    html += '</div>'; // Close dashboard-grid
                    
                    html += '<div class="refresh-info">Dashboard updates every 30 seconds</div>';
                    
                    content.innerHTML = html;
                }
                
                function startValidation() {
                    fetch('/api/start_validation')
                        .then(response => response.json())
                        .then(data => {
                            alert('Validation started: ' + data.message);
                            updateDashboard();
                        })
                        .catch(error => alert('Error starting validation: ' + error));
                }
                
                function stopValidation() {
                    fetch('/api/stop_validation')
                        .then(response => response.json())
                        .then(data => {
                            alert('Validation stopped: ' + data.message);
                            updateDashboard();
                        })
                        .catch(error => alert('Error stopping validation: ' + error));
                }
                
                // Initial load and auto-refresh
                updateDashboard();
                setInterval(updateDashboard, 30000); // Refresh every 30 seconds
            </script>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _serve_dashboard_data(self):
        """Serve dashboard data as JSON"""
        try:
            data = self.server.dashboard.get_dashboard_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
            
        except Exception as e:
            self._serve_error(str(e))
    
    def _start_validation(self):
        """Start validation testing"""
        try:
            validator = self.server.dashboard.validator
            if not validator.validation_active:
                validator.start_validation()
                message = "Validation testing started"
            else:
                message = "Validation already running"
            
            response = {"status": "success", "message": message}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self._serve_error(str(e))
    
    def _stop_validation(self):
        """Stop validation testing"""
        try:
            validator = self.server.dashboard.validator
            if validator.validation_active:
                validator.stop_validation()
                message = "Validation testing stopped"
            else:
                message = "Validation not running"
            
            response = {"status": "success", "message": message}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self._serve_error(str(e))
    
    def _serve_404(self):
        """Serve 404 error"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 Not Found</h1>')
    
    def _serve_error(self, error_message):
        """Serve error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_response = {"error": error_message}
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to suppress HTTP log messages"""
        pass


def ensure_single_instance():
    """Ensure only one instance of monitoring dashboard runs"""
    try:
        # Create lock file in temp directory
        lock_file_path = os.path.join(tempfile.gettempdir(), 'clipboard_monitor_dashboard.lock')
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
        print(f"✅ Monitoring Dashboard singleton lock acquired (PID: {os.getpid()})")
        return True

    except (IOError, OSError):
        print("❌ Another instance of Monitoring Dashboard is already running!")
        print("   Opening existing dashboard at http://localhost:8002")
        try:
            webbrowser.open('http://localhost:8002')
        except Exception:
            pass
        return False


def main():
    """Main function to start the monitoring dashboard"""
    # Ensure only one instance runs
    if not ensure_single_instance():
        sys.exit(0)

    import argparse

    parser = argparse.ArgumentParser(description="Memory Monitoring Dashboard")
    parser.add_argument("--port", type=int, default=8002, help="Port for web dashboard (default: 8002)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    dashboard = MemoryMonitoringDashboard(port=args.port)
    
    try:
        dashboard.start_dashboard()
        
        if not args.no_browser:
            print(f"   Opening browser...")
        
        print(f"\n📊 Dashboard Features:")
        print(f"   • Real-time memory monitoring")
        print(f"   • Memory leak detection")
        print(f"   • Fix validation testing")
        print(f"   • Advanced profiling analysis")
        print(f"   • Automated alerting")
        print(f"\nPress Ctrl+C to stop the dashboard")
        
        # Keep running until interrupted
        while dashboard.dashboard_active:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        dashboard.stop_dashboard()


if __name__ == "__main__":
    main()
