const { chromium } = require('playwright');

async function testChartFix() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('Testing chart fix...');
        await page.goto('http://localhost:8001', { waitUntil: 'networkidle' });
        
        // Wait for chart to initialize
        await page.waitForTimeout(3000);
        
        // Get chart position info
        const chartInfo = await page.evaluate(() => {
            const canvas = document.getElementById('memoryChart');
            if (!canvas) return { error: 'Canvas not found' };
            
            const rect = canvas.getBoundingClientRect();
            return {
                position: {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                },
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                inViewport: rect.top >= 0 && rect.top < window.innerHeight,
                isVisible: rect.width > 0 && rect.height > 0
            };
        });
        
        console.log('Chart Info:', chartInfo);
        
        if (chartInfo.inViewport) {
            console.log('✅ SUCCESS: Memory chart is now visible in viewport!');
        } else {
            console.log('❌ ISSUE: Memory chart is still outside viewport');
        }
        
        // Take a screenshot
        await page.screenshot({ path: 'chart_fix_test.png', fullPage: false });
        console.log('Screenshot saved as chart_fix_test.png');
        
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

testChartFix();
