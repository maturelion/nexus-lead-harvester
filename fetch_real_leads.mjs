import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const DOMAINS = [
    'villagecharteracademy.com',
    'yubacitycharter.com',
    'theeducationcorps.com',
    'siatechschools.org',
    'twinriverscharter.com'
];

(async () => {
    const userDataDir = path.join(__dirname, '../google_user_data_osint');
    const browserContext = await chromium.launchPersistentContext(userDataDir, {
        headless: true,
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    });

    const page = await browserContext.newPage();
    const results = [];

    for (const domain of DOMAINS) {
        console.log(`🔍 Hunting for staff at ${domain}...`);
        try {
            // Search Google for staff directory
            const query = `site:${domain} staff directory email position`;
            await page.goto(`https://www.google.com/search?q=${encodeURIComponent(query)}`);
            await page.waitForTimeout(3000);

            // Click the first result if it looks like a staff page
            const links = await page.$$eval('a', as => as.map(a => a.href).filter(href => href.includes('staff') || href.includes('directory') || href.includes('about')));
            
            if (links.length > 0) {
                console.log(`🔗 Found likely directory: ${links[0]}`);
                await page.goto(links[0]);
                await page.waitForTimeout(5000);

                // Extract text and try to find names/emails/positions
                const bodyText = await page.innerText('body');
                
                // Regex for emails
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
                const emails = bodyText.match(emailRegex) || [];
                
                // Try to find lines with emails and extract nearby text for Name/Position
                const lines = bodyText.split('\n');
                for (const line of lines) {
                    const foundEmail = line.match(emailRegex);
                    if (foundEmail) {
                        // Very basic heuristic: Name is often before Email, Position is nearby
                        // We'll just take the line for now and clean it
                        results.push({
                            Domain: domain,
                            Name: line.split(foundEmail[0])[0].trim() || "Unknown",
                            Email: foundEmail[0],
                            Position: "Staff/Teacher" // Placeholder if not found
                        });
                    }
                }
            }
        } catch (e) {
            console.error(`❌ Error processing ${domain}: ${e.message}`);
        }
    }

    // Save to CSV
    const csvPath = path.join(__dirname, '../output/marketing/real_leads_verified.csv');
    const header = "Name,Email,Position,Source_Domain\n";
    const rows = results.map(r => `"${r.Name.replace(/"/g, '""')}","${r.Email}","${r.Position}","${r.Domain}"`).join('\n');
    
    fs.writeFileSync(csvPath, header + rows);
    console.log(`\n✅ Saved ${results.length} real leads to ${csvPath}`);

    await browserContext.close();
})();
