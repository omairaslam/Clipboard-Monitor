import { test, expect } from '@playwright/test';

// Covers switching Memory chart between Live and Historical and adjusting ranges

test.describe('Memory chart modes and ranges', () => {
  test('switch live ranges and historical ranges', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(e.message));

    await page.goto('http://localhost:8001/', { waitUntil: 'load' });

    // Live is default; verify title and badge
    await expect(page.locator('#chart-title')).toHaveText(/Live Memory Usage/);
    await expect(page.locator('#mode-badge')).toHaveText('Live');

    // Change live range to 2h and 4h
    const liveRange = page.locator('#live-range-select');
    await expect(liveRange).toHaveCount(1);
    await liveRange.selectOption('2h');
    await expect(page.locator('#chart-title')).toHaveText(/Live Memory Usage/);
    await liveRange.selectOption('4h');
    await expect(page.locator('#chart-title')).toHaveText(/Live Memory Usage/);

    // Open Historical options
    const historicalBtn = page.locator('#historical-btn');
    await historicalBtn.click();
    await expect(page.locator('#historical-options')).toBeVisible();

    // Select 24h historical
    const histRange = page.locator('#historical-range');
    await histRange.selectOption('24');
    // Title should switch to historical
    await expect(page.locator('#chart-title')).toHaveText(/Historical Memory Usage|Loading historical data/);

    // Switch back to live
    const realtimeBtn = page.locator('#realtime-btn');
    await realtimeBtn.click();
    await expect(page.locator('#mode-badge')).toHaveText('Live');

    // Open historical again and choose 'all' with confirmation popup
    await historicalBtn.click();
    page.once('dialog', async dialog => { await dialog.accept(); });
    await histRange.selectOption('all');
    await expect(page.locator('#chart-title')).toHaveText(/Historical Memory Usage|Loading historical data/);

    // Return to live to finish
    await realtimeBtn.click();
    await expect(page.locator('#mode-badge')).toHaveText('Live');

    if (errors.length) throw new Error('Page error: ' + errors[0]);
  });
});

