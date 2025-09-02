import { test, expect } from '@playwright/test';

// Basic smoke: loads dashboard, waits for key elements, and surfaces script errors

test('dashboard loads without script errors and shows header data', async ({ page }) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', err => {
    pageErrors.push(err.message || String(err));
  });

  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  // Report immediate errors if any
  if (pageErrors.length) {
    throw new Error('Page script error: ' + pageErrors[0]);
  }

  // Wait for updateDashboard to exist (defined by inline script)
  await page.waitForFunction(() => (window as any).updateDashboard !== undefined, undefined, { timeout: 10000 });

  // Kick a fetch to render data if needed
  await page.evaluate(() => {
    if (typeof (window as any).fetchMemoryData === 'function') {
      return (window as any).fetchMemoryData();
    }
  });

  // Wait a moment for DOM updates
  await page.waitForTimeout(750);

  // Key header elements should be present
  await expect(page.locator('#header-total-memory')).toHaveCount(1);
  await expect(page.locator('#header-menubar-memory')).toHaveCount(1);
  await expect(page.locator('#header-service-memory')).toHaveCount(1);

  // Surface console syntax errors if present
  const syntaxErr = consoleErrors.find(e => /SyntaxError|Invalid|Unexpected token|await is only valid/i.test(e));
  if (syntaxErr) throw new Error('Console error found: ' + syntaxErr);
});

