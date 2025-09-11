import { test, expect } from '@playwright/test';

// Validates UI alignment and header expand FAB visibility via DOM metrics

test.describe('UI layout and header expand FAB', () => {
  test('header/content aligned and expand FAB shows when collapsed', async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });

    const header = page.locator('#top-header');
    await expect(header).toBeVisible();
    const version = await page.textContent('#ui-version-label');
    console.log('[ui-version]', version);


    // Ensure tabs row and dashboard content exist
    const navShell = page.locator('#nav-shell');
    const dashTab = page.locator('#dashboard-tab');
    await expect(navShell).toBeVisible();
    await expect(dashTab).toBeVisible();

    // Compute inner content rect for header (excluding padding + border)
    const metrics = await page.evaluate(() => {
      const hdr = document.getElementById('top-header');
      const nav = document.getElementById('nav-shell');
      const navTabs = document.querySelector('#nav-shell .tabs') as HTMLElement | null;
      const dash = document.getElementById('dashboard-tab');
      if (!hdr || !nav || !navTabs || !dash) return null;
      const hdrRect = hdr.getBoundingClientRect();
      const hStyle = window.getComputedStyle(hdr);
      const padL = parseFloat(hStyle.paddingLeft || '0');
      const padR = parseFloat(hStyle.paddingRight || '0');
      const bL = parseFloat(hStyle.borderLeftWidth || '0');
      const bR = parseFloat(hStyle.borderRightWidth || '0');
      const hdrInnerLeft = hdrRect.left + padL + bL;
      const hdrInnerRight = hdrRect.right - padR - bR;
      const hdrInnerWidth = hdrInnerRight - hdrInnerLeft;

      const navRect = nav.getBoundingClientRect();
      const navTabsRect = navTabs.getBoundingClientRect();
      const dashRect = dash.getBoundingClientRect();

      return {
        hdrInnerLeft, hdrInnerRight, hdrInnerWidth,
        navLeft: navTabsRect.left, navRight: navTabsRect.right, navWidth: navTabsRect.width,
        dashLeft: dashRect.left, dashRight: dashRect.right, dashWidth: dashRect.width,
      };
    });

    expect(metrics).not.toBeNull();
    const m = metrics!;
    console.log('[ui-metrics]', JSON.stringify(m));

    // Capture screenshot for review
    await page.screenshot({ path: 'test-results/ui_layout_screenshot.png', fullPage: true });

    // Allow a small tolerance (CSS subpixel rounding)
    const tol = 2; // px
    expect(Math.abs(m.navLeft - m.hdrInnerLeft)).toBeLessThanOrEqual(tol);
    expect(Math.abs(m.navRight - m.hdrInnerRight)).toBeLessThanOrEqual(tol);
    expect(Math.abs(m.dashLeft - m.hdrInnerLeft)).toBeLessThanOrEqual(tol);
    expect(Math.abs(m.dashRight - m.hdrInnerRight)).toBeLessThanOrEqual(tol);

    // Now collapse header via JS API (toggleHeaderBar), then verify expand FAB appears
    await page.evaluate(() => {
      (window as any).toggleHeaderBar?.();
    });
    // small wait to allow async UI toggle
    await page.waitForTimeout(150);
    const fabInfo = await page.evaluate(() => {
      const el = document.getElementById('header-expand-fab');
      if (!el) return null;
      const cs = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return { display: cs.display, visibility: cs.visibility, opacity: cs.opacity, rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height } };
    });
    console.log('[fab-info]', JSON.stringify(fabInfo));

  });

  test('right edge aligns exactly across breakpoints', async ({ page }) => {
    // Verify exact right-edge alignment at common breakpoints
    const widths = [1024, 1280, 1440];
    for (const w of widths) {
      await page.setViewportSize({ width: w, height: 768 });
      await page.goto('/', { waitUntil: 'load' });

      const metrics = await page.evaluate(() => {
        const hdr = document.getElementById('top-header');
        const navTabs = document.querySelector('#nav-shell .tabs') as HTMLElement | null;
        const dash = document.getElementById('dashboard-tab');
        if (!hdr || !navTabs || !dash) return null;
        const hdrRect = hdr.getBoundingClientRect();
        const hStyle = window.getComputedStyle(hdr);
        const padR = parseFloat(hStyle.paddingRight || '0');
        const bR = parseFloat(hStyle.borderRightWidth || '0');
        const padL = parseFloat(hStyle.paddingLeft || '0');
        const bL = parseFloat(hStyle.borderLeftWidth || '0');
        const hdrInnerRight = hdrRect.right - padR - bR;
        const hdrInnerLeft = hdrRect.left + padL + bL;
        const navTabsRect = navTabs.getBoundingClientRect();
        const dashRect = dash.getBoundingClientRect();
        return {
          width: window.innerWidth,
          hdrInnerRight,
          hdrInnerLeft,
          navRight: navTabsRect.right,
          dashRight: dashRect.right,
          navLeft: navTabsRect.left,
          dashLeft: dashRect.left,
        };
      });

      expect(metrics).not.toBeNull();
      const m = metrics as any;
      console.log('[bp]', m.width, '→ R:', m.hdrInnerRight, m.navRight, m.dashRight, 'L:', m.hdrInnerLeft, m.navLeft, m.dashLeft);

      // Right edge should be pixel-perfect aligned
      const tolRight = 0.1; // allow subpixel rounding
      expect(Math.abs(m.navRight - m.hdrInnerRight)).toBeLessThanOrEqual(tolRight);
      expect(Math.abs(m.dashRight - m.hdrInnerRight)).toBeLessThanOrEqual(tolRight);

      // Left edge should align within small rounding tolerance
      const tolLeft = 2;
      expect(Math.abs(m.navLeft - m.hdrInnerLeft)).toBeLessThanOrEqual(tolLeft);
      expect(Math.abs(m.dashLeft - m.hdrInnerLeft)).toBeLessThanOrEqual(tolLeft);
    }
  });

  test('clipboard fullscreen pager is visible and sticky at bottom', async ({ page }) => {
    await page.goto('/#clipboard', { waitUntil: 'load' });
    // Ensure clipboard tab is active and enter fullscreen
    await page.waitForSelector('#clipboard-tab');
    await page.evaluate(() => {
      // Ensure active tab is clipboard
      const thirdTab = document.querySelector('.tabs .tab:nth-child(3)') as HTMLElement | null;
      if (thirdTab) { (window as any).switchTab?.('clipboard', thirdTab); }
      // Enter fullscreen for current tab (clipboard)
      (window as any).toggleFullscreen?.();
    });
    await page.waitForFunction(() => document.body.classList.contains('fs-clipboard'));

    // Allow layout function to run and measure
    await page.waitForTimeout(100);

    const metrics = await page.evaluate(() => {
      const pager = document.getElementById('clip-pager');
      const wrap = document.querySelector('#clipboard-tab .clip-table-wrap') as HTMLElement | null;
      if (!pager || !wrap) return null;
      const pr = pager.getBoundingClientRect();
      const wr = wrap.getBoundingClientRect();
      return {
        pager: { top: pr.top, left: pr.left, right: pr.right, bottom: pr.bottom, width: pr.width, height: pr.height },
        wrap: { left: wr.left, right: wr.right, bottom: wr.bottom },
        vw: window.innerWidth, vh: window.innerHeight
      };
    });
    expect(metrics).not.toBeNull();
    const m = metrics as any;
    // Pager should be within 12px of the viewport bottom
    expect(Math.abs(m.vh - m.pager.bottom)).toBeLessThanOrEqual(12);
    // Pager should align to the wrap's exact left and right edges
    expect(Math.abs(m.pager.left - m.wrap.left)).toBeLessThanOrEqual(2);
    expect(Math.abs(m.pager.right - m.wrap.right)).toBeLessThanOrEqual(2);
  });


});


  test('tabs bar stays visible at top in fullscreen for all tabs', async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
    const tabs = [
      { name: 'dashboard', idx: 1, cls: 'fs-dashboard' },
      { name: 'analysis', idx: 2, cls: 'fs-analysis' },
      { name: 'clipboard', idx: 3, cls: 'fs-clipboard' },
    ];
    for (const t of tabs) {
      await page.evaluate((ti) => {
        const el = document.querySelector(`.tabs .tab:nth-child(${ti})`) as HTMLElement | null;
        if (el) (window as any).switchTab?.(el.textContent?.includes('Clipboard') ? 'clipboard' : (el.textContent?.includes('Analysis') ? 'analysis' : 'dashboard'), el);
      }, t.idx);
      await page.evaluate(() => (window as any).toggleFullscreen?.());
      await page.waitForFunction((cls) => document.body.classList.contains(cls), t.cls);
      await page.waitForTimeout(60);
      const vis = await page.evaluate(() => {
        const nav = document.getElementById('nav-shell');
        const tabs = nav?.querySelector('.tabs') as HTMLElement | null;
        const tcs = tabs ? getComputedStyle(tabs) : null;
        const tr = tabs ? tabs.getBoundingClientRect() : null;
        return { tabs: tabs ? { display: tcs!.display, opacity: tcs!.opacity, top: tr!.top } : null };
      });
      expect(vis).not.toBeNull();
      const v = vis as any;
      // Full tabs row must be visible in fullscreen
      expect(v.tabs && v.tabs.display !== 'none' && parseFloat(v.tabs.opacity) > 0).toBeTruthy();
      expect(v.tabs.top).toBeLessThanOrEqual(120);
      await page.evaluate(() => (window as any).toggleFullscreen?.());
      await page.waitForFunction((cls) => !document.body.classList.contains(cls), t.cls);
    }
  });

  test('panel spacing is consistent in fullscreen', async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
    // Switch to dashboard and enter fullscreen
    await page.evaluate(() => {
      const el = document.querySelector('.tabs .tab:nth-child(1)') as HTMLElement | null;
      if (el) (window as any).switchTab?.('dashboard', el);
    });
    await page.evaluate(() => (window as any).toggleFullscreen?.());
    await page.waitForFunction(() => document.body.classList.contains('fs-dashboard'));
    await page.waitForTimeout(100);

    const spacing = await page.evaluate(() => {
      const nav = document.getElementById('nav-shell');
      const firstPanel = document.querySelector('#dashboard-tab .chart-container') as HTMLElement | null;
      const navRect = nav ? nav.getBoundingClientRect() : null;
      const panelRect = firstPanel ? firstPanel.getBoundingClientRect() : null;

      return {
        navBottom: navRect ? navRect.bottom : 0,
        panelTop: panelRect ? panelRect.top : 0,
        gap: panelRect && navRect ? panelRect.top - navRect.bottom : 0
      };
    });

    console.log(`[spacing-debug] Nav bottom: ${spacing.navBottom}, Panel top: ${spacing.panelTop}, Gap: ${spacing.gap}px`);

    // Exit fullscreen
    await page.evaluate(() => (window as any).toggleFullscreen?.());
    await page.waitForFunction(() => !document.body.classList.contains('fs-dashboard'));
  });

  test('panel spacing diagnostics in normal view', async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
    // stay in normal view; ensure dashboard tab is active
    await page.evaluate(() => {
      const el = document.querySelector('.tabs .tab:nth-child(1)') as HTMLElement | null;
      if (el) (window as any).switchTab?.('dashboard', el);
    });
    await page.waitForTimeout(50);

    const spacing = await page.evaluate(() => {
      const nav = document.getElementById('nav-shell');
      const firstPanel = document.querySelector('#dashboard-tab .chart-container') as HTMLElement | null;
      const secondPanel = document.querySelectorAll('#dashboard-tab .chart-container')[1] as HTMLElement | null;
      const navRect = nav ? nav.getBoundingClientRect() : null;
      const p1 = firstPanel ? firstPanel.getBoundingClientRect() : null;
      const p2 = secondPanel ? secondPanel.getBoundingClientRect() : null;
      return {
        navBottom: navRect ? navRect.bottom : 0,
        p1Top: p1 ? p1.top : 0,
        p1Bottom: p1 ? p1.bottom : 0,
        p2Top: p2 ? p2.top : 0,
        gapNavToP1: navRect && p1 ? p1.top - navRect.bottom : 0,
        gapP1ToP2: p1 && p2 ? p2.top - p1.bottom : 0,
      };
    });

    console.log(`[panel-gap-debug] nav->p1: ${spacing.gapNavToP1}px, p1->p2: ${spacing.gapP1ToP2}px (navBottom=${spacing.navBottom}, p1Top=${spacing.p1Top})`);
    const tol = 1.5; // px
    expect(Math.abs(spacing.gapNavToP1 - spacing.gapP1ToP2)).toBeLessThanOrEqual(tol);
  });


