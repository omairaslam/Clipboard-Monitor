const { chromium } = require('playwright');

async function testProcessesDetailed() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Detailed Processes Tab Analysis...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            
            // Check initial state immediately
            console.log('\n2. Immediate state after click:');
            let tableHTML = await page.$eval('#process-list', el => el.innerHTML);
            console.log('   Initial table HTML:', tableHTML.substring(0, 200) + '...');
            
            // Wait and check again
            await page.waitForTimeout(1000);
            console.log('\n3. After 1 second:');
            tableHTML = await page.$eval('#process-list', el => el.innerHTML);
            console.log('   Table HTML:', tableHTML.substring(0, 200) + '...');
            
            // Wait longer and check
            await page.waitForTimeout(3000);
            console.log('\n4. After 4 seconds total:');
            tableHTML = await page.$eval('#process-list', el => el.innerHTML);
            console.log('   Table HTML:', tableHTML.substring(0, 300) + '...');
            
            // Check if fetchProcessData was called
            const fetchCalled = await page.evaluate(() => {
                return window.__fetchProcessDataCalled || false;
            });
            console.log('   fetchProcessData called:', fetchCalled);
            
            // Manually call fetchProcessData and monitor
            console.log('\n5. Manually calling fetchProcessData...');
            await page.evaluate(() => {
                window.__fetchProcessDataCalled = true;
                console.log('About to call fetchProcessData manually...');
                if (typeof fetchProcessData === 'function') {
                    fetchProcessData();
                } else {
                    console.log('fetchProcessData not found!');
                }
            });
            
            // Wait for the manual call to complete
            await page.waitForTimeout(2000);
            console.log('\n6. After manual fetchProcessData call:');
            tableHTML = await page.$eval('#process-list', el => el.innerHTML);
            console.log('   Final table HTML:', tableHTML);
            
            // Check if there are any JavaScript errors
            const errors = await page.evaluate(() => {
                return window.__jsErrors || [];
            });
            console.log('   JavaScript errors:', errors);
            
            // Check network requests
            console.log('\n7. Testing direct API call:');
            const apiResult = await page.evaluate(async () => {
                try {
                    const response = await fetch('/api/processes');
                    const data = await response.json();
                    return { success: true, data: data };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            });
            console.log('   API call result:', apiResult.success ? 'SUCCESS' : 'FAILED');
            if (apiResult.success) {
                console.log('   Process count:', apiResult.data.clipboard_processes.length);
            } else {
                console.log('   API error:', apiResult.error);
            }
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ Analysis completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testProcessesDetailed();
