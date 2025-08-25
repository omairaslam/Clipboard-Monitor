# Troubleshooting

## Dashboard shows no data
- Refresh the page and check browser console
- Open /api/current in a new tab to ensure it returns valid JSON
- Ensure no proxies are rewriting responses
- If errors persist, set `CM_DEBUG=1` in environment and restart the server

## Multiple dashboards or ports busy
- Use the VS Code button “Clear & Restart All” to relaunch services
- Ensure port 8001 is free (lsof -i :8001)

## Playwright report doesn’t open
- Use the VS Code task: “📊 Playwright: Show Report”
- Or run `npx playwright show-report`

## Advanced monitoring does not start
- Confirm /api/start_monitoring returns JSON `{status: 'started'}`
- Check that interval is a number and try a larger interval (e.g. 10s)
- Inspect the mini banner; countdown should begin and points should increase

## Excessive logs
- By default, server suppresses noisy tracebacks for common disconnects
- To enable verbose logging for debugging, set `CM_DEBUG=1` before start

