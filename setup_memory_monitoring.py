#!/usr/bin/env python3
"""
Memory Monitoring Setup
Complete setup and initialization of all memory monitoring and leak detection tools.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error


class MemoryMonitoringSetup:
    """Setup and configuration for memory monitoring system"""
    
    def __init__(self):
        self.setup_complete = False
        self.components_status = {}
        
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        required_modules = [
            'psutil', 'tracemalloc', 'gc', 'threading', 'json', 'time', 'datetime'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                print(f"   ✅ {module}")
            except ImportError:
                missing_modules.append(module)
                print(f"   ❌ {module}")
        
        if missing_modules:
            print(f"\n⚠️  Missing dependencies: {', '.join(missing_modules)}")
            print("Install with: pip install psutil")
            return False
        
        print("✅ All dependencies available")
        return True
    
    def setup_data_directories(self):
        """Create necessary data directories"""
        print("\n📁 Setting up data directories...")
        
        directories = [
            safe_expanduser("~/Library/Application Support/ClipboardMonitor"),
            safe_expanduser("~/Library/Logs"),
            safe_expanduser("~/Library/LaunchAgents")
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"   ✅ {directory}")
            except Exception as e:
                print(f"   ❌ {directory}: {e}")
                return False
        
        print("✅ Data directories ready")
        return True
    
    def test_monitoring_components(self):
        """Test all monitoring components"""
        print("\n🧪 Testing monitoring components...")
        
        # Test advanced profiler
        try:
            from advanced_memory_profiler import get_advanced_profiler
            profiler = get_advanced_profiler()
            snapshot = profiler.take_detailed_snapshot()
            if snapshot and "process_info" in snapshot:
                print("   ✅ Advanced profiler")
                self.components_status["advanced_profiler"] = "OK"
            else:
                print("   ❌ Advanced profiler: No snapshot data")
                self.components_status["advanced_profiler"] = "FAIL"
        except Exception as e:
            print(f"   ❌ Advanced profiler: {e}")
            self.components_status["advanced_profiler"] = "FAIL"
        
        # Test long-term monitor
        try:
            from long_term_memory_monitor import LongTermMemoryMonitor
            monitor = LongTermMemoryMonitor()
            data_point = monitor.collect_monitoring_data()
            if data_point and "timestamp" in data_point:
                print("   ✅ Long-term monitor")
                self.components_status["long_term_monitor"] = "OK"
            else:
                print("   ❌ Long-term monitor: No data collected")
                self.components_status["long_term_monitor"] = "FAIL"
        except Exception as e:
            print(f"   ❌ Long-term monitor: {e}")
            self.components_status["long_term_monitor"] = "FAIL"
        
        # Test validator
        try:
            from validate_leak_fixes import MemoryLeakFixValidator
            validator = MemoryLeakFixValidator()
            data_point = validator.collect_validation_data()
            if data_point and "timestamp" in data_point:
                print("   ✅ Fix validator")
                self.components_status["validator"] = "OK"
            else:
                print("   ❌ Fix validator: No data collected")
                self.components_status["validator"] = "FAIL"
        except Exception as e:
            print(f"   ❌ Fix validator: {e}")
            self.components_status["validator"] = "FAIL"
        
        # Test dashboard
        try:
            from memory_monitoring_dashboard import MemoryMonitoringDashboard
            dashboard = MemoryMonitoringDashboard()
            data = dashboard.get_dashboard_data()
            if data and "timestamp" in data:
                print("   ✅ Monitoring dashboard")
                self.components_status["dashboard"] = "OK"
            else:
                print("   ❌ Monitoring dashboard: No data")
                self.components_status["dashboard"] = "FAIL"
        except Exception as e:
            print(f"   ❌ Monitoring dashboard: {e}")
            self.components_status["dashboard"] = "FAIL"
        
        working_components = sum(1 for status in self.components_status.values() if status == "OK")
        total_components = len(self.components_status)
        
        print(f"\n📊 Component Status: {working_components}/{total_components} working")
        
        return working_components == total_components
    
    def create_launch_scripts(self):
        """Create convenient launch scripts"""
        print("\n📝 Creating launch scripts...")
        
        scripts = {
            "start_monitoring.sh": """#!/bin/bash
# Start comprehensive memory monitoring
echo "🚀 Starting Memory Monitoring System..."
cd "$(dirname "$0")"

# Start long-term monitoring in background
python3 long_term_memory_monitor.py &
LONGTERM_PID=$!
echo "Long-term monitor started (PID: $LONGTERM_PID)"

# Start dashboard
python3 memory_monitoring_dashboard.py &
DASHBOARD_PID=$!
echo "Dashboard started (PID: $DASHBOARD_PID)"

echo "✅ Memory monitoring system started"
echo "   Dashboard: http://localhost:8002"
echo "   Long-term monitoring: Active"
echo ""
echo "To stop monitoring:"
echo "   kill $LONGTERM_PID $DASHBOARD_PID"
echo "   or run: ./stop_monitoring.sh"

# Save PIDs for stop script
echo "$LONGTERM_PID $DASHBOARD_PID" > .monitoring_pids
""",
            
            "stop_monitoring.sh": """#!/bin/bash
# Stop memory monitoring
echo "🛑 Stopping Memory Monitoring System..."
cd "$(dirname "$0")"

if [ -f .monitoring_pids ]; then
    PIDS=$(cat .monitoring_pids)
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping process $PID..."
            kill $PID
        fi
    done
    rm .monitoring_pids
    echo "✅ Memory monitoring stopped"
else
    echo "⚠️  No PID file found - manually kill processes if needed"
fi
""",
            
            "validate_fixes.sh": """#!/bin/bash
# Run memory leak fix validation
echo "🧪 Starting Memory Leak Fix Validation..."
cd "$(dirname "$0")"

python3 validate_leak_fixes.py --duration 60 --interval 60

echo "✅ Validation complete"
echo "View results with: python3 validate_leak_fixes.py --report"
""",
            
            "quick_status.sh": """#!/bin/bash
# Quick status check
echo "📊 Memory Monitoring Quick Status"
echo "================================="
cd "$(dirname "$0")"

echo "Long-term Monitor:"
python3 long_term_memory_monitor.py --status

echo ""
echo "Fix Validation:"
python3 validate_leak_fixes.py --report 2>/dev/null || echo "No validation data available"

echo ""
echo "Advanced Profiler:"
python3 -c "
from advanced_memory_profiler import get_advanced_profiler
profiler = get_advanced_profiler()
snapshot = profiler.take_detailed_snapshot()
print(f'Memory: {snapshot[\"process_info\"][\"memory_rss_mb\"]:.1f} MB')
print(f'Objects: {snapshot[\"object_analysis\"][\"total_objects\"]:,}')
print(f'GC Effectiveness: {snapshot[\"gc_analysis\"][\"gc_effectiveness\"]:.1%}')
"
"""
        }
        
        for script_name, script_content in scripts.items():
            script_path = Path(script_name)
            try:
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                # Make executable
                os.chmod(script_path, 0o755)
                print(f"   ✅ {script_name}")
                
            except Exception as e:
                print(f"   ❌ {script_name}: {e}")
                return False
        
        print("✅ Launch scripts created")
        return True
    
    def create_configuration_file(self):
        """Create configuration file with monitoring settings"""
        print("\n⚙️  Creating configuration file...")
        
        config = {
            "memory_monitoring": {
                "long_term_check_interval_seconds": 300,
                "validation_test_duration_minutes": 60,
                "dashboard_port": 8002,
                "alert_thresholds": {
                    "memory_mb": 100,
                    "growth_rate_mb_per_hour": 5,
                    "consecutive_growth_periods": 6,
                    "object_count": 50000,
                    "gc_effectiveness": 0.05
                },
                "data_retention": {
                    "long_term_data_points": 288,
                    "advanced_profiler_snapshots": 100,
                    "validation_data_points": 1000
                }
            },
            "leak_fixes": {
                "memory_tracking_max_points": 200,
                "memory_tracking_auto_disable_minutes": 60,
                "history_update_interval_seconds": 120,
                "menu_cleanup_enabled": True,
                "exit_cleanup_enabled": True
            },
            "setup_info": {
                "setup_date": time.time(),
                "components_status": self.components_status,
                "version": "1.0.0"
            }
        }
        
        config_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/monitoring_config.json")
        
        try:
            import json
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"   ✅ Configuration saved to: {config_file}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to create configuration: {e}")
            return False
    
    def run_setup(self):
        """Run complete setup process"""
        print("🚀 MEMORY MONITORING SYSTEM SETUP")
        print("=" * 50)
        
        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Setup Data Directories", self.setup_data_directories),
            ("Test Monitoring Components", self.test_monitoring_components),
            ("Create Launch Scripts", self.create_launch_scripts),
            ("Create Configuration", self.create_configuration_file)
        ]
        
        for step_name, step_function in steps:
            print(f"\n{step_name}...")
            if not step_function():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        self.setup_complete = True
        
        print("\n" + "=" * 50)
        print("✅ MEMORY MONITORING SETUP COMPLETE!")
        print("=" * 50)
        
        print("\n📋 Next Steps:")
        print("1. Restart your menu bar app to apply memory leak fixes")
        print("2. Start monitoring with: ./start_monitoring.sh")
        print("3. Access dashboard at: http://localhost:8002")
        print("4. Run validation with: ./validate_fixes.sh")
        print("5. Check status with: ./quick_status.sh")
        
        print("\n📁 Data Locations:")
        print(f"   Config: ~/Library/Application Support/ClipboardMonitor/")
        print(f"   Logs: ~/Library/Logs/")
        print(f"   Scripts: {os.getcwd()}/")
        
        print("\n🔧 Available Commands:")
        print("   ./start_monitoring.sh    - Start all monitoring")
        print("   ./stop_monitoring.sh     - Stop all monitoring")
        print("   ./validate_fixes.sh      - Run fix validation")
        print("   ./quick_status.sh        - Quick status check")
        
        working_components = sum(1 for status in self.components_status.values() if status == "OK")
        total_components = len(self.components_status)
        
        if working_components == total_components:
            print(f"\n🎉 All {total_components} monitoring components are working correctly!")
        else:
            print(f"\n⚠️  {working_components}/{total_components} components working - some features may be limited")
        
        return True


def main():
    """Main setup function"""
    setup = MemoryMonitoringSetup()
    
    try:
        success = setup.run_setup()
        
        if success:
            print("\n🚀 Ready to start monitoring!")
            
            # Ask if user wants to start monitoring immediately
            try:
                response = input("\nStart monitoring now? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    print("Starting monitoring system...")
                    subprocess.run(['./start_monitoring.sh'], check=True)
            except (KeyboardInterrupt, EOFError):
                print("\nSetup complete. Start monitoring manually when ready.")
        else:
            print("\n❌ Setup failed. Please check the errors above and try again.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
