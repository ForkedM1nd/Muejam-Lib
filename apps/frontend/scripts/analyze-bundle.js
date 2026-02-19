#!/usr/bin/env node

/**
 * Bundle Size Analyzer
 * 
 * Analyzes the production build to identify large dependencies
 * and opportunities for optimization.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distPath = path.join(__dirname, '../dist/assets');

/**
 * Get file size in KB
 */
function getFileSizeInKB(filePath) {
    const stats = fs.statSync(filePath);
    return (stats.size / 1024).toFixed(2);
}

/**
 * Analyze bundle
 */
function analyzeBundle() {
    if (!fs.existsSync(distPath)) {
        console.error('❌ Build directory not found. Run `npm run build` first.');
        process.exit(1);
    }

    const files = fs.readdirSync(distPath);

    const jsFiles = files.filter(f => f.endsWith('.js'));
    const cssFiles = files.filter(f => f.endsWith('.css'));

    console.log('\n📦 Bundle Analysis\n');
    console.log('═'.repeat(80));

    // Analyze JavaScript files
    console.log('\n📄 JavaScript Files:\n');

    const jsStats = jsFiles.map(file => ({
        name: file,
        size: parseFloat(getFileSizeInKB(path.join(distPath, file))),
    })).sort((a, b) => b.size - a.size);

    let totalJSSize = 0;
    jsStats.forEach(({ name, size }) => {
        totalJSSize += size;
        const sizeStr = `${size} KB`.padStart(12);
        const bar = '█'.repeat(Math.min(50, Math.floor(size / 10)));
        console.log(`  ${sizeStr}  ${bar}  ${name}`);
    });

    console.log(`\n  Total JS: ${totalJSSize.toFixed(2)} KB`);

    // Analyze CSS files
    console.log('\n🎨 CSS Files:\n');

    const cssStats = cssFiles.map(file => ({
        name: file,
        size: parseFloat(getFileSizeInKB(path.join(distPath, file))),
    })).sort((a, b) => b.size - a.size);

    let totalCSSSize = 0;
    cssStats.forEach(({ name, size }) => {
        totalCSSSize += size;
        const sizeStr = `${size} KB`.padStart(12);
        const bar = '█'.repeat(Math.min(50, Math.floor(size / 10)));
        console.log(`  ${sizeStr}  ${bar}  ${name}`);
    });

    console.log(`\n  Total CSS: ${totalCSSSize.toFixed(2)} KB`);

    // Summary
    console.log('\n📊 Summary:\n');
    console.log(`  Total Bundle Size: ${(totalJSSize + totalCSSSize).toFixed(2)} KB`);
    console.log(`  JavaScript: ${totalJSSize.toFixed(2)} KB (${((totalJSSize / (totalJSSize + totalCSSSize)) * 100).toFixed(1)}%)`);
    console.log(`  CSS: ${totalCSSSize.toFixed(2)} KB (${((totalCSSSize / (totalJSSize + totalCSSSize)) * 100).toFixed(1)}%)`);

    // Recommendations
    console.log('\n💡 Recommendations:\n');

    const largeChunks = jsStats.filter(s => s.size > 500);
    if (largeChunks.length > 0) {
        console.log('  ⚠️  Large chunks detected (>500 KB):');
        largeChunks.forEach(({ name, size }) => {
            console.log(`     - ${name} (${size} KB)`);
        });
        console.log('     Consider splitting these chunks further or lazy loading them.');
    }

    if (totalJSSize > 2000) {
        console.log('  ⚠️  Total JS size is large (>2 MB)');
        console.log('     Consider:');
        console.log('     - Lazy loading heavy features');
        console.log('     - Using dynamic imports for large dependencies');
        console.log('     - Removing unused dependencies');
    }

    if (jsStats.length > 20) {
        console.log('  ℹ️  Many chunk files detected');
        console.log('     This is normal for code-split applications.');
        console.log('     Ensure critical chunks are loaded first.');
    }

    console.log('\n═'.repeat(80));
    console.log('\n✅ Analysis complete!\n');
}

// Run analysis
analyzeBundle();
