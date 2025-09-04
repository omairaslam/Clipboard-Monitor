// Non-module version: use globals from app-core.js and hybrid-memory.js

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
    // Health score (server-computed)
    if (data && data.health && typeof data.health.score === 'number') {
      const el = document.getElementById('header-health-score');
      if (el) el.textContent = data.health.score.toFixed(1) + '%';
      const banner = document.getElementById('health-banner');
      if (banner) {
        const s = data.health.score;
        banner.style.background = s >= 80 ? '#e8f5e9' : s >= 60 ? '#fff8e1' : '#ffebee';
        banner.style.borderLeft = '4px solid ' + (s >= 80 ? '#4CAF50' : s >= 60 ? '#f39c12' : '#e74c3c');
      }
    }

    }
    return true;
  } catch (e) {
    if (window.CM_DEBUG) console.error('Error fetching memory data:', e);
    return false;
  }
}

// bootstrap managers after DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
  // Wait until inline script defines updateDashboard (attached to window in non-module scripts)
  const start = performance.now();
  const boot = () => {
    if (!window.updateDashboard && performance.now() - start < 4000) {
      setTimeout(boot, 50);
      return;
    }
    if (window.UnifiedMemoryChart) {
      window.chartManager = window.chartManager || new window.UnifiedMemoryChart();
      if (typeof window.chartManager.initialize === 'function') {
        window.chartManager.initialize().then(() => {
          setTimeout(() => { if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData(); }, 200);
        }).catch(() => {});
      }
    } else {
      if (window.CM_DEBUG) console.warn('UnifiedMemoryChart not defined yet; skipping chart init');
    }
  };
  boot();
  // CPU manager is initialized inline to ensure Chart canvas exists; we avoid double-init here
  // Kick Top Offenders once on load to clear the loading placeholder even if analysis is empty
  setTimeout(() => {
    try {
      const sel = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
      const hours = sel ? sel.value : 24;
      if (typeof updateTopOffenders === 'function') updateTopOffenders(hours);
    } catch {}
  }, 800);
});


// Analysis/system/monitoring migration
async function fetchSystemData() {
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
  } catch (e) { if (window.CM_DEBUG) console.error('Error fetching system data:', e); }
}
// expose functions used by inline scripts
if (typeof window !== 'undefined') {
  window.fetchSystemData = fetchSystemData;
  window.loadAnalysisData = loadAnalysisData;
}

// Safely parse JSON; returns {} on empty/invalid bodies
async function readJsonSafe(response) {
  try {
    const ct = response.headers.get('content-type') || '';
    const text = await response.text();
    if (!text || !text.trim()) return {};
    if (ct.includes('application/json') || text.trim().startsWith('{') || text.trim().startsWith('[')) {
      try { return JSON.parse(text); } catch (e) { if (window.CM_DEBUG) console.error('Invalid JSON body', e, text.slice(0, 200)); return {}; }
    }
    if (window.CM_DEBUG) console.warn('Non-JSON response body', text.slice(0, 200));
    return {};
  } catch (e) {
    if (window.CM_DEBUG) console.error('Failed to read body', e);
    return {};
  }
}


async function loadAnalysisData() {
  try {
    if (typeof window.isTabActive === 'function' && !window.isTabActive('analysis')) return;
    if (window.analysisAbortController) window.analysisAbortController.abort();
    window.analysisAbortController = new AbortController();
    const signal = window.analysisAbortController.signal;
    const timeRangeElement = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
    const hours = timeRangeElement ? timeRangeElement.value : 24;
    const response = await fetch(`/api/analysis?hours=${hours}`, { signal });
    const data = await readJsonSafe(response);
    if (typeof window.updateAnalysisDisplay === 'function') window.updateAnalysisDisplay(data);
    const leakResponse = await fetch('/api/leak_analysis', { signal });
    const leakData = await readJsonSafe(leakResponse);
    if (typeof window.updateLeakAnalysisDisplay === 'function') window.updateLeakAnalysisDisplay(leakData);
    if (typeof window.updateSessionFindings === 'function') window.updateSessionFindings(data, leakData);
    // Update Top Offenders based on the same hours range
    try { await updateTopOffenders(hours); } catch {}

  } catch (e) {
    if (e.name !== 'AbortError' && window.CM_DEBUG) console.error('Error loading analysis data:', e);
  }
}

async function updateTopOffenders(hours) {
  try {
    const container = document.getElementById('top-offenders');
    if (!container) return;
    const resp = await fetch(`/api/top_offenders?hours=${hours || '24'}`);
    const data = await readJsonSafe(resp);
    const list = Array.isArray(data) ? data : (Array.isArray(data?.offenders) ? data.offenders : []);
    if (!list.length) {
      container.innerHTML = '<div style="padding:10px; color:#666;">No offenders found for this range.</div>';
      return;
    }
    const top = list.slice(0, 5);
    let html = '<div style="display:grid; gap:8px;">';
    for (const o of top) {
      const name = o.name || o.label || 'Unknown';
      const growth = Number(o.growth_mb ?? o.total_growth_mb ?? 0);
      const rate = Number(o.growth_rate_mb ?? 0);
      const points = Number(o.points ?? o.data_points ?? 0);
      const sev = (o.severity || (growth > 50 ? 'high' : growth > 10 ? 'medium' : 'low'));
      const sevColor = sev === 'high' ? '#e74c3c' : sev === 'medium' ? '#f39c12' : '#27ae60';
      html += `
        <div style="padding:10px; background:#fff; border-left:4px solid ${sevColor}; border-radius:5px;">
          <div style="display:flex; justify-content:space-between;">
            <strong>${name}</strong>
            <span style="color:${sevColor}; text-transform:uppercase; font-size:12px;">${sev}</span>
          </div>
          <div style="font-size:12px; color:#666;">Total Growth: ${growth.toFixed(2)} MB • Rate: ${rate.toFixed(2)} MB/h • Points: ${points}</div>
        </div>`;
    }
    html += '</div>';
    container.innerHTML = html;
  } catch (e) {
    if (window.CM_DEBUG) console.error('Failed to update top offenders', e);
    const container = document.getElementById('top-offenders');
    if (container) container.innerHTML = '<div style="padding:10px; color:#B00020;">Failed to load top offenders</div>';
  }
}


async function toggleAdvancedMonitoring() {
  const toggleBtn = document.getElementById('monitoringToggleBtn');
  const toggleBtnMini = document.getElementById('monitoringToggleBtnMini');
  window.isMonitoringActive = window.isMonitoringActive || false;
  if (!window.isMonitoringActive) {
    try {
      const interval = document.getElementById('monitorInterval').value;
      const response = await fetch(`/api/start_monitoring?interval=${interval}`);
      const result = await response.json();
      if (result.status === 'started') {
        window.isMonitoringActive = true;
        if (toggleBtn) {
          toggleBtn.style.background = '#f44336';
          toggleBtn.innerHTML = '🛑 Stop Advanced Monitoring';
          toggleBtn.style.animation = 'pulse 2s infinite';
        }
        if (toggleBtnMini) {
          toggleBtnMini.style.background = '#f44336';
          toggleBtnMini.textContent = '🛑 Stop';
          toggleBtnMini.style.animation = 'pulse 2s infinite';
        }
        // Immediate badge flip for responsiveness; periodic status will keep it in sync
        const badge = document.getElementById('advanced-status');
        if (badge) {
          if (typeof window.updateAdvancedStatus === 'function') window.updateAdvancedStatus(true);
          else { badge.textContent = '🔴 Advanced'; badge.style.background = '#F44336'; }
        }
        // Start countdown immediately
        window.__liveCountdown = window.__liveCountdown || { active: false, interval: 30, remaining: 0, timerId: null, lastPoints: 0 };
        window.__liveCountdown.active = true;
        window.__liveCountdown.interval = Number(interval) || 30;
        window.__liveCountdown.remaining = window.__liveCountdown.interval;
        showToast(`✅ ${result.message} — collecting every ${result.interval}s`, 'success');
        if (typeof window.updateMonitoringStatus === 'function') window.updateMonitoringStatus();
      }
    } catch (e) { showToast('❌ Error starting monitoring: ' + e, 'error'); }
  } else {
    try {
      const response = await fetch('/api/stop_monitoring');
      const result = await response.json();
      if (result.status === 'stopped') {
        window.isMonitoringActive = false;
        if (toggleBtn) {
          toggleBtn.style.background = '#4CAF50';
          toggleBtn.innerHTML = '🚀 Start Advanced Monitoring';
          toggleBtn.style.animation = 'none';
        }
        if (toggleBtnMini) {
          toggleBtnMini.style.background = '#4CAF50';
          toggleBtnMini.textContent = '🚀 Start';
          toggleBtnMini.style.animation = 'none';
        }
        // Immediate badge flip off
        const badge = document.getElementById('advanced-status');
        if (badge) {
          if (typeof window.updateAdvancedStatus === 'function') window.updateAdvancedStatus(false);
          else { badge.textContent = '⚫ Advanced'; badge.style.background = '#999'; }
        }
        // Stop countdown
        if (window.__liveCountdown) { window.__liveCountdown.active = false; window.__liveCountdown.remaining = 0; }
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
function updateAnalysisDisplay(data) {
  const trendAnalysis = document.getElementById('trend-analysis');
  if (window.CM_DEBUG) console.log('[analysis] renderer: updateAnalysisDisplay');
  if (!data || typeof data !== 'object') {
    const msg = '<div style="color:#e74c3c; padding:10px;">❌ Unexpected analysis payload</div>';
    if (trendAnalysis) trendAnalysis.innerHTML = msg;
    return;
  }
  if (Object.keys(data).length === 0) {
    if (trendAnalysis) {
      const loading = trendAnalysis.querySelector('.loading');
      if (loading) loading.remove();
      trendAnalysis.innerHTML = '<div style="padding:12px; color:#666;">No analysis data yet. Start Advanced Monitoring and let it collect for a minute, then stop to analyze.</div>';
    }
    return;
  }

  let trendHtml = '<div class="grid-3-12" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px;">';
  for (const [process, analysis] of Object.entries(data)) {
    const statusColor = analysis.severity === 'high' ? '#e74c3c' : analysis.severity === 'medium' ? '#f39c12' : '#27ae60';
    const sparklineId = `sparkline-${process}`;
    trendHtml += `
      <div style="padding: 15px; background: rgba(0,0,0,0.05); border-radius: 8px;">
        <h4>${process.replace(/_/g, ' ').toUpperCase()}</h4>
        <p><strong>Status:</strong> <span style="color: ${statusColor};">${analysis.status}</span></p>
        <p><strong>Start Memory:</strong> ${(analysis.start_memory_mb?.toFixed(2) || 0)} MB</p>
        <p><strong>End Memory:</strong> ${(analysis.end_memory_mb?.toFixed(2) || 0)} MB</p>
        <p><strong>Total Growth:</strong> ${(analysis.total_growth_mb?.toFixed(2) || 0)} MB</p>
        <p><strong>Growth Rate:</strong> ${(analysis.growth_rate_mb?.toFixed(2) || 0)} MB/hour</p>
        <p><strong>Data Points:</strong> ${analysis.data_points || 0}</p>
        <div class="sparkline-container" style="height: 50px; margin-top: 10px;">
          <canvas id="${sparklineId}"></canvas>
        </div>
      </div>`;
  }
  trendHtml += '</div>';

  const trendContainer = document.getElementById('trend-analysis');
  if (trendContainer) {
    const loading = trendContainer.querySelector('.loading');
    if (loading) loading.remove();

    let cards = document.getElementById('trend-cards');
    if (!cards) {
      cards = document.createElement('div');
      cards.id = 'trend-cards';
      trendContainer.appendChild(cards);
    }
    cards.innerHTML = trendHtml;

    // Draw sparklines after a short delay to ensure canvases are in the DOM
    setTimeout(() => {
      for (const [process, analysis] of Object.entries(data)) {
        if (analysis.sparkline && analysis.sparkline.length > 0) {
          const sparklineId = `sparkline-${process}`;
          drawSparkline(sparklineId, analysis.sparkline, '#2196F3');
        }
      }
    }, 100);
  }
}

function drawSparkline(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(data.length).fill(''),
            datasets: [{
                data: data,
                borderColor: color,
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

function updateLeakAnalysisDisplay(leakData) {
  const leakAnalysis = document.getElementById('leak-analysis');
  if (!leakAnalysis) return;

  const header = (meta, extra = '') => {
    const parts = [];
    if (meta) {
      const on = meta.monitoring_active ? '🟢' : '⚪️';
      parts.push(`${on} Monitoring ${meta.monitoring_active ? 'Active' : 'Inactive'}`);
      if (typeof meta.advanced_points === 'number') parts.push(`Advanced points: ${meta.advanced_points}`);
      if (typeof meta.snapshots_total === 'number') parts.push(`Snapshots: ${meta.snapshots_total}`);
      if (typeof meta.interval === 'number') parts.push(`Interval: ${meta.interval}s`);
    }
    const snapshotsCountHeader = Number((meta?.snapshots_total ?? meta?.snapshots_analyzed ?? 0));
    const dotIconHeader = (snapshotsCountHeader >= 2)
      ? '<span title="Ready: sufficient snapshots for trend analysis" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#2ecc71;box-shadow:0 0 0 0 rgba(46,204,113,0.7);animation:pulseDot 1.6s infinite;margin-right:6px;vertical-align:middle;"></span>'
      : '<span title="Not ready: collecting snapshots" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#bbb;margin-right:6px;vertical-align:middle;"></span>';
    const metaLine = `<div style="margin-top:4px; font-size:11px; color:#2b5a3a; display:flex; align-items:center; gap:8px;">${dotIconHeader}<span>${parts.join(' • ')}</span>${extra}</div>`;
    return `<div style="padding: 10px; background: #e8f5e9; border-radius: 5px; margin-bottom: 15px;">
      <strong>🔍 Advanced Leak Detection Results</strong><br>
      <small>Based on advanced monitoring data collection</small>
      ${metaLine}
    </div>`;
  };

  const extractMeta = (obj) => ({
    monitoring_active: obj?.monitoring_active,
    advanced_points: obj?.advanced_points,
    snapshots_total: obj?.snapshots_total,
    interval: obj?.interval,
  });

  // Also update the top meta line (always-on banner under Growth Trend Analysis)
  try {
    const metaTop = document.getElementById('analysis-top-meta');
    if (metaTop && leakData) {
      const metaA = extractMeta(leakData);
      const parts = [];
      const snapshotsCount = Number((metaA && (metaA.snapshots_total ?? leakData.snapshots_analyzed)) ?? 0);
      const dotIcon = (snapshotsCount >= 2)
        ? '<span title="Ready: sufficient snapshots for trend analysis" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#2ecc71;box-shadow:0 0 0 0 rgba(46,204,113,0.7);animation:pulseDot 1.6s infinite;margin-right:6px;vertical-align:middle;"></span>'
        : '<span title="Not ready: collecting snapshots" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#bbb;margin-right:6px;vertical-align:middle;"></span>';
      if (metaA && metaA.monitoring_active !== undefined) parts.push(`Monitoring: ${metaA.monitoring_active ? 'Active' : 'Inactive'}`);
      if (metaA && typeof metaA.advanced_points === 'number') parts.push(`Advanced points: ${metaA.advanced_points}`);
      if (!Number.isNaN(snapshotsCount)) parts.push(`Snapshots: ${snapshotsCount}`);
      if (metaA && typeof metaA.interval === 'number') parts.push(`Interval: ${metaA.interval}s`);

      // Optional: include trend badge in top meta when available
      try {
        const delta = Number(((leakData?.end_memory_mb ?? 0) - (leakData?.start_memory_mb ?? 0)) || 0);
        const rate = (leakData?.growth_rate_mb?.toFixed?.(2) ?? null);
        if (!Number.isNaN(delta) && rate !== null) {
          const badge = `<span style="background:#eef7ff; color:#266eb6; border:1px solid #cfe8ff; padding:2px 6px; border-radius:6px; font-size:11px; margin-left:8px;">${delta>=0?'+':''}${delta.toFixed(2)} MB · ${rate} MB/h</span>`;
          metaTop.innerHTML = dotIcon + parts.join(' • ') + badge;
        }
      } catch {}

      metaTop.innerHTML = dotIcon + parts.join(' • ');
      metaTop.style.display = (parts.length || dotIcon) ? 'block' : 'none';
      if (window.CM_DEBUG) console.log('[analysis] metaTop', { snapshotsCount, metaA });
    }
  } catch {}

  const showMsg = (msg, meta) => {
    leakAnalysis.innerHTML = header(meta) + `<div style="padding: 20px; text-align: center; color: #666;">${msg}</div>`;
  };

  if (!leakData || Object.keys(leakData).length === 0) {
    showMsg('No leak analysis data available. Start Advanced Monitoring and let it run for a minute.');
    return;
  }

  // Shape A: flat object with status/severity fields (+ meta fields)
  if (typeof leakData === 'object' && typeof leakData.status === 'string') {
    const status = leakData.status;
    const severity = leakData.severity || 'low';
    const statusColor = severity === 'high' ? '#e74c3c' : severity === 'medium' ? '#f39c12' : '#27ae60';
    const meta = extractMeta(leakData);

    if (status === 'insufficient_data') {
      showMsg('Insufficient monitoring data yet. Start Advanced Monitoring and let it run for a minute, then refresh.', meta);
      return;
    }
    if (status === 'analyzing') {
      showMsg('Analyzing… Please wait while more samples are collected.', meta);
      return;
    }

    // Trend badge and copy icon
    const delta = ((leakData.end_memory_mb ?? 0) - (leakData.start_memory_mb ?? 0)) || 0;
    const rate = (leakData.growth_rate_mb?.toFixed?.(2) ?? 0);
    const trendBadge = `<span style="background:#eef7ff; color:#266eb6; border:1px solid #cfe8ff; padding:2px 6px; border-radius:6px; font-size:11px;">${delta>=0?'+':''}${(delta).toFixed(2)} MB · ${rate} MB/h</span>`;
    const copyIcon = `<span id="copy-analysis-meta" title="Copy analysis meta" style="cursor:pointer; font-size:12px; color:#266eb6;">📋</span>`;

    const html = `
      ${header(meta, `<span style="display:flex; align-items:center; gap:8px;">${trendBadge}${copyIcon}</span>`)}
      <div style="padding: 15px; border-left: 4px solid ${statusColor}; background: rgba(0,0,0,0.05); border-radius: 5px;">
        <h4 style="margin: 0 0 10px 0;">OVERALL</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div>
            <p><strong>Status:</strong> <span style="color: ${statusColor};">${status}</span></p>
            <p><strong>Severity:</strong> <span style="color: ${statusColor};">${severity}</span></p>
          </div>
          <div>
            <p><strong>Growth Rate:</strong> ${(leakData.growth_rate_mb?.toFixed?.(2) ?? 0)} MB/hour</p>
            <p><strong>Snapshots:</strong> ${leakData.snapshots_analyzed || 0}</p>
          </div>
        </div>
      </div>`;
    leakAnalysis.innerHTML = html;
    return;
  }

    // Copy handler
    try {
      const btn = document.getElementById('copy-analysis-meta');
      if (btn) {
        btn.onclick = async () => {
          const metaTop = document.getElementById('analysis-top-meta');
          const text = metaTop ? metaTop.textContent : '';
          try {
            await navigator.clipboard.writeText(text);
            showToast('✅ Copied analysis meta', 'success');
          } catch (e) {
            showToast('❌ Failed to copy meta: ' + e, 'error');
          }
        };
      }
    } catch {}


  // Shape B: per-process object map
  let rendered = 0;
  let metaFromAny = null;
  let html = '<div style="display: grid; gap: 12px;">';
  for (const [key, analysis] of Object.entries(leakData)) {
    if (!metaFromAny) metaFromAny = extractMeta(analysis);
    if (analysis && typeof analysis === 'object' && 'status' in analysis) {
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
              <p><strong>Growth Rate:</strong> ${(analysis.growth_rate_mb?.toFixed?.(2) ?? 0)} MB/hour</p>
              <p><strong>Snapshots:</strong> ${analysis.snapshots_analyzed || 0}</p>
            </div>
          </div>
        </div>`;
      rendered++;
    }
  }
  html = header(metaFromAny) + html + '</div>';

  if (rendered === 0) {
    showMsg('No renderable leak results yet. Start Advanced Monitoring and try again shortly.', metaFromAny);
    return;
  }

  leakAnalysis.innerHTML = html;
}

function updateAnalysisSummary(data, hours) {
  const summaryDiv = document.getElementById('analysis-summary');
  if (!summaryDiv) return;
  // Cache last analysis payload for fallback
  window.__lastAnalysisData = data;
  window.__lastAnalysisHours = hours;

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

  // Fallback: if still showing loading soon after, trigger a reload
  setTimeout(() => {
    const s = document.getElementById('analysis-summary');
    if (!s) return;
    const txt = (s.textContent || '').toLowerCase();
    if (txt.includes('loading')) {
      window.loadAnalysisData?.();
    }
  }, 1500);
}

function updateMonitoringHistory() {
  const historyDiv = document.getElementById('monitoring-history');
  if (!historyDiv) return;
  // If we have cached analysis data, show counts to avoid an empty feel
  const cached = window.__lastAnalysisData;
  const html = `
    <div style="padding: 15px; background: #f8f9fa; border-radius: 5px;">
      <p><strong>📈 Monitoring Sessions:</strong></p>
      ${cached ? `<div style='font-size:12px; color:#666;'>Showing recent analysis (${Object.keys(cached).length} processes)</div>` : ''}
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

function updateSessionFindings(analysisData, leakData) {
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

async function updateMonitoringStatus() {
  try {
    const response = await fetch('/api/current');
    const data = await response.json();

    // Support both payload shapes: monitoring_status (new) and long_term_monitoring (compat)
    const ms = data.monitoring_status || data.long_term_monitoring || {};
    const isActive = (ms.status === 'active') || (ms.active === true);
    const interval = ms.interval || 0;
    const advPoints = (typeof ms.data_points === 'number') ? ms.data_points : (ms.advanced_data_points || 0);

    // Update always-on top analysis readiness badge
    try {
      const readyDot = document.getElementById('analysis-ready-dot');
      const readyText = document.getElementById('analysis-ready-text');
      const snapshots = Number((data.snapshots_total ?? data.snapshots_analyzed ?? 0));
      const ready = snapshots >= 2;
      if (readyDot) {
        readyDot.style.background = ready ? '#2ecc71' : '#bbb';
        readyDot.style.animation = ready ? 'pulseDot 1.6s infinite' : 'none';
        readyDot.title = ready ? 'Ready: sufficient snapshots for trend analysis' : 'Not ready: collecting snapshots';
      }
      if (readyText) readyText.textContent = ready ? 'Ready' : 'Not ready';
    } catch {}

    // Controls panel widgets
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const dataPointsSpan = document.getElementById('advanced-data-points');
    const collectionRateSpan = document.getElementById('collection-rate');
    const toggleBtn = document.getElementById('monitoringToggleBtn');

    if (statusIndicator) statusIndicator.style.background = isActive ? '#4caf50' : '#ccc';
    if (statusText) statusText.textContent = isActive ? 'ACTIVE' : 'INACTIVE';


    // Top bar analysis-ready badge text update + one-time toast
    try {
      const readyText = document.getElementById('analysis-ready-text');
      if (readyText) {
        const current = await (await fetch('/api/leak_analysis')).json();
        const snaps = Number(current.snapshots_total ?? current.snapshots_analyzed ?? 0);
        const wasReady = window.__analysisReadyOnce === true;
        const isReady = snaps >= 2;
        readyText.textContent = isReady ? 'Ready' : 'Not ready';
        if (!wasReady && isReady) {
          window.__analysisReadyOnce = true;
          showToast('✅ Analysis ready: sufficient snapshots collected', 'success');
        }
      }
    } catch {}

    // Top banner badge
    const advancedBadge = document.getElementById('advanced-status');
    if (advancedBadge) {
      if (typeof window.updateAdvancedStatus === 'function') window.updateAdvancedStatus(isActive);
      else {
        advancedBadge.textContent = isActive ? '🔴 Advanced' : '⚫ Advanced';
        advancedBadge.style.background = isActive ? '#F44336' : '#999';
      }
    }

    if (dataPointsSpan) dataPointsSpan.textContent = advPoints;
    if (collectionRateSpan) collectionRateSpan.textContent = isActive ? `${interval}s` : 'Stopped';

    // Mirror into Live Collection strip (mini banner)
    const liveDot = document.getElementById('live-status-dot');
    const liveText = document.getElementById('live-status-text');
    const liveInterval = document.getElementById('live-interval');
    const liveNext = document.getElementById('live-next');
    const livePts = document.getElementById('live-adv-points');
    const liveDuration = document.getElementById('live-duration');
    let liveLastInc = document.getElementById('live-last-inc');
    if (!liveLastInc) {
      // Retro-fit missing element if server HTML is older
      const lastSample = document.getElementById('live-last-sample');
      if (lastSample && lastSample.parentElement) {
        const div = document.createElement('div');
        div.id = 'live-last-inc';
        div.style.cssText = 'margin-top:2px; font-size:12px; color:#666; font-variant-numeric: tabular-nums;';
        div.innerHTML = '<em>Last inc: --</em>';
        lastSample.parentElement.insertBefore(div, lastSample.nextSibling);
        liveLastInc = div;
      }
    }

    if (liveDot) liveDot.style.background = isActive ? '#4CAF50' : '#ccc';
    if (liveText) liveText.textContent = isActive ? 'ACTIVE' : 'INACTIVE';
    if (liveInterval) liveInterval.textContent = isActive ? `Every ${interval}s` : 'Stopped';

    // Total session points in title + tooltip
    if (livePts) {
      livePts.textContent = String(advPoints);
      const lastInc = window.__lastAdvPointsTimestamp ? new Date(window.__lastAdvPointsTimestamp) : null;
      if (lastInc) {
        const t = lastInc.toLocaleTimeString();
        livePts.setAttribute('title', `Last increment at ${t}`);
        if (liveLastInc) liveLastInc.innerHTML = `<em>Last inc: ${t}</em>`;
      } else {
        livePts.removeAttribute('title');
        if (liveLastInc) liveLastInc.innerHTML = '<em>Last inc: --</em>';
      }
    }

    // Compute duration from start_time if available
    const startIso = ms.start_time || null;
    if (startIso && liveDuration) {
      const start = new Date(startIso).getTime();
      const now = Date.now();
      const hours = Math.max(0, (now - start) / 3600000);
      liveDuration.textContent = hours.toFixed(2) + 'h';
    } else if (liveDuration) {
      liveDuration.textContent = '0.00h';
    }

    // Initialize/reset countdown for next sample (approximate)
    window.__liveCountdown = window.__liveCountdown || { active: false, interval: 30, remaining: 0, timerId: null, lastPoints: 0 };
    const lc = window.__liveCountdown;
    if (isActive) {
      lc.active = true;
      lc.interval = interval || lc.interval || 30;
      // Reset remaining periodically to avoid drift
      if (!lc.remaining || lc.remaining <= 0 || (typeof advPoints === 'number' && advPoints !== lc.lastPoints)) {
        lc.remaining = lc.interval;
        lc.lastPoints = advPoints;
      }
      if (liveNext) liveNext.textContent = formatCountdown(lc.remaining);
    } else {
      lc.active = false;
      lc.remaining = 0;
      if (liveNext) liveNext.textContent = '--';
    }

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

    // Tooltips for clarity
    if (liveNext) liveNext.setAttribute('title', 'Next sample ETA (approx)');
    if (liveInterval) liveInterval.setAttribute('title', 'Server-configured interval');

    // Last sample timestamp
    const lastSampleDiv = document.getElementById('live-last-sample');
    if (lastSampleDiv && data && data.timestamp) {
      try {
        const t = new Date(data.timestamp);
        lastSampleDiv.textContent = `Last sample: ${t.toLocaleTimeString()}`;
      } catch {}
    }

    // Flash points when they increase
    if (typeof window.__lastAdvPoints !== 'number') window.__lastAdvPoints = advPoints;
    if (advPoints > window.__lastAdvPoints) {
      if (livePts) {

// One-time toast when analysis becomes ready
if (typeof window !== 'undefined') {
  if (!window.__analysisReadyOnce) window.__analysisReadyOnce = false;
}

        livePts.classList.add('point-flash');
        setTimeout(() => livePts.classList.remove('point-flash'), 400);
      }
      window.__lastAdvPoints = advPoints;
      window.__lastAdvPointsTimestamp = Date.now();
      // Refresh tooltip immediately
      try {
        livePts.setAttribute('title', `Last increment at ${new Date(window.__lastAdvPointsTimestamp).toLocaleTimeString()}`);
      } catch {}
    }
  } catch (e) {
    if (window.CM_DEBUG) console.error('Error updating monitoring status:', e);
    const statusText = document.getElementById('status-text');
    const lastUpdateSpan = document.getElementById('last-update');
    if (statusText) statusText.textContent = 'ERROR';
    if (lastUpdateSpan) lastUpdateSpan.textContent = 'Error fetching status';
  }
}

// Expose Top Offenders updater for inline callers
if (typeof window !== 'undefined') {
  window.__module_updateTopOffenders = updateTopOffenders;
}

// Format seconds into mm:ss
function formatCountdown(sec) {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return m > 0 ? `${m}m ${r}s` : `${r}s`;
}

// Install a 1s ticker to update the mini banner countdown
if (typeof window !== 'undefined') {
  if (!window.__liveCountdownTicker) {
    window.__liveCountdownTicker = setInterval(() => {

// Auto-refresh analysis meta while monitoring is active
if (typeof window !== 'undefined') {
  if (!window.__analysisAutoRefresh) {
    window.__analysisAutoRefresh = setInterval(async () => {
      try {
        const current = await (await fetch('/api/current')).json();
        const ms = current.monitoring_status || current.long_term_monitoring || {};
        const isActive = (ms.status === 'active') || (ms.active === true);
        if (!isActive) return;
        // Refresh analysis (lightweight calls already implemented)
        await loadAnalysisData();
      } catch {}
    }, 5000);
  }
}

      try {
        const lc = window.__liveCountdown;
        if (!lc || !lc.active) return;
        lc.remaining = (lc.remaining || lc.interval || 30) - 1;
        const liveNext = document.getElementById('live-next');
        if (liveNext) {
          liveNext.textContent = formatCountdown(lc.remaining);
          liveNext.classList.add('flash');
          setTimeout(() => liveNext.classList.remove('flash'), 120);
        }
        if (lc.remaining <= 0) lc.remaining = lc.interval || 30;
      } catch {}
    }, 1000);
  }
}

if (typeof window !== 'undefined') {
  // Expose module implementations under non-colliding names; inline stubs will forward here
  window.__module_updateAnalysisDisplay = updateAnalysisDisplay;
  window.__module_updateLeakAnalysisDisplay = updateLeakAnalysisDisplay;
  window.__module_updateAnalysisSummary = updateAnalysisSummary;
  window.__module_updateMonitoringHistory = updateMonitoringHistory;
  window.__module_updateSessionFindings = updateSessionFindings;
  window.__module_updateMonitoringStatus = updateMonitoringStatus;
}

async function copyLatestAnalysisJson() {
  try {
    const timeRangeElement = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
    const hours = timeRangeElement ? timeRangeElement.value : 24;
    const resp = await fetch(`/api/analysis?hours=${hours}`);
    const data = await resp.json();
    await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    showToast('✅ Copied latest analysis JSON to clipboard', 'success');
  } catch (e) {
    showToast('❌ Failed to copy analysis JSON: ' + e, 'error');
  }
}

if (typeof window !== 'undefined') {
  window.copyLatestAnalysisJson = copyLatestAnalysisJson;
}