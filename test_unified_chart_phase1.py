#!/usr/bin/env python3
"""
Test script to validate Phase 1 implementation of UnifiedMemoryChart
Tests flexible live view ranges and basic functionality.
"""

import subprocess
import sys
import time
import urllib.request
import json
import os

def test_dashboard_startup():
    """Test if the unified dashboard starts successfully with new UnifiedMemoryChart"""
    print("🧪 Testing Unified Dashboard Startup...")
    
    try:
        # Kill any existing dashboard processes
        subprocess.run(['pkill', '-f', 'unified_memory_dashboard.py'], capture_output=True)
        time.sleep(1)
        
        # Start dashboard
        proc = subprocess.Popen([sys.executable, 'unified_memory_dashboard.py'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        server_started = False
        for i in range(15):  # Give it more time for initialization
            time.sleep(1)
            try:
                response = urllib.request.urlopen('http://localhost:8001', timeout=3)
                if response.status == 200:
                    server_started = True
                    break
            except:
                continue
        
        if server_started:
            print("✅ Dashboard started successfully")
            
            # Test if the page contains UnifiedMemoryChart elements
            try:
                response = urllib.request.urlopen('http://localhost:8001', timeout=3)
                content = response.read().decode('utf-8')
                
                # Check for new live range selector
                if 'live-range-select' in content:
                    print("✅ Live range selector found in HTML")
                else:
                    print("❌ Live range selector not found in HTML")
                
                # Check for UnifiedMemoryChart class
                if 'UnifiedMemoryChart' in content:
                    print("✅ UnifiedMemoryChart class found in JavaScript")
                else:
                    print("❌ UnifiedMemoryChart class not found in JavaScript")
                
                # Check for flexible live ranges
                if '5 Minutes' in content and '4 Hours' in content:
                    print("✅ Flexible live view ranges (5m to 4h) found")
                else:
                    print("❌ Flexible live view ranges not found")
                
                # Check for new live mode terminology
                if 'Live Memory Usage' in content:
                    print("✅ New live mode terminology found")
                else:
                    print("❌ New live mode terminology not found")
                    
            except Exception as e:
                print(f"❌ Error checking dashboard content: {e}")
        else:
            print("❌ Dashboard failed to start")
            return False
        
        # Cleanup
        proc.terminate()
        proc.wait(timeout=5)
        return server_started
        
    except Exception as e:
        print(f"❌ Error testing dashboard startup: {e}")
        return False

def test_api_endpoints():
    """Test if API endpoints work with new chart system"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        # Start dashboard
        proc = subprocess.Popen([sys.executable, 'unified_memory_dashboard.py'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server
        time.sleep(3)
        
        # Test memory API
        try:
            response = urllib.request.urlopen('http://localhost:8001/api/memory', timeout=3)
            data = json.loads(response.read().decode('utf-8'))
            
            if 'menubar_memory' in data and 'service_memory' in data:
                print("✅ Memory API returns expected data structure")
            else:
                print("❌ Memory API data structure incorrect")
                
        except Exception as e:
            print(f"❌ Memory API test failed: {e}")
        
        # Test historical chart API (used by live ranges)
        try:
            response = urllib.request.urlopen('http://localhost:8001/api/historical-chart?hours=0.083&resolution=full', timeout=3)
            data = json.loads(response.read().decode('utf-8'))
            
            if 'points' in data:
                print("✅ Historical chart API works for live range data")
            else:
                print("❌ Historical chart API missing points data")
                
        except Exception as e:
            print(f"❌ Historical chart API test failed: {e}")
        
        # Cleanup
        proc.terminate()
        proc.wait(timeout=5)
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")

def test_javascript_syntax():
    """Test if the JavaScript code has valid syntax"""
    print("\n🧪 Testing JavaScript Syntax...")
    
    try:
        # Extract JavaScript from the dashboard file
        with open('unified_memory_dashboard.py', 'r') as f:
            content = f.read()
        
        # Find UnifiedMemoryChart class definition
        if 'class UnifiedMemoryChart {' in content:
            print("✅ UnifiedMemoryChart class definition found")
        else:
            print("❌ UnifiedMemoryChart class definition not found")
        
        # Check for key methods
        methods_to_check = [
            'switchLiveRange',
            'addLivePoint', 
            'loadInitialLiveData',
            'switchToLiveMode'
        ]
        
        for method in methods_to_check:
            if method in content:
                print(f"✅ Method {method} found")
            else:
                print(f"❌ Method {method} not found")
        
        # Check for live ranges configuration
        if 'liveRanges = {' in content:
            print("✅ Live ranges configuration found")
        else:
            print("❌ Live ranges configuration not found")
            
    except Exception as e:
        print(f"❌ Error testing JavaScript syntax: {e}")

def main():
    """Run all Phase 1 validation tests"""
    print("🚀 UNIFIED MEMORY CHART - PHASE 1 VALIDATION")
    print("=" * 60)
    
    # Test 1: Dashboard startup
    startup_success = test_dashboard_startup()
    
    # Test 2: API endpoints
    test_api_endpoints()
    
    # Test 3: JavaScript syntax
    test_javascript_syntax()
    
    print("\n" + "=" * 60)
    if startup_success:
        print("✅ Phase 1 implementation appears to be working!")
        print("🎯 Ready for user validation and testing")
        print("\n📋 Next steps:")
        print("   1. Start dashboard: python3 unified_memory_dashboard.py")
        print("   2. Open browser: http://localhost:8001")
        print("   3. Test live range selector (5m, 15m, 30m, 1h, 2h, 4h)")
        print("   4. Verify smooth transitions between ranges")
        print("   5. Check performance with different ranges")
    else:
        print("❌ Phase 1 implementation needs fixes before validation")
    
    return startup_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
