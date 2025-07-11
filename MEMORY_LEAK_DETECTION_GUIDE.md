# 🔍 Enhanced Memory Leak Detection Guide

## Overview

This guide explains how to use the enhanced memory monitoring tools to detect and fix memory leaks in the Clipboard Monitor Menu Bar service.

## 🚀 Quick Start

### 1. Start Enhanced Memory Monitoring

```bash
# Start with default settings (30-second intervals)
./start_memory_monitoring.py

# Start with custom interval (60 seconds)
./start_memory_monitoring.py --interval 60

# Start without leak detection profiling
./start_memory_monitoring.py --no-leak-detection
```

### 2. Access Monitoring Interfaces

- **Web Dashboard**: http://localhost:8001
- **Menu Bar App**: Enhanced memory menu with leak analysis
- **Command Line**: `./start_memory_monitoring.py --status`

## 📊 Monitoring Features

### Real-time Memory Tracking
- **Process Memory**: RSS, VMS, memory percentage
- **Object Counts**: Python objects by type
- **Garbage Collection**: Collection stats and effectiveness
- **System Resources**: File handles, threads, context switches

### Advanced Leak Detection
- **Growth Rate Analysis**: MB/hour memory growth tracking
- **Trend Detection**: Consistent growth pattern identification
- **Object Leak Detection**: Unbounded object accumulation
- **Tracemalloc Integration**: Detailed allocation tracking

### Alert System
- **Automatic Alerts**: Triggered on leak detection
- **Severity Levels**: High, Medium, Low priority alerts
- **Historical Tracking**: Alert history and patterns

## 🔧 Using the Tools

### Menu Bar App Integration

The menu bar app now includes enhanced memory monitoring:

1. **Memory Usage Menu**:
   - Current usage display
   - Memory trends visualization
   - **🔍 Leak Analysis**: Detailed leak reports
   - **🧹 Force Garbage Collection**: Manual GC with analysis
   - **📊 Object Tracking**: Object growth analysis
   - **⚠️ Memory Alerts**: Recent leak alerts

### Web Dashboard

Access the web interface at http://localhost:8001:

- Real-time memory charts
- Historical data analysis
- Leak detection reports
- System resource monitoring

### Command Line Tools

```bash
# Check current status
./start_memory_monitoring.py --status

# Stop monitoring
./start_memory_monitoring.py --stop

# View help
./start_memory_monitoring.py --help
```

## 🎯 Leak Detection Strategy

### Phase 1: Data Collection (First 24 hours)
1. Start monitoring with default settings
2. Let the system collect baseline data
3. Monitor for initial leak patterns

### Phase 2: Analysis (After 24 hours)
1. Review leak analysis reports
2. Check memory growth trends
3. Identify problematic components

### Phase 3: Investigation
1. Use object tracking to identify growing object types
2. Force garbage collection to test effectiveness
3. Review tracemalloc allocation data

### Phase 4: Fix Implementation
1. Address identified leak sources
2. Monitor fix effectiveness
3. Establish ongoing monitoring

## 🚨 Common Leak Patterns

### 1. Unbounded Data Structures
**Symptoms**: Consistent memory growth, increasing object counts
**Location**: `memory_data`, `memory_timestamps` arrays
**Fix**: Implement size limits and cleanup

### 2. Timer/Handler Leaks
**Symptoms**: Memory spikes, thread count growth
**Location**: NSTimer objects, rumps event handlers
**Fix**: Proper cleanup in destructors

### 3. Module Loading Leaks
**Symptoms**: Memory growth on clipboard events
**Location**: Module manager, imported modules
**Fix**: Module unloading, reference cleanup

### 4. File Handle Leaks
**Symptoms**: Resource exhaustion, slow growth
**Location**: History file operations, logging
**Fix**: Proper file handle management

## 📈 Interpreting Results

### Memory Growth Rates
- **< 1 MB/hour**: Normal operation
- **1-5 MB/hour**: Slow leak, investigate
- **> 5 MB/hour**: Active leak, immediate action needed

### Object Growth
- **< 100 objects/hour**: Normal
- **100-1000 objects/hour**: Monitor closely
- **> 1000 objects/hour**: Likely leak

### Garbage Collection Effectiveness
- **High collection rate**: Memory pressure
- **Low freed objects**: Possible reference cycles
- **Growing uncollectable**: Reference leaks

## 🛠️ Troubleshooting

### Monitoring Not Starting
1. Check Python dependencies: `psutil`, `tracemalloc`
2. Verify file permissions
3. Check log files for errors

### Web Interface Not Accessible
1. Verify port 8001 is available
2. Check firewall settings
3. Try alternative port in code

### No Leak Detection
1. Ensure tracemalloc is enabled
2. Check profiler initialization
3. Verify sufficient data collection time

### False Positives
1. Review growth thresholds in code
2. Check for legitimate memory usage patterns
3. Adjust detection sensitivity

## 📁 Data Locations

All monitoring data is stored in:
```
~/Library/Application Support/ClipboardMonitor/
├── memory_data.json          # Main memory monitoring data
├── leak_analysis.json        # Leak detection results
├── menubar_profile.json      # Menu bar profiling data
└── clipboard_monitor.log     # General logs
```

## 🔄 Continuous Monitoring

### Automated Monitoring
1. Set up monitoring as a background service
2. Configure alert thresholds
3. Schedule regular analysis reports

### Performance Impact
- **Minimal**: Basic memory tracking (~1% CPU)
- **Low**: Enhanced profiling (~2-3% CPU)
- **Configurable**: Adjust intervals to balance accuracy vs. performance

## 📞 Getting Help

If you encounter issues:

1. Check the logs in `~/Library/Application Support/ClipboardMonitor/`
2. Run with verbose logging: `python -v start_memory_monitoring.py`
3. Review the leak analysis reports for specific guidance
4. Use the force garbage collection feature to test memory cleanup

## 🎯 Next Steps

After implementing enhanced monitoring:

1. **Establish Baseline**: Run for 24-48 hours to establish normal patterns
2. **Identify Leaks**: Use the analysis tools to pinpoint leak sources
3. **Implement Fixes**: Address the most critical leaks first
4. **Validate**: Confirm fixes with continued monitoring
5. **Optimize**: Fine-tune monitoring intervals and thresholds

The enhanced memory monitoring provides comprehensive leak detection capabilities. Start with the default settings and gradually customize based on your specific needs and findings.
