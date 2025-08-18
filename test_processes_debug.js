const { chromium } = require('playwright');

async function debugProcessesTab() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('Opening dashboard...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        // Click on Processes tab
        console.log('Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(2000);
            
            // Listen to console logs
            page.on('console', msg => {
                console.log('BROWSER CONSOLE:', msg.text());
            });
            
            // Manually trigger fetchProcessData
            console.log('Triggering fetchProcessData...');
            await page.evaluate(() => {
                if (typeof fetchProcessData === 'function') {
                    fetchProcessData();
                } else {
                    console.log('fetchProcessData function not found');
                }
            });
            
            await page.waitForTimeout(5000);
            
            // Check what's in the process list
            const processListHTML = await page.$eval('#process-list', el => el.innerHTML);
            console.log('Process list HTML:', processListHTML);
            
            // Check if there are any errors
            const errorMessages = await page.$$eval('#process-list td', cells => 
                cells.map(cell => cell.textContent).filter(text => text.includes('Error') || text.includes('Loading'))
            );
            console.log('Error/Loading messages:', errorMessages);
            
        } else {
            console.log('Processes tab not found');
        }
        
        console.log('\nPress Enter to close...');
        await new Promise(resolve => {
            process.stdin.once('data', resolve);
        });
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

debugProcessesTab();
