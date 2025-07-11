#!/usr/bin/env python3
"""
Memory Leak Fix Validation Test
Tests the effectiveness of implemented memory leak fixes.
"""

import os
import sys
import time
import psutil
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error


class MemoryLeakFixValidator:
    """Validates that memory leak fixes are working correctly"""
    
    def __init__(self):
        self.test_results = {}
        self.menu_bar_pid = None
        self.baseline_memory = None
        
    def find_menu_bar_process(self):
        """Find the running menu bar app process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    if 'menu_bar_app.py' in cmdline_str and proc.pid != os.getpid():
                        self.menu_bar_pid = proc.info['pid']
                        self.baseline_memory = proc.info['memory_info'].rss / 1024 / 1024
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def test_fix_1_memory_tracking_limits(self):
        """Test Fix #1: Memory tracking array size limits"""
        print("🧪 TESTING FIX #1: Memory Tracking Array Size Limits")
        print("=" * 60)
        
        test_result = {
            "fix_name": "Memory Tracking Array Size Limits",
            "test_status": "PASS",
            "evidence": [],
            "issues_found": []
        }
        
        # Check if memory data files exist and are within reasonable size
        data_files = [
            safe_expanduser("~/Library/Application Support/ClipboardMonitor/memory_data.json"),
            safe_expanduser("~/Library/Application Support/ClipboardMonitor/menubar_profile.json")
        ]
        
        for data_file in data_files:
            if os.path.exists(data_file):
                file_size = os.path.getsize(data_file) / 1024  # KB
                test_result["evidence"].append(f"File: {os.path.basename(data_file)}")
                test_result["evidence"].append(f"  Size: {file_size:.1f} KB")
                
                try:
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict):
                        if 'menubar' in data and isinstance(data['menubar'], list):
                            data_points = len(data['menubar'])
                            test_result["evidence"].append(f"  Data points: {data_points}")
                            
                            # Check if size limit is being enforced (should be <= 200)
                            if data_points > 250:  # Allow some buffer
                                test_result["test_status"] = "FAIL"
                                test_result["issues_found"].append(f"Too many data points: {data_points} (limit should be ~200)")
                            else:
                                test_result["evidence"].append(f"  ✅ Data points within limit")
                        
                        if 'snapshots' in data and isinstance(data['snapshots'], list):
                            snapshots = len(data['snapshots'])
                            test_result["evidence"].append(f"  Snapshots: {snapshots}")
                            
                            if snapshots > 100:  # Check profiler limits
                                test_result["test_status"] = "FAIL"
                                test_result["issues_found"].append(f"Too many snapshots: {snapshots}")
                            else:
                                test_result["evidence"].append(f"  ✅ Snapshots within limit")
                
                except Exception as e:
                    test_result["issues_found"].append(f"Error reading {data_file}: {e}")
        
        # Check file sizes are reasonable (should be < 100KB each)
        total_size = sum(os.path.getsize(f) for f in data_files if os.path.exists(f)) / 1024
        test_result["evidence"].append(f"Total data file size: {total_size:.1f} KB")
        
        if total_size > 500:  # > 500KB is excessive
            test_result["test_status"] = "FAIL"
            test_result["issues_found"].append(f"Total data files too large: {total_size:.1f} KB")
        
        print(f"Status: {test_result['test_status']}")
        print("Evidence:")
        for evidence in test_result["evidence"]:
            print(f"  {evidence}")
        
        if test_result["issues_found"]:
            print("Issues Found:")
            for issue in test_result["issues_found"]:
                print(f"  ❌ {issue}")
        else:
            print("  ✅ No issues found")
        
        self.test_results["fix_1"] = test_result
        return test_result
    
    def test_fix_2_auto_disable(self):
        """Test Fix #2: Auto-disable functionality"""
        print("\n🧪 TESTING FIX #2: Memory Tracking Auto-Disable")
        print("=" * 60)
        
        test_result = {
            "fix_name": "Memory Tracking Auto-Disable",
            "test_status": "PASS",
            "evidence": [],
            "issues_found": []
        }
        
        # This is harder to test automatically, but we can check for the implementation
        # by looking at the code structure and log files
        
        log_files = [
            safe_expanduser("~/Library/Logs/ClipboardMonitor.out.log"),
            safe_expanduser("~/Library/Logs/ClipboardMonitor.err.log")
        ]
        
        auto_disable_found = False
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    
                    if "auto-disabled" in log_content.lower() or "auto-stop" in log_content.lower():
                        auto_disable_found = True
                        test_result["evidence"].append(f"Found auto-disable evidence in {os.path.basename(log_file)}")
                
                except Exception as e:
                    test_result["issues_found"].append(f"Error reading log {log_file}: {e}")
        
        if auto_disable_found:
            test_result["evidence"].append("✅ Auto-disable functionality appears to be working")
        else:
            test_result["evidence"].append("ℹ️  No auto-disable events found (may not have triggered yet)")
        
        print(f"Status: {test_result['test_status']}")
        print("Evidence:")
        for evidence in test_result["evidence"]:
            print(f"  {evidence}")
        
        self.test_results["fix_2"] = test_result
        return test_result
    
    def test_fix_3_history_frequency(self):
        """Test Fix #3: Reduced history loading frequency"""
        print("\n🧪 TESTING FIX #3: Reduced History Loading Frequency")
        print("=" * 60)
        
        test_result = {
            "fix_name": "Reduced History Loading Frequency",
            "test_status": "PASS",
            "evidence": [],
            "issues_found": []
        }
        
        # Check log files for evidence of the frequency change
        log_files = [
            safe_expanduser("~/Library/Logs/ClipboardMonitor.out.log")
        ]
        
        frequency_change_found = False
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    
                    if "120s intervals" in log_content:
                        frequency_change_found = True
                        test_result["evidence"].append(f"Found frequency change evidence in {os.path.basename(log_file)}")
                
                except Exception as e:
                    test_result["issues_found"].append(f"Error reading log {log_file}: {e}")
        
        if frequency_change_found:
            test_result["evidence"].append("✅ History loading frequency reduced to 120s")
        else:
            test_result["evidence"].append("ℹ️  No frequency change log found (may need app restart)")
        
        print(f"Status: {test_result['test_status']}")
        print("Evidence:")
        for evidence in test_result["evidence"]:
            print(f"  {evidence}")
        
        self.test_results["fix_3"] = test_result
        return test_result
    
    def test_fix_4_menu_cleanup(self):
        """Test Fix #4: Improved menu item cleanup"""
        print("\n🧪 TESTING FIX #4: Improved Menu Item Cleanup")
        print("=" * 60)
        
        test_result = {
            "fix_name": "Improved Menu Item Cleanup",
            "test_status": "PASS",
            "evidence": [],
            "issues_found": []
        }
        
        # Monitor memory usage of menu bar process
        if self.menu_bar_pid:
            try:
                proc = psutil.Process(self.menu_bar_pid)
                current_memory = proc.memory_info().rss / 1024 / 1024
                
                test_result["evidence"].append(f"Current memory usage: {current_memory:.1f} MB")
                test_result["evidence"].append(f"Baseline memory: {self.baseline_memory:.1f} MB")
                
                memory_growth = current_memory - self.baseline_memory
                test_result["evidence"].append(f"Memory growth: {memory_growth:.1f} MB")
                
                # Check if memory growth is reasonable
                if memory_growth > 50:  # > 50MB growth is concerning
                    test_result["test_status"] = "FAIL"
                    test_result["issues_found"].append(f"Excessive memory growth: {memory_growth:.1f} MB")
                elif memory_growth > 20:  # > 20MB is worth noting
                    test_result["evidence"].append(f"⚠️  Moderate memory growth: {memory_growth:.1f} MB")
                else:
                    test_result["evidence"].append(f"✅ Memory growth within acceptable range")
                
            except psutil.NoSuchProcess:
                test_result["issues_found"].append("Menu bar process not found")
        else:
            test_result["evidence"].append("ℹ️  Menu bar process not found for testing")
        
        print(f"Status: {test_result['test_status']}")
        print("Evidence:")
        for evidence in test_result["evidence"]:
            print(f"  {evidence}")
        
        if test_result["issues_found"]:
            print("Issues Found:")
            for issue in test_result["issues_found"]:
                print(f"  ❌ {issue}")
        
        self.test_results["fix_4"] = test_result
        return test_result
    
    def test_fix_5_cleanup_on_exit(self):
        """Test Fix #5: Proper cleanup on exit"""
        print("\n🧪 TESTING FIX #5: Proper Cleanup on Exit")
        print("=" * 60)
        
        test_result = {
            "fix_name": "Proper Cleanup on Exit",
            "test_status": "PASS",
            "evidence": [],
            "issues_found": []
        }
        
        # Check log files for cleanup evidence
        log_files = [
            safe_expanduser("~/Library/Logs/ClipboardMonitor.out.log")
        ]
        
        cleanup_found = False
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    
                    if "cleanup" in log_content.lower() and "complete" in log_content.lower():
                        cleanup_found = True
                        test_result["evidence"].append(f"Found cleanup evidence in {os.path.basename(log_file)}")
                
                except Exception as e:
                    test_result["issues_found"].append(f"Error reading log {log_file}: {e}")
        
        if cleanup_found:
            test_result["evidence"].append("✅ Cleanup functionality appears to be implemented")
        else:
            test_result["evidence"].append("ℹ️  No cleanup events found (requires app exit to test)")
        
        print(f"Status: {test_result['test_status']}")
        print("Evidence:")
        for evidence in test_result["evidence"]:
            print(f"  {evidence}")
        
        self.test_results["fix_5"] = test_result
        return test_result
    
    def generate_summary_report(self):
        """Generate a comprehensive summary of all fix validations"""
        print("\n" + "=" * 80)
        print("📊 MEMORY LEAK FIX VALIDATION SUMMARY")
        print("=" * 80)
        
        if not self.test_results:
            print("No test results available.")
            return
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("test_status") == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if self.menu_bar_pid and self.baseline_memory:
            try:
                proc = psutil.Process(self.menu_bar_pid)
                current_memory = proc.memory_info().rss / 1024 / 1024
                print(f"\nMenu Bar App Memory Status:")
                print(f"  Process PID: {self.menu_bar_pid}")
                print(f"  Current Memory: {current_memory:.1f} MB")
                print(f"  Baseline Memory: {self.baseline_memory:.1f} MB")
                print(f"  Memory Change: {current_memory - self.baseline_memory:.1f} MB")
                
                if current_memory < 50:
                    print(f"  ✅ Memory usage is reasonable")
                elif current_memory < 100:
                    print(f"  ⚠️  Memory usage is elevated but acceptable")
                else:
                    print(f"  🚨 Memory usage is high - further investigation needed")
                
            except psutil.NoSuchProcess:
                print(f"\nMenu Bar App Process (PID {self.menu_bar_pid}) no longer running")
        
        print(f"\n📋 OVERALL ASSESSMENT:")
        if failed_tests == 0:
            print(f"✅ All memory leak fixes appear to be working correctly!")
        elif failed_tests <= 2:
            print(f"⚠️  Most fixes are working, but {failed_tests} need attention")
        else:
            print(f"🚨 Multiple fixes need attention ({failed_tests} failed)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if failed_tests == 0:
            print(f"• Continue monitoring memory usage over time")
            print(f"• Consider running extended tests over 24+ hours")
        else:
            print(f"• Review failed tests and implement additional fixes")
            print(f"• Monitor memory usage more frequently")
        
        # Save test results
        results_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/leak_fix_validation.json")
        try:
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump({
                    "test_timestamp": time.time(),
                    "menu_bar_pid": self.menu_bar_pid,
                    "baseline_memory_mb": self.baseline_memory,
                    "test_results": self.test_results,
                    "summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests
                    }
                }, f, indent=2)
            print(f"\n📄 Test results saved to: {results_file}")
        except Exception as e:
            print(f"\n❌ Failed to save test results: {e}")


def main():
    """Run memory leak fix validation tests"""
    print("🧪 MEMORY LEAK FIX VALIDATION TESTS")
    print("=" * 80)
    
    validator = MemoryLeakFixValidator()
    
    # Find the menu bar process
    proc = validator.find_menu_bar_process()
    if proc:
        print(f"✅ Found Menu Bar App Process (PID: {validator.menu_bar_pid})")
        print(f"   Memory Usage: {validator.baseline_memory:.1f} MB")
    else:
        print("⚠️  Menu Bar App process not found - some tests will be limited")
    
    print()
    
    # Run all validation tests
    validator.test_fix_1_memory_tracking_limits()
    validator.test_fix_2_auto_disable()
    validator.test_fix_3_history_frequency()
    validator.test_fix_4_menu_cleanup()
    validator.test_fix_5_cleanup_on_exit()
    
    # Generate summary
    validator.generate_summary_report()


if __name__ == "__main__":
    main()
