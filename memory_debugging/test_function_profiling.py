#!/usr/bin/env python3
"""
Test Function-Level Memory Profiling

This script tests the function-level memory profiling by triggering
the profiled functions in the menu bar app.
"""

import time
import subprocess

def trigger_function_profiling():
    """Trigger various functions to see memory profiling in action."""
    
    print("🔍 Testing Function-Level Memory Profiling")
    print("=" * 50)
    
    # Test 1: Trigger clipboard history update (should show profiling)
    print("1. Triggering clipboard history operations...")
    try:
        # Copy some text to clipboard to trigger history updates
        test_texts = [
            "Test clipboard content 1 - memory profiling test",
            "Test clipboard content 2 - function profiling test", 
            "Test clipboard content 3 - enhanced debugging test"
        ]
        
        for i, text in enumerate(test_texts):
            print(f"   Copying text {i+1}...")
            subprocess.run(['pbcopy'], input=text.encode(), check=True)
            time.sleep(2)  # Wait for history update
            
    except Exception as e:
        print(f"   Error triggering clipboard operations: {e}")
    
    # Test 2: Check if we can see the profiling in the log
    print("\n2. Checking memory debug log for function profiling...")
    try:
        with open("../memory_leak_debug.log", "r") as f:
            lines = f.readlines()
            
        # Look for function profiling entries
        function_entries = [line for line in lines if "Function:" in line]
        
        if function_entries:
            print(f"   ✅ Found {len(function_entries)} function profiling entries!")
            print("   Recent function profiling:")
            for entry in function_entries[-5:]:
                print(f"   {entry.strip()}")
        else:
            print("   ❌ No function profiling entries found yet")
            print("   Recent log entries:")
            for entry in lines[-10:]:
                print(f"   {entry.strip()}")
                
    except Exception as e:
        print(f"   Error reading log file: {e}")
    
    # Test 3: Try to trigger memory status update
    print("\n3. Waiting for timer-based functions to execute...")
    print("   (update_status runs every 5s, update_memory_status every 5s)")
    print("   Waiting 15 seconds to capture function calls...")
    
    start_time = time.time()
    while time.time() - start_time < 15:
        print(f"   Waiting... {15 - int(time.time() - start_time)}s remaining", end='\r')
        time.sleep(1)
    
    print("\n   Checking log again...")
    try:
        with open("../memory_leak_debug.log", "r") as f:
            lines = f.readlines()
            
        # Look for recent function profiling entries
        recent_lines = lines[-20:]
        function_entries = [line for line in recent_lines if "Function:" in line]
        
        if function_entries:
            print(f"   ✅ Found {len(function_entries)} recent function profiling entries!")
            for entry in function_entries:
                print(f"   {entry.strip()}")
        else:
            print("   ❌ Still no function profiling entries")
            print("   Recent enhanced log entries:")
            enhanced_entries = [line for line in recent_lines if "RSS:" in line]
            for entry in enhanced_entries[-5:]:
                print(f"   {entry.strip()}")
                
    except Exception as e:
        print(f"   Error reading log file: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 How to See Function-Level Profiling:")
    print("1. Click '🔍 Memory Debug Log' button in VS Code")
    print("2. Look for entries containing 'Function:' and 'Delta:'")
    print("3. Function profiling triggers when:")
    print("   - Memory delta > 0.1MB")
    print("   - Execution time > 0.1s")
    print("4. Profiled functions:")
    print("   - update_status()")
    print("   - update_memory_status()")
    print("   - periodic_history_update()")
    print("   - update_recent_history_menu()")

if __name__ == "__main__":
    trigger_function_profiling()
