export let cpuChart = null;
export class SimpleCPUChart {
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
          { label: 'Menu Bar App (%)', data: [], borderColor: '#2196F3', backgroundColor: 'rgba(33,150,243,0.1)', fill: true, tension: 0.3 },
          { label: 'Main Service (%)', data: [], borderColor: '#4CAF50', backgroundColor: 'rgba(76,175,80,0.1)', fill: true, tension: 0.3 }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true, position: 'top' },
          title: { display: false }
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
    const chartTitle = document.getElementById('cpu-chart-title');
    const frequencyLabel = document.getElementById('cpu-frequency-label');
    const modeIndicator = document.getElementById('cpu-chart-mode-indicator');
    if (realtimeBtn && historicalBtn && historicalOptions) {
      realtimeBtn.style.background = '#4CAF50';
      realtimeBtn.style.color = 'white';
      historicalBtn.style.background = '#f5f5f5';
      historicalBtn.style.color = '#333';
      historicalOptions.style.display = 'none';
      if (chartTitle) chartTitle.textContent = 'Real-time CPU Usage';
      if (frequencyLabel) frequencyLabel.textContent = 'Data collected every 2 seconds';
      if (modeIndicator) modeIndicator.textContent = 'Real-time';
    }
  }

  switchToHistoricalMode() {
    const realtimeBtn = document.getElementById('cpu-realtime-btn');
    const historicalBtn = document.getElementById('cpu-historical-btn');
    const historicalOptions = document.getElementById('cpu-historical-options');
    const chartTitle = document.getElementById('cpu-chart-title');
    const frequencyLabel = document.getElementById('cpu-frequency-label');
    const modeIndicator = document.getElementById('cpu-chart-mode-indicator');
    if (realtimeBtn && historicalBtn && historicalOptions) {
      realtimeBtn.style.background = '#f5f5f5';
      realtimeBtn.style.color = '#333';
      historicalBtn.style.background = '#2196F3';
      historicalBtn.style.color = 'white';
      historicalOptions.style.display = 'flex';
      if (chartTitle) chartTitle.textContent = 'Historical CPU Usage';
      if (frequencyLabel) frequencyLabel.textContent = 'Historical data frequency varies';
      if (modeIndicator) modeIndicator.textContent = 'Historical';
    }
  }

  async loadHistoricalData() {
    // Same implementation pattern as inline version; depends on DOM ids
    try {
      const startTime = performance.now();
      const timeRange = document.getElementById('cpu-time-range').value;
      const resolution = document.getElementById('cpu-resolution').value;
      const response = await fetch(`/api/historical-chart?hours=${timeRange}&resolution=${resolution}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      const loadTime = performance.now() - startTime;
      // Update CPU chart datasets (global cpuChart from inline init)
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
    } catch (e) {
      console.warn('CPU chart auto-init skipped:', e);
    }
  });
}

