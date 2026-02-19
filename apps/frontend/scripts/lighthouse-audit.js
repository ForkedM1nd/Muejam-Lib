#!/usr/bin/env node

/**
 * Lighthouse Audit Script
 * 
 * Runs Lighthouse audits on key pages and generates a report.
 * This script can be run manually or as part of CI/CD.
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BASE_URL = process.env.LIGHTHOUSE_URL || 'http://localhost:8080';
const OUTPUT_DIR = path.join(__dirname, '../lighthouse-reports');

// Pages to audit
const PAGES = [
    { name: 'Home', url: '/' },
    { name: 'Discover', url: '/discover' },
    { name: 'Sign In', url: '/sign-in' },
    { name: 'Story Page', url: '/story/example-story' },
    { name: 'Reader', url: '/story/example-story/chapter/1' },
];

/**
 * Check if Lighthouse is installed
 */
function checkLighthouse() {
    try {
        execSync('lighthouse --version', { stdio: 'ignore' });
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Run Lighthouse audit for a page
 */
function runAudit(page) {
    const url = `${BASE_URL}${page.url}`;
    const outputPath = path.join(OUTPUT_DIR, `${page.name.toLowerCase().replace(/\s+/g, '-')}.html`);

    console.log(`\n🔍 Auditing: ${page.name} (${url})`);

    try {
        const command = `lighthouse "${url}" \
      --output=html \
      --output-path="${outputPath}" \
      --chrome-flags="--headless" \
      --quiet`;

        execSync(command, { stdio: 'inherit' });
        console.log(`✅ Report saved: ${outputPath}`);

        return true;
    } catch (error) {
        console.error(`❌ Failed to audit ${page.name}:`, error.message);
        return false;
    }
}

/**
 * Main function
 */
function main() {
    console.log('\n🚀 Starting Lighthouse Audits\n');
    console.log('═'.repeat(80));

    // Check if Lighthouse is installed
    if (!checkLighthouse()) {
        console.error('\n❌ Lighthouse is not installed.');
        console.error('   Install it globally: npm install -g lighthouse');
        console.error('   Or use npx: npx lighthouse <url>');
        process.exit(1);
    }

    // Create output directory
    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    // Run audits
    let successCount = 0;
    let failCount = 0;

    for (const page of PAGES) {
        const success = runAudit(page);
        if (success) {
            successCount++;
        } else {
            failCount++;
        }
    }

    // Summary
    console.log('\n═'.repeat(80));
    console.log('\n📊 Audit Summary:\n');
    console.log(`  ✅ Successful: ${successCount}`);
    console.log(`  ❌ Failed: ${failCount}`);
    console.log(`\n  Reports saved to: ${OUTPUT_DIR}`);

    // Instructions
    console.log('\n💡 Next Steps:\n');
    console.log('  1. Open the HTML reports in your browser');
    console.log('  2. Review performance, accessibility, best practices, and SEO scores');
    console.log('  3. Address any issues identified in the reports');
    console.log('  4. Aim for scores above 90 in all categories');

    console.log('\n═'.repeat(80));
    console.log('\n✅ Audits complete!\n');

    process.exit(failCount > 0 ? 1 : 0);
}

// Run main function
main();
