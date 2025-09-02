#!/usr/bin/env python3
"""
Quick Memory Status Checker for Clipboard Monitor
Works in Emergency Safe Mode - checks memory usage of both processes
"""

import psutil
import sys
import os

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}TB"

def find_clipboard_processes():
    """Find clipboard monitor processes"""
    processes = {
        'menu_bar': None,
        'main_service': None
    }
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if not cmdline:
                continue
                
            cmdline_str = ' '.join(cmdline)
            
            # Check for menu bar app
            if 'menu_bar_app.py' in cmdline_str:
                processes['menu_bar'] = proc
            
            # Check for main service
            elif 'main.py' in cmdline_str and 'clipboard' in cmdline_str.lower():
                processes['main_service'] = proc
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return processes

def get_process_info(proc):
    """Get detailed process information"""
    try:
        memory_info = proc.memory_info()
        cpu_percent = proc.cpu_percent()
        
        return {
            'pid': proc.pid,
            'memory_rss': memory_info.rss,
            'memory_vms': memory_info.vms,
            'cpu_percent': cpu_percent,
            'num_threads': proc.num_threads(),
            'status': proc.status()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def main():
    print("🔍 Clipboard Monitor - Memory Status Check")
    print("=" * 50)
    
    processes = find_clipboard_processes()
    
    total_memory = 0
    found_processes = 0
    
    for name, proc in processes.items():
        if proc is None:
            print(f"❌ {name.replace('_', ' ').title()}: Not running")
            continue
            
        info = get_process_info(proc)
        if info is None:
            print(f"❌ {name.replace('_', ' ').title()}: Process access denied")
            continue
            
        found_processes += 1
        total_memory += info['memory_rss']
        
        print(f"\n✅ {name.replace('_', ' ').title()}:")
        print(f"   PID: {info['pid']}")
        print(f"   Memory (RSS): {format_bytes(info['memory_rss'])}")
        print(f"   Memory (VMS): {format_bytes(info['memory_vms'])}")
        print(f"   CPU Usage: {info['cpu_percent']:.1f}%")
        print(f"   Threads: {info['num_threads']}")
        print(f"   Status: {info['status']}")
    
    if found_processes > 0:
        print(f"\n📊 Summary:")
        print(f"   Total Processes: {found_processes}")
        print(f"   Combined Memory: {format_bytes(total_memory)}")
        
        # Memory health assessment
        total_mb = total_memory / (1024 * 1024)
        if total_mb < 100:
            print(f"   Health: ✅ Excellent (< 100MB)")
        elif total_mb < 200:
            print(f"   Health: ✅ Good (< 200MB)")
        elif total_mb < 500:
            print(f"   Health: ⚠️  Moderate (< 500MB)")
        else:
            print(f"   Health: ❌ High memory usage (> 500MB)")
    else:
        print("\n❌ No Clipboard Monitor processes found!")
        return 1
    
    # System memory info
    system_memory = psutil.virtual_memory()
    print(f"\n🖥️  System Memory:")
    print(f"   Total: {format_bytes(system_memory.total)}")
    print(f"   Available: {format_bytes(system_memory.available)}")
    print(f"   Used: {system_memory.percent:.1f}%")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
