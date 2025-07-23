#!/usr/bin/env python3
"""
Memory Monitoring Status Checker

Quick script to check the current status of all memory monitoring capabilities
in the Clipboard Manager.
"""

import os
import sys
import psutil
import subprocess
from datetime import datetime, timedelta

def check_monitoring_status():
    """Check the status of all memory monitoring components."""
    
    print("🔍 Clipboard Manager - Memory Monitoring Status Check")
    print("=" * 60)
    
    # Check 1: Menu Bar App Process
    print("1. 📱 Menu Bar App Status:")
    menu_process = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'menu_bar_app.py' in cmdline:
                    menu_process = proc
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    cpu_percent = proc.info['cpu_percent']
                    print(f"   ✅ RUNNING - PID: {proc.pid}")
                    print(f"   📊 Memory: {memory_mb:.1f}MB")
                    print(f"   ⚡ CPU: {cpu_percent:.1f}%")
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not menu_process:
        print("   ❌ NOT RUNNING - Menu bar app not found")
        print("   💡 Try: ./restart_menubar.sh")
        return False
    
    # Check 2: Memory Debug Log
    print("\n2. 📋 Memory Debug Log:")
    log_path = "memory_leak_debug.log"
    if os.path.exists(log_path):
        try:
            stat = os.stat(log_path)
            size_kb = stat.st_size / 1024
            modified = datetime.fromtimestamp(stat.st_mtime)
            age = datetime.now() - modified
            
            print(f"   ✅ EXISTS - Size: {size_kb:.1f}KB")
            print(f"   🕐 Last Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ⏰ Age: {age.total_seconds():.0f} seconds ago")
            
            # Check if log is being actively written
            if age.total_seconds() < 600:  # Less than 10 minutes old
                print("   ✅ ACTIVE - Recently updated")
            else:
                print("   ⚠️  STALE - No recent updates")
                
            # Get recent entries
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            if lines:
                print(f"   📊 Total Entries: {len(lines)}")
                print("   📝 Recent Entries:")
                for line in lines[-3:]:
                    print(f"      {line.strip()}")
            else:
                print("   ❌ EMPTY - No log entries found")
                
        except Exception as e:
            print(f"   ❌ ERROR - Cannot read log: {e}")
    else:
        print("   ❌ MISSING - Log file not found")
        print("   💡 Log should be created automatically when app starts")
    
    # Check 3: Background Monitoring
    print("\n3. 🔄 Background Monitoring:")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Look for monitoring indicators
            monitor_entries = content.count("monitor_loop")
            memory_checks = content.count("Memory check")
            baseline_entries = content.count("Baseline")
            
            print(f"   📊 Monitor Loop Entries: {monitor_entries}")
            print(f"   🔍 Memory Checks: {memory_checks}")
            print(f"   📍 Baseline Entries: {baseline_entries}")
            
            if monitor_entries > 0:
                print("   ✅ ACTIVE - Background monitoring detected")
            else:
                print("   ⚠️  INACTIVE - No background monitoring detected")
                
        except Exception as e:
            print(f"   ❌ ERROR - Cannot analyze log: {e}")
    
    # Check 4: VS Code Integration
    print("\n4. 🎛️ VS Code Integration:")
    vscode_tasks = ".vscode/tasks.json"
    vscode_settings = ".vscode/settings.json"
    
    if os.path.exists(vscode_tasks):
        try:
            with open(vscode_tasks, 'r') as f:
                tasks_content = f.read()
            
            memory_tasks = tasks_content.count("Memory Monitor")
            debug_tasks = tasks_content.count("Memory Debug")
            
            print(f"   ✅ TASKS - {memory_tasks} memory monitoring tasks found")
            print(f"   🔍 DEBUG - {debug_tasks} debug tasks found")
            
        except Exception as e:
            print(f"   ❌ ERROR - Cannot read tasks.json: {e}")
    else:
        print("   ❌ MISSING - .vscode/tasks.json not found")
    
    if os.path.exists(vscode_settings):
        try:
            with open(vscode_settings, 'r') as f:
                settings_content = f.read()
            
            memory_buttons = settings_content.count("Memory")
            
            print(f"   🎛️ BUTTONS - {memory_buttons} memory-related buttons configured")
            
        except Exception as e:
            print(f"   ❌ ERROR - Cannot read settings.json: {e}")
    else:
        print("   ❌ MISSING - .vscode/settings.json not found")
    
    # Check 5: Monitoring Tools
    print("\n5. 🛠️ Monitoring Tools:")
    tools = [
        "memory_debugging/quick_monitor.py",
        "memory_debugging/simple_monitor.py", 
        "memory_debugging/memory_leak_analyzer.py"
    ]
    
    for tool in tools:
        if os.path.exists(tool):
            print(f"   ✅ {os.path.basename(tool)} - Available")
        else:
            print(f"   ❌ {os.path.basename(tool)} - Missing")
    
    # Check 6: Current Memory Health
    print("\n6. 🏥 Current Memory Health:")
    if menu_process:
        try:
            memory_info = menu_process.memory_info()
            rss_mb = memory_info.rss / 1024 / 1024
            vms_mb = memory_info.vms / 1024 / 1024
            cpu_percent = menu_process.cpu_percent()
            
            print(f"   📊 RSS Memory: {rss_mb:.1f}MB")
            print(f"   💾 VMS Memory: {vms_mb:.1f}MB")
            print(f"   ⚡ CPU Usage: {cpu_percent:.1f}%")
            
            # Health assessment
            if rss_mb < 100 and cpu_percent < 5:
                print("   ✅ HEALTHY - Memory and CPU usage normal")
            elif rss_mb < 200 and cpu_percent < 15:
                print("   ⚠️  CAUTION - Elevated resource usage")
            else:
                print("   🚨 CRITICAL - High resource usage detected")
                
        except Exception as e:
            print(f"   ❌ ERROR - Cannot get memory info: {e}")
    
    # Summary and Recommendations
    print("\n" + "=" * 60)
    print("📋 SUMMARY & RECOMMENDATIONS:")
    
    if menu_process and os.path.exists(log_path):
        print("✅ Core monitoring is operational")
        print("💡 Recommendations:")
        print("   • Use 'tail -f memory_leak_debug.log' for real-time monitoring")
        print("   • Run periodic checks with VS Code buttons")
        print("   • Monitor memory growth trends weekly")
    else:
        print("❌ Core monitoring has issues")
        print("🔧 Troubleshooting steps:")
        print("   1. Restart the menu bar app: ./restart_menubar.sh")
        print("   2. Check for error messages in console")
        print("   3. Verify file permissions in project directory")
    
    print("\n🎯 Quick Actions:")
    print("   • Real-time log: tail -f memory_leak_debug.log")
    print("   • Quick check: cd memory_debugging && python3 quick_monitor.py 0.1 10")
    print("   • VS Code: Click '🔍 Memory Debug Log' button")

def main():
    """Main function."""
    try:
        check_monitoring_status()
    except KeyboardInterrupt:
        print("\n\n⏹️  Status check interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during status check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
