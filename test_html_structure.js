const { chromium } = require('playwright');

async function testHTMLStructure() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 HTML Structure Analysis...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Getting complete HTML structure around tabs...');
        
        // Get the HTML structure around the tabs
        const htmlStructure = await page.evaluate(() => {
            const container = document.querySelector('.container');
            if (!container) return 'Container not found';
            
            // Find the tabs section and everything after it
            const tabsDiv = container.querySelector('.tabs');
            if (!tabsDiv) return 'Tabs not found';
            
            // Get all siblings after the tabs div
            let html = '';
            let current = tabsDiv;
            
            while (current) {
                if (current.nodeType === 1) { // Element node
                    const tagName = current.tagName.toLowerCase();
                    const id = current.id ? ` id="${current.id}"` : '';
                    const className = current.className ? ` class="${current.className}"` : '';
                    
                    if (tagName === 'div' && (current.id === 'dashboard-tab' || current.id === 'analysis-tab' || current.id === 'processes-tab')) {
                        html += `<${tagName}${id}${className}>\n`;
                        
                        // For tab content, show the first few children
                        const children = Array.from(current.children).slice(0, 3);
                        children.forEach(child => {
                            const childTag = child.tagName.toLowerCase();
                            const childId = child.id ? ` id="${child.id}"` : '';
                            const childClass = child.className ? ` class="${child.className}"` : '';
                            html += `  <${childTag}${childId}${childClass}>...</${childTag}>\n`;
                        });
                        
                        html += `</${tagName}>\n\n`;
                    } else if (tagName === 'div' && current.className === 'tabs') {
                        html += `<${tagName}${className}>...</${tagName}>\n\n`;
                    }
                }
                current = current.nextSibling;
            }
            
            return html;
        });
        
        console.log('HTML Structure:');
        console.log(htmlStructure);
        
        console.log('\n2. Checking parent-child relationships...');
        
        const relationships = await page.evaluate(() => {
            const dashboard = document.getElementById('dashboard-tab');
            const analysis = document.getElementById('analysis-tab');
            const processes = document.getElementById('processes-tab');
            
            const getParentInfo = (element, name) => {
                if (!element) return { name, exists: false };
                
                const parent = element.parentElement;
                return {
                    name,
                    exists: true,
                    parent: parent ? {
                        tagName: parent.tagName,
                        id: parent.id,
                        className: parent.className
                    } : null,
                    nextSibling: element.nextElementSibling ? {
                        tagName: element.nextElementSibling.tagName,
                        id: element.nextElementSibling.id,
                        className: element.nextElementSibling.className
                    } : null,
                    previousSibling: element.previousElementSibling ? {
                        tagName: element.previousElementSibling.tagName,
                        id: element.previousElementSibling.id,
                        className: element.previousElementSibling.className
                    } : null
                };
            };
            
            return {
                dashboard: getParentInfo(dashboard, 'dashboard-tab'),
                analysis: getParentInfo(analysis, 'analysis-tab'),
                processes: getParentInfo(processes, 'processes-tab')
            };
        });
        
        console.log('Relationships:');
        Object.entries(relationships).forEach(([key, info]) => {
            console.log(`\n   ${key.toUpperCase()}:`);
            if (info.exists) {
                console.log(`     Parent: ${info.parent?.tagName}#${info.parent?.id}.${info.parent?.className}`);
                console.log(`     Previous: ${info.previousSibling?.tagName}#${info.previousSibling?.id || 'none'}`);
                console.log(`     Next: ${info.nextSibling?.tagName}#${info.nextSibling?.id || 'none'}`);
            } else {
                console.log(`     NOT FOUND`);
            }
        });
        
        console.log('\n3. Checking if processes tab is nested inside analysis tab...');
        
        const isNested = await page.evaluate(() => {
            const analysis = document.getElementById('analysis-tab');
            const processes = document.getElementById('processes-tab');
            
            if (!analysis || !processes) return false;
            
            // Check if processes is a descendant of analysis
            return analysis.contains(processes);
        });
        
        console.log('   Processes tab nested inside analysis tab:', isNested);
        
        if (isNested) {
            console.log('\n4. Finding the exact nesting path...');
            
            const nestingPath = await page.evaluate(() => {
                const analysis = document.getElementById('analysis-tab');
                const processes = document.getElementById('processes-tab');
                
                if (!analysis || !processes) return [];
                
                const path = [];
                let current = processes.parentElement;
                
                while (current && current !== analysis.parentElement) {
                    path.push({
                        tagName: current.tagName,
                        id: current.id,
                        className: current.className
                    });
                    current = current.parentElement;
                }
                
                return path;
            });
            
            console.log('   Nesting path (from processes to analysis):');
            nestingPath.forEach((element, index) => {
                console.log(`     ${index + 1}. ${element.tagName}#${element.id}.${element.className}`);
            });
        }
        
        console.log('\n✅ HTML structure analysis completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testHTMLStructure();
