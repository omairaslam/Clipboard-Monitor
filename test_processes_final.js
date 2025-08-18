const { chromium } = require('playwright');

async function testProcessesFinal() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🧪 Final Processes Tab Test...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 10000 });
        
        // Wait for page to load
        await page.waitForTimeout(2000);
        
        // Click on Processes tab
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(3000);
            
            // Check table data
            const tableData = await page.$$eval('#process-list tr', rows => 
                rows.map(row => {
                    const cells = row.querySelectorAll('td');
                    return Array.from(cells).map(cell => cell.textContent.trim());
                })
            );
            
            console.log('✅ Process table data:');
            tableData.forEach((row, index) => {
                if (row.length === 6) {
                    console.log(`   Row ${index + 1}: ${row[0]} | PID: ${row[1]} | Memory: ${row[2]}MB | CPU: ${row[3]}% | Uptime: ${row[4]} | Status: ${row[5]}`);
                } else {
                    console.log(`   Row ${index + 1}: ${row.join(' | ')}`);
                }
            });
            
            // Check if uptime is showing correctly (not NaN)
            const uptimeValues = tableData.map(row => row[4]).filter(uptime => uptime && uptime !== '--');
            const hasValidUptime = uptimeValues.some(uptime => !uptime.includes('NaN'));
            
            console.log('✅ Uptime values:', uptimeValues);
            console.log('✅ Valid uptime display:', hasValidUptime ? 'YES' : 'NO');
            
            // Check refresh button
            const refreshBtn = await page.$('#processes-refresh');
            if (refreshBtn) {
                console.log('✅ Refresh button found');
                await refreshBtn.click();
                console.log('✅ Refresh button clicked successfully');
                await page.waitForTimeout(2000);
            }
            
            // Take final screenshot
            await page.screenshot({ path: 'processes_tab_final_working.png' });
            console.log('✅ Screenshot saved as processes_tab_final_working.png');
            
        } else {
            console.log('❌ Processes tab not found');
        }
        
        console.log('\n🎉 Test completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testProcessesFinal();
