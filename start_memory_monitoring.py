#!/usr/bin/env python3
"""
Enhanced Memory Monitoring Launcher
Starts comprehensive memory monitoring with leak detection for Clipboard Monitor.
"""

import os
import sys
import time
import argparse
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_visualizer import MemoryMonitor
from menu_bar_memory_profiler import start_menu_bar_profiling, stop_menu_bar_profiling
from utils import log_event, log_error


class EnhancedMemoryMonitoringService:
    """Service to coordinate all memory monitoring components"""
    
    def __init__(self, interval=30, enable_leak_detection=True):
        self.interval = interval
        self.enable_leak_detection = enable_leak_detection
        self.running = False
        self.memory_monitor = None
        self.menu_bar_profiler = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start all memory monitoring components"""
        if self.running:
            print("Memory monitoring is already running")
            return
        
        print("🚀 Starting Enhanced Memory Monitoring...")
        
        try:
            # Start main memory monitor
            self.memory_monitor = MemoryMonitor()
            self.memory_monitor.start_monitoring(interval=self.interval)
            print(f"✅ Main memory monitor started (interval: {self.interval}s)")
            
            # Start menu bar profiler
            if self.enable_leak_detection:
                self.menu_bar_profiler = start_menu_bar_profiling(interval=60)
                print("✅ Menu bar memory profiler started")
            
            self.running = True
            
            # Start web interface
            self._start_web_interface()
            
            print("\n📊 Memory Monitoring Dashboard:")
            print("   Web Interface: http://localhost:8001")
            print("   Leak Analysis: Available in menu bar app")
            print("   Data Location: ~/Library/Application Support/ClipboardMonitor/")
            print("\nPress Ctrl+C to stop monitoring...")
            
            # Keep the service running
            self._monitor_loop()
            
        except Exception as e:
            log_error(f"Failed to start memory monitoring: {e}")
            print(f"❌ Error: {e}")
            self.stop()
    
    def _start_web_interface(self):
        """Start the web interface for memory visualization"""
        try:
            import threading
            from memory_visualizer import main as start_visualizer
            
            # Start visualizer in a separate thread
            visualizer_thread = threading.Thread(target=start_visualizer, daemon=True)
            visualizer_thread.start()
            
            # Give it a moment to start
            time.sleep(2)
            print("✅ Web interface started at http://localhost:8001")
            
        except Exception as e:
            log_error(f"Failed to start web interface: {e}")
            print(f"⚠️  Web interface failed to start: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop with status updates"""
        last_status_time = 0
        status_interval = 300  # Show status every 5 minutes
        
        while self.running:
            try:
                current_time = time.time()
                
                # Show periodic status updates
                if current_time - last_status_time >= status_interval:
                    self._show_status()
                    last_status_time = current_time
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                log_error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _show_status(self):
        """Show current monitoring status"""
        try:
            if self.memory_monitor:
                status = self.memory_monitor.get_current_status()
                if status:
                    print(f"\n📈 Status Update ({time.strftime('%H:%M:%S')}):")
                    
                    if status.get("main_service"):
                        print(f"   Main Service: {status['main_service']['memory_mb']:.1f} MB")
                    
                    if status.get("menu_bar"):
                        print(f"   Menu Bar App: {status['menu_bar']['memory_mb']:.1f} MB")
                    
                    # Check for leak alerts
                    leak_analysis = self.memory_monitor.get_leak_analysis()
                    if leak_analysis["current_analysis"]["leak_detected"]:
                        print(f"   ⚠️  LEAK DETECTED: {leak_analysis['current_analysis']['memory_trend']}")
                        print(f"   Growth Rate: {leak_analysis['current_analysis']['growth_rate_mb_per_hour']:.2f} MB/hour")
                    else:
                        print("   ✅ No leaks detected")
        
        except Exception as e:
            log_error(f"Error showing status: {e}")
    
    def stop(self):
        """Stop all monitoring components"""
        if not self.running:
            return
        
        print("\n🛑 Stopping memory monitoring...")
        self.running = False
        
        try:
            if self.memory_monitor:
                self.memory_monitor.stop_monitoring()
                print("✅ Main memory monitor stopped")
            
            if self.menu_bar_profiler:
                stop_menu_bar_profiling()
                print("✅ Menu bar profiler stopped")
                
        except Exception as e:
            log_error(f"Error stopping monitoring: {e}")
            print(f"⚠️  Error during shutdown: {e}")
        
        print("✅ Memory monitoring stopped")
    
    def get_status(self):
        """Get current status of all monitoring components"""
        status = {
            "running": self.running,
            "interval": self.interval,
            "leak_detection_enabled": self.enable_leak_detection,
            "components": {}
        }
        
        if self.memory_monitor:
            try:
                status["components"]["memory_monitor"] = self.memory_monitor.get_current_status()
            except Exception as e:
                status["components"]["memory_monitor"] = {"error": str(e)}
        
        if self.menu_bar_profiler:
            try:
                status["components"]["menu_bar_profiler"] = self.menu_bar_profiler.get_current_status()
            except Exception as e:
                status["components"]["menu_bar_profiler"] = {"error": str(e)}
        
        return status


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Memory Monitoring for Clipboard Monitor")
    parser.add_argument("--interval", type=int, default=30, 
                       help="Monitoring interval in seconds (default: 30)")
    parser.add_argument("--no-leak-detection", action="store_true",
                       help="Disable leak detection profiling")
    parser.add_argument("--status", action="store_true",
                       help="Show current monitoring status and exit")
    parser.add_argument("--stop", action="store_true",
                       help="Stop any running monitoring and exit")
    
    args = parser.parse_args()
    
    if args.status:
        # Show status and exit
        try:
            monitor = MemoryMonitor()
            status = monitor.get_current_status()
            leak_analysis = monitor.get_leak_analysis()
            
            print("📊 Current Memory Monitoring Status:")
            print(f"   Timestamp: {status.get('timestamp', 'Unknown')}")
            
            if status.get("main_service"):
                print(f"   Main Service: {status['main_service']['memory_mb']:.1f} MB")
            
            if status.get("menu_bar"):
                print(f"   Menu Bar App: {status['menu_bar']['memory_mb']:.1f} MB")
            
            print(f"   Leak Detection: {'Active' if leak_analysis.get('tracemalloc_enabled', False) else 'Inactive'}")
            print(f"   Total Snapshots: {leak_analysis.get('total_snapshots', 0)}")

            current_analysis = leak_analysis.get("current_analysis", {})
            if current_analysis.get("leak_detected", False):
                print(f"   ⚠️  LEAK DETECTED: {current_analysis.get('memory_trend', 'unknown')}")
            else:
                print("   ✅ No leaks detected")
                
        except Exception as e:
            print(f"❌ Error getting status: {e}")
        return
    
    if args.stop:
        # Stop monitoring and exit
        try:
            stop_menu_bar_profiling()
            print("✅ Memory monitoring stopped")
        except Exception as e:
            print(f"⚠️  Error stopping monitoring: {e}")
        return
    
    # Start monitoring service
    service = EnhancedMemoryMonitoringService(
        interval=args.interval,
        enable_leak_detection=not args.no_leak_detection
    )
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        service.stop()


if __name__ == "__main__":
    main()
