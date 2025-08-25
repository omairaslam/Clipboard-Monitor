# Memory Optimisation: Unified Dashboard (Option 1)

This document summarizes the unified memory dashboard work, focusing on Option 1: charts owned by modules, with inline scripts acting only as thin adapters.

## Goals
- CPU and Memory charts initialized by their modules (no inline instantiation)
- Safe inline-to-module collaboration via guarded globals
- Aligned monitoring endpoints and responsive UI status updates
- Automated tests and reports (Playwright) to prevent regressions

## Architecture
- CPU chart (static/js/charts/cpu-chart.js)
  - Auto-boot on DOMContentLoaded and expose `window.cpuChart`
  - `window.cpuChartManager` created once by the module; inline references are guarded
- Memory chart (UnifiedMemoryChart in unified_memory_dashboard.py)
  - Owns live polling, live/historical switching, and downsampling
  - Persists `umc_mode`, `umc_live_range`, `umc_time_range`, and `umc_resolution`
  - Updates UI via DOM ids (mode badge, title, range selectors)
- Monitoring
  - JS uses `/api/start_monitoring` and `/api/stop_monitoring`
  - Status polling via `/api/current`; also instantly flips `#advanced-status` on toggle for responsive UX

## Key UI IDs
- Memory: `#chart-title`, `#mode-badge`, `#live-range-select`, `#historical-range`, `#resolution-select`, `#memoryChart`
- CPU: `#cpuChart`, `#cpu-chart-title`, `#cpu-chart-mode-indicator`, `#cpu-chart-points-count`
- Monitoring: `#monitoringToggleBtn`, `#advanced-status`, `#advanced-data-points`, `#collection-rate`

## Endpoints (aligned)
- Start monitoring: `GET /api/start_monitoring?interval=...`
- Stop monitoring: `GET /api/stop_monitoring`
- Current status: `GET /api/current`
- Historical data (chart): `GET /api/historical-chart?hours=...&resolution=...` (frontend-managed)
- Historical data (legacy): `GET /api/historical?hours=...` (accepts `all`)
- Analysis data: `GET /api/analysis?hours=...` (accepts `all`)

## Performance
- Title settle sentinel during resolution switch with soft threshold (1.5s). Exposed via Playwright perf test; does not fail CI but logs a warning.

## Notes
- Inline code only forwards to module functions and checks for their presence
- No duplicate chart creation; guarded access avoids race conditions on page load

See Testing.md for how to run and inspect tests.

