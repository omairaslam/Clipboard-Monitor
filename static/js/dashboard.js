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
  // Wait until inline script defines updateDashboard (attached to window in non-module scripts)
  const start = performance.now();
  while (!window.updateDashboard && performance.now() - start < 4000) {
    await new Promise(r => setTimeout(r, 50));
  }
  window.chartManager = window.chartManager || new UnifiedMemoryChart();
  await window.chartManager.initialize();
  // Kick a manual fetch in case the first poll ran before updateDashboard was ready
  setTimeout(() => { if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData(); }, 200);
  // CPU manager is initialized inline to ensure Chart canvas exists; we avoid double-init here
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

// Analysis renderers and monitoring status
export function updateAnalysisDisplay(data) {
  const leakAnalysis = document.getElementById('leak-analysis');
  const trendAnalysis = document.getElementById('trend-analysis');
  let leakHtml = '<div style="display: grid; gap: 12px;">';
  let trendHtml = '<div style="display: grid; gap: 12px;">';
  for (const [process, analysis] of Object.entries(data)) {
    const statusColor = analysis.severity === 'high' ? '#e74c3c' : analysis.severity === 'medium' ? '#f39c12' : '#27ae60';
    leakHtml += `
      <div style="padding: 15px; border-left: 4px solid ${statusColor}; background: rgba(0,0,0,0.05);">
        <h4>${process.replace('_', ' ').toUpperCase()}</h4>
        <p><strong>Status:</strong> <span style="color: ${statusColor};">${analysis.status}</span></p>
        <p><strong>Growth Rate:</strong> ${(analysis.growth_rate_mb?.toFixed(2) || 0)} MB/hour</p>
        <p><strong>Data Points:</strong> ${analysis.data_points || 0}</p>
      </div>`;
    trendHtml += `
      <div style="padding: 15px; background: rgba(0,0,0,0.05); border-radius: 8px;">
        <h4>${process.replace('_', ' ').toUpperCase()}</h4>
        <p><strong>Start Memory:</strong> ${(analysis.start_memory_mb?.toFixed(2) || 0)} MB</p>
        <p><strong>End Memory:</strong> ${(analysis.end_memory_mb?.toFixed(2) || 0)} MB</p>
        <p><strong>Total Growth:</strong> ${(analysis.total_growth_mb?.toFixed(2) || 0)} MB</p>
      </div>`;
  }
  leakHtml += '</div>'; trendHtml += '</div>';
  if (leakAnalysis) leakAnalysis.innerHTML = leakHtml;
  const trendContainer = document.getElementById('trend-analysis');
  if (trendContainer && trendContainer.dataset.init !== '1') trendContainer.innerHTML = trendHtml;
}

export function updateLeakAnalysisDisplay(leakData) {
  const leakAnalysis = document.getElementById('leak-analysis');
  if (!leakAnalysis) return;
  if (!leakData || Object.keys(leakData).length === 0) {
    leakAnalysis.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No leak analysis data available. Start advanced monitoring to collect data.</div>';
    return;
  }
  let html = '<div style="display: grid; gap: 12px;">';
  html += `<div style="padding: 10px; background: #e8f5e9; border-radius: 5px; margin-bottom: 15px;">
    <strong>🔍 Advanced Leak Detection Results</strong><br>
    <small>Based on advanced monitoring data collection</small>
  </div>`;
  for (const [key, analysis] of Object.entries(leakData)) {
    if (typeof analysis === 'object' && analysis.status) {
      const statusColor = analysis.severity === 'high' ? '#e74c3c' : analysis.severity === 'medium' ? '#f39c12' : '#27ae60';
      html += `
        <div style="padding: 15px; border-left: 4px solid ${statusColor}; background: rgba(0,0,0,0.05); border-radius: 5px;">
          <h4 style="margin: 0 0 10px 0;">${key.replace('_', ' ').toUpperCase()}</h4>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
              <p><strong>Status:</strong> <span style="color: ${statusColor};">${analysis.status}</span></p>
              <p><strong>Severity:</strong> <span style="color: ${statusColor};">${analysis.severity}</span></p>
            </div>
            <div>
              <p><strong>Growth Rate:</strong> ${(analysis.growth_rate_mb?.toFixed(2) || 0)} MB/hour</p>
              <p><strong>Snapshots:</strong> ${analysis.snapshots_analyzed || 0}</p>
            </div>
          </div>
        </div>`;
    }
  }
  html += '</div>';
  leakAnalysis.innerHTML = html;
}

export function updateAnalysisSummary(data, hours) {
  const summaryDiv = document.getElementById('analysis-summary');
  if (!summaryDiv) return;
  const processCount = Object.keys(data).length;
  const highSeverityCount = Object.values(data).filter(d => d.severity === 'high').length;
  const mediumSeverityCount = Object.values(data).filter(d => d.severity === 'medium').length;
  const html = `
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
      <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
        <div style="font-size: 12px; color: #666;">Processes Analyzed</div>
        <div style="font-size: 24px; font-weight: bold;">${processCount}</div>
      </div>
      <div style="background: #fff5f5; padding: 10px; border-radius: 5px;">
        <div style="font-size: 12px; color: #666;">High Severity</div>
        <div style="font-size: 24px; font-weight: bold; color: #e74c3c;">${highSeverityCount}</div>
      </div>
      <div style="background: #fffaf0; padding: 10px; border-radius: 5px;">
        <div style="font-size: 12px; color: #666;">Medium Severity</div>
        <div style="font-size: 24px; font-weight: bold; color: #f39c12;">${mediumSeverityCount}</div>
      </div>
    </div>
    <div style="margin-top: 10px; font-size: 12px; color: #666;">Time Range: Last ${hours} hours</div>`;
  summaryDiv.innerHTML = html;
}

export function updateMonitoringHistory() {
  const historyDiv = document.getElementById('monitoring-history');
  if (!historyDiv) return;
  const html = `
    <div style="padding: 15px; background: #f8f9fa; border-radius: 5px;">
      <p><strong>📈 Monitoring Sessions:</strong></p>
      <div style="margin-top: 10px;">
        <div style="padding: 10px; background: white; border-radius: 3px; margin-bottom: 5px;">
          <strong>Current Session:</strong> ${new Date().toLocaleDateString()}<br>
          <small>Advanced monitoring data available for analysis</small>
        </div>
      </div>
      <p style="margin-top: 15px; color: #666; font-size: 14px;"><strong>💡 Tip:</strong> Use the Advanced Monitoring Controls above to collect more detailed analysis data.</p>
    </div>`;
  historyDiv.innerHTML = html;
}

export function updateSessionFindings(analysisData, leakData) {
  const container = document.getElementById('session-findings');
  if (!container) return;
  const hasLeakData = leakData && Object.keys(leakData).some(k => leakData[k] && leakData[k].status);
  const hasAnalysis = analysisData && Object.keys(analysisData).length > 0;
  if (!hasLeakData && !hasAnalysis) {
    container.innerHTML = '<div style="padding: 12px; color: #666;">No session findings yet. Start Advanced Monitoring and stop to analyze the last session.</div>';
    return;
  }
  const entries = [];
  const pushEntry = (name, a, l) => {
    if (!a && !l) return;
    const growth = (a && a.growth_rate_mb) ?? (l && l.growth_rate_mb) ?? 0;
    const totalGrowth = (a && a.total_growth_mb) ?? 0;
    const points = (a && a.data_points) ?? (l && l.snapshots_analyzed) ?? 0;
    const severity = (l && l.severity) || (a && a.severity) || 'low';
    entries.push({ name, growth, totalGrowth, points, severity });
  };
  pushEntry('Menu Bar App', analysisData.menu_bar_app, leakData.menu_bar_app);
  pushEntry('Main Service', analysisData.main_service, leakData.main_service);
  pushEntry('Total Memory', analysisData.total_memory, leakData.total_memory);
  const sevColor = (s) => s === 'high' ? '#e74c3c' : s === 'medium' ? '#f39c12' : '#27ae60';
  let html = '<div style="display: grid; gap: 10px;">';
  for (const e of entries) {
    html += `
      <div style="padding: 10px; background: white; border-left: 4px solid ${sevColor(e.severity)}; border-radius: 5px;">
        <div style="display:flex; justify-content: space-between;">
          <strong>${e.name}</strong>
          <span style="color: ${sevColor(e.severity)}; text-transform: uppercase; font-size: 12px;">${e.severity}</span>
        </div>
        <div style="font-size: 12px; color: #666;">Avg Growth: ${(e.growth || 0).toFixed(2)} MB/hour • Total Growth: ${(e.totalGrowth || 0).toFixed(2)} MB • Points: ${e.points}</div>
      </div>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

export async function updateMonitoringStatus() {
  try {
    const response = await fetch('/api/current');
    const data = await response.json();
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const dataPointsSpan = document.getElementById('data-points');
    const collectionRateSpan = document.getElementById('collection-rate');
    const toggleBtn = document.getElementById('monitoringToggleBtn');
    const isActive = data.long_term_monitoring && data.long_term_monitoring.status === 'active';
    if (statusIndicator) statusIndicator.style.background = isActive ? '#4caf50' : '#ccc';
    if (statusText) statusText.textContent = isActive ? 'ACTIVE' : 'INACTIVE';
    if (dataPointsSpan) dataPointsSpan.textContent = data.long_term_monitoring?.data_points || 0;
    if (collectionRateSpan) collectionRateSpan.textContent = isActive ? `${data.long_term_monitoring?.interval || 0}s` : 'Stopped';
    if (toggleBtn) {
      if (isActive && !window.isMonitoringActive) {
        window.isMonitoringActive = true;
        toggleBtn.style.background = '#f44336';
        toggleBtn.innerHTML = '🛑 Stop Advanced Monitoring';
        toggleBtn.style.animation = 'pulse 2s infinite';
      } else if (!isActive && window.isMonitoringActive) {
        window.isMonitoringActive = false;
        toggleBtn.style.background = '#4CAF50';
        toggleBtn.innerHTML = '🚀 Start Advanced Monitoring';
        toggleBtn.style.animation = 'none';
      }
    }
  } catch (e) {
    console.error('Error updating monitoring status:', e);
    const statusText = document.getElementById('status-text');
    const lastUpdateSpan = document.getElementById('last-update');
    if (statusText) statusText.textContent = 'ERROR';
    if (lastUpdateSpan) lastUpdateSpan.textContent = 'Error fetching status';
  }
}

if (typeof window !== 'undefined') {
  window.updateAnalysisDisplay = updateAnalysisDisplay;
  window.updateLeakAnalysisDisplay = updateLeakAnalysisDisplay;
  window.updateAnalysisSummary = updateAnalysisSummary;
  window.updateMonitoringHistory = updateMonitoringHistory;
  window.updateSessionFindings = updateSessionFindings;
  window.updateMonitoringStatus = updateMonitoringStatus;
}
