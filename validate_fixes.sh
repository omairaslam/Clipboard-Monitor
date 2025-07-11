#!/bin/bash
# Run memory leak fix validation
echo "🧪 Starting Memory Leak Fix Validation..."
cd "$(dirname "$0")"

python3 validate_leak_fixes.py --duration 60 --interval 60

echo "✅ Validation complete"
echo "View results with: python3 validate_leak_fixes.py --report"
