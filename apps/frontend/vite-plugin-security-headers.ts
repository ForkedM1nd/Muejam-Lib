import type { Plugin } from 'vite';

/**
 * Vite plugin to add security headers
 * Note: In production, these should be set by your web server (nginx, Apache, etc.)
 * This plugin is mainly for development and preview mode
 */
export function securityHeadersPlugin(): Plugin {
    return {
        name: 'security-headers',
        configureServer(server) {
            server.middlewares.use((req, res, next) => {
                // Content Security Policy
                // Note: This is a permissive policy for development
                // In production, tighten these restrictions
                const csp = [
                    "default-src 'self'",
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://clerk.muejam.com https://*.clerk.accounts.dev",
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: https: blob:",
                    "font-src 'self' data:",
                    "connect-src 'self' https://api.muejam.com https://clerk.muejam.com https://*.clerk.accounts.dev wss://api.muejam.com",
                    "media-src 'self' https:",
                    "object-src 'none'",
                    "frame-ancestors 'none'",
                    "base-uri 'self'",
                    "form-action 'self'",
                    "upgrade-insecure-requests",
                ].join('; ');

                res.setHeader('Content-Security-Policy', csp);

                // X-Frame-Options - Prevent clickjacking
                res.setHeader('X-Frame-Options', 'DENY');

                // X-Content-Type-Options - Prevent MIME sniffing
                res.setHeader('X-Content-Type-Options', 'nosniff');

                // Referrer-Policy - Control referrer information
                res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

                // Permissions-Policy - Restrict browser features
                const permissionsPolicy = [
                    'camera=()',
                    'microphone=()',
                    'geolocation=()',
                    'interest-cohort=()',
                    'payment=()',
                ].join(', ');
                res.setHeader('Permissions-Policy', permissionsPolicy);

                // X-XSS-Protection - Enable XSS filter (legacy browsers)
                res.setHeader('X-XSS-Protection', '1; mode=block');

                next();
            });
        },
        configurePreviewServer(server) {
            server.middlewares.use((req, res, next) => {
                // Same headers for preview mode
                const csp = [
                    "default-src 'self'",
                    "script-src 'self' https://clerk.muejam.com https://*.clerk.accounts.dev",
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: https: blob:",
                    "font-src 'self' data:",
                    "connect-src 'self' https://api.muejam.com https://clerk.muejam.com https://*.clerk.accounts.dev wss://api.muejam.com",
                    "media-src 'self' https:",
                    "object-src 'none'",
                    "frame-ancestors 'none'",
                    "base-uri 'self'",
                    "form-action 'self'",
                    "upgrade-insecure-requests",
                ].join('; ');

                res.setHeader('Content-Security-Policy', csp);
                res.setHeader('X-Frame-Options', 'DENY');
                res.setHeader('X-Content-Type-Options', 'nosniff');
                res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
                res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), interest-cohort=(), payment=()');
                res.setHeader('X-XSS-Protection', '1; mode=block');

                next();
            });
        },
    };
}
