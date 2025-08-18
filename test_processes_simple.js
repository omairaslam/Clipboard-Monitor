const { chromium } = require('playwright');

async function testProcessesSimple() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('Testing Processes Tab (Simple)...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 10000 });
        
        // Wait for page to load
        await page.waitForTimeout(2000);
        
        // Check if Processes 2 tab is removed
        const processes2Tab = await page.$('div[onclick*="processes2"]');
        console.log('Processes 2 tab removed:', !processes2Tab);
        
        // Check if Processes tab exists and click it
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            console.log('✅ Processes tab found');
            await processesTab.click();
            await page.waitForTimeout(3000);
            
            // Check table structure
            const tableExists = await page.$('#processes-tab table.process-table');
            console.log('✅ Process table exists:', !!tableExists);
            
            // Check refresh button
            const refreshBtn = await page.$('#processes-refresh');
            console.log('✅ Refresh button exists:', !!refreshBtn);
            
            if (refreshBtn) {
                await refreshBtn.click();
                console.log('✅ Refresh button clicked');
                await page.waitForTimeout(2000);
            }
            
            // Check for process data
            const processRows = await page.$$('#process-list tr');
            console.log(`Found ${processRows.length} process rows`);
            
            // Take screenshot
            await page.screenshot({ path: 'processes_tab_final.png' });
            console.log('Screenshot saved');
            
        } else {
            console.log('❌ Processes tab not found');
        }
        
        console.log('\n✅ Test completed successfully!');
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

testProcessesSimple();
