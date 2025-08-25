import { test, expect } from '@playwright/test';

// Log size metrics of /api/historical-chart payload to aid perf monitoring

test('log historical payload size for 24h minute resolution', async ({ page, request }) => {
  await page.goto('http://localhost:8001/', { waitUntil: 'load' });
  const resp = await request.get('http://localhost:8001/api/historical-chart?hours=24&resolution=minute');
  expect(resp.ok()).toBeTruthy();
  const body = await resp.body();
  console.log(`[perf] historical-chart 24h minute bytes=${body.byteLength}`);
});

