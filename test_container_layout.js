const { chromium } = require('playwright');

async function testContainerLayout() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Container Layout Debug...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Initial state - checking all tabs:');
        const initialState = await page.evaluate(() => {
            const dashboard = document.getElementById('dashboard-tab');
            const analysis = document.getElementById('analysis-tab');
            const processes = document.getElementById('processes-tab');
            
            const getInfo = (el, name) => {
                if (!el) return { name, exists: false };
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                return {
                    name,
                    exists: true,
                    active: el.classList.contains('active'),
                    rect: { width: rect.width, height: rect.height },
                    styles: { display: styles.display, position: styles.position }
                };
            };
            
            return {
                dashboard: getInfo(dashboard, 'dashboard'),
                analysis: getInfo(analysis, 'analysis'),
                processes: getInfo(processes, 'processes')
            };
        });
        
        console.log('   Dashboard:', initialState.dashboard);
        console.log('   Analysis:', initialState.analysis);
        console.log('   Processes:', initialState.processes);
        
        console.log('\n2. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(3000);
            
            // Check state after clicking
            const afterClick = await page.evaluate(() => {
                const dashboard = document.getElementById('dashboard-tab');
                const analysis = document.getElementById('analysis-tab');
                const processes = document.getElementById('processes-tab');
                
                const getInfo = (el, name) => {
                    if (!el) return { name, exists: false };
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    return {
                        name,
                        exists: true,
                        active: el.classList.contains('active'),
                        rect: { width: rect.width, height: rect.height, x: rect.x, y: rect.y },
                        styles: { 
                            display: styles.display, 
                            position: styles.position,
                            width: styles.width,
                            height: styles.height
                        }
                    };
                };
                
                return {
                    dashboard: getInfo(dashboard, 'dashboard'),
                    analysis: getInfo(analysis, 'analysis'),
                    processes: getInfo(processes, 'processes')
                };
            });
            
            console.log('\n3. After clicking processes tab:');
            console.log('   Dashboard:', afterClick.dashboard);
            console.log('   Analysis:', afterClick.analysis);
            console.log('   Processes:', afterClick.processes);
            
            // Try to force the processes tab to be visible by adding content
            console.log('\n4. Adding test content to processes tab...');
            await page.evaluate(() => {
                const processes = document.getElementById('processes-tab');
                if (processes) {
                    // Add a simple test div
                    const testDiv = document.createElement('div');
                    testDiv.innerHTML = '<h1 style="color: red; font-size: 48px; padding: 50px; background: yellow; border: 5px solid black;">TEST CONTENT - PROCESSES TAB</h1>';
                    testDiv.style.width = '100%';
                    testDiv.style.height = '200px';
                    testDiv.style.display = 'block';
                    testDiv.style.position = 'relative';
                    
                    // Insert at the beginning
                    processes.insertBefore(testDiv, processes.firstChild);
                }
            });
            
            await page.waitForTimeout(2000);
            
            // Check if the test content is visible
            const testContentVisible = await page.evaluate(() => {
                const processes = document.getElementById('processes-tab');
                if (!processes) return false;
                
                const rect = processes.getBoundingClientRect();
                const testDiv = processes.querySelector('div');
                const testRect = testDiv ? testDiv.getBoundingClientRect() : null;
                
                return {
                    processesRect: rect,
                    testDivExists: !!testDiv,
                    testRect: testRect
                };
            });
            
            console.log('\n5. Test content visibility:');
            console.log('   Processes tab rect:', testContentVisible.processesRect);
            console.log('   Test div exists:', testContentVisible.testDivExists);
            console.log('   Test div rect:', testContentVisible.testRect);
            
            // Take a screenshot
            await page.screenshot({ path: 'container_layout_debug.png', fullPage: true });
            console.log('   Screenshot saved as container_layout_debug.png');
            
            // Try switching to dashboard and back
            console.log('\n6. Switching to dashboard and back...');
            const dashboardTab = await page.$('div[onclick*="dashboard"]');
            if (dashboardTab) {
                await dashboardTab.click();
                await page.waitForTimeout(1000);
                
                const processesTabAgain = await page.$('div[onclick*="processes"]');
                if (processesTabAgain) {
                    await processesTabAgain.click();
                    await page.waitForTimeout(2000);
                    
                    const finalRect = await page.evaluate(() => {
                        const processes = document.getElementById('processes-tab');
                        return processes ? processes.getBoundingClientRect() : null;
                    });
                    
                    console.log('   Final processes tab rect:', finalRect);
                }
            }
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ Container layout debug completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testContainerLayout();
