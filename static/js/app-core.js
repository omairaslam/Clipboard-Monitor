// Core helpers: toast, tooltip, safe DOM updates

function showToast(message, type = 'info', timeout = 2500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, timeout);
}

let currentTooltip = null;
function showTooltip(element, text) {
  hideTooltip();
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  tooltip.textContent = text;
  tooltip.style.cssText = `
    position: absolute; background: #333; color: white; padding: 6px 8px; border-radius: 4px;
    font-size: 10px; white-space: normal; z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.2s;
    max-width: 250px; line-height: 1.3;`;
  document.body.appendChild(tooltip);
  const rect = element.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();
  let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
  let top = rect.top - tooltipRect.height - 5;
  if (left < 5) left = 5;
  if (left + tooltipRect.width > window.innerWidth - 5) left = window.innerWidth - tooltipRect.width - 5;
  if (top < 5) top = rect.bottom + 5;
  tooltip.style.left = left + 'px';
  tooltip.style.top = top + 'px';
  setTimeout(() => { tooltip.style.opacity = '1'; }, 10);
  currentTooltip = tooltip;
}

function hideTooltip() {
  if (currentTooltip) {
    currentTooltip.remove();
    currentTooltip = null;
  }
}

function safeUpdateElement(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// Also attach to window so legacy inline handlers keep working
if (typeof window !== 'undefined') {
  window.showToast = showToast;
  window.showTooltip = showTooltip;
  window.hideTooltip = hideTooltip;
  window.safeUpdateElement = safeUpdateElement;
}

