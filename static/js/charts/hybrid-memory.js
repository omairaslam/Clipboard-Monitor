// Expect showToast from window (app-core.js)
const toastFn = (typeof window !== 'undefined' && window.showToast) ? window.showToast : function(){};

// Non-module build: expose UnifiedMemoryChart via window without redeclaring global symbol
const UMC = class {
  constructor() {
    this.mode = 'live';
    this.liveData = [];
    this.historicalData = null;
    this.isInitialized = false;
    this.currentLiveRange = '2m';
    this.currentTimeRange = '1';
    this.currentResolution = '1min';
    this.lastUpdateTime = 0;
    this.livePollTimer = null;
    this.livePollIntervalMs = 2000;
    this.livePollFailureCount = 0;
    this.liveErrorNotified = false;
    this.paused = false;
  }

  async initialize() {
    if (this.isInitialized) return;
    try {
      const savedMode = localStorage.getItem('umc_mode');
      if (savedMode === 'live' || savedMode === 'historical') {
        this.mode = savedMode;
      }
      const savedRange = localStorage.getItem('umc_live_range');
      if (savedRange) this.currentLiveRange = savedRange;
      const savedTimeRange = localStorage.getItem('umc_hist_range');
      if (savedTimeRange) this.currentTimeRange = savedTimeRange;
      const savedRes = localStorage.getItem('umc_hist_res');
      if (savedRes) this.currentResolution = savedRes;
    } catch {}

    await this.loadInitialLiveData();
    this.attachEventHandlers();
    this.startLivePolling();
    this.updateUI();
    this.isInitialized = true;
  }

  startLivePolling() {
    this.stopLivePolling();
    const tick = async () => {
      if (this.paused) return;
      const ok = await window.fetchMemoryData?.();
      if (ok) {
        this.livePollFailureCount = 0;
        if (this.livePollIntervalMs !== 2000) this.setLivePollInterval(2000);
        if (this.liveErrorNotified) { toastFn('✅ Connection restored', 'success', 1800); this.liveErrorNotified = false; }
      } else {
        this.livePollFailureCount += 1;
        let next = this.livePollIntervalMs;
        if (this.livePollFailureCount >= 3 && this.livePollIntervalMs < 5000) next = 5000;
        if (this.livePollFailureCount >= 6 && this.livePollIntervalMs < 10000) next = 10000;
        if (next !== this.livePollIntervalMs) this.setLivePollInterval(next);
        if (!this.liveErrorNotified && this.livePollFailureCount >= 3) { toastFn('⚠️ Connection issues: slowing updates', 'error', 2600); this.liveErrorNotified = true; }
      }
    };
    tick();
    this.livePollTimer = setInterval(tick, this.livePollIntervalMs);
  }

  stopLivePolling() {
    if (this.livePollTimer) { clearInterval(this.livePollTimer); this.livePollTimer = null; }
  }

  setLivePollInterval(ms) {
    this.livePollIntervalMs = ms;
    if (this.livePollTimer) { clearInterval(this.livePollTimer); this.livePollTimer = setInterval(async () => {
      if (this.paused) return;
      const ok = await window.fetchMemoryData?.();
      if (!ok) {
        this.livePollFailureCount += 1;
        if (!this.liveErrorNotified && this.livePollFailureCount >= 3) { toastFn('⚠️ Connection issues: slowing updates', 'error', 2600); this.liveErrorNotified = true; }
      } else {
        this.livePollFailureCount = 0;
        if (this.liveErrorNotified) { toastFn('✅ Connection restored', 'success', 1800); this.liveErrorNotified = false; }
      }
    }, this.livePollIntervalMs); }
  }

  async loadInitialLiveData() {
    try {
      const response = await fetch('/api/history');
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const historyData = await response.json();
      const formattedData = historyData.map(p => ({
        timestamp: p.timestamp,
        menubar_memory: p.menubar_memory || 0,
        service_memory: p.service_memory || 0,
        total_memory: (p.menubar_memory || 0) + (p.service_memory || 0),
      }));
      this.liveData = formattedData.slice(-200);
      this.updateChart();
    } catch (e) {
      console.warn('Failed to load initial live data:', e);
    }
  }

  attachEventHandlers() {
    const rangeSel = document.getElementById('live-range');
    if (rangeSel) {
      rangeSel.addEventListener('change', (e) => {
        this.currentLiveRange = e.target.value; localStorage.setItem('umc_live_range', this.currentLiveRange);
        this.updateChart();
      });
    }
  }

  updateChart() {
    // Placeholder: the actual chart drawing remains inline for now; this class manages data state and polling
    const headerDataPointsElement = document.getElementById('header-data-points');
    if (headerDataPointsElement) headerDataPointsElement.textContent = (this.liveData?.length || 0) + ' pts';
  }

  updateUI() {
    const chartModeIndicator = document.getElementById('chart-mode-indicator');
    if (chartModeIndicator) chartModeIndicator.textContent = this.mode === 'live' ? 'Live' : 'Historical';
  }
}

// Overlay events and anomalies onto Chart.js instance (exported and attached to window)
function overlayEventsAndAnomalies(chart, events = [], anomalies = []) {
  if (!chart) return;
  const plugs = chart.options.plugins = chart.options.plugins || {};
  plugs.annotation = plugs.annotation || { annotations: {} };
  const ann = plugs.annotation.annotations = plugs.annotation.annotations || {};
  anomalies.forEach((a, i) => {
    ann['anomaly_' + i] = {
      type: 'line',
      xMin: chart.data.labels.length - 1,
      xMax: chart.data.labels.length - 1,
      borderColor: '#e74c3c',
      borderWidth: 1,
      label: { display: true, content: a.type || 'anomaly', position: 'start', backgroundColor: 'rgba(231,76,60,0.1)' }
    };
  });
  events.slice(-3).forEach((e, i) => {
    ann['event_' + i] = {
      type: 'line',
      xMin: Math.max(0, chart.data.labels.length - (5 - i)),
      xMax: Math.max(0, chart.data.labels.length - (5 - i)),
      borderColor: '#3498db',
      borderWidth: 1,
      label: { display: true, content: e.type || 'event', backgroundColor: 'rgba(52,152,219,0.1)' }
    };
  });
  try { chart.update('none'); } catch {}
}

if (typeof window !== 'undefined') {
  window.overlayEventsAndAnomalies = overlayEventsAndAnomalies;
}

// Attach class to window for non-module usage
if (typeof window !== 'undefined') {
  if (!window.UnifiedMemoryChart) window.UnifiedMemoryChart = UMC;
}

