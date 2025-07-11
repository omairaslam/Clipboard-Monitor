#!/usr/bin/env python3
"""
Test Mini Graph Display
Demonstrates the new mini graph functionality for memory usage.
"""

def generate_mini_graph(values, max_value=100):
    """Generate a compact mini graph using thin vertical bars with proper spacing and alignment"""
    if not values:
        return " ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌"  # 10 thin gray bars with gaps

    # Ensure we have exactly 10 values (pad with zeros or trim)
    if len(values) < 10:
        values = [0] * (10 - len(values)) + values
    else:
        values = values[-10:]  # Take last 10 values

    # Calculate trend (is memory growing, stable, or decreasing?)
    trend = "stable"
    if len(values) >= 3:
        recent_avg = sum(values[-3:]) / 3
        older_avg = sum(values[:3]) / 3 if len(values) >= 6 else sum(values[:-3]) / max(1, len(values) - 3)

        if recent_avg > older_avg * 1.1:  # 10% increase
            trend = "growing"
        elif recent_avg < older_avg * 0.9:  # 10% decrease
            trend = "decreasing"

    # Normalize values to bar heights (0-4 levels for compact display)
    actual_max = max(values) if values else max_value
    if actual_max == 0:
        actual_max = 1

    bars = []
    for i, value in enumerate(values):
        # Normalize to 0-4 range for compact look
        normalized = min(4, int((value / actual_max) * 4))

        # Use actual thin Unicode block characters instead of emoji squares
        if normalized == 0:
            bar = "▁"  # Very thin gray bar for zero/very low
        elif normalized == 1:
            if trend == "growing":
                bar = "▃"  # Short bar for low but growing
            elif trend == "decreasing":
                bar = "▃"  # Short bar for low and decreasing (good)
            else:
                bar = "▃"  # Short bar for low and stable
        elif normalized == 2:
            if trend == "growing":
                bar = "▅"  # Medium bar for medium and growing
            elif trend == "decreasing":
                bar = "▅"  # Medium bar for medium but decreasing
            else:
                bar = "▅"  # Medium bar for medium and stable
        elif normalized == 3:
            if trend == "growing":
                bar = "▇"  # Tall bar for high and growing (warning!)
            elif trend == "decreasing":
                bar = "▇"  # Tall bar for high but decreasing
            else:
                bar = "▇"  # Tall bar for high and stable
        else:  # normalized == 4
            if trend == "growing":
                bar = "█"  # Full bar for very high and growing (danger!)
            elif trend == "decreasing":
                bar = "█"  # Full bar for very high but decreasing
            else:
                bar = "█"  # Full bar for very high and stable (concern)

        bars.append(bar)

    # Join with 2-pixel gaps and right-align
    graph = " ".join(bars)
    return f" {graph}"  # Leading space for right alignment

def main():
    print("🎯 Mini Graph Display Test")
    print("=" * 50)
    
    # Test different memory usage patterns
    test_cases = [
        {
            "name": "Stable Usage",
            "values": [75, 76, 74, 75, 77, 75, 76, 74, 75, 76],
            "description": "Memory usage is stable around 75MB"
        },
        {
            "name": "Growing Usage (Memory Leak)",
            "values": [60, 65, 70, 75, 80, 85, 90, 95, 100, 105],
            "description": "Memory is steadily increasing - potential leak"
        },
        {
            "name": "Decreasing Usage",
            "values": [100, 95, 90, 85, 80, 75, 70, 65, 60, 55],
            "description": "Memory usage decreasing - cleanup working"
        },
        {
            "name": "Spiky Usage",
            "values": [50, 80, 45, 85, 40, 90, 35, 95, 30, 100],
            "description": "Erratic memory usage - investigate"
        },
        {
            "name": "Low Usage",
            "values": [20, 22, 18, 25, 19, 23, 21, 24, 20, 22],
            "description": "Low, stable memory usage - healthy"
        }
    ]
    
    for test in test_cases:
        graph = generate_mini_graph(test["values"], max_value=150)
        current = test["values"][-1] if test["values"] else 0
        
        print(f"\n📊 {test['name']}:")
        print(f"   Menu Bar: {current:.1f}MB {graph}")
        print(f"   {test['description']}")
    
    print("\n" + "=" * 50)
    print("🎯 How to Read the Thin Vertical Bar Graphs:")
    print("   ▁ = Very low usage (minimal bar)")
    print("   ▃ = Low usage (short bar)")
    print("   ▅ = Medium usage (medium bar)")
    print("   ▇ = High usage (tall bar)")
    print("   █ = Very high usage (full bar)")
    print("   Bar height = Memory usage level")
    print("   Each bar = one measurement (10 bars = last 10 measurements)")
    print("   Trend left→right = oldest→newest")
    print("   Thin Unicode bars = Much narrower than emoji squares")

    print("\n📋 What You'll See in Your Menu:")
    print("   📋 Clipboard Monitor")
    print("   ├── Status: Running")
    print("   ├── Menu Bar: 75.2MB  ▅ ▅ ▃ ▇ ▅ ▅ ▃ ▅ ▅ ▅")
    print("   ├── Service: 45.1MB   ▃ ▃ ▃ ▃ ▃ ▃ ▃ ▃ ▃ ▃")
    print("   ├── ─────────────────────────────")
    print("   ├── Pause Monitoring")
    print("   └── ...")

    print("\n✅ Thin vertical bar graphs update every 5 seconds automatically!")
    print("🚨 █ Full bars = High memory usage (investigate!)")
    print("✅ ▃ Short bars = Low memory usage (good)")
    print("📊 ▅ Medium bars = Normal operation")
    print("📏 Actual thin Unicode bars with 2-pixel gaps, right-aligned")

if __name__ == "__main__":
    main()
