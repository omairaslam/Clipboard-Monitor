import { test, expect } from '@playwright/test';

const SOFT_MS = parseInt(process.env.PERF_SOFT_MS || '1500', 10);

// Non-blocking performance check: measure time to settle title after resolution switch

test('resolution switch settles under soft threshold', async ({ page }) => {
  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  // Enter historical 24h
  await page.locator('#historical-btn').click();
  await page.locator('#historical-options').waitFor();
  await page.locator('#historical-range').selectOption('24');

  const res = page.locator('#resolution-select');
  const title = page.locator('#chart-title');

  // Switch resolution and measure settle time
  const start = Date.now();
  await res.selectOption('minute');
  await expect(title).toHaveText(/Historical Memory Usage/, { timeout: 15000 });
  const elapsed = Date.now() - start;

  console.log(`[perf] resolution switch settle ms=${elapsed} (soft=${SOFT_MS})`);
  if (elapsed > SOFT_MS) {
    console.warn(`[perf] settle time ${elapsed}ms exceeded soft threshold ${SOFT_MS}ms`);
  }

  await expect(title).toHaveText(/Historical Memory Usage/);
});

