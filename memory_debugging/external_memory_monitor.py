#!/usr/bin/env python3
"""
External Memory Monitor

Monitors the menu bar app's memory usage externally without modifying its code.
This is a safe, non-intrusive way to track memory usage and detect potential leaks.
"""

import psutil
import time
import json
import argparse
from datetime import datetime
import os
import signal
import sys

class ExternalMemoryMonitor:
    def __init__(self, process_name="menu_bar_app.py", log_file="memory_leak_debug.log"):
        self.process_name = process_name
        self.log_file = log_file
        self.monitoring = False
        self.start_time = None
        self.baseline_memory = None
        
    def find_target_process(self):
        """Find the target process by name."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if it's a Python process running our script
                if proc.info['name'] == 'Python' or proc.info['name'] == 'python3':
                    cmdline = proc.info['cmdline']
                    if cmdline and any(self.process_name in arg for arg in cmdline):
                        return proc
                        
                # Also check direct process name match
                if self.process_name.replace('.py', '') in proc.info['name']:
                    return proc
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None
    
    def log_memory_data(self, process, message="", level="INFO"):
        """Log memory data to file."""
        try:
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            vms_mb = memory_info.vms / 1024 / 1024
            
            # Get additional process info
            cpu_percent = process.cpu_percent()
            num_threads = process.num_threads()
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            system_memory_percent = system_memory.percent
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Calculate memory delta if we have baseline
            memory_delta = ""
            if self.baseline_memory:
                delta = memory_mb - self.baseline_memory
                memory_delta = f" Delta: {delta:+.1f}MB"
            
            # Build log entry
            log_entry = (
                f"[{timestamp}] [{level}] "
                f"RSS: {memory_mb:.1f}MB "
                f"VMS: {vms_mb:.1f}MB "
                f"CPU: {cpu_percent:.1f}% "
                f"Threads: {num_threads} "
                f"System: {system_memory_percent:.1f}%"
                f"{memory_delta}"
                f" | {message}"
            )
            
            # Write to log file
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
            
            # Print to console for important events
            if level in ["WARNING", "ERROR"] or "started" in message.lower() or "stopped" in message.lower():
                print(log_entry)
                
            return memory_mb
            
        except Exception as e:
            error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Failed to log memory data: {e}"
            with open(self.log_file, "a") as f:
                f.write(error_msg + "\n")
            print(error_msg)
            return None
    
    def monitor_process(self, duration_minutes=30, interval_seconds=5):
        """Monitor the process for specified duration."""
        print(f"🔍 External Memory Monitor Starting")
        print(f"📱 Target: {self.process_name}")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        print(f"📊 Interval: {interval_seconds} seconds")
        print(f"📁 Log file: {self.log_file}")
        print("")
        
        # Find the target process
        process = self.find_target_process()
        if not process:
            print(f"❌ Process '{self.process_name}' not found!")
            print("   Make sure the menu bar app is running.")
            return False
        
        print(f"✅ Found process: PID {process.pid}")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Monitoring stopped by user")
            self.monitoring = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Initialize monitoring
        self.monitoring = True
        self.start_time = time.time()
        end_time = self.start_time + (duration_minutes * 60)
        
        # Log initial state
        initial_memory = self.log_memory_data(process, f"External monitoring started (PID: {process.pid})", "INFO")
        if initial_memory:
            self.baseline_memory = initial_memory
        
        sample_count = 0
        memory_readings = []
        
        try:
            while self.monitoring and time.time() < end_time:
                # Check if process still exists
                if not process.is_running():
                    self.log_memory_data(process, "Process terminated", "WARNING")
                    print("⚠️  Target process terminated")
                    break
                
                # Log memory data
                current_memory = self.log_memory_data(process, f"Sample #{sample_count + 1}")
                if current_memory:
                    memory_readings.append(current_memory)
                    sample_count += 1
                
                # Show progress every 10 samples
                if sample_count % 10 == 0:
                    elapsed = time.time() - self.start_time
                    remaining = end_time - time.time()
                    progress = (elapsed / (duration_minutes * 60)) * 100
                    
                    if memory_readings:
                        current_mem = memory_readings[-1]
                        min_mem = min(memory_readings)
                        max_mem = max(memory_readings)
                        
                        print(f"📊 Progress: {progress:.1f}% | "
                              f"Samples: {sample_count} | "
                              f"Current: {current_mem:.1f}MB | "
                              f"Range: {min_mem:.1f}-{max_mem:.1f}MB | "
                              f"Remaining: {remaining/60:.1f}m")
                
                time.sleep(interval_seconds)
                
        except Exception as e:
            self.log_memory_data(process, f"Monitoring error: {e}", "ERROR")
            print(f"❌ Monitoring error: {e}")
        
        # Final summary
        self.monitoring = False
        elapsed_time = time.time() - self.start_time
        
        if memory_readings:
            final_memory = self.log_memory_data(process, f"External monitoring completed ({sample_count} samples)", "INFO")
            
            min_memory = min(memory_readings)
            max_memory = max(memory_readings)
            avg_memory = sum(memory_readings) / len(memory_readings)
            memory_growth = memory_readings[-1] - memory_readings[0] if len(memory_readings) > 1 else 0
            
            print(f"\n📊 Monitoring Summary:")
            print(f"   Duration: {elapsed_time/60:.1f} minutes")
            print(f"   Samples: {sample_count}")
            print(f"   Memory Range: {min_memory:.1f}MB - {max_memory:.1f}MB")
            print(f"   Average Memory: {avg_memory:.1f}MB")
            print(f"   Memory Growth: {memory_growth:+.1f}MB")
            
            # Detect potential issues
            if memory_growth > 10:
                print(f"⚠️  Potential memory leak detected! Growth: {memory_growth:.1f}MB")
            elif max_memory - min_memory > 20:
                print(f"⚠️  High memory variation detected! Range: {max_memory - min_memory:.1f}MB")
            else:
                print(f"✅ Memory usage appears stable")
        
        print(f"\n📁 Complete log saved to: {self.log_file}")
        return True

def main():
    parser = argparse.ArgumentParser(description='External Memory Monitor for Menu Bar App')
    parser.add_argument('--duration', type=int, default=30, help='Monitoring duration in minutes (default: 30)')
    parser.add_argument('--interval', type=int, default=5, help='Sampling interval in seconds (default: 5)')
    parser.add_argument('--process', type=str, default='menu_bar_app.py', help='Process name to monitor')
    parser.add_argument('--log', type=str, default='memory_leak_debug.log', help='Log file path')
    parser.add_argument('--clear-log', action='store_true', help='Clear log file before starting')
    
    args = parser.parse_args()
    
    # Clear log file if requested
    if args.clear_log and os.path.exists(args.log):
        os.remove(args.log)
        print(f"🗑️  Cleared log file: {args.log}")
    
    # Create monitor and start monitoring
    monitor = ExternalMemoryMonitor(args.process, args.log)
    success = monitor.monitor_process(args.duration, args.interval)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
