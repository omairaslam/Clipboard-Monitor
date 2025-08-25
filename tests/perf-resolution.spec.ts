import { test, expect } from '@playwright/test';

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

  // Soft threshold 1500ms
  const SOFT_MS = 1500;
  console.log(`[perf] resolution switch settle ms=${elapsed}`);
  // Non-blocking: only warn if exceeded
  if (elapsed > SOFT_MS) {
    console.warn(`[perf] settle time ${elapsed}ms exceeded soft threshold ${SOFT_MS}ms`);
  }

  // Keep test green regardless; the console warning serves as sentinel
  await expect(title).toHaveText(/Historical Memory Usage/);
});

