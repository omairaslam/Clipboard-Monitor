const { chromium } = require('playwright');

async function debugDashboard() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Listen for console messages
    page.on('console', msg => {
        console.log(`BROWSER CONSOLE [${msg.type()}]:`, msg.text());
    });
    
    // Listen for errors
    page.on('pageerror', error => {
        console.log('PAGE ERROR:', error.message);
    });
    
    try {
        console.log('Navigating to dashboard...');
        await page.goto('http://localhost:8001', { waitUntil: 'networkidle' });
        
        // Wait a bit for the page to load
        await page.waitForTimeout(3000);
        
        // Check if memory chart canvas exists
        const memoryCanvas = await page.$('#memoryChart');
        console.log('Memory chart canvas exists:', !!memoryCanvas);
        
        if (memoryCanvas) {
            // Get canvas dimensions
            const canvasInfo = await page.evaluate(() => {
                const canvas = document.getElementById('memoryChart');
                if (!canvas) return null;
                
                return {
                    width: canvas.width,
                    height: canvas.height,
                    clientWidth: canvas.clientWidth,
                    clientHeight: canvas.clientHeight,
                    style: canvas.style.cssText,
                    parentElement: canvas.parentElement?.className,
                    hasChart: !!window.Chart && !!canvas.getContext('2d')
                };
            });
            console.log('Canvas info:', canvasInfo);
        }
        
        // Check if Chart.js is loaded
        const chartJsLoaded = await page.evaluate(() => {
            return typeof Chart !== 'undefined';
        });
        console.log('Chart.js loaded:', chartJsLoaded);
        
        // Check if chartManager exists and is initialized
        const chartManagerInfo = await page.evaluate(() => {
            if (typeof chartManager === 'undefined') {
                return { exists: false };
            }

            return {
                exists: true,
                isInitialized: chartManager.isInitialized,
                mode: chartManager.mode,
                liveDataLength: chartManager.liveData?.length || 0,
                hasChart: !!chartManager.chart,
                currentLiveRange: chartManager.currentLiveRange,
                chartData: chartManager.chart ? {
                    labels: chartManager.chart.data.labels.slice(0, 5), // First 5 labels
                    datasets: chartManager.chart.data.datasets.map(ds => ({
                        label: ds.label,
                        dataLength: ds.data.length,
                        firstFewPoints: ds.data.slice(0, 5),
                        lastFewPoints: ds.data.slice(-5)
                    }))
                } : null,
                sampleLiveData: chartManager.liveData?.slice(0, 3) || [] // First 3 data points
            };
        });
        console.log('Chart manager info:', JSON.stringify(chartManagerInfo, null, 2));
        
        // Check for any JavaScript errors in the page
        const jsErrors = await page.evaluate(() => {
            return window.jsErrors || [];
        });
        console.log('JS Errors:', jsErrors);
        
        // Take a screenshot
        await page.screenshot({ path: 'dashboard_debug.png', fullPage: true });
        console.log('Screenshot saved as dashboard_debug.png');
        
        // Check API endpoints
        console.log('Testing API endpoints...');
        
        try {
            const currentResponse = await page.evaluate(async () => {
                const response = await fetch('/api/current');
                return {
                    ok: response.ok,
                    status: response.status,
                    data: response.ok ? await response.json() : null
                };
            });
            console.log('API /api/current:', currentResponse);
        } catch (error) {
            console.log('Error testing /api/current:', error.message);
        }
        
        try {
            const historyResponse = await page.evaluate(async () => {
                const response = await fetch('/api/history');
                return {
                    ok: response.ok,
                    status: response.status,
                    dataLength: response.ok ? (await response.json()).length : null
                };
            });
            console.log('API /api/history:', historyResponse);
        } catch (error) {
            console.log('Error testing /api/history:', error.message);
        }
        
        // Wait for user input before closing
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

debugDashboard();
