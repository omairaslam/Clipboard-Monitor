#!/usr/bin/env python3

import psutil

print("=== DEBUG: Testing clipboard process detection ===")

# Get the specific PIDs we know are running
target_pids = [71235, 71483, 71481]  # menu_bar_app.py, main.py (user), main.py (root)

print(f"Looking for PIDs: {target_pids}")
print()

for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
    try:
        pid = proc.info['pid']
        
        # Only check our target PIDs
        if pid not in target_pids:
            continue
            
        name = proc.info['name']
        cmdline = proc.info.get('cmdline', [])
        
        # Get memory and CPU from the iterator
        memory_info = proc.info.get('memory_info')
        if memory_info:
            memory_mb = memory_info.rss / 1024 / 1024
        else:
            memory_mb = 0
        
        cpu_percent = proc.info.get('cpu_percent', 0) or 0

        print(f"PID {pid}:")
        print(f"  Name: {name}")
        print(f"  Cmdline: {cmdline}")
        print(f"  Memory: {memory_mb:.2f} MB")
        print(f"  CPU: {cpu_percent}%")
        
        # Test detection logic
        is_clipboard_process = False
        cmdline_str = ""
        
        if cmdline:
            cmdline_str = ' '.join(cmdline).lower()
            print(f"  Cmdline string: '{cmdline_str}'")
            
            # Check by command line (original logic)
            is_clipboard_process = any(keyword in cmdline_str for keyword in [
                'clipboard', 'menu_bar_app', 'main.py'
            ])
            print(f"  Matches clipboard keywords: {is_clipboard_process}")
            
            # Test specific matches
            if 'menu_bar_app.py' in cmdline_str:
                print(f"  → DETECTED AS MENU BAR APP")
            elif 'main.py' in cmdline_str:
                has_clipboard = any(path_part in cmdline_str for path_part in [
                    'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                ])
                print(f"  → DETECTED AS MAIN.PY, has clipboard path: {has_clipboard}")
                if has_clipboard:
                    print(f"  → DETECTED AS MAIN SERVICE")
        
        # Also check by process name (for PyInstaller executables)
        if not is_clipboard_process and name == 'ClipboardMonitor':
            is_clipboard_process = True
            print(f"  → DETECTED BY PROCESS NAME")
        
        print(f"  Final detection: {is_clipboard_process}")
        print()
        
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"Error with PID {pid}: {e}")
        print()

print("=== END DEBUG ===")
