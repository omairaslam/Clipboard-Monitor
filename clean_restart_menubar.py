#!/usr/bin/env python3
"""
Clean Menu Bar App Restart
Ensures proper cleanup before starting new instance to prevent duplicates.
"""

import os
import sys
import time
import psutil
import subprocess
from pathlib import Path


def kill_all_menu_bar_processes():
    """Kill all existing menu bar app processes"""
    killed_pids = []
    
    print("🔍 Finding existing menu bar processes...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'menu_bar_app.py' in ' '.join(cmdline):
                pid = proc.info['pid']
                print(f"   Found process PID {pid}")
                
                try:
                    # Try graceful termination first
                    proc.terminate()
                    killed_pids.append(pid)
                    print(f"   Terminated PID {pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed_pids:
        print(f"⏳ Waiting for graceful shutdown of {len(killed_pids)} processes...")
        time.sleep(3)
        
        # Force kill any remaining processes
        remaining = []
        for pid in killed_pids:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    proc.kill()
                    remaining.append(pid)
                    print(f"   Force killed PID {pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if remaining:
            print(f"⏳ Waiting for force kill cleanup...")
            time.sleep(2)

            # Final check and force kill any stubborn processes
            for attempt in range(3):
                stubborn = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and 'menu_bar_app.py' in ' '.join(cmdline):
                            stubborn.append(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if not stubborn:
                    break

                print(f"   Attempt {attempt + 1}: Force killing stubborn processes: {stubborn}")
                for pid in stubborn:
                    try:
                        os.kill(pid, 9)  # SIGKILL
                    except (ProcessLookupError, PermissionError):
                        pass
                time.sleep(1)
    else:
        print("   No existing processes found")

    return len(killed_pids)


def verify_no_processes():
    """Verify no menu bar processes are running"""
    remaining = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'menu_bar_app.py' in ' '.join(cmdline):
                remaining.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if remaining:
        print(f"⚠️  Warning: {len(remaining)} processes still running: {remaining}")
        return False
    else:
        print("✅ All menu bar processes stopped")
        return True


def start_new_instance():
    """Start a fresh menu bar app instance"""
    print("🚀 Starting fresh menu bar app...")
    
    script_dir = Path(__file__).parent
    script_path = script_dir / 'menu_bar_app.py'
    
    if not script_path.exists():
        print(f"❌ Error: menu_bar_app.py not found at {script_path}")
        return None
    
    try:
        # Start new process
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(script_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"   Started new process PID {proc.pid}")
        
        # Give it a moment to initialize
        time.sleep(3)
        
        # Verify it's running
        if proc.poll() is None:
            # Check memory usage
            try:
                process = psutil.Process(proc.pid)
                memory_mb = process.memory_info().rss / 1024 / 1024
                print(f"   ✅ Process running successfully")
                print(f"   Memory usage: {memory_mb:.1f} MB")
                
                if memory_mb > 100:
                    print(f"   ⚠️  Memory usage seems high for fresh process")
                else:
                    print(f"   ✅ Memory usage looks good")
                    
                return proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"   ❌ Process started but can't read memory info")
                return proc.pid
        else:
            print(f"   ❌ Process failed to start (exit code: {proc.returncode})")
            return None
            
    except Exception as e:
        print(f"   ❌ Error starting process: {e}")
        return None


def main():
    """Main clean restart function"""
    print("🔄 CLEAN MENU BAR APP RESTART")
    print("=" * 50)
    
    # Step 1: Kill all existing processes
    killed_count = kill_all_menu_bar_processes()
    
    # Step 2: Verify cleanup
    if not verify_no_processes():
        print("❌ Failed to clean up all processes")
        return False
    
    # Step 3: Start fresh instance
    new_pid = start_new_instance()
    
    if new_pid:
        print("\n" + "=" * 50)
        print("✅ CLEAN RESTART SUCCESSFUL!")
        print(f"   New process PID: {new_pid}")
        print(f"   Killed old processes: {killed_count}")
        print("   Check your menu bar for a single clipboard monitor icon")
        return True
    else:
        print("\n" + "=" * 50)
        print("❌ RESTART FAILED!")
        print("   Could not start new menu bar app")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
