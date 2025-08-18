const { chromium } = require('playwright');

async function testCSSDebug() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 CSS Debug - Deep Analysis...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(2000);
            
            // Get ALL computed styles for the processes tab
            const allStyles = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (!processesTab) return null;
                
                const styles = window.getComputedStyle(processesTab);
                const styleObj = {};
                
                // Get all CSS properties
                for (let i = 0; i < styles.length; i++) {
                    const prop = styles[i];
                    styleObj[prop] = styles.getPropertyValue(prop);
                }
                
                return {
                    element: processesTab.tagName + '#' + processesTab.id,
                    className: processesTab.className,
                    styles: styleObj,
                    parentElement: processesTab.parentElement ? {
                        tagName: processesTab.parentElement.tagName,
                        className: processesTab.parentElement.className,
                        id: processesTab.parentElement.id
                    } : null
                };
            });
            
            console.log('\n2. Complete CSS Analysis:');
            console.log('   Element:', allStyles.element);
            console.log('   Class:', allStyles.className);
            console.log('   Parent:', allStyles.parentElement);
            
            // Check key layout properties
            const keyProps = [
                'display', 'position', 'width', 'height', 'min-width', 'min-height',
                'max-width', 'max-height', 'margin', 'padding', 'border',
                'box-sizing', 'overflow', 'visibility', 'opacity', 'z-index',
                'transform', 'left', 'top', 'right', 'bottom'
            ];
            
            console.log('\n3. Key Layout Properties:');
            keyProps.forEach(prop => {
                if (allStyles.styles[prop]) {
                    console.log(`   ${prop}: ${allStyles.styles[prop]}`);
                }
            });
            
            // Check if there are any CSS rules that might be overriding
            const cssRules = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (!processesTab) return [];
                
                const rules = [];
                const sheets = Array.from(document.styleSheets);
                
                sheets.forEach(sheet => {
                    try {
                        const cssRules = Array.from(sheet.cssRules || sheet.rules || []);
                        cssRules.forEach(rule => {
                            if (rule.selectorText && rule.selectorText.includes('processes-tab')) {
                                rules.push({
                                    selector: rule.selectorText,
                                    cssText: rule.cssText
                                });
                            }
                        });
                    } catch (e) {
                        // Cross-origin or other access issues
                    }
                });
                
                return rules;
            });
            
            console.log('\n4. CSS Rules targeting processes-tab:');
            cssRules.forEach(rule => {
                console.log(`   ${rule.selector}: ${rule.cssText}`);
            });
            
            // Try to force the element to be visible by removing all CSS classes
            console.log('\n5. Removing all CSS classes and forcing visibility...');
            await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                if (processesTab) {
                    // Remove all classes
                    processesTab.className = '';
                    
                    // Force basic styles
                    processesTab.style.cssText = `
                        display: block !important;
                        position: static !important;
                        width: 1000px !important;
                        height: 500px !important;
                        background: lime !important;
                        color: black !important;
                        font-size: 20px !important;
                        padding: 50px !important;
                        margin: 20px !important;
                        border: 5px solid purple !important;
                        visibility: visible !important;
                        opacity: 1 !important;
                        z-index: 9999 !important;
                        overflow: visible !important;
                        box-sizing: border-box !important;
                    `;
                    
                    // Add simple content
                    processesTab.innerHTML = '<h1>FORCED VISIBILITY TEST</h1><p>This should definitely be visible now!</p>';
                }
            });
            
            await page.waitForTimeout(2000);
            
            // Check the result
            const forcedResult = await page.evaluate(() => {
                const processesTab = document.getElementById('processes-tab');
                return processesTab ? processesTab.getBoundingClientRect() : null;
            });
            
            console.log('\n6. After forcing visibility:');
            console.log('   Rect:', forcedResult);
            
            // Take a screenshot
            await page.screenshot({ path: 'css_debug_forced.png', fullPage: true });
            console.log('   Screenshot saved as css_debug_forced.png');
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ CSS debug completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testCSSDebug();
