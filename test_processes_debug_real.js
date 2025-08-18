const { chromium } = require('playwright');

async function debugProcessesReal() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Debugging Real Processes Tab Issue...');
        
        // Listen to all console messages
        page.on('console', msg => {
            console.log(`BROWSER: ${msg.type()}: ${msg.text()}`);
        });
        
        // Listen to page errors
        page.on('pageerror', error => {
            console.log(`PAGE ERROR: ${error.message}`);
        });
        
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking on Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            console.log('   Processes tab clicked');
            await page.waitForTimeout(5000); // Wait longer for data to load
            
            // Check if fetchProcessData function exists
            const functionExists = await page.evaluate(() => {
                return typeof fetchProcessData === 'function';
            });
            console.log('   fetchProcessData function exists:', functionExists);
            
            // Manually call fetchProcessData and see what happens
            console.log('\n2. Manually calling fetchProcessData...');
            await page.evaluate(() => {
                console.log('About to call fetchProcessData...');
                if (typeof fetchProcessData === 'function') {
                    fetchProcessData();
                } else {
                    console.log('fetchProcessData function not found!');
                }
            });
            
            await page.waitForTimeout(3000);
            
            // Check the process list content
            const processListHTML = await page.$eval('#process-list', el => el.innerHTML);
            console.log('\n3. Process list HTML content:');
            console.log(processListHTML);
            
            // Check if there are any network requests
            console.log('\n4. Testing API call directly from browser...');
            const apiResponse = await page.evaluate(async () => {
                try {
                    const response = await fetch('/api/processes');
                    const data = await response.json();
                    console.log('API Response:', data);
                    return data;
                } catch (error) {
                    console.log('API Error:', error);
                    return { error: error.message };
                }
            });
            
            console.log('   API response from browser:', JSON.stringify(apiResponse, null, 2));
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\nPress Enter to close...');
        await new Promise(resolve => {
            process.stdin.once('data', resolve);
        });
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

debugProcessesReal();
