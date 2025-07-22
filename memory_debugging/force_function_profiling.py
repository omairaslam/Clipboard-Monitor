#!/usr/bin/env python3
"""
Force Function Profiling Test

This script will force function profiling to trigger by creating
memory-intensive operations and checking the results.
"""

import time
import subprocess
import os

def force_function_profiling():
    """Force function profiling by triggering memory-intensive operations."""
    
    print("🔍 Forcing Function-Level Memory Profiling")
    print("=" * 60)
    
    # Step 1: Check current log state
    print("1. Checking current memory debug log...")
    try:
        with open("../memory_leak_debug.log", "r") as f:
            lines = f.readlines()
        
        print(f"   Current log has {len(lines)} entries")
        
        # Look for any function profiling
        function_entries = [line for line in lines if "Function:" in line]
        print(f"   Found {len(function_entries)} function profiling entries")
        
        if function_entries:
            print("   Recent function profiling entries:")
            for entry in function_entries[-3:]:
                print(f"   {entry.strip()}")
        else:
            print("   No function profiling entries found")
            
    except Exception as e:
        print(f"   Error reading log: {e}")
    
    # Step 2: Force clipboard operations to trigger history updates
    print("\n2. Forcing clipboard operations...")
    try:
        # Create larger text content to potentially trigger memory changes
        large_texts = []
        for i in range(10):
            # Create progressively larger text content
            text = f"Memory profiling test {i+1} - " + "X" * (1000 * (i+1))
            large_texts.append(text)
            
            print(f"   Copying large text {i+1} ({len(text)} chars)...")
            subprocess.run(['pbcopy'], input=text.encode(), check=True)
            time.sleep(1)  # Wait for processing
            
    except Exception as e:
        print(f"   Error with clipboard operations: {e}")
    
    # Step 3: Wait and check for new function profiling entries
    print("\n3. Waiting for function profiling to trigger...")
    print("   Waiting 10 seconds for processing...")
    
    for i in range(10):
        print(f"   {10-i}s remaining...", end='\r')
        time.sleep(1)
    
    print("\n   Checking for new function profiling entries...")
    try:
        with open("../memory_leak_debug.log", "r") as f:
            new_lines = f.readlines()
        
        # Get only new entries
        new_entries = new_lines[len(lines):] if len(new_lines) > len(lines) else []
        print(f"   Found {len(new_entries)} new log entries")
        
        # Look for function profiling in new entries
        new_function_entries = [line for line in new_entries if "Function:" in line]
        
        if new_function_entries:
            print(f"   ✅ SUCCESS! Found {len(new_function_entries)} new function profiling entries:")
            for entry in new_function_entries:
                print(f"   📊 {entry.strip()}")
        else:
            print("   ❌ No new function profiling entries found")
            print("   Recent new entries:")
            for entry in new_entries[-5:]:
                print(f"   {entry.strip()}")
                
    except Exception as e:
        print(f"   Error checking new entries: {e}")
    
    # Step 4: Check if decorators are working at all
    print("\n4. Debugging decorator implementation...")
    
    # Check if we can find any evidence of decorator execution
    try:
        with open("../memory_leak_debug.log", "r") as f:
            all_lines = f.readlines()
        
        # Look for any mention of the profiled functions
        profiled_functions = ['update_status', 'update_memory_status', 'periodic_history_update', 'update_recent_history_menu']
        
        for func_name in profiled_functions:
            func_mentions = [line for line in all_lines if func_name in line]
            print(f"   Function '{func_name}': {len(func_mentions)} mentions in log")
            
            # Look specifically for function profiling format
            profiling_mentions = [line for line in func_mentions if "Function:" in line and "Delta:" in line]
            if profiling_mentions:
                print(f"     ✅ Has profiling entries: {len(profiling_mentions)}")
                for entry in profiling_mentions[-2:]:
                    print(f"     📊 {entry.strip()}")
            else:
                print(f"     ❌ No profiling entries found")
                
    except Exception as e:
        print(f"   Error debugging decorators: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("Function-level profiling should appear in memory_leak_debug.log with format:")
    print("   [timestamp] [level] RSS: XXMb ... Function: function_name Delta: +X.XXMb | Execution time: X.XXXs")
    print("\nTo see it in VS Code:")
    print("   1. Click '🔍 Memory Debug Log' button")
    print("   2. Look for entries containing 'Function:' and 'Delta:'")
    print("   3. If not visible, the decorators may need debugging")

if __name__ == "__main__":
    force_function_profiling()
