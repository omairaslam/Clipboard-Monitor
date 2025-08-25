# Changelog (Unified Dashboard)

## Phase 1
- Move CPU chart ownership to module; remove inline `new SimpleCPUChart()`
- Expose `window.cpuChart` from module; guard inline references
- Align monitoring endpoints to `/api/start_monitoring` and `/api/stop_monitoring`
- Wire `updateMonitoringStatus` to update `#advanced-status` and counters
- Add Playwright tests + config with webServer; HTML report, retries + trace enabled
- Add VS Code tasks + buttons to run tests and show report

## Phase 2
- UnifiedMemoryChart: live/historical switching, ranges, persistence
- Accept `hours=all` for `/api/historical` and `/api/analysis`
- Tests:
  - Live/historical modes & ranges
  - Historical resolution changes
  - Transitions stress (Live ↔ Historical)
  - Persisted state (mode & live range)
- Perf sentinel: non-blocking threshold (1.5s) for resolution settle

## Phase 3 (in progress)
- Monitoring points increment test (Analysis & Controls)
- Additional UX polish for monitoring counters and indicators

