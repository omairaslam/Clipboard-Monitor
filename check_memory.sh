#!/bin/bash
# Quick Memory Status Checker for Clipboard Monitor
# Compatible with Emergency Safe Mode

echo "🔍 Clipboard Monitor - Quick Memory Check"
echo "=========================================="

python3 check_memory_status.py

echo ""
echo "💡 Tip: This works in Emergency Safe Mode!"
echo "📊 For continuous monitoring, use: cd memory_debugging && python3 external_memory_monitor.py"
