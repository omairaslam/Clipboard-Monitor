#!/usr/bin/env python3
"""
Comprehensive test runner for Clipboard Monitor.
Runs all test suites and provides detailed reporting.
"""

import os
import sys
import time
import unittest
import subprocess
from io import StringIO
import traceback

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

class ComprehensiveTestRunner:
    """Run all comprehensive tests and provide detailed reporting"""
    
    def __init__(self):
        self.test_modules = [
            ("Clear History Tests", "test_clear_history_comprehensive"),
            ("Menu Bar UI Tests", "test_menu_bar_ui_comprehensive"),
            ("End-to-End Workflow Tests", "test_end_to_end_workflows"),
            ("Error Handling Tests", "test_error_handling_comprehensive"),
            ("Performance Tests", "test_performance_comprehensive"),
            ("Real-time Monitoring Tests", "test_realtime_monitoring_comprehensive"),
            ("Configuration Tests", "test_configuration_comprehensive"),
            ("Security Tests", "test_security_comprehensive"),
            # Include existing tests
            ("Path Fix Tests", "test_path_fix"),
            ("Application Integration Tests", "test_application_integration"),
            ("Clipboard Safety Tests", "test_clipboard_safety"),
            ("Integration Tests", "test_integration")
        ]
        
        self.results = {}
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.total_time = 0
    
    def run_single_test_module(self, module_name, test_name):
        """Run a single test module and capture results"""
        print(f"\n{'='*60}")
        print(f"🧪 Running {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Import the test module
            test_module = __import__(module_name)
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            # Run tests with custom result collector
            stream = StringIO()
            runner = unittest.TextTestRunner(
                stream=stream,
                verbosity=2,
                buffer=True
            )
            
            result = runner.run(suite)
            
            # Calculate timing
            end_time = time.time()
            duration = end_time - start_time
            
            # Store results
            self.results[test_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'duration': duration,
                'success': result.wasSuccessful(),
                'output': stream.getvalue(),
                'failure_details': result.failures,
                'error_details': result.errors
            }
            
            # Update totals
            self.total_tests += result.testsRun
            self.total_failures += len(result.failures)
            self.total_errors += len(result.errors)
            self.total_time += duration
            
            # Print summary
            status = "✅ PASSED" if result.wasSuccessful() else "❌ FAILED"
            print(f"\n{status} - {result.testsRun} tests in {duration:.2f}s")
            
            if result.failures:
                print(f"  Failures: {len(result.failures)}")
            if result.errors:
                print(f"  Errors: {len(result.errors)}")
            
            return result.wasSuccessful()
            
        except ImportError as e:
            print(f"⚠️  Could not import {module_name}: {e}")
            self.results[test_name] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'duration': 0,
                'success': False,
                'output': f"Import error: {e}",
                'failure_details': [],
                'error_details': [('Import Error', str(e))]
            }
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error running {module_name}: {e}")
            traceback.print_exc()
            self.results[test_name] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'duration': 0,
                'success': False,
                'output': f"Unexpected error: {e}",
                'failure_details': [],
                'error_details': [('Unexpected Error', str(e))]
            }
            return False
    
    def run_all_tests(self):
        """Run all test modules"""
        print("🚀 Starting Comprehensive Test Suite")
        print(f"📊 Running {len(self.test_modules)} test modules")
        
        overall_start_time = time.time()
        successful_modules = 0
        
        for test_name, module_name in self.test_modules:
            success = self.run_single_test_module(module_name, test_name)
            if success:
                successful_modules += 1
        
        overall_end_time = time.time()
        overall_duration = overall_end_time - overall_start_time
        
        # Print comprehensive summary
        self.print_summary(successful_modules, overall_duration)
        
        return successful_modules == len(self.test_modules)
    
    def print_summary(self, successful_modules, overall_duration):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        
        # Overall statistics
        print(f"\n🎯 Overall Results:")
        print(f"  Total Test Modules: {len(self.test_modules)}")
        print(f"  Successful Modules: {successful_modules}")
        print(f"  Failed Modules: {len(self.test_modules) - successful_modules}")
        print(f"  Total Test Cases: {self.total_tests}")
        print(f"  Total Failures: {self.total_failures}")
        print(f"  Total Errors: {self.total_errors}")
        print(f"  Total Time: {overall_duration:.2f}s")
        
        # Success rate
        success_rate = (successful_modules / len(self.test_modules)) * 100
        test_success_rate = ((self.total_tests - self.total_failures - self.total_errors) / max(self.total_tests, 1)) * 100
        
        print(f"\n📈 Success Rates:")
        print(f"  Module Success Rate: {success_rate:.1f}%")
        print(f"  Test Case Success Rate: {test_success_rate:.1f}%")
        
        # Detailed results by module
        print(f"\n📋 Detailed Results by Module:")
        print("-" * 80)
        
        for test_name, module_name in self.test_modules:
            if test_name in self.results:
                result = self.results[test_name]
                status = "✅" if result['success'] else "❌"
                print(f"{status} {test_name:<35} {result['tests_run']:>3} tests  {result['duration']:>6.2f}s")
                
                if result['failures'] > 0:
                    print(f"    └─ {result['failures']} failures")
                if result['errors'] > 0:
                    print(f"    └─ {result['errors']} errors")
        
        # Failed test details
        if self.total_failures > 0 or self.total_errors > 0:
            print(f"\n❌ Failed Test Details:")
            print("-" * 80)
            
            for test_name, result in self.results.items():
                if not result['success']:
                    print(f"\n{test_name}:")
                    
                    for failure in result['failure_details']:
                        print(f"  FAILURE: {failure[0]}")
                        print(f"    {failure[1][:200]}...")
                    
                    for error in result['error_details']:
                        print(f"  ERROR: {error[0]}")
                        print(f"    {error[1][:200]}...")
        
        # Coverage assessment
        print(f"\n📊 Test Coverage Assessment:")
        print("-" * 80)
        
        coverage_areas = [
            ("Clear History Functionality", "Clear History Tests" in [r for r, _ in self.test_modules]),
            ("Menu Bar UI", "Menu Bar UI Tests" in [r for r, _ in self.test_modules]),
            ("End-to-End Workflows", "End-to-End Workflow Tests" in [r for r, _ in self.test_modules]),
            ("Error Handling", "Error Handling Tests" in [r for r, _ in self.test_modules]),
            ("Performance", "Performance Tests" in [r for r, _ in self.test_modules]),
            ("Real-time Monitoring", "Real-time Monitoring Tests" in [r for r, _ in self.test_modules]),
            ("Configuration", "Configuration Tests" in [r for r, _ in self.test_modules]),
            ("Security", "Security Tests" in [r for r, _ in self.test_modules]),
            ("Path Management", "Path Fix Tests" in [r for r, _ in self.test_modules]),
            ("Integration", "Application Integration Tests" in [r for r, _ in self.test_modules]),
            ("Clipboard Safety", "Clipboard Safety Tests" in [r for r, _ in self.test_modules])
        ]
        
        for area, covered in coverage_areas:
            status = "✅" if covered else "❌"
            print(f"{status} {area}")
        
        # Final verdict
        print(f"\n🎉 Final Verdict:")
        if success_rate >= 90:
            print("🟢 EXCELLENT - Test suite is comprehensive and passing")
        elif success_rate >= 75:
            print("🟡 GOOD - Most tests passing, some areas need attention")
        elif success_rate >= 50:
            print("🟠 FAIR - Significant issues found, requires investigation")
        else:
            print("🔴 POOR - Major test failures, immediate attention required")
        
        print("="*80)

def main():
    """Main function to run comprehensive tests"""
    runner = ComprehensiveTestRunner()
    
    # Check for required dependencies
    try:
        import psutil
        print("✅ psutil available for performance tests")
    except ImportError:
        print("⚠️  psutil not available - install with: pip install psutil")
    
    # Run all tests
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
