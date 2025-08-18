const { chromium } = require('playwright');

async function testDOMHierarchy() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 DOM Hierarchy Debug...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(5000);
            
            // Check the entire DOM hierarchy for the processes tab
            const hierarchyInfo = await page.evaluate(() => {
                const getElementInfo = (selector, name) => {
                    const el = document.querySelector(selector);
                    if (!el) return { name, exists: false };
                    
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    return {
                        name,
                        exists: true,
                        tagName: el.tagName,
                        className: el.className,
                        rect: {
                            width: rect.width,
                            height: rect.height,
                            x: rect.x,
                            y: rect.y
                        },
                        styles: {
                            display: styles.display,
                            position: styles.position,
                            width: styles.width,
                            height: styles.height,
                            minWidth: styles.minWidth,
                            minHeight: styles.minHeight,
                            maxWidth: styles.maxWidth,
                            maxHeight: styles.maxHeight,
                            overflow: styles.overflow,
                            boxSizing: styles.boxSizing
                        }
                    };
                };
                
                return {
                    body: getElementInfo('body', 'body'),
                    container: getElementInfo('.container', 'container'),
                    processesTab: getElementInfo('#processes-tab', 'processes-tab'),
                    card: getElementInfo('#processes-tab .card', 'card'),
                    processList: getElementInfo('#processes-tab .process-list', 'process-list'),
                    processTable: getElementInfo('#processes-tab .process-table', 'process-table'),
                    tableHead: getElementInfo('#processes-tab .process-table thead', 'table-head'),
                    tableBody: getElementInfo('#processes-tab .process-table tbody', 'table-body')
                };
            });
            
            console.log('\n2. DOM Hierarchy Information:');
            Object.entries(hierarchyInfo).forEach(([key, info]) => {
                console.log(`\n   ${key.toUpperCase()}:`);
                if (info.exists) {
                    console.log(`     Tag: ${info.tagName}, Class: "${info.className}"`);
                    console.log(`     Rect: ${info.rect.width}x${info.rect.height} at (${info.rect.x}, ${info.rect.y})`);
                    console.log(`     Display: ${info.styles.display}, Position: ${info.styles.position}`);
                    console.log(`     Width: ${info.styles.width}, Height: ${info.styles.height}`);
                    console.log(`     Min: ${info.styles.minWidth}x${info.styles.minHeight}`);
                    console.log(`     Max: ${info.styles.maxWidth}x${info.styles.maxHeight}`);
                } else {
                    console.log(`     NOT FOUND`);
                }
            });
            
            // Check if there are any CSS rules that might be causing issues
            const cssIssues = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (!processesTab) return [];
                
                const issues = [];
                const styles = window.getComputedStyle(processesTab);
                
                // Check for common layout issues
                if (styles.display === 'none') issues.push('display: none');
                if (styles.visibility === 'hidden') issues.push('visibility: hidden');
                if (styles.opacity === '0') issues.push('opacity: 0');
                if (styles.width === '0px') issues.push('width: 0px');
                if (styles.height === '0px') issues.push('height: 0px');
                if (styles.position === 'absolute' && (styles.left === '-9999px' || styles.top === '-9999px')) {
                    issues.push('positioned off-screen');
                }
                
                return issues;
            });
            
            console.log('\n3. Potential CSS Issues:', cssIssues.length > 0 ? cssIssues : 'None detected');
            
            // Force refresh the page and try again
            console.log('\n4. Refreshing page and retrying...');
            await page.reload({ waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(3000);
            
            // Click processes tab again
            const processesTabAfterReload = await page.$('div[onclick*="processes"]');
            if (processesTabAfterReload) {
                await processesTabAfterReload.click();
                await page.waitForTimeout(3000);
                
                const rectAfterReload = await page.evaluate(() => {
                    const tab = document.getElementById('processes-tab');
                    const table = document.querySelector('#processes-tab .process-table');
                    return {
                        tab: tab ? tab.getBoundingClientRect() : null,
                        table: table ? table.getBoundingClientRect() : null
                    };
                });
                
                console.log('   After reload - Tab rect:', rectAfterReload.tab);
                console.log('   After reload - Table rect:', rectAfterReload.table);
            }
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ DOM hierarchy debug completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testDOMHierarchy();
