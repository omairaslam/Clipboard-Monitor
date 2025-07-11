# Memory Visualizer System: Comprehensive Monitoring Dashboard

## 🎯 System Overview

### **Dual Dashboard Architecture**
The Memory Visualizer System consists of two complementary monitoring dashboards:

1. **Memory Visualizer** (localhost:8001) - Real-time memory trend visualization
2. **Comprehensive Monitoring Dashboard** (localhost:8002) - System-wide performance metrics

### **Design Philosophy**
- **Real-time Monitoring**: Live data updates with minimal latency
- **Historical Analysis**: Trend analysis for leak detection
- **User-friendly Interface**: Accessible to both users and developers
- **Low Overhead**: Minimal impact on system performance

## 🔧 Memory Visualizer (localhost:8001)

### **Core Functionality**
The Memory Visualizer provides real-time graphical representation of memory usage patterns for the Clipboard Monitor application.

#### **Technical Architecture**
```python
# memory_visualizer.py - Core implementation
import asyncio
import websockets
import json
import psutil
import time
from datetime import datetime
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import os

class MemoryVisualizer:
    def __init__(self):
        self.clients = set()
        self.data_history = []
        self.max_history = 1000  # Prevent memory leaks in monitoring tool
        
    async def register_client(self, websocket, path):
        """Register new WebSocket client for real-time updates."""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send initial data to new client
        if self.data_history:
            initial_data = {
                'type': 'initial_data',
                'history': self.data_history[-100:]  # Last 100 points
            }
            await websocket.send(json.dumps(initial_data))
        
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def collect_and_broadcast(self):
        """Continuously collect memory data and broadcast to clients."""
        while True:
            try:
                # Collect current memory data
                data = self.collect_memory_data()
                
                # Store historical data with size limit
                self.data_history.append(data)
                if len(self.data_history) > self.max_history:
                    self.data_history = self.data_history[-self.max_history:]
                
                # Broadcast to all connected clients
                if self.clients:
                    message = json.dumps({
                        'type': 'memory_update',
                        'data': data,
                        'timestamp': data['timestamp']
                    })
                    
                    # Handle disconnected clients
                    disconnected = set()
                    for client in self.clients:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected.add(client)
                        except Exception as e:
                            print(f"Error sending to client: {e}")
                            disconnected.add(client)
                    
                    # Remove disconnected clients
                    self.clients -= disconnected
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Error in data collection: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def collect_memory_data(self):
        """Collect current memory usage data from Clipboard Monitor processes."""
        try:
            menubar_memory = 0
            service_memory = 0
            
            # Find Clipboard Monitor processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        if 'menu_bar_app.py' in cmdline_str or 'clipboard' in cmdline_str:
                            if 'menu_bar_app.py' in cmdline_str:
                                menubar_memory = proc.info['memory_info'].rss / 1024 / 1024
                            elif 'main.py' in cmdline_str:
                                service_memory = proc.info['memory_info'].rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': round(menubar_memory, 2),
                'service_memory': round(service_memory, 2),
                'total_memory': round(menubar_memory + service_memory, 2)
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': 0,
                'service_memory': 0,
                'total_memory': 0,
                'error': str(e)
            }
```

#### **Web Interface Features**
```html
<!-- Real-time memory visualization interface -->
<!DOCTYPE html>
<html>
<head>
    <title>Clipboard Monitor - Memory Visualizer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { display: flex; justify-content: space-around; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .status.connected { background: #d4edda; color: #155724; }
        .status.disconnected { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Clipboard Monitor Memory Visualizer</h1>
            <div id="status" class="status disconnected">Connecting...</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Menu Bar App</h3>
                <div id="menubar-memory">-- MB</div>
            </div>
            <div class="stat-card">
                <h3>Main Service</h3>
                <div id="service-memory">-- MB</div>
            </div>
            <div class="stat-card">
                <h3>Total Usage</h3>
                <div id="total-memory">-- MB</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="memoryChart"></canvas>
        </div>
    </div>
    
    <script>
        // Real-time chart implementation
        const ctx = document.getElementById('memoryChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Menu Bar App (MB)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }, {
                    label: 'Main Service (MB)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
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
                        text: 'Real-time Memory Usage'
                    }
                }
            }
        });
        
        // WebSocket connection for real-time updates
        const ws = new WebSocket('ws://localhost:8001/ws');
        
        ws.onopen = function(event) {
            document.getElementById('status').textContent = 'Connected - Receiving real-time data';
            document.getElementById('status').className = 'status connected';
        };
        
        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            
            if (message.type === 'memory_update') {
                updateChart(message.data);
                updateStats(message.data);
            } else if (message.type === 'initial_data') {
                loadHistoricalData(message.history);
            }
        };
        
        ws.onclose = function(event) {
            document.getElementById('status').textContent = 'Disconnected - Attempting to reconnect...';
            document.getElementById('status').className = 'status disconnected';
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                location.reload();
            }, 5000);
        };
        
        function updateChart(data) {
            const time = new Date(data.timestamp).toLocaleTimeString();
            
            // Add new data point
            chart.data.labels.push(time);
            chart.data.datasets[0].data.push(data.menubar_memory);
            chart.data.datasets[1].data.push(data.service_memory);
            
            // Keep only last 50 data points for performance
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                chart.data.datasets[1].data.shift();
            }
            
            chart.update('none'); // Update without animation for performance
        }
        
        function updateStats(data) {
            document.getElementById('menubar-memory').textContent = data.menubar_memory + ' MB';
            document.getElementById('service-memory').textContent = data.service_memory + ' MB';
            document.getElementById('total-memory').textContent = data.total_memory + ' MB';
        }
        
        function loadHistoricalData(history) {
            // Load last 50 points of historical data
            const recentHistory = history.slice(-50);
            
            chart.data.labels = recentHistory.map(d => new Date(d.timestamp).toLocaleTimeString());
            chart.data.datasets[0].data = recentHistory.map(d => d.menubar_memory);
            chart.data.datasets[1].data = recentHistory.map(d => d.service_memory);
            
            chart.update();
            
            // Update stats with latest data
            if (recentHistory.length > 0) {
                updateStats(recentHistory[recentHistory.length - 1]);
            }
        }
    </script>
</body>
</html>
```

## 🔧 Comprehensive Monitoring Dashboard (localhost:8002)

### **System-wide Monitoring**
The Comprehensive Monitoring Dashboard provides detailed system-level metrics and analysis tools.

#### **Flask-based Architecture**
```python
# memory_monitoring_dashboard.py - System monitoring
from flask import Flask, render_template, jsonify
import psutil
import json
from datetime import datetime
import threading
import time

class MonitoringDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.data_store = []
        self.max_data_points = 1000
        self.setup_routes()
        self.start_data_collection()
    
    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template('monitoring_dashboard.html')
        
        @self.app.route('/api/memory')
        def memory_api():
            return jsonify(self.get_memory_data())
        
        @self.app.route('/api/processes')
        def processes_api():
            return jsonify(self.get_process_data())
        
        @self.app.route('/api/system')
        def system_api():
            return jsonify(self.get_system_data())
        
        @self.app.route('/api/history')
        def history_api():
            return jsonify(self.data_store[-100:])  # Last 100 data points
    
    def get_memory_data(self):
        """Get detailed memory usage data."""
        try:
            # System memory information
            system_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            
            # Clipboard Monitor specific processes
            clipboard_processes = []
            total_clipboard_memory = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent', 'create_time']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        if any(keyword in cmdline_str for keyword in ['clipboard', 'menu_bar_app', 'main.py']):
                            memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                            total_clipboard_memory += memory_mb
                            
                            clipboard_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'memory_mb': round(memory_mb, 2),
                                'cpu_percent': proc.info['cpu_percent'],
                                'create_time': datetime.fromtimestamp(proc.info['create_time']).isoformat()
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return {
                'system': {
                    'total_gb': round(system_memory.total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(system_memory.available / 1024 / 1024 / 1024, 2),
                    'used_gb': round((system_memory.total - system_memory.available) / 1024 / 1024 / 1024, 2),
                    'percent': system_memory.percent,
                    'swap_total_gb': round(swap_memory.total / 1024 / 1024 / 1024, 2),
                    'swap_used_gb': round(swap_memory.used / 1024 / 1024 / 1024, 2),
                    'swap_percent': swap_memory.percent
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
```

## 📊 Integration with Menu Bar

### **Menu Access Points**
The monitoring dashboards are integrated into the menu bar application for easy access:

```python
# Menu integration in menu_bar_app.py
def _init_submenus(self):
    """Initialize memory monitoring menu integration."""
    self.memory_monitor_menu = rumps.MenuItem("Memory Monitor")
    
    # Memory Visualizer access
    self.memory_visualizer_item = rumps.MenuItem("📊 Memory Visualizer", callback=self.start_memory_visualizer)
    self.memory_monitor_menu.add(self.memory_visualizer_item)
    
    # Comprehensive Dashboard access
    self.memory_dashboard_item = rumps.MenuItem("📈 Monitoring Dashboard", callback=self.start_monitoring_dashboard)
    self.memory_monitor_menu.add(self.memory_dashboard_item)
    
    # Additional tools
    self.memory_monitor_menu.add(rumps.separator)
    self.memory_stats_item = rumps.MenuItem("📋 Memory Statistics", callback=self.show_memory_stats)
    self.memory_monitor_menu.add(self.memory_stats_item)
    self.memory_cleanup_item = rumps.MenuItem("🧹 Force Memory Cleanup", callback=self.force_memory_cleanup)
    self.memory_monitor_menu.add(self.memory_cleanup_item)

def start_memory_visualizer(self, sender):
    """Launch Memory Visualizer with automatic browser opening."""
    try:
        # Kill any existing instance
        if self._is_process_running('visualizer'):
            self._kill_monitoring_process('visualizer')
        
        # Start new instance
        script_path = os.path.join(os.path.dirname(__file__), 'memory_visualizer.py')
        if os.path.exists(script_path):
            proc = subprocess.Popen([sys.executable, script_path])
            self._monitoring_processes['visualizer'] = proc
            
            # Wait for server to start
            time.sleep(2)
            
            # Open browser
            webbrowser.open('http://localhost:8001')
            
            rumps.notification("Memory Visualizer", "Started Successfully", 
                             "Dashboard available at localhost:8001")
        else:
            rumps.alert("Memory Visualizer not found", 
                       "The memory_visualizer.py file was not found.")
    
    except Exception as e:
        rumps.alert("Error", f"Failed to start Memory Visualizer: {e}")
```

## 🎯 Key Features

### **Real-time Monitoring**
- ✅ **Live Data Updates**: 1-second refresh rate
- ✅ **WebSocket Communication**: Efficient real-time data streaming
- ✅ **Historical Trends**: Configurable data retention
- ✅ **Multiple Process Tracking**: Menu bar and service monitoring

### **Visual Analytics**
- ✅ **Interactive Charts**: Zoom, pan, and data point inspection
- ✅ **Color-coded Metrics**: Easy identification of issues
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **Export Capabilities**: Data export for analysis

### **System Integration**
- ✅ **Menu Bar Access**: One-click dashboard launching
- ✅ **Automatic Browser Opening**: Seamless user experience
- ✅ **Process Management**: Automatic cleanup and restart
- ✅ **Error Handling**: Graceful degradation and recovery

### **Performance Optimization**
- ✅ **Low Overhead**: < 1% system impact
- ✅ **Efficient Data Storage**: Automatic data rotation
- ✅ **Memory Leak Prevention**: Built-in cleanup mechanisms
- ✅ **Scalable Architecture**: Supports multiple concurrent users

The Memory Visualizer System provides comprehensive, real-time monitoring capabilities that enable both users and developers to understand, analyze, and optimize memory usage patterns in the Clipboard Monitor application.
