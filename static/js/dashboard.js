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

