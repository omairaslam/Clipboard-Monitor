#!/usr/bin/env python3
"""
Comprehensive Memory & CPU Monitor for Menu Bar App
Tracks detailed metrics during the 1-hour test
"""

import psutil
import time
import datetime
import json
import sys
import os

def find_menu_bar_process():
    """Find the menu bar app process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and any('menu_bar_app.py' in arg for arg in proc.info['cmdline']):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def monitor_comprehensive(duration_minutes=30, interval_seconds=60):
    """Run comprehensive monitoring"""
    pid = find_menu_bar_process()
    if not pid:
        print("❌ Menu bar app process not found!")
        return
    
    print(f"🔍 Starting Comprehensive Monitor")
    print(f"📱 Target PID: {pid}")
    print(f"⏱️  Duration: {duration_minutes} minutes")
    print(f"📊 Interval: {interval_seconds} seconds")
    print(f"📁 Log file: comprehensive_monitor.log")
    print()
    
    try:
        process = psutil.Process(pid)
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        log_data = []
        sample_count = 0
        
        while time.time() < end_time:
            try:
                # Get memory info
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                vms_mb = memory_info.vms / 1024 / 1024
                
                # Get CPU info
                cpu_percent = process.cpu_percent()
                
                # Get thread count
                thread_count = process.num_threads()
                
                # Get system memory
                system_memory = psutil.virtual_memory()
                system_cpu = psutil.cpu_percent()
                
                # Create log entry
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                elapsed_minutes = (time.time() - start_time) / 60
                
                log_entry = {
                    'timestamp': timestamp,
                    'elapsed_minutes': round(elapsed_minutes, 1),
                    'memory_mb': round(memory_mb, 1),
                    'vms_mb': round(vms_mb, 1),
                    'cpu_percent': round(cpu_percent, 1),
                    'threads': thread_count,
                    'system_memory_percent': round(system_memory.percent, 1),
                    'system_cpu_percent': round(system_cpu, 1)
                }
                
                log_data.append(log_entry)
                sample_count += 1
                
                # Progress update
                progress = (elapsed_minutes / duration_minutes) * 100
                remaining_minutes = duration_minutes - elapsed_minutes
                
                print(f"📊 Progress: {progress:.1f}% | Sample: {sample_count} | "
                      f"Memory: {memory_mb:.1f}MB | CPU: {cpu_percent:.1f}% | "
                      f"Threads: {thread_count} | Remaining: {remaining_minutes:.1f}m")
                
                # Save log periodically
                if sample_count % 5 == 0:
                    with open('comprehensive_monitor.log', 'w') as f:
                        json.dump(log_data, f, indent=2)
                
                time.sleep(interval_seconds)
                
            except psutil.NoSuchProcess:
                print("❌ Process terminated!")
                break
            except Exception as e:
                print(f"⚠️  Error during monitoring: {e}")
                time.sleep(interval_seconds)
        
        # Final save
        with open('comprehensive_monitor.log', 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Summary
        if log_data:
            memory_values = [entry['memory_mb'] for entry in log_data]
            cpu_values = [entry['cpu_percent'] for entry in log_data]
            
            print(f"\n📊 Comprehensive Monitoring Summary:")
            print(f"   Duration: {elapsed_minutes:.1f} minutes")
            print(f"   Samples: {len(log_data)}")
            print(f"   Memory Range: {min(memory_values):.1f}MB - {max(memory_values):.1f}MB")
            print(f"   Average Memory: {sum(memory_values)/len(memory_values):.1f}MB")
            print(f"   Memory Growth: {memory_values[-1] - memory_values[0]:+.1f}MB")
            print(f"   Average CPU: {sum(cpu_values)/len(cpu_values):.1f}%")
            print(f"   Max CPU: {max(cpu_values):.1f}%")
            print(f"📁 Complete log saved to: comprehensive_monitor.log")
        
    except psutil.NoSuchProcess:
        print("❌ Process not found!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    monitor_comprehensive()
