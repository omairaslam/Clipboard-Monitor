// Minimal, robust Trend Explorer sparklines (Canvas-only)
// - No SVG, no tooltip modules, no dynamic imports
// - Single codepath to reduce surface area

(function(){
  function get2DContext(canvas){
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('2D context not available');
    return ctx;
  }

  function stretchCanvas(canvas, width, height){
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(2, Math.floor(width * dpr));
    canvas.height = Math.max(2, Math.floor(height * dpr));
    canvas.style.width = Math.max(2, Math.floor(width)) + 'px';
    canvas.style.height = Math.max(2, Math.floor(height)) + 'px';
    return dpr;
  }

  function drawLine(canvas, values, color){
    if (!canvas || !values || values.length < 2) return false;
    const rect = canvas.getBoundingClientRect();
    const dpr = stretchCanvas(canvas, Math.max(160, rect.width || 300), Math.max(24, rect.height || 36));
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    const padL = 4, padR = 2, padT = 2, padB = 4;
    const innerW = Math.max(1, w - padL - padR);
    const innerH = Math.max(1, h - padT - padB);

    const min0 = Math.min(...values);
    const max0 = Math.max(...values);
    const min = (min0 === max0) ? min0 - 0.5 : min0;
    const max = (min0 === max0) ? max0 + 0.5 : max0;

    const mapX = (i, n) => padL + (i / (n - 1)) * innerW;
    const mapY = (v) => padT + innerH - ((v - min) / (max - min)) * innerH;

    const ctx = get2DContext(canvas);
    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    // background
    ctx.fillStyle = '#fbfdff';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = '#e3f2ff';
    ctx.strokeRect(0.5, 0.5, w-1, h-1);

    // area (subtle)
    ctx.beginPath();
    ctx.moveTo(mapX(0, values.length), mapY(values[0]));
    for (let i=1;i<values.length;i++) ctx.lineTo(mapX(i, values.length), mapY(values[i]));
    ctx.lineTo(padL + innerW, padT + innerH);
    ctx.lineTo(padL, padT + innerH);
    ctx.closePath();
    ctx.fillStyle = color + '14';
    ctx.fill();

    // line
    ctx.beginPath();
    ctx.moveTo(mapX(0, values.length), mapY(values[0]));
    for (let i=1;i<values.length;i++) ctx.lineTo(mapX(i, values.length), mapY(values[i]));
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // dot
    const lastX = mapX(values.length - 1, values.length);
    const lastY = mapY(values[values.length - 1]);
    ctx.beginPath();
    ctx.arc(lastX, lastY, 2.2, 0, Math.PI*2);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.restore();
    return true;
  }

  function miniRow(label, id, color) {
    return `
    <div id="row-${id}" style="display:flex; flex-direction:column; gap:4px; width:100%; box-sizing:border-box;">
      <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
        <div style="display:flex; align-items:center; gap:6px; font-size:12px; color:#333;">
          <span style="display:inline-block; width:8px; height:8px; border-radius:2px; background:${color};"></span>
          <span>${label}</span>
        </div>
        <div id="${id}-delta" style="min-width:80px; text-align:right; font-size:12px; color:#555; font-variant-numeric:tabular-nums;"></div>
      </div>
      <canvas id="${id}" style="width:100%; height:36px; display:block; border:1px solid #e3f2ff; background:#fbfdff; border-radius:4px; box-sizing:border-box;"></canvas>
    </div>`;
  }

  function setDelta(id, arr) {
    if (!arr || arr.length < 2) return;
    const start = arr[0];
    const end = arr[arr.length-1];
    const delta = end - start;
    const sign = delta >= 0 ? '+' : '';
    const el = document.getElementById(`${id}-delta`);
    if (el) { el.style.color = delta >= 0 ? '#2E7D32' : '#B00020'; el.textContent = `${sign}${delta.toFixed(2)} MB`; }
  }

  async function updateTrendExplorer(hours){
    const container = document.getElementById('trend-analysis');
    if (!container) return;

    let block = document.getElementById('trend-sparklines');
    if (!block){
      block = document.createElement('div');
      block.id = 'trend-sparklines';
      block.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <div style="font-weight:600; color:#266eb6;">Sparklines</div>
          <div id="spark-meta" style="font-size:11px; color:#666;">inline trend preview</div>
        </div>
        <div id="spark-rows" style="display:grid; grid-template-columns:1fr; gap:6px; width:100%;">
          ${miniRow('Menu Bar (MB)', 'spark-menubar', '#2196F3')}
          ${miniRow('Main Service (MB)', 'spark-service', '#8E44AD')}
          ${miniRow('Total (MB)', 'spark-total', '#2E7D32')}
        </div>
        <div id="spark-empty" style="display:none; font-size:12px; color:#a94442; background:#fff3cd; border:1px solid #ffeeba; padding:6px 8px; border-radius:6px;">No data for this range.</div>
      `;
      container.appendChild(block);
    }

    try {
      const resolution = 'full';
      const res = await fetch(`/api/historical-chart?hours=${hours||'24'}&resolution=${resolution}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();
      const points = Array.isArray(payload.points) ? payload.points : [];
      const meta = document.getElementById('spark-meta');
      if (meta) {
        const count = points.length || 0;
        meta.textContent = `Last ${hours||'24'} hours · ${resolution} · ${count} point${count===1?'':'s'}`;
      }
      if (!points.length) { document.getElementById('spark-empty').style.display='block'; return; }
      else { document.getElementById('spark-empty').style.display='none'; }

      const menubar = points.map(p => Number(p.menubar_memory || 0));
      const service = points.map(p => Number(p.service_memory || 0));
      const total = points.map(p => Number(p.total_memory || 0));

      const c1 = document.getElementById('spark-menubar');
      const c2 = document.getElementById('spark-service');
      const c3 = document.getElementById('spark-total');

      drawLine(c1, menubar, '#2196F3');
      drawLine(c2, service, '#8E44AD');
      drawLine(c3, total, '#2E7D32');

      setDelta('spark-menubar', menubar);
      setDelta('spark-service', service);
      setDelta('spark-total', total);
    } catch (err) {
      const msg = document.createElement('div');
      msg.style.cssText = 'margin-top:6px; font-size:12px; color:#B00020;';
      msg.textContent = 'Failed to load sparkline data';
      block.appendChild(msg);
      if (window.CM_DEBUG) console.error('[trend-explorer] error', err);
    }
  }

  // Expose
  if (typeof window !== 'undefined') {
    window.updateTrendExplorer = updateTrendExplorer;
    if (!window.requestTrendRedraw) {
      let rafId = 0;
      window.requestTrendRedraw = function(hours){
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => { rafId = 0; updateTrendExplorer(hours); });
      };
    }
  }

  // Kick once after DOM ready
  (function bootstrap(){
    const fire = () => {
      const hoursEl = document.getElementById('analysisTimeRange') || document.getElementById('timeRange') || document.getElementById('historical-range');
      const hours = hoursEl ? (hoursEl.value || '24') : '24';
      if (typeof window.updateTrendExplorer === 'function') window.updateTrendExplorer(hours);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(fire, 500));
    else setTimeout(fire, 300);
  })();
})();

