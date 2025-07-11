#!/usr/bin/env python3
"""
Memory Leak Source Analysis
Identifies and demonstrates the specific memory leak sources in the menu bar app.
"""

import os
import sys
import psutil
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error


class LeakSourceAnalyzer:
    """Analyzes specific memory leak sources in the menu bar app"""
    
    def __init__(self):
        self.analysis_results = {}
        self.menu_bar_pid = None
        self.baseline_memory = None
        
    def find_menu_bar_process(self):
        """Find the running menu bar app process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    if 'menu_bar_app.py' in cmdline_str and proc.pid != os.getpid():
                        self.menu_bar_pid = proc.info['pid']
                        self.baseline_memory = proc.info['memory_info'].rss / 1024 / 1024
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def analyze_leak_source_1_memory_tracking_arrays(self):
        """
        LEAK SOURCE #1: Unbounded Memory Tracking Arrays
        
        Location: menu_bar_app.py lines 1587-1589
        Issue: memory_data["menubar"], memory_data["service"], memory_timestamps arrays
        grow without bounds when memory_tracking_active is True
        """
        print("🔍 ANALYZING LEAK SOURCE #1: Memory Tracking Arrays")
        print("=" * 60)
        
        leak_info = {
            "source": "Memory Tracking Arrays",
            "location": "menu_bar_app.py:1587-1589",
            "description": "Unbounded arrays accumulating memory data every 5 seconds",
            "severity": "HIGH",
            "evidence": []
        }
        
        # Check if memory tracking is active by looking for data files
        data_locations = [
            safe_expanduser("~/Library/Application Support/ClipboardMonitor/memory_data.json"),
            safe_expanduser("~/Library/Application Support/ClipboardMonitor/menubar_profile.json")
        ]
        
        for data_file in data_locations:
            if os.path.exists(data_file):
                try:
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    file_size = os.path.getsize(data_file) / 1024  # KB
                    
                    if isinstance(data, dict):
                        if 'menubar' in data and isinstance(data['menubar'], list):
                            menubar_points = len(data['menubar'])
                            leak_info["evidence"].append(f"File: {data_file}")
                            leak_info["evidence"].append(f"  Size: {file_size:.1f} KB")
                            leak_info["evidence"].append(f"  Menu bar data points: {menubar_points}")
                            
                            if menubar_points > 1000:
                                leak_info["evidence"].append(f"  ⚠️  EXCESSIVE DATA POINTS: {menubar_points}")
                        
                        if 'snapshots' in data and isinstance(data['snapshots'], list):
                            snapshots = len(data['snapshots'])
                            leak_info["evidence"].append(f"  Memory snapshots: {snapshots}")
                            
                except Exception as e:
                    leak_info["evidence"].append(f"Error reading {data_file}: {e}")
        
        # Calculate potential memory usage
        # Each data point: ~8 bytes (float) + ~8 bytes (timestamp) = 16 bytes
        # Running every 5 seconds = 720 points per hour = 11.25 KB/hour
        # Over days/weeks this accumulates significantly
        
        leak_info["impact_analysis"] = {
            "data_rate": "720 points per hour (every 5 seconds)",
            "memory_per_point": "~16 bytes per data point",
            "hourly_growth": "~11.25 KB/hour",
            "daily_growth": "~270 KB/day",
            "weekly_growth": "~1.9 MB/week"
        }
        
        print(f"Source: {leak_info['source']}")
        print(f"Location: {leak_info['location']}")
        print(f"Severity: {leak_info['severity']}")
        print(f"Description: {leak_info['description']}")
        print("\nEvidence:")
        for evidence in leak_info["evidence"]:
            print(f"  {evidence}")
        
        print(f"\nImpact Analysis:")
        for key, value in leak_info["impact_analysis"].items():
            print(f"  {key}: {value}")
        
        self.analysis_results["leak_source_1"] = leak_info
        return leak_info
    
    def analyze_leak_source_2_timer_accumulation(self):
        """
        LEAK SOURCE #2: Timer and Event Handler Accumulation
        
        Location: menu_bar_app.py lines 138-139, 1277-1278
        Issue: Multiple timers running continuously without proper cleanup
        """
        print("\n🔍 ANALYZING LEAK SOURCE #2: Timer Accumulation")
        print("=" * 60)
        
        leak_info = {
            "source": "Timer and Event Handler Accumulation",
            "location": "menu_bar_app.py:138-139, 1277-1278",
            "description": "Multiple rumps.Timer objects running without cleanup",
            "severity": "MEDIUM",
            "timers_identified": [
                "memory_timer: rumps.Timer(update_memory_status, 5) - every 5 seconds",
                "history_timer: rumps.Timer(periodic_history_update, 30) - every 30 seconds",
                "status_timer: threading.Thread(update_status_periodically) - continuous"
            ]
        }
        
        # Check thread count in the menu bar process
        if self.menu_bar_pid:
            try:
                proc = psutil.Process(self.menu_bar_pid)
                thread_count = proc.num_threads()
                leak_info["current_thread_count"] = thread_count
                
                if thread_count > 10:
                    leak_info["evidence"] = [f"⚠️  HIGH THREAD COUNT: {thread_count} threads"]
                else:
                    leak_info["evidence"] = [f"Thread count: {thread_count} (normal)"]
                    
            except psutil.NoSuchProcess:
                leak_info["evidence"] = ["Menu bar process not found"]
        
        print(f"Source: {leak_info['source']}")
        print(f"Location: {leak_info['location']}")
        print(f"Severity: {leak_info['severity']}")
        print(f"Description: {leak_info['description']}")
        print("\nTimers Identified:")
        for timer in leak_info["timers_identified"]:
            print(f"  • {timer}")
        
        if "evidence" in leak_info:
            print(f"\nEvidence:")
            for evidence in leak_info["evidence"]:
                print(f"  {evidence}")
        
        self.analysis_results["leak_source_2"] = leak_info
        return leak_info
    
    def analyze_leak_source_3_history_loading(self):
        """
        LEAK SOURCE #3: Repeated History Loading
        
        Location: menu_bar_app.py lines 1299, 1284-1285
        Issue: Loading entire clipboard history every 30 seconds without cleanup
        """
        print("\n🔍 ANALYZING LEAK SOURCE #3: Repeated History Loading")
        print("=" * 60)
        
        leak_info = {
            "source": "Repeated History Loading",
            "location": "menu_bar_app.py:1299, 1284-1285",
            "description": "Loading entire clipboard history every 30 seconds",
            "severity": "MEDIUM",
            "evidence": []
        }
        
        # Check clipboard history file size
        history_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/clipboard_history.json")
        if os.path.exists(history_file):
            try:
                file_size = os.path.getsize(history_file) / 1024  # KB
                with open(history_file, 'r') as f:
                    history = json.load(f)
                
                history_items = len(history) if isinstance(history, list) else 0
                
                leak_info["evidence"].append(f"History file size: {file_size:.1f} KB")
                leak_info["evidence"].append(f"History items: {history_items}")
                
                # Calculate memory impact
                avg_item_size = file_size / history_items if history_items > 0 else 0
                memory_per_load = file_size  # Approximate memory usage per load
                loads_per_hour = 2  # Every 30 seconds = 120 loads per hour
                hourly_memory_churn = memory_per_load * loads_per_hour
                
                leak_info["impact_analysis"] = {
                    "file_size_kb": file_size,
                    "items_count": history_items,
                    "avg_item_size_kb": avg_item_size,
                    "loads_per_hour": loads_per_hour,
                    "memory_churn_per_hour_kb": hourly_memory_churn
                }
                
                if file_size > 100:  # > 100 KB
                    leak_info["evidence"].append(f"⚠️  LARGE HISTORY FILE: {file_size:.1f} KB loaded every 30s")
                
            except Exception as e:
                leak_info["evidence"].append(f"Error analyzing history file: {e}")
        else:
            leak_info["evidence"].append("History file not found")
        
        print(f"Source: {leak_info['source']}")
        print(f"Location: {leak_info['location']}")
        print(f"Severity: {leak_info['severity']}")
        print(f"Description: {leak_info['description']}")
        print("\nEvidence:")
        for evidence in leak_info["evidence"]:
            print(f"  {evidence}")
        
        if "impact_analysis" in leak_info:
            print(f"\nImpact Analysis:")
            for key, value in leak_info["impact_analysis"].items():
                print(f"  {key}: {value}")
        
        self.analysis_results["leak_source_3"] = leak_info
        return leak_info
    
    def analyze_leak_source_4_menu_item_accumulation(self):
        """
        LEAK SOURCE #4: Menu Item Object Accumulation
        
        Location: menu_bar_app.py lines 1296-1319
        Issue: Creating new rumps.MenuItem objects every 30 seconds without proper cleanup
        """
        print("\n🔍 ANALYZING LEAK SOURCE #4: Menu Item Accumulation")
        print("=" * 60)
        
        leak_info = {
            "source": "Menu Item Object Accumulation",
            "location": "menu_bar_app.py:1296-1319",
            "description": "Creating new rumps.MenuItem objects every 30 seconds",
            "severity": "HIGH",
            "evidence": []
        }
        
        # This is harder to detect externally, but we can infer from the code pattern
        leak_info["code_pattern_analysis"] = {
            "frequency": "Every 30 seconds",
            "operation": "self.recent_history_menu.clear() + new MenuItem creation",
            "potential_issue": "rumps.MenuItem objects may not be properly garbage collected",
            "accumulation_rate": "Up to 20 MenuItem objects every 30 seconds"
        }
        
        # Check if we can estimate based on memory growth
        if self.menu_bar_pid and self.baseline_memory:
            try:
                proc = psutil.Process(self.menu_bar_pid)
                current_memory = proc.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - self.baseline_memory
                
                leak_info["evidence"].append(f"Baseline memory: {self.baseline_memory:.1f} MB")
                leak_info["evidence"].append(f"Current memory: {current_memory:.1f} MB")
                leak_info["evidence"].append(f"Memory growth: {memory_growth:.1f} MB")
                
                if memory_growth > 50:  # > 50 MB growth
                    leak_info["evidence"].append(f"⚠️  SIGNIFICANT MEMORY GROWTH: {memory_growth:.1f} MB")
                
            except psutil.NoSuchProcess:
                leak_info["evidence"].append("Cannot measure current memory - process not found")
        
        print(f"Source: {leak_info['source']}")
        print(f"Location: {leak_info['location']}")
        print(f"Severity: {leak_info['severity']}")
        print(f"Description: {leak_info['description']}")
        print("\nCode Pattern Analysis:")
        for key, value in leak_info["code_pattern_analysis"].items():
            print(f"  {key}: {value}")
        
        if leak_info["evidence"]:
            print(f"\nEvidence:")
            for evidence in leak_info["evidence"]:
                print(f"  {evidence}")
        
        self.analysis_results["leak_source_4"] = leak_info
        return leak_info
    
    def generate_summary_report(self):
        """Generate a comprehensive summary of all identified leak sources"""
        print("\n" + "=" * 80)
        print("📊 MEMORY LEAK ANALYSIS SUMMARY")
        print("=" * 80)
        
        if not self.analysis_results:
            print("No analysis results available.")
            return
        
        total_sources = len(self.analysis_results)
        high_severity = sum(1 for result in self.analysis_results.values() if result.get("severity") == "HIGH")
        medium_severity = sum(1 for result in self.analysis_results.values() if result.get("severity") == "MEDIUM")
        
        print(f"Total Leak Sources Identified: {total_sources}")
        print(f"High Severity: {high_severity}")
        print(f"Medium Severity: {medium_severity}")
        
        if self.menu_bar_pid and self.baseline_memory:
            try:
                proc = psutil.Process(self.menu_bar_pid)
                current_memory = proc.memory_info().rss / 1024 / 1024
                print(f"\nMenu Bar App Memory Usage:")
                print(f"  Process PID: {self.menu_bar_pid}")
                print(f"  Current Memory: {current_memory:.1f} MB")
                print(f"  Baseline Memory: {self.baseline_memory:.1f} MB")
                print(f"  Memory Growth: {current_memory - self.baseline_memory:.1f} MB")
                
                if current_memory > 100:
                    print(f"  🚨 CRITICAL: Memory usage is extremely high ({current_memory:.1f} MB)")
                elif current_memory > 50:
                    print(f"  ⚠️  WARNING: Memory usage is high ({current_memory:.1f} MB)")
                
            except psutil.NoSuchProcess:
                print(f"\nMenu Bar App Process (PID {self.menu_bar_pid}) no longer running")
        
        print(f"\n📋 RECOMMENDED ACTIONS:")
        print(f"1. Implement size limits on memory_data arrays")
        print(f"2. Add proper timer cleanup in destructor")
        print(f"3. Optimize history loading frequency")
        print(f"4. Ensure proper MenuItem object cleanup")
        print(f"5. Add memory monitoring alerts")
        
        # Save analysis to file
        analysis_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/leak_analysis_report.json")
        try:
            os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
            with open(analysis_file, 'w') as f:
                json.dump({
                    "analysis_timestamp": time.time(),
                    "menu_bar_pid": self.menu_bar_pid,
                    "baseline_memory_mb": self.baseline_memory,
                    "analysis_results": self.analysis_results
                }, f, indent=2)
            print(f"\n📄 Analysis report saved to: {analysis_file}")
        except Exception as e:
            print(f"\n❌ Failed to save analysis report: {e}")


def main():
    """Run comprehensive leak source analysis"""
    print("🔍 CLIPBOARD MONITOR MEMORY LEAK SOURCE ANALYSIS")
    print("=" * 80)
    
    analyzer = LeakSourceAnalyzer()
    
    # Find the menu bar process
    proc = analyzer.find_menu_bar_process()
    if proc:
        print(f"✅ Found Menu Bar App Process (PID: {analyzer.menu_bar_pid})")
        print(f"   Memory Usage: {analyzer.baseline_memory:.1f} MB")
    else:
        print("⚠️  Menu Bar App process not found - some analysis will be limited")
    
    print()
    
    # Analyze each leak source
    analyzer.analyze_leak_source_1_memory_tracking_arrays()
    analyzer.analyze_leak_source_2_timer_accumulation()
    analyzer.analyze_leak_source_3_history_loading()
    analyzer.analyze_leak_source_4_menu_item_accumulation()
    
    # Generate summary
    analyzer.generate_summary_report()


if __name__ == "__main__":
    main()
