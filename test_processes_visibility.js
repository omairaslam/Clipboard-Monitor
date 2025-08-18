const { chromium } = require('playwright');

async function testProcessesVisibility() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Testing Processes Tab Visibility...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Initial state - Dashboard tab should be active:');
        const dashboardVisible = await page.evaluate(() => {
            const tab = document.getElementById('dashboard-tab');
            return tab && tab.classList.contains('active');
        });
        console.log('   Dashboard tab active:', dashboardVisible);
        
        console.log('\n2. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(2000);
            
            // Check if processes tab is active
            const processesTabActive = await page.evaluate(() => {
                const tab = document.getElementById('processes-tab');
                return tab && tab.classList.contains('active');
            });
            console.log('   Processes tab active:', processesTabActive);
            
            // Check if processes tab is visible
            const processesTabVisible = await page.evaluate(() => {
                const tab = document.getElementById('processes-tab');
                return tab && window.getComputedStyle(tab).display !== 'none';
            });
            console.log('   Processes tab visible:', processesTabVisible);
            
            // Check if dashboard tab is hidden
            const dashboardHidden = await page.evaluate(() => {
                const tab = document.getElementById('dashboard-tab');
                return tab && !tab.classList.contains('active');
            });
            console.log('   Dashboard tab hidden:', dashboardHidden);
            
            // Check table visibility
            const tableVisible = await page.evaluate(() => {
                const table = document.querySelector('#processes-tab .process-table');
                return table && window.getComputedStyle(table).display !== 'none';
            });
            console.log('   Process table visible:', tableVisible);
            
            // Check if table has data
            const tableRows = await page.$$('#process-list tr');
            console.log('   Table rows count:', tableRows.length);
            
            // Get computed styles for the processes tab
            const tabStyles = await page.evaluate(() => {
                const tab = document.getElementById('processes-tab');
                if (!tab) return null;
                const styles = window.getComputedStyle(tab);
                return {
                    display: styles.display,
                    visibility: styles.visibility,
                    opacity: styles.opacity,
                    height: styles.height,
                    overflow: styles.overflow
                };
            });
            console.log('   Processes tab styles:', tabStyles);
            
            // Take a screenshot
            await page.screenshot({ path: 'processes_visibility_test.png', fullPage: true });
            console.log('   Screenshot saved as processes_visibility_test.png');
            
        } else {
            console.log('   Processes tab button not found!');
        }
        
        console.log('\n✅ Test completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testProcessesVisibility();
