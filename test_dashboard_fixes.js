const { chromium } = require('playwright');

async function testDashboardFixes() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🧪 Testing Dashboard Fixes...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n📊 Testing Memory Chart Visibility...');
        
        // Test 1: Memory chart should be visible in Dashboard tab
        console.log('1. Dashboard tab (should show memory chart):');
        const dashboardTab = await page.$('div[onclick*="dashboard"]');
        if (dashboardTab) {
            await dashboardTab.click();
            await page.waitForTimeout(1000);
            
            const memoryChart = await page.$('#memoryChart');
            const chartVisible = await page.evaluate(() => {
                const chart = document.getElementById('memoryChart');
                return chart && chart.offsetParent !== null;
            });
            console.log('   Memory chart visible:', chartVisible ? '✅ YES' : '❌ NO');
        }
        
        // Test 2: Memory chart should NOT be visible in Analysis tab
        console.log('2. Analysis tab (should NOT show memory chart):');
        const analysisTab = await page.$('div[onclick*="analysis"]');
        if (analysisTab) {
            await analysisTab.click();
            await page.waitForTimeout(1000);
            
            const chartVisible = await page.evaluate(() => {
                const chart = document.getElementById('memoryChart');
                return chart && chart.offsetParent !== null;
            });
            console.log('   Memory chart visible:', chartVisible ? '❌ STILL VISIBLE' : '✅ HIDDEN');
        }
        
        // Test 3: Memory chart should NOT be visible in Processes tab
        console.log('3. Processes tab (should NOT show memory chart):');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(3000);
            
            const chartVisible = await page.evaluate(() => {
                const chart = document.getElementById('memoryChart');
                return chart && chart.offsetParent !== null;
            });
            console.log('   Memory chart visible:', chartVisible ? '❌ STILL VISIBLE' : '✅ HIDDEN');
            
            // Test 4: Check if processes data is showing
            console.log('\n⚙️ Testing Processes Tab Data...');
            const processRows = await page.$$('#process-list tr');
            console.log('   Process rows found:', processRows.length);
            
            if (processRows.length > 0) {
                const tableData = await page.$$eval('#process-list tr', rows => 
                    rows.map(row => {
                        const cells = row.querySelectorAll('td');
                        return Array.from(cells).map(cell => cell.textContent.trim());
                    })
                );
                
                console.log('   Process data:');
                tableData.forEach((row, index) => {
                    if (row.length === 6) {
                        console.log(`     ${row[0]} | PID: ${row[1]} | Memory: ${row[2]}MB | CPU: ${row[3]}% | Uptime: ${row[4]} | Status: ${row[5]}`);
                    } else if (row.length === 1) {
                        console.log(`     ${row[0]}`);
                    }
                });
                
                // Check if we have actual process data (not just loading message)
                const hasRealData = tableData.some(row => 
                    row.length === 6 && !row[0].includes('Loading') && !row[0].includes('Error')
                );
                console.log('   Real process data found:', hasRealData ? '✅ YES' : '❌ NO');
            }
        }
        
        // Test 5: Go back to Dashboard and verify chart is visible again
        console.log('\n4. Back to Dashboard tab (should show memory chart again):');
        if (dashboardTab) {
            await dashboardTab.click();
            await page.waitForTimeout(1000);
            
            const chartVisible = await page.evaluate(() => {
                const chart = document.getElementById('memoryChart');
                return chart && chart.offsetParent !== null;
            });
            console.log('   Memory chart visible:', chartVisible ? '✅ YES' : '❌ NO');
        }
        
        // Take screenshots
        await page.screenshot({ path: 'dashboard_fixes_test.png', fullPage: true });
        console.log('\n📸 Screenshot saved as dashboard_fixes_test.png');
        
        console.log('\n🎉 Test completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testDashboardFixes();
