/**
 * Lighthouse CI Configuration
 * 
 * Configuration for running Lighthouse audits on the application.
 * This ensures performance, accessibility, best practices, and SEO standards are met.
 */

export default {
    ci: {
        collect: {
            // URLs to audit
            url: [
                'http://localhost:8080/',
                'http://localhost:8080/discover',
                'http://localhost:8080/sign-in',
            ],
            // Number of runs per URL
            numberOfRuns: 3,
            // Settings for Lighthouse
            settings: {
                // Emulate mobile device
                emulatedFormFactor: 'mobile',
                // Throttling settings
                throttling: {
                    rttMs: 40,
                    throughputKbps: 10240,
                    cpuSlowdownMultiplier: 1,
                },
            },
        },
        assert: {
            // Assertions for minimum scores
            assertions: {
                'categories:performance': ['error', { minScore: 0.9 }],
                'categories:accessibility': ['error', { minScore: 0.9 }],
                'categories:best-practices': ['error', { minScore: 0.9 }],
                'categories:seo': ['error', { minScore: 0.9 }],

                // Specific metrics
                'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
                'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
                'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
                'total-blocking-time': ['error', { maxNumericValue: 300 }],

                // Accessibility
                'color-contrast': 'error',
                'image-alt': 'error',
                'label': 'error',
                'aria-*': 'error',

                // Best practices
                'uses-https': 'error',
                'no-vulnerable-libraries': 'error',

                // SEO
                'meta-description': 'error',
                'document-title': 'error',
            },
        },
        upload: {
            // Upload results to temporary storage
            target: 'temporary-public-storage',
        },
    },
};
