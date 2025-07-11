#!/usr/bin/env python3
"""
Test Mini Histogram Display
Shows how the new histogram visualization will look in the menu bar.
"""

def generate_mini_histogram(values, max_value=100):
    """Generate a mini histogram with peak/average indicators showing actual memory levels"""
    if not values:
        return "▁▁▁▁▁▁▁▁▁▁ No data"
    
    # Ensure we have exactly 10 values (pad with zeros or trim)
    if len(values) < 10:
        values = [0] * (10 - len(values)) + values
    else:
        values = values[-10:]  # Take last 10 values
    
    # Calculate statistics
    current_value = values[-1] if values else 0
    peak_value = max(values) if values else 0
    avg_value = sum(values) / len(values) if values else 0
    min_value = min(values) if values else 0
    
    # Use actual max for better scaling
    actual_max = max(peak_value, max_value) if peak_value > 0 else max_value
    if actual_max == 0:
        actual_max = 1
    
    # Generate histogram bars based on actual values
    bars = []
    for value in values:
        # Normalize to 0-8 range based on actual max
        normalized = min(8, int((value / actual_max) * 8))
        
        # Choose bar character based on height
        if normalized == 0:
            bar = "▁"  # Very low
        elif normalized == 1:
            bar = "▂"  # Low
        elif normalized == 2:
            bar = "▃"  # Low-medium
        elif normalized == 3:
            bar = "▄"  # Medium-low
        elif normalized == 4:
            bar = "▅"  # Medium
        elif normalized == 5:
            bar = "▆"  # Medium-high
        elif normalized == 6:
            bar = "▇"  # High
        elif normalized == 7:
            bar = "█"  # Very high
        else:  # normalized == 8
            bar = "█"  # Maximum
        
        bars.append(bar)
    
    # Create histogram display
    histogram = "".join(bars)
    
    # Generate statistics text
    if peak_value > avg_value * 1.5:
        # Show peak if significantly higher than average
        stats = f"Peak: {peak_value:.0f}MB"
    elif current_value > avg_value * 1.2:
        # Show current if above average
        stats = f"High: {current_value:.0f}MB"
    elif current_value < avg_value * 0.8:
        # Show current if below average
        stats = f"Low: {current_value:.0f}MB"
    else:
        # Show average for stable usage
        stats = f"Avg: {avg_value:.0f}MB"
    
    return f"{histogram} {stats}"


def main():
    print("🎯 Mini Histogram Display Test")
    print("=" * 60)
    
    # Test different memory patterns
    test_cases = [
        {
            "name": "Stable Usage",
            "values": [75, 76, 74, 75, 77, 75, 76, 74, 75, 76],
            "description": "Memory usage is stable around 75MB"
        },
        {
            "name": "Growing Usage (Memory Leak)",
            "values": [45, 52, 58, 65, 72, 78, 85, 92, 98, 105],
            "description": "Memory is steadily increasing - potential leak"
        },
        {
            "name": "Decreasing Usage",
            "values": [95, 88, 82, 75, 68, 62, 58, 55, 52, 50],
            "description": "Memory usage decreasing - cleanup working"
        },
        {
            "name": "Spiky Usage",
            "values": [45, 85, 40, 90, 35, 95, 30, 100, 25, 105],
            "description": "Erratic memory usage - investigate"
        },
        {
            "name": "Low Usage",
            "values": [20, 22, 18, 25, 19, 23, 21, 20, 22, 24],
            "description": "Low, stable memory usage - healthy"
        },
        {
            "name": "Peak Usage",
            "values": [45, 48, 52, 55, 125, 58, 52, 48, 45, 47],
            "description": "Had a memory spike but recovered"
        }
    ]
    
    for test in test_cases:
        histogram = generate_mini_histogram(test["values"])
        current = test["values"][-1]
        print(f"\n📊 {test['name']}:")
        print(f"   Menu Bar: {current:.1f}MB {histogram}")
        print(f"   {test['description']}")
    
    print("\n" + "=" * 60)
    print("🎯 How to Read the Mini Histogram:")
    print("   ▁▂▃▄▅▆▇█ = Bar height shows memory level (low → high)")
    print("   Peak: XMB = Highest usage in the time period")
    print("   Avg: XMB = Average usage (stable patterns)")
    print("   High: XMB = Current usage above average")
    print("   Low: XMB = Current usage below average")
    print("   Each bar = one measurement (10 bars = last 10 measurements)")
    print("   Left→Right = Oldest→Newest")
    print("   Histogram shows actual memory levels, not just trends")
    
    print("\n📋 What You'll See in Your Menu:")
    print("   📋 Clipboard Monitor")
    print("   ├── Status: Running")
    print("   ├── Menu Bar: 75.2MB ▂▃▅▇█▇▅▃▂▁ Peak: 95MB")
    print("   ├── Service: 45.1MB  ▃▃▃▃▃▃▃▃▃▃ Avg: 45MB")
    print("   ├── ─────────────────────────────")
    print("   ├── Pause Monitoring")
    print("   └── ...")
    
    print("\n✅ Mini histogram updates every 5 seconds automatically!")
    print("🚨 █ Full bars = High memory usage (investigate!)")
    print("📊 ▅ Medium bars = Normal operation")
    print("✅ ▂ Short bars = Low memory usage (good)")
    print("📈 Peak/Avg indicators = Quick statistics at a glance")
    print("🎯 Actual memory levels = More informative than trend-only")


if __name__ == "__main__":
    main()
