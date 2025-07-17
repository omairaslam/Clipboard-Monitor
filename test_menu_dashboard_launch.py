#!/usr/bin/env python3
"""
Test script to simulate the menu bar app launching the unified dashboard.
This tests the exact same logic used by the menu bar app.
"""

import os
import sys
import subprocess
import time
import urllib.request

def test_menu_dashboard_launch():
    """Test the dashboard launch logic from the menu bar app."""
    print("🧪 Testing Menu Bar Dashboard Launch Logic")
    print("=" * 50)
    
    # Kill any existing dashboard processes first
    print("1. Cleaning up existing dashboard processes...")
    try:
        subprocess.run(['pkill', '-f', 'unified_memory_dashboard.py'], capture_output=True)
        time.sleep(1)
        print("   ✅ Cleanup completed")
    except:
        print("   ⚠️  Cleanup failed (may be no processes to kill)")
    
    # Replicate the path resolution logic from menu_bar_app.py
    print("2. Testing path resolution...")
    script_path = os.path.join(os.path.dirname(__file__), 'unified_memory_dashboard.py')
    
    # For bundled app, try alternative paths
    if not os.path.exists(script_path):
        script_path = os.path.join(os.path.dirname(sys.executable), 'unified_memory_dashboard.py')
    
    if not os.path.exists(script_path):
        script_path = os.path.join(os.path.dirname(__file__), '..', 'Resources', 'unified_memory_dashboard.py')
    
    if os.path.exists(script_path):
        print(f"   ✅ Found dashboard script at: {script_path}")
    else:
        print(f"   ❌ Dashboard script not found. Searched: {script_path}")
        return False
    
    # Test if the script can be imported (syntax check)
    print("3. Testing dashboard import...")
    try:
        test_proc = subprocess.run([sys.executable, '-c', f'import sys; sys.path.insert(0, "{os.path.dirname(script_path)}"); import unified_memory_dashboard'],
                                 capture_output=True, timeout=10)
        if test_proc.returncode != 0:
            print(f"   ❌ Dashboard import failed: {test_proc.stderr.decode()}")
            return False
        else:
            print("   ✅ Dashboard import successful")
    except Exception as e:
        print(f"   ❌ Dashboard import test error: {e}")
        return False
    
    # Start new dashboard instance (same logic as menu bar app)
    print("4. Starting dashboard process...")
    try:
        proc = subprocess.Popen([sys.executable, script_path],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              cwd=os.path.dirname(script_path))
        print(f"   ✅ Dashboard process started (PID: {proc.pid})")
    except Exception as e:
        print(f"   ❌ Failed to start dashboard: {e}")
        return False
    
    # Wait for server to start and check if it's responding
    print("5. Waiting for dashboard server to start...")
    server_started = False
    for i in range(10):  # Wait up to 10 seconds
        time.sleep(1)
        try:
            response = urllib.request.urlopen('http://localhost:8001', timeout=1)
            if response.status == 200:
                print("   ✅ Dashboard server is responding")
                server_started = True
                break
        except:
            if i == 9:  # Last attempt
                print("   ❌ Dashboard server failed to start")
                # Check if process is still running
                if proc.poll() is not None:
                    stdout, stderr = proc.communicate()
                    print(f"   Process exited with code: {proc.returncode}")
                    if stdout:
                        print(f"   Stdout: {stdout.decode()}")
                    if stderr:
                        print(f"   Stderr: {stderr.decode()}")
                    return False
            continue
    
    if not server_started:
        proc.terminate()
        return False
    
    # Test that the dashboard content is not blank
    print("6. Testing dashboard content...")
    try:
        response = urllib.request.urlopen('http://localhost:8001', timeout=5)
        content = response.read().decode()
        if len(content) > 1000 and 'Unified Memory Dashboard' in content:
            print("   ✅ Dashboard content is valid (not blank)")
        else:
            print("   ❌ Dashboard content appears to be blank or invalid")
            proc.terminate()
            return False
    except Exception as e:
        print(f"   ❌ Failed to fetch dashboard content: {e}")
        proc.terminate()
        return False
    
    # Test API endpoints
    print("7. Testing API endpoints...")
    endpoints = ['/api/memory', '/api/current', '/api/data']
    all_endpoints_work = True
    
    for endpoint in endpoints:
        try:
            response = urllib.request.urlopen(f'http://localhost:8001{endpoint}', timeout=5)
            if response.status == 200:
                print(f"   ✅ API endpoint {endpoint} works")
            else:
                print(f"   ❌ API endpoint {endpoint} returned status {response.status}")
                all_endpoints_work = False
        except Exception as e:
            print(f"   ❌ API endpoint {endpoint} failed: {e}")
            all_endpoints_work = False
    
    # Cleanup
    print("8. Cleaning up...")
    proc.terminate()
    time.sleep(1)
    print("   ✅ Dashboard process terminated")
    
    # Final result
    print("=" * 50)
    if server_started and all_endpoints_work:
        print("🎉 Menu Bar Dashboard Launch Test PASSED")
        print("   The Unified Dashboard menu item should work correctly!")
        return True
    else:
        print("❌ Menu Bar Dashboard Launch Test FAILED")
        return False

if __name__ == "__main__":
    success = test_menu_dashboard_launch()
    sys.exit(0 if success else 1)
