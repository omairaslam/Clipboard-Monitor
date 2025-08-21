import { test, expect } from '@playwright/test';

// Toggles advanced monitoring via the UI and checks the badge state updates

test('advanced monitoring toggle updates badge', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));

  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  // Make sure toggle button is present
  const toggleBtn = page.locator('#monitoringToggleBtn');
  await expect(toggleBtn).toHaveCount(1);

  // Read current badge state
  const badge = page.locator('#advanced-badge');
  await expect(badge).toHaveCount(1);
  const beforeText = await badge.textContent();

  // Click toggle
  await toggleBtn.click();

  // Wait a bit for server call and UI update
  await page.waitForTimeout(1000);

  // Verify badge text flips between ON/OFF (or becomes Active/Inactive)
  const afterText = await badge.textContent();
  expect(afterText?.trim()).not.toBe(beforeText?.trim());

  // Click toggle back to restore state
  await toggleBtn.click();
  await page.waitForTimeout(1000);

  // Verify it flips back (best-effort)
  const finalText = await badge.textContent();
  expect(finalText?.trim()).toBe(beforeText?.trim());

  // Fail if page errors occurred
  if (errors.length) throw new Error('Page error: ' + errors[0]);
});

