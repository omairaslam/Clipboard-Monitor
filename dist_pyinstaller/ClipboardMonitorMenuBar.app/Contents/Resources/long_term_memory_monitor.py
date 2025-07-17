#!/usr/bin/env python3
"""
Long-term Memory Monitor
Continuous monitoring and validation of memory leak fixes with alerting.
"""

import os
import sys
import time
import json
import psutil
import threading
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error
from advanced_memory_profiler import get_advanced_profiler


class LongTermMemoryMonitor:
    """Long-term memory monitoring with leak detection and alerting"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread = None
        self.data_lock = threading.Lock()
        
        # Data storage
        self.data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/longterm_monitoring.json")
        self.alert_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/memory_alerts.json")
        
        # Monitoring configuration
        self.check_interval = 300  # 5 minutes
        self.alert_thresholds = {
            "memory_mb": 100,  # Alert if > 100 MB
            "growth_rate_mb_per_hour": 5,  # Alert if growing > 5 MB/hour
            "consecutive_growth_periods": 6,  # Alert after 6 consecutive growth periods (30 minutes)
            "object_count": 50000,  # Alert if > 50k objects
            "gc_effectiveness": 0.05  # Alert if GC effectiveness < 5%
        }
        
        # Historical data
        self.memory_history = deque(maxlen=288)  # 24 hours at 5-minute intervals
        self.alerts_sent = []
        
        # Process tracking
        self.tracked_processes = {}
        
        # Advanced profiler integration
        self.advanced_profiler = get_advanced_profiler()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Load existing data
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load existing monitoring data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Convert to deque with proper size limit
                history = data.get("memory_history", [])
                self.memory_history = deque(history[-288:], maxlen=288)  # Keep last 24 hours
                self.alerts_sent = data.get("alerts_sent", [])
                
                log_event(f"Loaded {len(self.memory_history)} historical data points", level="INFO")
        except Exception as e:
            log_error(f"Failed to load historical data: {e}")
    
    def save_data(self):
        """Save monitoring data to file"""
        try:
            with self.data_lock:
                data = {
                    "memory_history": list(self.memory_history),
                    "alerts_sent": self.alerts_sent[-100:],  # Keep last 100 alerts
                    "last_updated": datetime.now().isoformat(),
                    "monitoring_config": {
                        "check_interval": self.check_interval,
                        "alert_thresholds": self.alert_thresholds
                    }
                }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            log_error(f"Failed to save monitoring data: {e}")
    
    def find_clipboard_processes(self):
        """Find all clipboard monitor processes"""
        processes = {
            "main_service": None,
            "menu_bar": None
        }
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'create_time']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline)
                        
                        if 'main.py' in cmdline_str and 'clipboard' in cmdline_str.lower():
                            processes["main_service"] = proc
                        elif 'menu_bar_app.py' in cmdline_str:
                            processes["menu_bar"] = proc
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            log_error(f"Error finding processes: {e}")
        
        return processes
    
    def collect_monitoring_data(self):
        """Collect comprehensive monitoring data"""
        timestamp = datetime.now().isoformat()
        
        # Find processes
        processes = self.find_clipboard_processes()
        
        # Collect process data
        process_data = {}
        for proc_type, proc in processes.items():
            if proc:
                try:
                    memory_info = proc.memory_info()
                    process_data[proc_type] = {
                        "pid": proc.pid,
                        "memory_rss_mb": memory_info.rss / 1024 / 1024,
                        "memory_vms_mb": memory_info.vms / 1024 / 1024,
                        "memory_percent": proc.memory_percent(),
                        "num_threads": proc.num_threads(),
                        "cpu_percent": proc.cpu_percent(),
                        "create_time": proc.create_time()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_data[proc_type] = None
        
        # Get advanced profiling data
        advanced_data = {}
        try:
            if self.advanced_profiler:
                snapshot = self.advanced_profiler.take_detailed_snapshot()
                advanced_data = {
                    "total_objects": snapshot.get("object_analysis", {}).get("total_objects", 0),
                    "gc_effectiveness": snapshot.get("gc_analysis", {}).get("gc_effectiveness", 0),
                    "large_objects_count": len(snapshot.get("object_analysis", {}).get("large_objects", [])),
                    "leak_indicators_count": len(snapshot.get("leak_indicators", []))
                }
        except Exception as e:
            log_error(f"Error getting advanced profiling data: {e}")
        
        # Compile monitoring data point
        data_point = {
            "timestamp": timestamp,
            "processes": process_data,
            "advanced_analysis": advanced_data,
            "system_memory": self._get_system_memory()
        }
        
        # Add to history
        with self.data_lock:
            self.memory_history.append(data_point)
        
        return data_point
    
    def _get_system_memory(self):
        """Get system memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": memory.total / 1024 / 1024 / 1024,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "used_percent": memory.percent
            }
        except Exception as e:
            log_error(f"Error getting system memory: {e}")
            return {}
    
    def analyze_trends(self):
        """Analyze memory trends and detect potential issues"""
        if len(self.memory_history) < 3:
            return {"status": "insufficient_data"}
        
        with self.data_lock:
            recent_data = list(self.memory_history)[-12:]  # Last hour (12 * 5 minutes)
        
        analysis = {
            "status": "analyzed",
            "alerts": [],
            "trends": {},
            "recommendations": []
        }
        
        # Analyze each process type
        for proc_type in ["main_service", "menu_bar"]:
            memory_values = []
            object_counts = []
            
            for data_point in recent_data:
                proc_data = data_point.get("processes", {}).get(proc_type)
                if proc_data:
                    memory_values.append(proc_data.get("memory_rss_mb", 0))
                
                advanced_data = data_point.get("advanced_analysis", {})
                if advanced_data:
                    object_counts.append(advanced_data.get("total_objects", 0))
            
            if len(memory_values) >= 2:
                # Calculate trends
                memory_growth = memory_values[-1] - memory_values[0]
                time_span_hours = len(memory_values) * (self.check_interval / 3600)
                growth_rate = memory_growth / time_span_hours if time_span_hours > 0 else 0
                
                # Check for consecutive growth
                consecutive_growth = 0
                for i in range(1, len(memory_values)):
                    if memory_values[i] > memory_values[i-1]:
                        consecutive_growth += 1
                    else:
                        consecutive_growth = 0
                
                analysis["trends"][proc_type] = {
                    "current_memory_mb": memory_values[-1] if memory_values else 0,
                    "memory_growth_mb": memory_growth,
                    "growth_rate_mb_per_hour": growth_rate,
                    "consecutive_growth_periods": consecutive_growth,
                    "object_count": object_counts[-1] if object_counts else 0
                }
                
                # Check thresholds and generate alerts
                self._check_thresholds(proc_type, analysis["trends"][proc_type], analysis["alerts"])
        
        # Add recommendations based on analysis
        if analysis["alerts"]:
            analysis["recommendations"].extend([
                "Restart the affected process to clear accumulated memory",
                "Check for new memory leak sources",
                "Review recent code changes",
                "Enable detailed profiling for investigation"
            ])
        else:
            analysis["recommendations"].append("Memory usage appears stable - continue monitoring")
        
        return analysis
    
    def _check_thresholds(self, proc_type, trend_data, alerts):
        """Check if any thresholds are exceeded"""
        current_memory = trend_data.get("current_memory_mb", 0)
        growth_rate = trend_data.get("growth_rate_mb_per_hour", 0)
        consecutive_growth = trend_data.get("consecutive_growth_periods", 0)
        object_count = trend_data.get("object_count", 0)
        
        # Memory threshold
        if current_memory > self.alert_thresholds["memory_mb"]:
            alerts.append({
                "type": "high_memory",
                "process": proc_type,
                "severity": "high" if current_memory > 200 else "medium",
                "message": f"{proc_type} using {current_memory:.1f} MB (threshold: {self.alert_thresholds['memory_mb']} MB)",
                "value": current_memory,
                "threshold": self.alert_thresholds["memory_mb"]
            })
        
        # Growth rate threshold
        if growth_rate > self.alert_thresholds["growth_rate_mb_per_hour"]:
            alerts.append({
                "type": "high_growth_rate",
                "process": proc_type,
                "severity": "high",
                "message": f"{proc_type} growing at {growth_rate:.2f} MB/hour (threshold: {self.alert_thresholds['growth_rate_mb_per_hour']} MB/hour)",
                "value": growth_rate,
                "threshold": self.alert_thresholds["growth_rate_mb_per_hour"]
            })
        
        # Consecutive growth threshold
        if consecutive_growth >= self.alert_thresholds["consecutive_growth_periods"]:
            alerts.append({
                "type": "consecutive_growth",
                "process": proc_type,
                "severity": "medium",
                "message": f"{proc_type} has grown for {consecutive_growth} consecutive periods",
                "value": consecutive_growth,
                "threshold": self.alert_thresholds["consecutive_growth_periods"]
            })
        
        # Object count threshold
        if object_count > self.alert_thresholds["object_count"]:
            alerts.append({
                "type": "high_object_count",
                "process": proc_type,
                "severity": "medium",
                "message": f"{proc_type} has {object_count:,} objects (threshold: {self.alert_thresholds['object_count']:,})",
                "value": object_count,
                "threshold": self.alert_thresholds["object_count"]
            })
    
    def send_alert(self, alert):
        """Send alert notification"""
        try:
            # Log the alert
            log_event(f"MEMORY ALERT: {alert['message']}", level="WARNING")
            
            # Add to alerts history
            alert_record = {
                "timestamp": datetime.now().isoformat(),
                "alert": alert
            }
            self.alerts_sent.append(alert_record)
            
            # Save alert to file
            try:
                with open(self.alert_file, 'w') as f:
                    json.dump(self.alerts_sent[-50:], f, indent=2)  # Keep last 50 alerts
            except Exception as e:
                log_error(f"Failed to save alert: {e}")
            
            # Could add email/notification integration here
            print(f"🚨 MEMORY ALERT: {alert['message']}")
            
        except Exception as e:
            log_error(f"Failed to send alert: {e}")
    
    def start_monitoring(self):
        """Start long-term monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        log_event(f"Long-term memory monitoring started (interval: {self.check_interval}s)", level="INFO")
        print(f"🔬 Long-term memory monitoring started")
        print(f"   Check interval: {self.check_interval} seconds")
        print(f"   Data retention: {len(self.memory_history)} / 288 data points (24 hours)")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        log_event("Long-term memory monitoring stopped", level="INFO")
        print("🛑 Long-term memory monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect data
                data_point = self.collect_monitoring_data()
                
                # Analyze trends
                analysis = self.analyze_trends()
                
                # Send alerts if needed
                if analysis.get("alerts"):
                    for alert in analysis["alerts"]:
                        self.send_alert(alert)
                
                # Save data
                self.save_data()
                
                # Log status periodically
                if len(self.memory_history) % 12 == 0:  # Every hour
                    self._log_status(data_point, analysis)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                log_error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _log_status(self, data_point, analysis):
        """Log periodic status updates"""
        try:
            menu_bar_data = data_point.get("processes", {}).get("menu_bar")
            if menu_bar_data:
                memory_mb = menu_bar_data.get("memory_rss_mb", 0)
                log_event(f"Monitoring status: Menu bar app using {memory_mb:.1f} MB", level="INFO")
            
            if analysis.get("alerts"):
                log_event(f"Active alerts: {len(analysis['alerts'])}", level="WARNING")
            else:
                log_event("No memory alerts - system stable", level="INFO")
                
        except Exception as e:
            log_error(f"Error logging status: {e}")
    
    def get_status_report(self):
        """Get current monitoring status and recent data"""
        if not self.memory_history:
            return {"status": "no_data", "message": "No monitoring data available"}
        
        latest = self.memory_history[-1]
        analysis = self.analyze_trends()
        
        return {
            "status": "active" if self.monitoring_active else "inactive",
            "latest_data": latest,
            "trend_analysis": analysis,
            "data_points": len(self.memory_history),
            "alerts_sent": len(self.alerts_sent),
            "monitoring_duration_hours": len(self.memory_history) * (self.check_interval / 3600),
            "thresholds": self.alert_thresholds
        }


def main():
    """Main function to start long-term monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Long-term Memory Monitor for Clipboard Monitor")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--status", action="store_true", help="Show current status and exit")
    parser.add_argument("--stop", action="store_true", help="Stop monitoring and exit")
    
    args = parser.parse_args()
    
    monitor = LongTermMemoryMonitor()
    monitor.check_interval = args.interval
    
    if args.status:
        report = monitor.get_status_report()
        print("📊 Long-term Memory Monitoring Status:")
        print(f"   Status: {report['status']}")
        print(f"   Data Points: {report['data_points']}")
        print(f"   Monitoring Duration: {report['monitoring_duration_hours']:.1f} hours")
        print(f"   Alerts Sent: {report['alerts_sent']}")
        
        if report.get("latest_data"):
            latest = report["latest_data"]
            menu_bar = latest.get("processes", {}).get("menu_bar")
            if menu_bar:
                print(f"   Current Menu Bar Memory: {menu_bar['memory_rss_mb']:.1f} MB")
        
        return
    
    if args.stop:
        print("Stopping long-term monitoring...")
        return
    
    try:
        monitor.start_monitoring()
        
        print("\n📊 Monitoring Dashboard:")
        print("   Press Ctrl+C to stop monitoring")
        print("   Data saved to: ~/Library/Application Support/ClipboardMonitor/")
        print("   Alerts logged to: ~/Library/Logs/ClipboardMonitor.out.log")
        
        # Keep running until interrupted
        while monitor.monitoring_active:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
