const { chromium } = require('playwright');

async function testSwitchTabDebug() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Debugging switchTab Function...');
        
        // Listen to console messages
        page.on('console', msg => {
            console.log(`BROWSER: ${msg.type()}: ${msg.text()}`);
        });
        
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        // Inject debugging into switchTab function
        await page.evaluate(() => {
            // Store original switchTab function
            window.__originalSwitchTab = window.switchTab;
            
            // Override switchTab with debugging
            window.switchTab = function(tabName, el) {
                console.log(`switchTab called with tabName: "${tabName}"`);
                console.log('switchTab element:', el);
                
                if (tabName === 'processes') {
                    console.log('Processes tab detected - should call fetchProcessData');
                }
                
                // Call original function
                if (window.__originalSwitchTab) {
                    return window.__originalSwitchTab(tabName, el);
                } else {
                    console.log('Original switchTab function not found!');
                }
            };
            
            // Also debug fetchProcessData
            if (typeof fetchProcessData === 'function') {
                window.__originalFetchProcessData = window.fetchProcessData;
                window.fetchProcessData = function() {
                    console.log('fetchProcessData called!');
                    return window.__originalFetchProcessData();
                };
            } else {
                console.log('fetchProcessData function not found!');
            }
        });
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(3000);
            
            // Check if the tab is active
            const isActive = await page.evaluate(() => {
                const tab = document.getElementById('processes-tab');
                return tab && tab.classList.contains('active');
            });
            console.log('   Processes tab active:', isActive);
            
            // Check the onclick attribute
            const onclickAttr = await page.evaluate(() => {
                const tab = document.querySelector('div[onclick*="processes"]');
                return tab ? tab.getAttribute('onclick') : null;
            });
            console.log('   Onclick attribute:', onclickAttr);
            
            // Try calling switchTab manually
            console.log('\n2. Manually calling switchTab...');
            await page.evaluate(() => {
                console.log('About to call switchTab manually...');
                if (typeof switchTab === 'function') {
                    switchTab('processes', null);
                } else {
                    console.log('switchTab function not found!');
                }
            });
            
            await page.waitForTimeout(2000);
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ Debug completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testSwitchTabDebug();
