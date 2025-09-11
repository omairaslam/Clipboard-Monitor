import { test, expect } from '@playwright/test';

// Validates the fullscreen Exit button is a small button placed at the
// bottom-right, aligned with the content width, on all three tabs.

test.describe('Fullscreen Exit button placement', () => {
  const tabs = ['dashboard', 'analysis', 'clipboard'] as const;

  for (const tab of tabs) {
    test(`Exit button bottom-right on ${tab}`, async ({ page }) => {
      await page.goto('http://localhost:8001/');

      // Switch to desired tab via the global helper
      await page.evaluate((t) => {
        // @ts-ignore
        window.switchTab && window.switchTab(t);
      }, tab);

      // Enter fullscreen for this tab
      await page.evaluate(() => {
        // @ts-ignore
        window.toggleFullscreen && window.toggleFullscreen();
      });

      // Wait for fullscreen class on body
      await page.waitForFunction((t) => {
        return document.body.classList.contains(`fs-${t}`);
      }, tab);

      // Allow layout normalization to run
      await page.waitForTimeout(120);

      const exitBtn = page.locator('#fs-exit-btn');
      await expect(exitBtn).toBeVisible();

      // Collect geometry of exit button and content width wrapper
      const geo = await page.evaluate(() => {
        const btn = document.getElementById('fs-exit-btn');
        const wrap = document.getElementById('content-width-wrap');
        if (!btn || !wrap) return null;
        const b = btn.getBoundingClientRect();
        const w = wrap.getBoundingClientRect();
        const cs = window.getComputedStyle(btn);
        return {
          btn: { left: b.left, top: b.top, right: b.right, bottom: b.bottom, width: b.width, height: b.height },
          wrap: { right: w.right, bottom: w.bottom, left: w.left, width: w.width },
          vw: window.innerWidth,
          vh: window.innerHeight,
          fontSize: cs.fontSize,
          padding: cs.padding,
          styles: { left: cs.left, right: cs.right, position: cs.position, display: cs.display }
        };
      });
      expect(geo).not.toBeNull();
      console.log('FS exit geometry', JSON.stringify(geo));
      const { btn, wrap, vh } = geo!;

      // Should be at the bottom right of the viewport (within 4-16px from bottom)
      expect(btn.bottom).toBeGreaterThanOrEqual(vh - 20);
      expect(btn.bottom).toBeLessThanOrEqual(vh - 4);

      // Right edge should align with content right edge minus the 8px inner inset
      const expectedRight = wrap.right - 8; // nav/content use an 8px inner gutter
      const rightDelta = Math.abs(btn.right - expectedRight);
      expect(rightDelta).toBeLessThanOrEqual(10);

      // Button should be reasonably small
      expect(btn.height).toBeLessThanOrEqual(40);
      expect(btn.width).toBeLessThanOrEqual(140);

      // Save a screenshot for manual verification
      await page.screenshot({ path: `playwright-report/fs-exit-${tab}.png`, fullPage: true });

      // Exit fullscreen so the next test starts cleanly
      await page.evaluate(() => {
        // @ts-ignore
        window.exitFullscreenCurrent && window.exitFullscreenCurrent();
      });
    });
  }
});

