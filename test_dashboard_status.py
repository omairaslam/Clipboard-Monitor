#!/usr/bin/env python3
"""
Test script to verify dashboard status functionality in menu bar app
"""

import sys
import os
import time
import urllib.request
import json

# Add current directory to path to import menu bar app
sys.path.insert(0, os.path.dirname(__file__))

def test_dashboard_api():
    """Test the dashboard API endpoint directly"""
    print("Testing dashboard API endpoint...")
    try:
        with urllib.request.urlopen('http://localhost:8001/api/dashboard_status', timeout=2) as response:
            data = json.loads(response.read().decode())
        
        print(f"✅ API Response received")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Message: {data.get('status_message', 'Unknown')}")
        print(f"   Auto-start mode: {data.get('auto_start_mode', False)}")
        print(f"   Monitoring active: {data.get('monitoring_active', False)}")
        print(f"   Countdown: {data.get('countdown_seconds', 0):.0f}s")
        
        memory = data.get('memory', {})
        menubar = memory.get('menubar', {})
        service = memory.get('service', {})
        
        print(f"   Memory - Menu Bar: {menubar.get('current', 0):.1f}MB (Peak: {menubar.get('peak', 0):.1f}MB)")
        print(f"   Memory - Service: {service.get('current', 0):.1f}MB (Peak: {service.get('peak', 0):.1f}MB)")
        print(f"   CPU - Menu Bar: {menubar.get('cpu', 0):.1f}% (Peak: {menubar.get('peak_cpu', 0):.1f}%)")
        print(f"   CPU - Service: {service.get('cpu', 0):.1f}% (Peak: {service.get('peak_cpu', 0):.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_menu_bar_status_method():
    """Test the menu bar app's dashboard status method"""
    print("\nTesting menu bar app dashboard status method...")
    try:
        # Import the menu bar app class
        from menu_bar_app import ClipboardMonitorMenuBar
        
        # Create a minimal instance (without full initialization)
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        
        # Initialize just the items we need
        import rumps
        app.dashboard_status_item = rumps.MenuItem("Dashboard: Testing...")
        app.dashboard_memory_item = rumps.MenuItem("Memory: Testing...")
        app.dashboard_cpu_item = rumps.MenuItem("CPU: Testing...")
        app.dashboard_stats_item = rumps.MenuItem("Dashboard Stats: Testing...")
        app.memory_unified_dashboard_item = rumps.MenuItem("📊 Unified Dashboard")
        
        # Mock the log_error method
        app.log_error = lambda msg: print(f"LOG ERROR: {msg}")
        
        # Test the update method
        app.update_dashboard_status()
        
        print(f"✅ Dashboard status method executed")
        print(f"   Status item: {app.dashboard_status_item.title}")
        print(f"   Memory item: {app.dashboard_memory_item.title}")
        print(f"   CPU item: {app.dashboard_cpu_item.title}")
        print(f"   Dashboard stats item: {app.dashboard_stats_item.title}")
        print(f"   Dashboard menu item: {app.memory_unified_dashboard_item.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Menu bar status method test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Dashboard Status Functionality")
    print("=" * 50)
    
    # Test 1: API endpoint
    api_success = test_dashboard_api()
    
    # Test 2: Menu bar method
    method_success = test_menu_bar_status_method()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   API Endpoint: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   Menu Bar Method: {'✅ PASS' if method_success else '❌ FAIL'}")
    
    if api_success and method_success:
        print("\n🎉 All tests passed! Dashboard status functionality is working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return api_success and method_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
