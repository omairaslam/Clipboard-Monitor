const { chromium } = require('playwright');

async function debugChartPosition() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('Navigating to dashboard...');
        await page.goto('http://localhost:8001', { waitUntil: 'networkidle' });
        
        // Wait for chart to initialize
        await page.waitForTimeout(5000);
        
        // Get detailed positioning info for the memory chart
        const chartPositionInfo = await page.evaluate(() => {
            const canvas = document.getElementById('memoryChart');
            if (!canvas) return { error: 'Canvas not found' };
            
            const rect = canvas.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(canvas);
            const parentRect = canvas.parentElement?.getBoundingClientRect();
            
            return {
                canvas: {
                    id: canvas.id,
                    tagName: canvas.tagName,
                    width: canvas.width,
                    height: canvas.height,
                    clientWidth: canvas.clientWidth,
                    clientHeight: canvas.clientHeight,
                    offsetWidth: canvas.offsetWidth,
                    offsetHeight: canvas.offsetHeight,
                    scrollWidth: canvas.scrollWidth,
                    scrollHeight: canvas.scrollHeight
                },
                position: {
                    top: rect.top,
                    left: rect.left,
                    right: rect.right,
                    bottom: rect.bottom,
                    width: rect.width,
                    height: rect.height,
                    x: rect.x,
                    y: rect.y
                },
                computedStyle: {
                    display: computedStyle.display,
                    visibility: computedStyle.visibility,
                    opacity: computedStyle.opacity,
                    position: computedStyle.position,
                    top: computedStyle.top,
                    left: computedStyle.left,
                    right: computedStyle.right,
                    bottom: computedStyle.bottom,
                    transform: computedStyle.transform,
                    zIndex: computedStyle.zIndex,
                    overflow: computedStyle.overflow,
                    margin: computedStyle.margin,
                    padding: computedStyle.padding,
                    border: computedStyle.border,
                    backgroundColor: computedStyle.backgroundColor
                },
                parent: parentRect ? {
                    className: canvas.parentElement.className,
                    tagName: canvas.parentElement.tagName,
                    top: parentRect.top,
                    left: parentRect.left,
                    width: parentRect.width,
                    height: parentRect.height
                } : null,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    scrollX: window.scrollX,
                    scrollY: window.scrollY
                },
                isVisible: rect.width > 0 && rect.height > 0 && 
                          computedStyle.display !== 'none' && 
                          computedStyle.visibility !== 'hidden' &&
                          parseFloat(computedStyle.opacity) > 0
            };
        });
        
        console.log('Chart Position Info:', JSON.stringify(chartPositionInfo, null, 2));
        
        // Check if chart is in viewport
        const inViewport = await page.evaluate(() => {
            const canvas = document.getElementById('memoryChart');
            if (!canvas) return false;
            
            const rect = canvas.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= window.innerHeight &&
                rect.right <= window.innerWidth
            );
        });
        
        console.log('Chart in viewport:', inViewport);
        
        // Get all elements with similar positioning issues
        const hiddenElements = await page.evaluate(() => {
            const elements = document.querySelectorAll('canvas, .chart-wrapper, .chart-container');
            return Array.from(elements).map(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return {
                    tagName: el.tagName,
                    id: el.id,
                    className: el.className,
                    position: {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    },
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    isVisible: rect.width > 0 && rect.height > 0 && 
                              style.display !== 'none' && 
                              style.visibility !== 'hidden' &&
                              parseFloat(style.opacity) > 0
                };
            });
        });
        
        console.log('All chart-related elements:', JSON.stringify(hiddenElements, null, 2));
        
        // Scroll to the memory chart area
        await page.evaluate(() => {
            const canvas = document.getElementById('memoryChart');
            if (canvas) {
                canvas.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
        
        await page.waitForTimeout(2000);
        
        // Take a screenshot focused on the chart area
        await page.screenshot({ path: 'chart_position_debug.png', fullPage: true });
        console.log('Screenshot saved as chart_position_debug.png');
        
        // Try to highlight the chart area
        await page.evaluate(() => {
            const canvas = document.getElementById('memoryChart');
            if (canvas) {
                canvas.style.border = '5px solid red';
                canvas.style.backgroundColor = 'yellow';
            }
            
            const wrapper = document.querySelector('.chart-wrapper');
            if (wrapper) {
                wrapper.style.border = '3px solid blue';
                wrapper.style.backgroundColor = 'lightblue';
            }
        });
        
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'chart_highlighted_debug.png', fullPage: true });
        console.log('Highlighted screenshot saved as chart_highlighted_debug.png');
        
        console.log('Press Enter to close browser...');
        await new Promise(resolve => {
            process.stdin.once('data', resolve);
        });
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

debugChartPosition();
