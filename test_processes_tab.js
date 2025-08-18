const { chromium } = require('playwright');

async function testProcessesTab() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('Testing Processes Tab...');
        await page.goto('http://localhost:8001', { waitUntil: 'networkidle' });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        // Check if Processes 2 tab is removed
        const processes2Tab = await page.$('div[onclick="switchTab(\'processes2\', this)"]');
        if (processes2Tab) {
            console.log('❌ FAIL: Processes 2 tab still exists');
        } else {
            console.log('✅ SUCCESS: Processes 2 tab removed');
        }
        
        // Check if Processes tab exists
        const processesTab = await page.$('div[onclick="switchTab(\'processes\', this)"]');
        if (processesTab) {
            console.log('✅ SUCCESS: Processes tab exists');
            
            // Click on Processes tab
            await processesTab.click();
            await page.waitForTimeout(2000);
            
            // Check if processes table has correct headers
            const headers = await page.$$eval('#processes-tab th', elements => 
                elements.map(el => el.textContent.trim())
            );
            
            console.log('Table headers:', headers);
            
            const expectedHeaders = ['Process Name', 'PID', 'Memory (MB)', 'CPU (%)', 'Uptime', 'Status'];
            const headersMatch = expectedHeaders.every(header => headers.includes(header));
            
            if (headersMatch) {
                console.log('✅ SUCCESS: Table headers are correct');
            } else {
                console.log('❌ FAIL: Table headers incorrect');
                console.log('Expected:', expectedHeaders);
                console.log('Actual:', headers);
            }
            
            // Check if refresh button exists
            const refreshButton = await page.$('#processes-refresh');
            if (refreshButton) {
                console.log('✅ SUCCESS: Refresh button exists');
                
                // Test refresh button
                await refreshButton.click();
                await page.waitForTimeout(1000);
                console.log('✅ SUCCESS: Refresh button clicked successfully');
            } else {
                console.log('❌ FAIL: Refresh button not found');
            }
            
            // Check if process data is loading
            await page.waitForTimeout(3000);
            const processRows = await page.$$('#process-list tr');
            console.log(`Found ${processRows.length} process rows`);
            
            if (processRows.length > 0) {
                console.log('✅ SUCCESS: Process data is loading');
                
                // Check first row content
                const firstRowCells = await page.$$eval('#process-list tr:first-child td', 
                    cells => cells.map(cell => cell.textContent.trim())
                );
                console.log('First row data:', firstRowCells);
                
                if (firstRowCells.length === 6) {
                    console.log('✅ SUCCESS: Process rows have correct number of columns');
                } else {
                    console.log('❌ FAIL: Process rows have incorrect number of columns');
                }
            } else {
                console.log('⚠️ WARNING: No process data found (this might be normal if no processes are running)');
            }
            
        } else {
            console.log('❌ FAIL: Processes tab not found');
        }
        
        // Take a screenshot
        await page.screenshot({ path: 'processes_tab_test.png', fullPage: true });
        console.log('Screenshot saved as processes_tab_test.png');
        
        console.log('\nPress Enter to close browser...');
        await new Promise(resolve => {
            process.stdin.once('data', resolve);
        });
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

testProcessesTab();
