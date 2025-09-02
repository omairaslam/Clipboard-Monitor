import { test, expect } from '@playwright/test';

function getHours(page) {
  return page.evaluate(() => (document.getElementById('analysisTimeRange')?.value || document.getElementById('timeRange')?.value || document.getElementById('historical-range')?.value || '24'));
}

test('Sparklines render (smoke)', async ({ page }) => {
  await page.goto('http://localhost:8001/');
  await page.waitForLoadState('domcontentloaded');

  // Ensure Trend Explorer function is present
  await page.waitForFunction(() => !!(window as any).updateTrendExplorer, undefined, { timeout: 15000 });

  // Trigger a render
  const hours = await getHours(page);
  await page.evaluate((h) => (window as any).updateTrendExplorer?.(h), hours);

  const trend = page.locator('#trend-analysis');
  await expect(trend).toBeVisible();

  const canvas = trend.locator('#spark-menubar');
  await expect(canvas).toHaveCount(1);

  // Should have non-trivial width
  const width = await canvas.evaluate((el: HTMLCanvasElement) => el.getBoundingClientRect().width);
  expect(width).toBeGreaterThan(50);

  // Save screenshot for diagnostics
  await page.screenshot({ path: 'test-results/sparklines-smoke.png', fullPage: false });
});

