const { chromium } = require('playwright');

async function testSimpleContent() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Simple Content Test...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(2000);
            
            // Replace the entire processes tab content with simple HTML
            console.log('\n2. Replacing with simple content...');
            await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (processesTab) {
                    processesTab.innerHTML = `
                        <div style="
                            width: 800px !important; 
                            height: 400px !important; 
                            background: red !important; 
                            color: white !important; 
                            font-size: 24px !important; 
                            padding: 50px !important; 
                            margin: 20px !important;
                            border: 10px solid black !important;
                            display: block !important;
                            position: relative !important;
                        ">
                            <h1>SIMPLE TEST CONTENT</h1>
                            <p>This should be visible!</p>
                            <p>Width: 800px, Height: 400px</p>
                            <p>Background: RED</p>
                        </div>
                    `;
                }
            });
            
            await page.waitForTimeout(2000);
            
            // Check if the simple content is visible
            const simpleContentRect = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                const testDiv = processesTab ? processesTab.querySelector('div') : null;
                
                return {
                    processesTab: processesTab ? processesTab.getBoundingClientRect() : null,
                    testDiv: testDiv ? testDiv.getBoundingClientRect() : null,
                    processesTabHTML: processesTab ? processesTab.innerHTML.substring(0, 200) : null
                };
            });
            
            console.log('\n3. Simple content results:');
            console.log('   Processes tab rect:', simpleContentRect.processesTab);
            console.log('   Test div rect:', simpleContentRect.testDiv);
            console.log('   HTML preview:', simpleContentRect.processesTabHTML);
            
            // Take a screenshot
            await page.screenshot({ path: 'simple_content_test.png', fullPage: true });
            console.log('   Screenshot saved as simple_content_test.png');
            
            // Try to scroll to the element
            await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (processesTab) {
                    processesTab.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
            
            await page.waitForTimeout(2000);
            await page.screenshot({ path: 'simple_content_scrolled.png', fullPage: true });
            console.log('   Scrolled screenshot saved as simple_content_scrolled.png');
            
            // Check if we can see it by looking at the viewport
            const inViewport = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (!processesTab) return false;
                
                const rect = processesTab.getBoundingClientRect();
                return {
                    rect: rect,
                    inViewport: rect.top >= 0 && rect.left >= 0 && 
                               rect.bottom <= window.innerHeight && 
                               rect.right <= window.innerWidth,
                    viewport: { width: window.innerWidth, height: window.innerHeight }
                };
            });
            
            console.log('\n4. Viewport check:');
            console.log('   Element rect:', inViewport.rect);
            console.log('   In viewport:', inViewport.inViewport);
            console.log('   Viewport size:', inViewport.viewport);
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ Simple content test completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testSimpleContent();
