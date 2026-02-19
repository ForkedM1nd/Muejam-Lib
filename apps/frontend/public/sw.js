// Service Worker for MueJam Library
// Provides offline support with caching strategies

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `muejam-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `muejam-dynamic-${CACHE_VERSION}`;
const IMAGE_CACHE = `muejam-images-${CACHE_VERSION}`;
const API_CACHE = `muejam-api-${CACHE_VERSION}`;

// Static assets to precache
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
];

// Maximum cache sizes
const MAX_DYNAMIC_CACHE_SIZE = 50;
const MAX_IMAGE_CACHE_SIZE = 100;
const MAX_API_CACHE_SIZE = 50;

// Helper to limit cache size
async function limitCacheSize(cacheName, maxSize) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();

    if (keys.length > maxSize) {
        // Delete oldest entries
        const keysToDelete = keys.slice(0, keys.length - maxSize);
        await Promise.all(keysToDelete.map(key => cache.delete(key)));
    }
}

// Install event - precache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Precaching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            return name.startsWith('muejam-') &&
                                !name.includes(CACHE_VERSION);
                        })
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // API requests - Network first, fallback to cache
    if (url.pathname.startsWith('/v1/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Clone response before caching
                    const responseClone = response.clone();

                    // Only cache successful responses
                    if (response.ok) {
                        caches.open(API_CACHE).then((cache) => {
                            cache.put(request, responseClone);
                            limitCacheSize(API_CACHE, MAX_API_CACHE_SIZE);
                        });
                    }

                    return response;
                })
                .catch(() => {
                    // Network failed, try cache
                    return caches.match(request)
                        .then((cachedResponse) => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }

                            // Return offline response
                            return new Response(
                                JSON.stringify({
                                    error: {
                                        code: 'OFFLINE',
                                        message: 'You are offline. Please check your connection.',
                                    },
                                }),
                                {
                                    status: 503,
                                    headers: { 'Content-Type': 'application/json' },
                                }
                            );
                        });
                })
        );
        return;
    }

    // Image requests - Cache first, fallback to network
    if (request.destination === 'image') {
        event.respondWith(
            caches.match(request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    return fetch(request)
                        .then((response) => {
                            const responseClone = response.clone();

                            if (response.ok) {
                                caches.open(IMAGE_CACHE).then((cache) => {
                                    cache.put(request, responseClone);
                                    limitCacheSize(IMAGE_CACHE, MAX_IMAGE_CACHE_SIZE);
                                });
                            }

                            return response;
                        });
                })
        );
        return;
    }

    // Static assets - Cache first, fallback to network
    if (STATIC_ASSETS.includes(url.pathname)) {
        event.respondWith(
            caches.match(request)
                .then((cachedResponse) => {
                    return cachedResponse || fetch(request);
                })
        );
        return;
    }

    // Other requests - Stale while revalidate
    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                const fetchPromise = fetch(request)
                    .then((response) => {
                        const responseClone = response.clone();

                        if (response.ok) {
                            caches.open(DYNAMIC_CACHE).then((cache) => {
                                cache.put(request, responseClone);
                                limitCacheSize(DYNAMIC_CACHE, MAX_DYNAMIC_CACHE_SIZE);
                            });
                        }

                        return response;
                    })
                    .catch(() => cachedResponse);

                return cachedResponse || fetchPromise;
            })
    );
});

// Background sync for offline mutations
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-offline-queue') {
        event.waitUntil(
            // Notify clients to process offline queue
            self.clients.matchAll().then((clients) => {
                clients.forEach((client) => {
                    client.postMessage({
                        type: 'SYNC_OFFLINE_QUEUE',
                    });
                });
            })
        );
    }
});

// Handle messages from clients
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((name) => caches.delete(name))
                );
            })
        );
    }
});
