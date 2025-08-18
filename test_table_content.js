const { chromium } = require('playwright');

async function testTableContent() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Table Content Debug...');
        await page.goto('http://localhost:8001', { waitUntil: 'domcontentloaded', timeout: 15000 });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        console.log('\n1. Clicking Processes tab...');
        const processesTab = await page.$('div[onclick*="processes"]');
        if (processesTab) {
            await processesTab.click();
            await page.waitForTimeout(5000);
            
            // Get the complete table HTML
            const tableInfo = await page.evaluate(() => {
                const table = document.querySelector('#processes-tab .process-table');
                const tbody = document.querySelector('#processes-tab .process-table tbody');
                const rows = document.querySelectorAll('#processes-tab .process-table tbody tr');
                
                const rowDetails = Array.from(rows).map((row, index) => {
                    const rect = row.getBoundingClientRect();
                    const styles = window.getComputedStyle(row);
                    const cells = Array.from(row.querySelectorAll('td')).map(cell => ({
                        text: cell.textContent.trim(),
                        html: cell.innerHTML.trim(),
                        rect: cell.getBoundingClientRect()
                    }));
                    
                    return {
                        index,
                        rect: { width: rect.width, height: rect.height },
                        styles: {
                            display: styles.display,
                            height: styles.height,
                            padding: styles.padding
                        },
                        cellCount: cells.length,
                        cells: cells
                    };
                });
                
                return {
                    tableExists: !!table,
                    tbodyExists: !!tbody,
                    tableHTML: table ? table.outerHTML : null,
                    tbodyHTML: tbody ? tbody.innerHTML : null,
                    rowCount: rows.length,
                    rowDetails: rowDetails
                };
            });
            
            console.log('\n2. Table Information:');
            console.log('   Table exists:', tableInfo.tableExists);
            console.log('   Tbody exists:', tableInfo.tbodyExists);
            console.log('   Row count:', tableInfo.rowCount);
            
            console.log('\n3. Row Details:');
            tableInfo.rowDetails.forEach((row, index) => {
                console.log(`   Row ${index}:`);
                console.log(`     Dimensions: ${row.rect.width}x${row.rect.height}`);
                console.log(`     Display: ${row.styles.display}, Height: ${row.styles.height}`);
                console.log(`     Cell count: ${row.cellCount}`);
                if (row.cells.length > 0) {
                    console.log(`     First cell text: "${row.cells[0].text}"`);
                    console.log(`     First cell dimensions: ${row.cells[0].rect.width}x${row.cells[0].rect.height}`);
                }
            });
            
            console.log('\n4. Complete tbody HTML:');
            console.log(tableInfo.tbodyHTML);
            
            // Try to force the table to have dimensions
            console.log('\n5. Forcing table dimensions...');
            await page.evaluate(() => {
                const table = document.querySelector('#processes-tab .process-table');
                if (table) {
                    table.style.width = '100%';
                    table.style.minWidth = '600px';
                    table.style.height = 'auto';
                    table.style.minHeight = '100px';
                    table.style.border = '2px solid red'; // Debug border
                }
                
                const processesTab = document.getElementById('processes-tab');
                if (processesTab) {
                    processesTab.style.width = '100%';
                    processesTab.style.minHeight = '300px';
                    processesTab.style.border = '2px solid blue'; // Debug border
                }
            });
            
            await page.waitForTimeout(2000);
            
            // Check dimensions after forcing
            const dimensionsAfter = await page.evaluate(() => {
                const table = document.querySelector('#processes-tab .process-table');
                const tab = document.getElementById('processes-tab');
                return {
                    table: table ? table.getBoundingClientRect() : null,
                    tab: tab ? tab.getBoundingClientRect() : null
                };
            });
            
            console.log('\n6. Dimensions after forcing:');
            console.log('   Table:', dimensionsAfter.table);
            console.log('   Tab:', dimensionsAfter.tab);
            
            // Take a screenshot
            await page.screenshot({ path: 'table_debug.png', fullPage: true });
            console.log('   Screenshot saved as table_debug.png');
            
        } else {
            console.log('   Processes tab not found!');
        }
        
        console.log('\n✅ Table content debug completed!');
        
    } catch (error) {
        console.error('❌ Error:', error);
    } finally {
        await browser.close();
    }
}

testTableContent();
