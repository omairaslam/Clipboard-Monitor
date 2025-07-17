#!/usr/bin/env python3
"""
Test script to verify the unified dashboard fix works properly.
"""

import subprocess
import sys
import time
import urllib.request
import os

def test_dashboard_import():
    """Test if the dashboard can be imported without errors."""
    print("Testing dashboard import...")
    try:
        result = subprocess.run([sys.executable, '-c', 'import unified_memory_dashboard; print("Import successful")'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Dashboard import test passed")
            return True
        else:
            print(f"❌ Dashboard import test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Dashboard import test error: {e}")
        return False

def test_dashboard_startup():
    """Test if the dashboard can start and serve content."""
    print("Testing dashboard startup...")
    
    # Kill any existing dashboard processes
    try:
        subprocess.run(['pkill', '-f', 'unified_memory_dashboard.py'], capture_output=True)
        time.sleep(1)
    except:
        pass
    
    # Start dashboard
    try:
        proc = subprocess.Popen([sys.executable, 'unified_memory_dashboard.py'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        for i in range(10):
            time.sleep(1)
            try:
                response = urllib.request.urlopen('http://localhost:8001', timeout=2)
                if response.status == 200:
                    print("✅ Dashboard startup test passed")
                    proc.terminate()
                    return True
            except:
                continue
        
        # If we get here, server didn't start
        proc.terminate()
        stdout, stderr = proc.communicate()
        print(f"❌ Dashboard startup test failed")
        print(f"Stdout: {stdout.decode()}")
        print(f"Stderr: {stderr.decode()}")
        return False
        
    except Exception as e:
        print(f"❌ Dashboard startup test error: {e}")
        return False

def test_dashboard_api():
    """Test if the dashboard API endpoints work."""
    print("Testing dashboard API...")
    
    # Kill any existing dashboard processes
    try:
        subprocess.run(['pkill', '-f', 'unified_memory_dashboard.py'], capture_output=True)
        time.sleep(1)
    except:
        pass
    
    # Start dashboard
    try:
        proc = subprocess.Popen([sys.executable, 'unified_memory_dashboard.py'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        server_started = False
        for i in range(10):
            time.sleep(1)
            try:
                response = urllib.request.urlopen('http://localhost:8001', timeout=2)
                if response.status == 200:
                    server_started = True
                    break
            except:
                continue
        
        if not server_started:
            proc.terminate()
            print("❌ Dashboard API test failed - server didn't start")
            return False
        
        # Test API endpoints
        endpoints = [
            '/api/memory',
            '/api/current',
            '/api/data',
            '/api/processes',
            '/api/system'
        ]
        
        all_passed = True
        for endpoint in endpoints:
            try:
                response = urllib.request.urlopen(f'http://localhost:8001{endpoint}', timeout=5)
                if response.status == 200:
                    print(f"✅ API endpoint {endpoint} works")
                else:
                    print(f"❌ API endpoint {endpoint} returned status {response.status}")
                    all_passed = False
            except Exception as e:
                print(f"❌ API endpoint {endpoint} failed: {e}")
                all_passed = False
        
        proc.terminate()
        
        if all_passed:
            print("✅ Dashboard API test passed")
            return True
        else:
            print("❌ Dashboard API test failed")
            return False
        
    except Exception as e:
        print(f"❌ Dashboard API test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Unified Dashboard Fix")
    print("=" * 50)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    tests = [
        test_dashboard_import,
        test_dashboard_startup,
        test_dashboard_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The dashboard fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
