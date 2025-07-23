# 📦 Optional Dependencies for Memory Debugging

## 🎯 **Overview**

The memory debugging tools work perfectly without any additional dependencies. However, some optional features require extra packages.

## 📊 **Matplotlib (Optional - For Graphing)**

### **What it enables:**
- **Visual memory usage graphs** in the Memory Leak Analyzer
- **Trend visualization** with time-based charts
- **Export graphs** as PNG files for reports

### **What works without it:**
- ✅ **All external monitoring** (⚡🔍🔍⏱️)
- ✅ **Memory leak analysis** (🔬)
- ✅ **Live memory monitoring** (📈)
- ✅ **Log analysis and reports**
- ✅ **All VS Code buttons**

### **Installation (Optional):**

If you want graphing features, install matplotlib:

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Install matplotlib
pip install matplotlib

# Or if you prefer conda
conda install matplotlib
```

### **Usage with Graphs:**

Once matplotlib is installed, you can use graphing features:

```bash
cd memory_debugging

# Live monitoring with graph generation
python3 memory_leak_analyzer.py --live --duration 1800 --graph

# Analyze logs and generate graph
python3 memory_leak_analyzer.py --analyze-logs --graph
```

## 🔍 **Current Status**

**✅ Working without matplotlib:**
- All external monitoring tools
- Memory leak detection and analysis
- Live monitoring and statistics
- Log file analysis
- All VS Code buttons

**📊 Disabled without matplotlib:**
- Graph generation (--graph option)
- Visual trend charts
- PNG export of memory usage

## 💡 **Recommendation**

**For most users**: The tools work perfectly without matplotlib. The text-based analysis provides all the information you need to detect memory leaks.

**For advanced analysis**: If you want visual graphs for presentations or detailed trend analysis, install matplotlib.

## 🎯 **Example Output**

### **Without matplotlib:**
```
Note: matplotlib not available - graphing features disabled
Found clipboard monitor process: PID 7589
Starting live monitoring for 30 minutes...

[01:23:51] Memory: 88.6MB (+0.0MB) Objects: 11833
[01:24:21] Memory: 91.0MB (+2.4MB) Objects: 11833
[01:24:51] Memory: 89.2MB (-1.8MB) Objects: 11834

ANALYSIS COMPLETE:
Memory Range: 88.6MB - 91.0MB
Average: 89.6MB
Growth: +0.6MB (stable)
✅ No memory leak detected
```

### **With matplotlib:**
```
Found clipboard monitor process: PID 7589
Starting live monitoring for 30 minutes...

[01:23:51] Memory: 88.6MB (+0.0MB) Objects: 11833
[01:24:21] Memory: 91.0MB (+2.4MB) Objects: 11833
[01:24:51] Memory: 89.2MB (-1.8MB) Objects: 11834

ANALYSIS COMPLETE:
Memory Range: 88.6MB - 91.0MB
Average: 89.6MB
Growth: +0.6MB (stable)
✅ No memory leak detected

Memory usage graph saved to memory_usage_20250723_012451.png
```

---

**🎯 The memory debugging tools are fully functional without any additional dependencies!**
