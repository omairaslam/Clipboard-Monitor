# 📊 Memory Visualizer - Clipboard Monitor

## 🎯 Overview

The Memory Visualizer is a comprehensive monitoring tool designed to track and analyze memory usage for both the main Clipboard Monitor service and the menu bar application. It provides real-time monitoring, historical data visualization, and memory leak detection to help diagnose performance issues.

## ✨ Key Features

### **Real-Time Monitoring**
- 📈 **Live Memory Tracking** - Continuous monitoring of both processes
- 🔄 **Configurable Intervals** - Monitor every 10 seconds to 5 minutes
- 📊 **Current Status Cards** - Instant overview of memory usage
- 💻 **System Memory** - Overall system memory utilization

### **Historical Data Visualization**
- 📉 **Beautiful Charts** - Interactive graphs using Chart.js
- ⏰ **Flexible Time Ranges** - View data from 1 hour to 1 week
- 📈 **Trend Analysis** - Identify memory usage patterns
- 💾 **Persistent Storage** - Data saved between sessions

### **Memory Leak Detection**
- 🔍 **Automated Analysis** - Intelligent leak detection algorithms
- ⚠️ **Growth Rate Monitoring** - Track memory growth over time
- 🚨 **Alert System** - Visual warnings for potential issues
- 📊 **Detailed Metrics** - Growth rates, averages, and trends

## 🚀 Getting Started

### **Access Methods**

#### **From Menu Bar (Recommended)**
1. Click the 📋 Clipboard Monitor icon in your menu bar
2. Navigate to **Preferences** → **Advanced Settings**
3. Click **📊 Memory Visualizer**
4. The visualizer will open in your default browser

#### **Direct Launch**
```bash
cd /path/to/clipboard-monitor
python3 memory_visualizer.py
```

### **First Time Setup**
1. The visualizer automatically starts monitoring when launched
2. Data collection begins immediately with 30-second intervals
3. Historical data accumulates over time for trend analysis
4. No configuration required - works out of the box

## 📊 Interface Overview

### **Control Panel**
- **Time Range Selector** - Choose data timeframe (1 hour to 1 week)
- **Monitor Interval** - Set collection frequency (10s to 5 minutes)
- **Start/Stop Monitoring** - Control data collection
- **Refresh Data** - Manual data update

### **Status Cards**
- **🖥️ Main Service** - Memory usage for the core monitoring service
- **📋 Menu Bar App** - Memory usage for the menu bar application
- **💻 System Memory** - Overall system memory statistics

### **Charts & Graphs**
- **📈 Memory Usage Over Time** - Line chart showing historical trends
- **📊 Memory Usage Comparison** - Bar chart comparing current usage
- **🔍 Memory Leak Analysis** - Detailed analysis with recommendations

## 🔍 Memory Leak Detection

### **Detection Criteria**
The visualizer uses intelligent algorithms to detect potential memory leaks:

#### **Status Levels**
- **🟢 Normal** - Memory growth < 2 MB/hour
- **🟡 Monitoring Needed** - Memory growth 2-5 MB/hour
- **🔴 Potential Leak** - Memory growth > 5 MB/hour

#### **Analysis Metrics**
- **Growth Rate** - Memory increase per hour (MB/hour)
- **Total Growth** - Cumulative memory increase
- **Average Memory** - Mean memory usage over time period
- **Current Memory** - Latest memory reading
- **Data Points** - Number of measurements analyzed

### **Interpreting Results**

#### **Normal Behavior**
```
Status: Normal
Growth Rate: 0.5 MB/hour
Total Growth: 2.1 MB
Average Memory: 45.2 MB
```

#### **Potential Memory Leak**
```
Status: Potential Memory Leak Detected!
Growth Rate: 8.3 MB/hour
Total Growth: 67.2 MB
Average Memory: 78.5 MB
```

## 📈 Understanding the Data

### **Memory Metrics Explained**

#### **Physical Memory (RSS)**
- **Definition** - Resident Set Size - actual RAM usage
- **Importance** - Shows real memory consumption
- **Normal Range** - 20-100 MB for typical usage

#### **Virtual Memory (VMS)**
- **Definition** - Virtual Memory Size - total virtual memory
- **Importance** - Indicates memory allocation patterns
- **Normal Range** - Usually 2-5x physical memory

#### **Memory Percentage**
- **Definition** - Percentage of total system memory used
- **Importance** - Shows relative impact on system
- **Normal Range** - < 1% for lightweight applications

### **Chart Interpretation**

#### **Healthy Memory Pattern**
- Stable baseline with minor fluctuations
- Periodic increases during activity
- Memory returns to baseline after operations
- No sustained upward trend

#### **Memory Leak Pattern**
- Continuous upward trend over time
- Memory doesn't return to baseline
- Steady increase regardless of activity
- Exponential growth in severe cases

## 🛠️ Troubleshooting

### **Common Issues**

#### **"Process Not Running" Status**
- **Cause** - Service is stopped or crashed
- **Solution** - Restart Clipboard Monitor services
- **Check** - Look for process in Activity Monitor

#### **No Historical Data**
- **Cause** - Monitoring recently started
- **Solution** - Wait for data collection (minimum 2 data points)
- **Note** - Analysis requires at least 1 hour of data

#### **High Memory Usage**
- **Investigation** - Check for large clipboard content
- **Action** - Clear clipboard history if needed
- **Monitor** - Watch for continued growth

### **Performance Optimization**

#### **Monitoring Frequency**
- **High Frequency** (10-30s) - Better leak detection, more CPU usage
- **Low Frequency** (5 minutes) - Less overhead, slower detection
- **Recommended** - 30 seconds for balanced monitoring

#### **Data Retention**
- **Default** - Last 1000 data points per process
- **Storage** - Data saved to `~/Library/Application Support/ClipboardMonitor/memory_data.json`
- **Cleanup** - Automatic pruning of old data

## 🔧 Advanced Features

### **API Endpoints**
The visualizer provides REST API endpoints for integration:

- `GET /api/current` - Current memory status
- `GET /api/historical?hours=24` - Historical data
- `GET /api/analysis?hours=24` - Memory leak analysis
- `POST /api/start_monitoring?interval=30` - Start monitoring
- `POST /api/stop_monitoring` - Stop monitoring

### **Data Export**
Memory data is stored in JSON format and can be exported for external analysis:

```json
{
  "main_service": [
    {
      "timestamp": "2025-07-10T10:30:00",
      "rss_mb": 45.2,
      "vms_mb": 180.5,
      "percent": 0.8
    }
  ],
  "menu_bar": [...],
  "system": [...]
}
```

## 📝 Best Practices

### **Regular Monitoring**
- Check memory visualizer weekly for trends
- Monitor after major updates or changes
- Set up regular monitoring during development

### **Leak Investigation**
1. **Identify** - Use visualizer to detect potential leaks
2. **Correlate** - Match memory spikes with user actions
3. **Isolate** - Test specific features or operations
4. **Document** - Record findings for debugging

### **Performance Baseline**
- Establish normal memory usage patterns
- Document typical memory ranges for your usage
- Monitor changes after configuration updates

## 🚀 Future Enhancements

### **Planned Features**
- **Email Alerts** - Automatic notifications for memory leaks
- **Comparative Analysis** - Compare memory usage across time periods
- **Memory Profiling** - Detailed breakdown of memory allocation
- **Export Reports** - Generate PDF reports for analysis

### **Integration Possibilities**
- **Slack/Discord Notifications** - Team alerts for memory issues
- **Grafana Dashboard** - Enterprise monitoring integration
- **Log Correlation** - Match memory spikes with log events

The Memory Visualizer is a powerful tool for maintaining optimal performance of your Clipboard Monitor installation. Regular use helps ensure smooth operation and early detection of potential issues.
