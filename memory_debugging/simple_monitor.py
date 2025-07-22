#!/usr/bin/env python3
"""
Simple Memory Monitor for Clipboard Monitor

This script monitors the menu bar app's memory usage without requiring
additional dependencies like matplotlib.
"""

import psutil
import time
import os
from datetime import datetime

class SimpleMemoryMonitor:
    def __init__(self):
        self.process = None
        self.baseline_memory = None
        self.samples = []
        self.start_time = time.time()
        
    def find_clipboard_process(self):
        """Find the clipboard monitor menu bar process."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'menu_bar_app.py' in cmdline:
                        self.process = proc
                        print(f"✅ Found clipboard monitor process: PID {proc.pid}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("❌ Clipboard monitor menu bar process not found!")
        return False
    
    def get_memory_info(self):
        """Get current memory information."""
        if not self.process:
            return None
            
        try:
            memory_info = self.process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': self.process.memory_percent(),
                'timestamp': time.time()
            }
        except psutil.NoSuchProcess:
            print("❌ Process no longer exists")
            return None
        except Exception as e:
            print(f"❌ Error getting memory info: {e}")
            return None
    
    def monitor(self, duration_hours=2, sample_interval=60):
        """Monitor memory usage for specified duration."""
        if not self.find_clipboard_process():
            return
        
        duration_seconds = duration_hours * 3600
        print(f"🔍 Starting memory monitoring for {duration_hours} hours...")
        print(f"📊 Sample interval: {sample_interval} seconds")
        print(f"⏰ Monitoring until: {datetime.fromtimestamp(time.time() + duration_seconds).strftime('%H:%M:%S')}")
        print("Press Ctrl+C to stop early\n")
        
        # Take initial sample
        initial_sample = self.get_memory_info()
        if initial_sample:
            self.baseline_memory = initial_sample['rss_mb']
            self.samples.append(initial_sample)
            print(f"📍 Baseline memory: {self.baseline_memory:.1f}MB")
        
        try:
            while time.time() - self.start_time < duration_seconds:
                sample = self.get_memory_info()
                if sample:
                    self.samples.append(sample)
                    
                    # Calculate increase from baseline
                    increase = sample['rss_mb'] - self.baseline_memory
                    elapsed_hours = (time.time() - self.start_time) / 3600
                    
                    # Display current status
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] Memory: {sample['rss_mb']:.1f}MB "
                          f"(+{increase:+.1f}MB) "
                          f"| Elapsed: {elapsed_hours:.1f}h")
                    
                    # Alert on significant increases
                    if increase > 20:
                        print(f"⚠️  ALERT: Memory increased by {increase:.1f}MB!")
                    
                    # Calculate growth rate if we have enough samples
                    if len(self.samples) >= 5:
                        recent_samples = self.samples[-5:]
                        time_span = recent_samples[-1]['timestamp'] - recent_samples[0]['timestamp']
                        memory_growth = recent_samples[-1]['rss_mb'] - recent_samples[0]['rss_mb']
                        
                        if time_span > 0:
                            growth_rate = (memory_growth / (time_span / 3600))  # MB per hour
                            if abs(growth_rate) > 5:  # More than 5MB/hour growth
                                print(f"📈 Growth rate: {growth_rate:+.1f}MB/hour")
                
                time.sleep(sample_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate a final monitoring report."""
        if len(self.samples) < 2:
            print("❌ Not enough samples for analysis")
            return
        
        print("\n" + "="*60)
        print("📊 MEMORY MONITORING REPORT")
        print("="*60)
        
        first_sample = self.samples[0]
        last_sample = self.samples[-1]
        
        total_time = (last_sample['timestamp'] - first_sample['timestamp']) / 3600
        memory_increase = last_sample['rss_mb'] - first_sample['rss_mb']
        growth_rate = memory_increase / total_time if total_time > 0 else 0
        
        print(f"📅 Monitoring Duration: {total_time:.2f} hours")
        print(f"📊 Total Samples: {len(self.samples)}")
        print(f"🎯 Baseline Memory: {first_sample['rss_mb']:.1f}MB")
        print(f"🔚 Final Memory: {last_sample['rss_mb']:.1f}MB")
        print(f"📈 Memory Increase: {memory_increase:+.1f}MB")
        print(f"⚡ Growth Rate: {growth_rate:+.2f}MB/hour")
        
        # Analyze trend
        if growth_rate > 10:
            print(f"🚨 HIGH LEAK DETECTED: {growth_rate:.1f}MB/hour growth!")
        elif growth_rate > 5:
            print(f"⚠️  MODERATE LEAK: {growth_rate:.1f}MB/hour growth")
        elif growth_rate > 1:
            print(f"⚠️  MINOR LEAK: {growth_rate:.1f}MB/hour growth")
        else:
            print(f"✅ STABLE: {growth_rate:.1f}MB/hour growth (normal)")
        
        # Find peak memory usage
        peak_memory = max(sample['rss_mb'] for sample in self.samples)
        peak_increase = peak_memory - first_sample['rss_mb']
        print(f"🏔️  Peak Memory: {peak_memory:.1f}MB (+{peak_increase:.1f}MB)")
        
        # Calculate average memory over time
        avg_memory = sum(sample['rss_mb'] for sample in self.samples) / len(self.samples)
        print(f"📊 Average Memory: {avg_memory:.1f}MB")
        
        print("\n📋 RECOMMENDATIONS:")
        if growth_rate > 5:
            print("• Check memory_leak_debug.log for function-level profiling")
            print("• Focus on timer functions (update_status, update_memory_status)")
            print("• Review clipboard history management")
            print("• Consider adding periodic garbage collection")
        else:
            print("• Memory usage appears stable")
            print("• Continue monitoring for longer periods")
        
        # Save detailed report
        report_file = f"memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w') as f:
                f.write("MEMORY MONITORING DETAILED REPORT\n")
                f.write("="*50 + "\n\n")
                f.write(f"Monitoring Duration: {total_time:.2f} hours\n")
                f.write(f"Growth Rate: {growth_rate:+.2f}MB/hour\n")
                f.write(f"Memory Increase: {memory_increase:+.1f}MB\n\n")
                f.write("SAMPLE DATA:\n")
                f.write("Timestamp\t\tMemory(MB)\tIncrease(MB)\n")
                f.write("-" * 50 + "\n")
                
                for sample in self.samples:
                    timestamp = datetime.fromtimestamp(sample['timestamp']).strftime('%H:%M:%S')
                    increase = sample['rss_mb'] - first_sample['rss_mb']
                    f.write(f"{timestamp}\t\t{sample['rss_mb']:.1f}\t\t{increase:+.1f}\n")
            
            print(f"📄 Detailed report saved: {report_file}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")

def main():
    monitor = SimpleMemoryMonitor()
    
    print("🔍 Simple Memory Monitor for Clipboard Monitor")
    print("=" * 50)
    
    # Default: Monitor for 2 hours with 1-minute intervals
    duration = 2  # hours
    interval = 60  # seconds
    
    try:
        duration_input = input(f"Monitor duration in hours (default {duration}): ").strip()
        if duration_input:
            duration = float(duration_input)
    except ValueError:
        print("Using default duration")
    
    try:
        interval_input = input(f"Sample interval in seconds (default {interval}): ").strip()
        if interval_input:
            interval = int(interval_input)
    except ValueError:
        print("Using default interval")
    
    monitor.monitor(duration, interval)

if __name__ == "__main__":
    main()
