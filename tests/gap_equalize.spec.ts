import { test, expect } from '@playwright/test';

test('measure gaps above and below tabs', async ({ page }) => {
  await page.goto('/', { waitUntil: 'load' });

  const vals = await page.evaluate(() => {
    const header = document.getElementById('top-header');
    const nav = document.getElementById('nav-shell');
    const firstContent = document.querySelector('#dashboard-tab > .chart-container');
    if (!header || !nav || !firstContent) return null;
    const hb = header.getBoundingClientRect();
    const nb = nav.getBoundingClientRect();
    const cb = (firstContent as HTMLElement).getBoundingClientRect();
    const gapAbove = Math.round(nb.top - hb.bottom);
    const gapBelow = Math.round(cb.top - nb.bottom);
    const hmb = getComputedStyle(header).marginBottom;
    const nmt = getComputedStyle(nav).marginTop;
    const nmb = getComputedStyle(nav).marginBottom;
    const parent = header.parentElement as HTMLElement | null;
    const sibs = parent ? Array.from(parent.children).map(el => ({ tag: el.tagName, id: (el as HTMLElement).id, cls: (el as HTMLElement).className })).slice(0,5) : null;
    return { gapAbove, gapBelow, headerMarginBottom: hmb, navMarginTop: nmt, navMarginBottom: nmb, hb: {bottom: hb.bottom}, nb: {top: nb.top, bottom: nb.bottom}, cb: {top: cb.top}, parentInfo: parent ? { tag: parent.tagName, id: parent.id, cls: parent.className } : null, siblings: sibs };
  });

  console.log('[gaps]', vals);
  expect(vals).toBeTruthy();

  await page.screenshot({ path: 'playwright-report/gap_screenshot.png', fullPage: false });
});

