import { showToast, safeUpdateElement } from './app-core.js';
import { UnifiedMemoryChart } from './charts/hybrid-memory.js';

// expose fetchMemoryData so UnifiedMemoryChart can call it
window.fetchMemoryData = async function fetchMemoryData() {
  try {
    const response = await fetch('/api/current');
    if (!response.ok) throw new Error(`Failed to fetch data: ${response.statusText}`);
    const data = await response.json();

    if (data && data.clipboard) {
      // Pass through to inline updater if present
      if (typeof window.updateDashboard === 'function') {
        window.updateDashboard({
          ...data,
          clipboard: data.clipboard,
          analytics: data.analytics,
          system: data.system,
          session: data.session
        });
      }
    }
    return true;
  } catch (e) {
    console.error('Error fetching memory data:', e);
    return false;
  }
}

// bootstrap managers after DOM is loaded
window.addEventListener('DOMContentLoaded', async () => {
  window.chartManager = new UnifiedMemoryChart();
  window.cpuChartManager = new SimpleCPUChart();
  await window.chartManager.initialize();
});


// Analysis/system/monitoring migration
export async function fetchSystemData() {
  try {
    const response = await fetch('/api/system');
    const data = await response.json();
    if (data.system) {
      const s = data.system;
      const toFixed = (v) => (typeof v === 'number' ? v.toFixed(1) : v);
      const el = (id) => document.getElementById(id);
      const set = (id, val) => { const n = el(id); if (n) n.textContent = val; };
      set('header-system-memory', data.system.percent + '%');
      set('header-total-ram', toFixed(s.total_gb));
      set('header-available-ram', toFixed(s.available_gb));
    }
    if (data.cpu_percent !== undefined) {
      const el = document.getElementById('header-cpu-usage');
      if (el) el.textContent = data.cpu_percent + '%';
    }
    if (data.uptime) {
      const el = document.getElementById('header-uptime');
      if (el) el.textContent = data.uptime;
    }
  } catch (e) { console.error('Error fetching system data:', e); }
}

export async function loadAnalysisData() {
  try {
    if (typeof window.isTabActive === 'function' && !window.isTabActive('analysis')) return;
    if (window.analysisAbortController) window.analysisAbortController.abort();
    window.analysisAbortController = new AbortController();
    const signal = window.analysisAbortController.signal;
    const timeRangeElement = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
    const hours = timeRangeElement ? timeRangeElement.value : 24;
    const response = await fetch(`/api/analysis?hours=${hours}`, { signal });
    const data = await response.json();
    if (typeof window.updateAnalysisDisplay === 'function') window.updateAnalysisDisplay(data);
    const leakResponse = await fetch('/api/leak_analysis', { signal });
    const leakData = await leakResponse.json();
    if (typeof window.updateLeakAnalysisDisplay === 'function') window.updateLeakAnalysisDisplay(leakData);
    if (typeof window.updateSessionFindings === 'function') window.updateSessionFindings(data, leakData);
  } catch (e) {
    if (e.name !== 'AbortError') console.error('Error loading analysis data:', e);
  }
}

export async function toggleAdvancedMonitoring() {
  const toggleBtn = document.getElementById('monitoringToggleBtn');
  window.isMonitoringActive = window.isMonitoringActive || false;
  if (!window.isMonitoringActive) {
    try {
      const interval = document.getElementById('monitorInterval').value;
      const response = await fetch(`/api/start_advanced?interval=${interval}`);
      const result = await response.json();
      if (result.status === 'started') {
        window.isMonitoringActive = true;
        if (toggleBtn) {
          toggleBtn.style.background = '#f44336';
          toggleBtn.innerHTML = '🛑 Stop Advanced Monitoring';
          toggleBtn.style.animation = 'pulse 2s infinite';
        }
        showToast(`✅ ${result.message} — collecting every ${result.interval}s`, 'success');
        if (typeof window.updateMonitoringStatus === 'function') window.updateMonitoringStatus();
      }
    } catch (e) { showToast('❌ Error starting monitoring: ' + e, 'error'); }
  } else {
    try {
      const response = await fetch('/api/stop_advanced');
      const result = await response.json();
      if (result.status === 'stopped') {
        window.isMonitoringActive = false;
        if (toggleBtn) {
          toggleBtn.style.background = '#4CAF50';
          toggleBtn.innerHTML = '🚀 Start Advanced Monitoring';
          toggleBtn.style.animation = 'none';
        }
        const duration = result.duration_seconds ? Math.round(result.duration_seconds) : 0;
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        const durationText = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
        const dataPoints = result.data_points_collected || 0;
        showToast(`✅ ${result.message} — ${dataPoints} points in ${durationText}`, 'success');
        if (typeof window.updateMonitoringStatus === 'function') window.updateMonitoringStatus();
        await loadAnalysisData();
      }
    } catch (e) { showToast('❌ Error stopping monitoring: ' + e, 'error'); }
  }
}

// expose to window for onclick handlers
if (typeof window !== 'undefined') {
  window.fetchSystemData = fetchSystemData;
  window.loadAnalysisData = loadAnalysisData;
  window.toggleAdvancedMonitoring = toggleAdvancedMonitoring;
}
