import { test, expect } from '@playwright/test';

// Phase 2: Stress switching Live ↔ Historical multiple times and assert stability

test('live-historical transitions remain stable', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));

  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  const title = page.locator('#chart-title');
  const badge = page.locator('#mode-badge');
  const liveBtn = page.locator('#realtime-btn');
  const histBtn = page.locator('#historical-btn');

  // Ensure initial
  await expect(title).toHaveText(/Live Memory Usage/);
  await expect(badge).toHaveText('Live');

  for (let i = 0; i < 3; i++) {
    // Go to historical (24h)
    await histBtn.click();
    await page.locator('#historical-options').waitFor({ state: 'visible' });
    const histRange = page.locator('#historical-range');
    await histRange.selectOption('24');
    await expect(title).toHaveText(/Historical Memory Usage|Loading historical data/);

    // Back to live
    await liveBtn.click();
    await expect(badge).toHaveText('Live');
    await expect(title).toHaveText(/Live Memory Usage/);
  }

  // Sanity: chart visible
  await expect(page.locator('#memoryChart')).toBeVisible();

  if (errors.length) throw new Error('Page error: ' + errors[0]);
});

