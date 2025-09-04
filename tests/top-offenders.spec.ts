import { test, expect } from '@playwright/test';

// Verifies Top Offenders card resolves from "Loading..." to either a list or a clear empty-state message

test('Top Offenders resolves and shows content or empty-state', async ({ page }) => {
  await page.goto('/', { waitUntil: 'load' });

  // Go to Analysis & Controls
  await page.getByText('Analysis & Controls', { exact: false }).click();

  const offenders = page.locator('#top-offenders');
  await expect(offenders).toHaveCount(1);

  // Kick analysis refresh
  await page.evaluate(() => (window as any).loadAnalysisData?.());

  // Wait for the card to resolve out of the loading state
  await page.waitForFunction(() => {
    const el = document.getElementById('top-offenders');
    if (!el) return false;
    const txt = (el.textContent || '').toLowerCase();
    return !txt.includes('loading top offenders');
  }, {}, { timeout: 15000 });

  // Assert we either have an empty-state message or rendered entries
  const html = await offenders.innerHTML();
  const normalized = html.replace(/\s+/g, ' ').toLowerCase();
  const showsEmptyState = normalized.includes('no offenders found');
  const showsError = normalized.includes('failed to load top offenders');

  expect(showsError).toBeFalsy();

  if (!showsEmptyState) {
    // Should render at least one offender entry (card divs)
    const cardsCount = await offenders.locator('div[style*="border-left:"]').count();
    expect(cardsCount).toBeGreaterThan(0);
  }
});

