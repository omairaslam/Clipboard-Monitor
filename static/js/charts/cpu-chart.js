let cpuChart = null;
const CPU_LIVE_RANGES = { '2m': 60, '5m': 150, '15m': 450 };
function getCpuMaxPoints(){ try{ const v = localStorage.getItem('cpu_live_range') || '2m'; return CPU_LIVE_RANGES[v] || 60; } catch { return 60; } }
class SimpleCPUChart {
  initChart() {
    const canvas = document.getElementById('cpuChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (cpuChart) return cpuChart;
    cpuChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          { label: 'Menu Bar App (%)', data: [], borderColor: '#2196F3', backgroundColor: 'rgba(33, 150, 243, 0.1)', fill: true, tension: 0.4 },
          { label: 'Main Service (%)', data: [], borderColor: '#4CAF50', backgroundColor: 'rgba(76, 175, 80, 0.1)', fill: true, tension: 0.4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: { display: true, position: 'top' }
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: 'CPU (%)' } },
          x: { title: { display: true, text: 'Time' } }
        }
      }
    });
    // Expose chart instance globally so inline code can push points
    if (typeof window !== 'undefined') window.cpuChart = cpuChart;
    return cpuChart;
  }

  constructor() { this.isPaused = false; }

  switchToRealtimeMode() {
    const realtimeBtn = document.getElementById('cpu-realtime-btn');
    const historicalBtn = document.getElementById('cpu-historical-btn');
    const historicalOptions = document.getElementById('cpu-historical-options');
    const liveOptions = document.getElementById('cpu-live-options');
    const chartTitle = document.getElementById('cpu-chart-title');
    const frequencyLabel = document.getElementById('cpu-frequency-label');
    const modeIndicator = document.getElementById('cpu-chart-mode-indicator');
    const modeBadge = document.getElementById('cpu-mode-badge');
    const liveRangeSelect = document.getElementById('cpu-live-range-select');
    if (realtimeBtn && historicalBtn) {
      realtimeBtn.style.background = '#4CAF50';
      realtimeBtn.style.color = 'white';
      historicalBtn.style.background = 'white';
      historicalBtn.style.color = '#666';
      if (historicalOptions) historicalOptions.style.display = 'none';
      if (liveOptions) liveOptions.style.display = 'flex';
      if (chartTitle) chartTitle.textContent = 'Live CPU Usage';
      if (frequencyLabel) frequencyLabel.textContent = 'Data: 2s intervals';
      if (modeIndicator) {
        const label = liveRangeSelect ? liveRangeSelect.options[liveRangeSelect.selectedIndex].text : 'Live';
        modeIndicator.textContent = `Live: ${label}`;
      }
      if (modeBadge) { modeBadge.textContent = 'Live'; modeBadge.style.background = '#4CAF50'; }
    }
  }

  switchToHistoricalMode() {
    const realtimeBtn = document.getElementById('cpu-realtime-btn');
    const historicalBtn = document.getElementById('cpu-historical-btn');
    const historicalOptions = document.getElementById('cpu-historical-options');
    const liveOptions = document.getElementById('cpu-live-options');
    const chartTitle = document.getElementById('cpu-chart-title');
    const frequencyLabel = document.getElementById('cpu-frequency-label');
    const modeIndicator = document.getElementById('cpu-chart-mode-indicator');
    const modeBadge = document.getElementById('cpu-mode-badge');
    if (realtimeBtn && historicalBtn) {
      realtimeBtn.style.background = 'white';
      realtimeBtn.style.color = '#666';
      historicalBtn.style.background = '#2196F3';
      historicalBtn.style.color = 'white';
      if (historicalOptions) historicalOptions.style.display = 'flex';
      if (liveOptions) liveOptions.style.display = 'none';
      if (chartTitle) chartTitle.textContent = 'Historical CPU Usage';
      if (frequencyLabel) frequencyLabel.textContent = 'Historical data frequency varies';
      if (modeIndicator) modeIndicator.textContent = 'Historical';
      if (modeBadge) { modeBadge.textContent = 'Historical'; modeBadge.style.background = '#2196F3'; }
    }
  }

  async loadHistoricalData() {
    try {
      const startTime = performance.now();
      const timeRange = document.getElementById('cpu-time-range').value;
      const resolution = 'full';
      const response = await fetch(`/api/historical-chart?hours=${timeRange}&resolution=${resolution}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      const loadTime = performance.now() - startTime;
      cpuChart.data.labels = data.points.map(p => new Date(p.timestamp).toLocaleTimeString());
      cpuChart.data.datasets[0].data = data.points.map(p => p.menubar_cpu || 0);
      cpuChart.data.datasets[1].data = data.points.map(p => p.service_cpu || 0);
      cpuChart.update();
      const modeIndicator = document.getElementById('cpu-chart-mode-indicator');
      const pointsCount = document.getElementById('cpu-chart-points-count');
      const lastRefresh = document.getElementById('cpu-last-refresh');
      if (modeIndicator) modeIndicator.textContent = 'Historical';
      if (pointsCount) pointsCount.textContent = `${data.points.length} pts`;
      if (lastRefresh) lastRefresh.textContent = `Loaded in ${loadTime.toFixed(0)}ms`;
    } catch (err) {
      console.error('Error loading historical CPU data:', err);
    }
  }

  changeLiveRange(val){
    try { localStorage.setItem('cpu_live_range', val); } catch {}
    const select = document.getElementById('cpu-live-range-select');
    if (select && select.value !== val) select.value = val;
    const modeIndicator = document.getElementById('cpu-chart-mode-indicator');
    if (modeIndicator) modeIndicator.textContent = `Live: ${select.options[select.selectedIndex].text}`;
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    const pauseBtn = document.getElementById('cpu-pause-btn');
    if (pauseBtn) pauseBtn.textContent = this.isPaused ? '▶️ Resume' : '⏸️ Pause';
  }

  clearChart() {
    cpuChart.data.labels = [];
    cpuChart.data.datasets[0].data = [];
    cpuChart.data.datasets[1].data = [];
    cpuChart.update();
  }
}

// Expose globally for onclick handlers
if (typeof window !== 'undefined') {
  window.SimpleCPUChart = SimpleCPUChart;
  // Auto-boot the CPU chart manager when DOM is ready
  window.addEventListener('DOMContentLoaded', () => {
    try {
      if (!window.cpuChartManager) {
        window.cpuChartManager = new SimpleCPUChart();
      }
      if (typeof window.cpuChartManager.initChart === 'function') {
        window.cpuChartManager.initChart();
      }
      // Force initial UI to Live semantics on first load
      try {
        const modeBadge = document.getElementById('cpu-mode-badge');
        if (modeBadge) { modeBadge.textContent = 'Live'; modeBadge.style.background = '#4CAF50'; }
        const chartTitle = document.getElementById('cpu-chart-title');
        if (chartTitle) chartTitle.textContent = 'Live CPU Usage';
        const freq = document.getElementById('cpu-frequency-label');
        if (freq) freq.textContent = 'Data: 2s intervals';
        const saved = localStorage.getItem('cpu_live_range') || '2m';
        const sel = document.getElementById('cpu-live-range-select');
        if (sel) {
          sel.value = saved;
          const label = sel.options[sel.selectedIndex]?.text || '';
          const ind = document.getElementById('cpu-chart-mode-indicator');
          if (ind) ind.textContent = label ? `Live: ${label}` : 'Live';
        }
        const rtBtn = document.getElementById('cpu-realtime-btn');
        const histBtn = document.getElementById('cpu-historical-btn');
        const liveOptions = document.getElementById('cpu-live-options');
        const historicalOptions = document.getElementById('cpu-historical-options');
        if (rtBtn && histBtn) {
          rtBtn.style.background = '#4CAF50'; rtBtn.style.color = '#fff';
          histBtn.style.background = 'white'; histBtn.style.color = '#666';
        }
        if (liveOptions) liveOptions.style.display = 'flex';
        if (historicalOptions) historicalOptions.style.display = 'none';
      } catch {}
    } catch (e) {
      console.warn('CPU chart auto-init skipped:', e);
    }
  });
}

