#!/usr/bin/env python3
"""
Test that the developer mode toggle works safely without crashing
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_safe_toggle():
    """Test that toggling developer mode doesn't crash the app"""
    print("🔧 Testing Safe Developer Mode Toggle")
    print("=" * 45)
    
    try:
        from utils import set_config_value, get_config
        
        print("📋 Step 1: Get current developer mode setting")
        current_value = get_config('advanced', 'developer_mode', False)
        print(f"   Current value: {current_value}")
        
        print("\n📋 Step 2: Toggle to opposite value")
        new_value = not current_value
        success = set_config_value('advanced', 'developer_mode', new_value)
        print(f"   Set to {new_value}: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if success:
            print("\n📋 Step 3: Wait for menu rebuild (5 seconds)")
            time.sleep(5)
            
            print("\n📋 Step 4: Check if menu bar app is still running")
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'menu_bar_app.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                pid = result.stdout.strip()
                print(f"   ✅ Menu bar app still running (PID: {pid})")
                
                print("\n📋 Step 5: Toggle back to original value")
                reset_success = set_config_value('advanced', 'developer_mode', current_value)
                print(f"   Reset to {current_value}: {'✅ SUCCESS' if reset_success else '❌ FAILED'}")
                
                if reset_success:
                    print("\n📋 Step 6: Wait for second menu rebuild (5 seconds)")
                    time.sleep(5)
                    
                    # Check if still running after second toggle
                    result2 = subprocess.run(['pgrep', '-f', 'menu_bar_app.py'], 
                                           capture_output=True, text=True)
                    
                    if result2.returncode == 0:
                        pid2 = result2.stdout.strip()
                        print(f"   ✅ Menu bar app still running after second toggle (PID: {pid2})")
                        return True
                    else:
                        print(f"   ❌ Menu bar app crashed on second toggle")
                        return False
                
                return reset_success
            else:
                print(f"   ❌ Menu bar app crashed on first toggle")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Safe toggle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_error_log():
    """Check for any new errors in the log"""
    print("\n📋 Checking Error Log")
    print("=" * 25)
    
    try:
        log_path = Path.home() / "Library" / "Logs" / "ClipboardMonitorMenuBar.err.log"
        
        if log_path.exists():
            # Get the last 10 lines
            import subprocess
            result = subprocess.run(['tail', '-n', '10', str(log_path)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                recent_errors = [line for line in lines if 'Traceback' in line or 'Error' in line]
                
                if recent_errors:
                    print(f"   ⚠️  Found {len(recent_errors)} recent error(s)")
                    for error in recent_errors[-3:]:  # Show last 3 errors
                        print(f"      {error}")
                    return False
                else:
                    print(f"   ✅ No recent errors found")
                    return True
            else:
                print(f"   ❌ Could not read error log")
                return False
        else:
            print(f"   ✅ No error log file (no errors)")
            return True
            
    except Exception as e:
        print(f"❌ Error log check failed: {e}")
        return False

def main():
    """Run the safe toggle test"""
    print("🧪 Testing Safe Developer Mode Toggle")
    print("=" * 50)
    
    # Test 1: Safe toggle
    toggle_success = test_safe_toggle()
    
    # Test 2: Error log check
    log_success = check_error_log()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Safe Toggle: {'✅ PASS' if toggle_success else '❌ FAIL'}")
    print(f"   Error Log: {'✅ CLEAN' if log_success else '❌ ERRORS'}")
    
    if toggle_success and log_success:
        print("\n🎉 Safe toggle test passed!")
        print("✅ Developer mode toggle works without crashing")
        print("✅ No errors in the log")
        print("✅ Menu rebuilds successfully")
        
        print("\n🚀 You can now safely toggle Developer Mode!")
        print("   Go to: Settings → Advanced Settings → 🔧 Developer Mode")
    else:
        print("\n⚠️  Issues detected. Check the output above.")
        if not toggle_success:
            print("   The toggle may still cause crashes.")
        if not log_success:
            print("   Check the error log for details.")
    
    return toggle_success and log_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
