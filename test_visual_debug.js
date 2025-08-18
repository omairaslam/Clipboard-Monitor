const { chromium } = require('playwright');

async function testVisualDebug() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Visual Debug - Checking Element Positions...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(5000); // Wait longer for data to load
            
            // Check element dimensions and positions
            const elementInfo = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                const processTable = document.querySelector('#processes-tab .process-table');
                const processRows = document.querySelectorAll('#process-list tr');
                
                const getElementInfo = (el, name) => {
                    if (!el) return { name, exists: false };
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    return {
                        name,
                        exists: true,
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            left: rect.left
                        },
                        styles: {
                            display: styles.display,
                            visibility: styles.visibility,
                            opacity: styles.opacity,
                            overflow: styles.overflow,
                            position: styles.position,
                            zIndex: styles.zIndex
                        },
                        innerHTML: el.innerHTML.substring(0, 200)
                    };
                };
                
                return {
                    processesTab: getElementInfo(processesTab, 'processes-tab'),
                    processTable: getElementInfo(processTable, 'process-table'),
                    rowCount: processRows.length,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                };
            });
            
            console.log('\n2. Element Information:');
            console.log('   Processes Tab:', JSON.stringify(elementInfo.processesTab, null, 2));
            console.log('   Process Table:', JSON.stringify(elementInfo.processTable, null, 2));
            console.log('   Row Count:', elementInfo.rowCount);
            console.log('   Viewport:', elementInfo.viewport);
            
            // Check if elements are in viewport
            const inViewport = await page.evaluate(() => {
                const processTable = document.querySelector('#processes-tab .process-table');
                if (!processTable) return false;
                
                const rect = processTable.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= window.innerHeight &&
                    rect.right <= window.innerWidth
                );
            });
            console.log('   Table in viewport:', inViewport);
            
            // Take a screenshot for visual inspection
            await page.screenshot({ path: 'visual_debug.png', fullPage: true });
            console.log('   Screenshot saved as visual_debug.png');
            
            // Scroll to the table to make sure it's visible
            await page.evaluate(() => {
                const processTable = document.querySelector('#processes-tab .process-table');
                if (processTable) {
                    processTable.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
            
            await page.waitForTimeout(2000);
            await page.screenshot({ path: 'visual_debug_scrolled.png', fullPage: true });
            console.log('   Scrolled screenshot saved as visual_debug_scrolled.png');
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ Visual debug completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testVisualDebug();
