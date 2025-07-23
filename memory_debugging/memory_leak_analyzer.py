#!/usr/bin/env python3
"""
Memory Leak Analyzer for Clipboard Monitor

This script analyzes memory usage patterns and identifies potential leak sources
in the menu bar application. It provides detailed analysis and recommendations.

Usage:
    python3 memory_leak_analyzer.py [--live] [--analyze-logs] [--duration=3600]

Note: matplotlib is optional - graphing features will be disabled if not available
"""

import psutil
import gc
import sys
import os
import time
import argparse
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import tracemalloc

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Note: matplotlib not available - graphing features disabled")

class MemoryLeakAnalyzer:
    def __init__(self):
        self.process = None
        self.baseline_memory = None
        self.memory_samples = []
        self.object_samples = []
        self.leak_patterns = []
        
        # Common leak patterns to detect
        self.leak_indicators = {
            'gradual_increase': {'threshold': 1.0, 'description': 'Steady memory growth over time'},
            'periodic_spikes': {'threshold': 5.0, 'description': 'Regular memory spikes that don\'t release'},
            'object_accumulation': {'threshold': 1000, 'description': 'Excessive object creation without cleanup'},
            'timer_leaks': {'threshold': 0.5, 'description': 'Memory growth correlated with timer events'},
            'history_leaks': {'threshold': 2.0, 'description': 'Memory growth during history operations'}
        }
    
    def find_clipboard_process(self):
        """Find the clipboard monitor menu bar process."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'menu_bar_app.py' in cmdline:
                        self.process = proc
                        print(f"Found clipboard monitor process: PID {proc.pid}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("Clipboard monitor menu bar process not found!")
        return False
    
    def collect_memory_sample(self):
        """Collect a comprehensive memory sample."""
        if not self.process:
            return None
        
        try:
            # Basic memory info
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # CPU info
            cpu_percent = self.process.cpu_percent()
            
            # Thread info
            threads = self.process.num_threads()
            
            # File descriptors (on Unix systems)
            try:
                fds = self.process.num_fds()
            except AttributeError:
                fds = 0
            
            # Garbage collection info
            gc_objects = len(gc.get_objects())
            
            sample = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'threads': threads,
                'file_descriptors': fds,
                'gc_objects': gc_objects
            }
            
            self.memory_samples.append(sample)
            
            # Set baseline if first sample
            if self.baseline_memory is None:
                self.baseline_memory = sample['rss_mb']
                print(f"Baseline memory set: {self.baseline_memory:.1f}MB")
            
            return sample
            
        except psutil.NoSuchProcess:
            print("Process no longer exists")
            return None
        except Exception as e:
            print(f"Error collecting memory sample: {e}")
            return None
    
    def analyze_memory_trend(self):
        """Analyze memory usage trends to detect leaks."""
        if len(self.memory_samples) < 10:
            print("Not enough samples for trend analysis")
            return
        
        print("\n" + "="*60)
        print("MEMORY TREND ANALYSIS")
        print("="*60)
        
        # Calculate overall trend
        first_sample = self.memory_samples[0]
        last_sample = self.memory_samples[-1]
        
        time_span_hours = (last_sample['timestamp'] - first_sample['timestamp']) / 3600
        memory_increase = last_sample['rss_mb'] - first_sample['rss_mb']
        growth_rate = memory_increase / time_span_hours if time_span_hours > 0 else 0
        
        print(f"Time span: {time_span_hours:.2f} hours")
        print(f"Memory increase: {memory_increase:.1f}MB")
        print(f"Growth rate: {growth_rate:.2f}MB/hour")
        
        # Detect leak patterns
        self.detect_leak_patterns()
        
        # Analyze object growth
        self.analyze_object_growth()
        
        # Generate recommendations
        self.generate_recommendations()
    
    def detect_leak_patterns(self):
        """Detect common memory leak patterns."""
        print("\nLEAK PATTERN DETECTION:")
        print("-" * 40)
        
        memory_values = [sample['rss_mb'] for sample in self.memory_samples]
        
        # 1. Gradual increase detection
        if len(memory_values) >= 5:
            recent_avg = sum(memory_values[-5:]) / 5
            early_avg = sum(memory_values[:5]) / 5
            
            if recent_avg > early_avg + self.leak_indicators['gradual_increase']['threshold']:
                pattern = {
                    'type': 'gradual_increase',
                    'severity': 'HIGH' if recent_avg > early_avg + 10 else 'MEDIUM',
                    'description': f"Gradual memory increase detected: {recent_avg - early_avg:.1f}MB"
                }
                self.leak_patterns.append(pattern)
                print(f"⚠️  {pattern['severity']}: {pattern['description']}")
        
        # 2. Periodic spikes detection
        spikes = []
        for i in range(1, len(memory_values)):
            if memory_values[i] > memory_values[i-1] + self.leak_indicators['periodic_spikes']['threshold']:
                spikes.append(i)
        
        if len(spikes) > 3:
            pattern = {
                'type': 'periodic_spikes',
                'severity': 'MEDIUM',
                'description': f"Detected {len(spikes)} memory spikes"
            }
            self.leak_patterns.append(pattern)
            print(f"⚠️  {pattern['severity']}: {pattern['description']}")
        
        # 3. Object accumulation detection
        if len(self.memory_samples) >= 2:
            first_objects = self.memory_samples[0]['gc_objects']
            last_objects = self.memory_samples[-1]['gc_objects']
            object_increase = last_objects - first_objects
            
            if object_increase > self.leak_indicators['object_accumulation']['threshold']:
                pattern = {
                    'type': 'object_accumulation',
                    'severity': 'HIGH' if object_increase > 5000 else 'MEDIUM',
                    'description': f"Object count increased by {object_increase}"
                }
                self.leak_patterns.append(pattern)
                print(f"⚠️  {pattern['severity']}: {pattern['description']}")
    
    def analyze_object_growth(self):
        """Analyze object count growth patterns."""
        if len(self.memory_samples) < 2:
            return
        
        print("\nOBJECT GROWTH ANALYSIS:")
        print("-" * 40)
        
        object_counts = [sample['gc_objects'] for sample in self.memory_samples]
        
        # Calculate object growth rate
        first_count = object_counts[0]
        last_count = object_counts[-1]
        time_span = (self.memory_samples[-1]['timestamp'] - self.memory_samples[0]['timestamp']) / 3600
        
        object_growth_rate = (last_count - first_count) / time_span if time_span > 0 else 0
        
        print(f"Object count growth: {last_count - first_count} objects")
        print(f"Object growth rate: {object_growth_rate:.0f} objects/hour")
        
        # Correlate object growth with memory growth
        memory_growth = self.memory_samples[-1]['rss_mb'] - self.memory_samples[0]['rss_mb']
        if object_growth_rate > 100 and memory_growth > 5:
            print("⚠️  Strong correlation between object growth and memory growth detected!")
    
    def generate_recommendations(self):
        """Generate recommendations based on detected patterns."""
        print("\nRECOMMENDATIONS:")
        print("-" * 40)
        
        if not self.leak_patterns:
            print("✅ No significant leak patterns detected")
            return
        
        recommendations = []
        
        for pattern in self.leak_patterns:
            if pattern['type'] == 'gradual_increase':
                recommendations.extend([
                    "• Add memory profiling to timer functions (update_status, update_memory_status)",
                    "• Check for unclosed file handles or network connections",
                    "• Review clipboard history management for proper cleanup",
                    "• Add periodic garbage collection in long-running timers"
                ])
            
            elif pattern['type'] == 'periodic_spikes':
                recommendations.extend([
                    "• Profile memory usage during periodic operations",
                    "• Check timer callbacks for memory leaks",
                    "• Review rumps MenuItem creation and cleanup",
                    "• Add memory checkpoints around timer executions"
                ])
            
            elif pattern['type'] == 'object_accumulation':
                recommendations.extend([
                    "• Use weak references for cached objects",
                    "• Implement proper cleanup in object destructors",
                    "• Review clipboard history item storage",
                    "• Add object lifecycle tracking"
                ])
        
        # Remove duplicates and print
        unique_recommendations = list(set(recommendations))
        for rec in unique_recommendations:
            print(rec)
    
    def live_monitoring(self, duration_seconds=3600, sample_interval=30):
        """Perform live memory monitoring."""
        if not self.find_clipboard_process():
            return
        
        print(f"Starting live monitoring for {duration_seconds/60:.0f} minutes...")
        print(f"Sample interval: {sample_interval} seconds")
        print("Press Ctrl+C to stop early and analyze\n")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_seconds:
                sample = self.collect_memory_sample()
                if sample:
                    current_increase = sample['rss_mb'] - self.baseline_memory
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Memory: {sample['rss_mb']:.1f}MB "
                          f"(+{current_increase:.1f}MB) "
                          f"Objects: {sample['gc_objects']}")
                    
                    # Alert on significant increases
                    if current_increase > 50:
                        print(f"⚠️  ALERT: Memory increased by {current_increase:.1f}MB!")
                
                time.sleep(sample_interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        # Analyze collected data
        self.analyze_memory_trend()
    
    def analyze_log_files(self, log_pattern="memory_leak_debug.log"):
        """Analyze existing memory debug log files."""
        print(f"Analyzing log files matching pattern: {log_pattern}")
        
        # Find log files
        log_files = []
        for file in os.listdir('.'):
            if log_pattern in file:
                log_files.append(file)
        
        if not log_files:
            print("No log files found")
            return
        
        print(f"Found {len(log_files)} log files")
        
        # Parse log files
        memory_data = []
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        # Parse memory information from log lines
                        match = re.search(r'Memory: ([\d.]+)MB', line)
                        if match:
                            memory_mb = float(match.group(1))
                            timestamp_match = re.search(r'\[([\d-]+ [\d:]+)\]', line)
                            if timestamp_match:
                                timestamp_str = timestamp_match.group(1)
                                try:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    memory_data.append({
                                        'timestamp': timestamp.timestamp(),
                                        'memory_mb': memory_mb,
                                        'datetime': timestamp_str
                                    })
                                except ValueError:
                                    continue
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
        
        if memory_data:
            # Convert to memory samples format
            self.memory_samples = [
                {
                    'timestamp': data['timestamp'],
                    'datetime': data['datetime'],
                    'rss_mb': data['memory_mb'],
                    'gc_objects': 0  # Not available in logs
                }
                for data in sorted(memory_data, key=lambda x: x['timestamp'])
            ]
            
            if self.memory_samples:
                self.baseline_memory = self.memory_samples[0]['rss_mb']
                print(f"Loaded {len(self.memory_samples)} memory samples from logs")
                self.analyze_memory_trend()
        else:
            print("No memory data found in log files")
    
    def generate_memory_graph(self, output_file="memory_usage_graph.png"):
        """Generate a graph of memory usage over time."""
        if len(self.memory_samples) < 2:
            print("Not enough data for graph generation")
            return
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime
            
            # Prepare data
            timestamps = [datetime.fromtimestamp(sample['timestamp']) for sample in self.memory_samples]
            memory_values = [sample['rss_mb'] for sample in self.memory_samples]
            
            # Create graph
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps, memory_values, 'b-', linewidth=2, label='Memory Usage')
            
            # Add baseline line
            if self.baseline_memory:
                plt.axhline(y=self.baseline_memory, color='g', linestyle='--', 
                           label=f'Baseline ({self.baseline_memory:.1f}MB)')
            
            # Add leak threshold line
            if self.baseline_memory:
                leak_threshold = self.baseline_memory + 50
                plt.axhline(y=leak_threshold, color='r', linestyle='--', 
                           label=f'Leak Threshold ({leak_threshold:.1f}MB)')
            
            plt.xlabel('Time')
            plt.ylabel('Memory Usage (MB)')
            plt.title('Clipboard Monitor Menu Bar - Memory Usage Over Time')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Memory usage graph saved to {output_file}")
            
        except ImportError:
            print("matplotlib not available for graph generation")
        except Exception as e:
            print(f"Error generating graph: {e}")

def main():
    parser = argparse.ArgumentParser(description='Memory Leak Analyzer for Clipboard Monitor')
    parser.add_argument('--live', action='store_true', help='Perform live monitoring')
    parser.add_argument('--analyze-logs', action='store_true', help='Analyze existing log files')
    parser.add_argument('--duration', type=int, default=3600, help='Monitoring duration in seconds (default: 3600)')
    parser.add_argument('--interval', type=int, default=30, help='Sample interval in seconds (default: 30)')
    parser.add_argument('--graph', action='store_true', help='Generate memory usage graph (requires matplotlib)')
    
    args = parser.parse_args()
    
    analyzer = MemoryLeakAnalyzer()
    
    if args.live:
        analyzer.live_monitoring(args.duration, args.interval)
    elif args.analyze_logs:
        analyzer.analyze_log_files()
    else:
        print("Please specify --live or --analyze-logs")
        return
    
    if args.graph:
        analyzer.generate_memory_graph()

if __name__ == "__main__":
    main()
