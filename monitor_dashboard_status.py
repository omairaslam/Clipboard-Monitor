#!/usr/bin/env python3
"""
Monitor dashboard status changes in real-time
"""

import time
import urllib.request
import json
import sys

def get_dashboard_status():
    """Get current dashboard status"""
    try:
        with urllib.request.urlopen('http://localhost:8001/api/dashboard_status', timeout=2) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def format_status(data):
    """Format status data for display"""
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    status = data.get('status', 'unknown')
    message = data.get('status_message', 'Unknown')
    last_activity = data.get('last_activity_seconds', 0)
    countdown = data.get('countdown_seconds', 0)
    
    # Status icon
    icons = {
        'active_in_use': '🟢',
        'active_not_in_use': '🟡',
        'active_persistent': '🔵',
        'inactive': '🔴',
        'error': '❌'
    }
    icon = icons.get(status, '❓')
    
    result = f"{icon} {message}"
    
    if last_activity > 0:
        result += f" (Last activity: {last_activity:.1f}s ago)"
    
    if countdown > 0:
        minutes = int(countdown // 60)
        seconds = int(countdown % 60)
        result += f" [Countdown: {minutes}:{seconds:02d}]"
    
    return result

def main():
    """Monitor dashboard status"""
    print("🔍 Monitoring Dashboard Status (Press Ctrl+C to stop)")
    print("=" * 60)
    
    last_status = None
    
    try:
        while True:
            data = get_dashboard_status()
            current_status = format_status(data)
            
            # Only print if status changed
            if current_status != last_status:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] {current_status}")
                last_status = current_status
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    main()
