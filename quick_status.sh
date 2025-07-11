#!/bin/bash
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
print(f'Memory: {snapshot["process_info"]["memory_rss_mb"]:.1f} MB')
print(f'Objects: {snapshot["object_analysis"]["total_objects"]:,}')
print(f'GC Effectiveness: {snapshot["gc_analysis"]["gc_effectiveness"]:.1%}')
"
