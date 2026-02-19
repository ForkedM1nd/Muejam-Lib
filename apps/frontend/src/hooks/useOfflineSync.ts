// ── Offline Sync Hook ──
// Handles syncing queued requests when connection is restored

import { useEffect, useRef } from 'react';
import { useOfflineStore } from '@/stores/useOfflineStore';
import { useWebSocketStore } from '@/stores/useWebSocketStore';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Hook to sync queued requests when connection is restored
 * Processes offline queue and retries failed requests
 */
export function useOfflineSync() {
    const { isOnline, queuedRequests, removeFromQueue, incrementRetryCount } = useOfflineStore();
    const { connectionState } = useWebSocketStore();
    const queryClient = useQueryClient();
    const isSyncing = useRef(false);

    useEffect(() => {
        // Only sync when online and connected
        if (!isOnline || connectionState !== 'connected' || queuedRequests.length === 0) {
            return;
        }

        // Prevent concurrent syncing
        if (isSyncing.current) {
            return;
        }

        isSyncing.current = true;

        // Process queue
        const processQueue = async () => {
            console.log(`[OfflineSync] Processing ${queuedRequests.length} queued requests`);

            for (const request of queuedRequests) {
                try {
                    // Attempt to replay the request
                    const response = await fetch(request.url, {
                        method: request.method,
                        headers: {
                            'Content-Type': 'application/json',
                            ...request.headers,
                        },
                        body: request.body ? JSON.stringify(request.body) : undefined,
                    });

                    if (response.ok) {
                        console.log(`[OfflineSync] Successfully synced request ${request.id}`);
                        removeFromQueue(request.id);

                        // Invalidate related queries to refresh data
                        // Extract resource type from URL for targeted invalidation
                        const urlPath = new URL(request.url).pathname;
                        if (urlPath.includes('/stories')) {
                            queryClient.invalidateQueries({ queryKey: ['stories'] });
                        } else if (urlPath.includes('/whispers')) {
                            queryClient.invalidateQueries({ queryKey: ['whispers'] });
                        } else if (urlPath.includes('/highlights')) {
                            queryClient.invalidateQueries({ queryKey: ['highlights'] });
                        } else if (urlPath.includes('/users')) {
                            queryClient.invalidateQueries({ queryKey: ['users'] });
                        }
                    } else {
                        console.warn(`[OfflineSync] Failed to sync request ${request.id}: ${response.status}`);

                        // Increment retry count
                        incrementRetryCount(request.id);

                        // Remove if exceeded max retries
                        if (request.retryCount >= 2) {
                            console.error(`[OfflineSync] Max retries exceeded for request ${request.id}, removing from queue`);
                            removeFromQueue(request.id);
                        }
                    }
                } catch (error) {
                    console.error(`[OfflineSync] Error syncing request ${request.id}:`, error);

                    // Increment retry count
                    incrementRetryCount(request.id);

                    // Remove if exceeded max retries
                    if (request.retryCount >= 2) {
                        console.error(`[OfflineSync] Max retries exceeded for request ${request.id}, removing from queue`);
                        removeFromQueue(request.id);
                    }
                }

                // Small delay between requests to avoid overwhelming the server
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            console.log('[OfflineSync] Queue processing complete');
            isSyncing.current = false;
        };

        processQueue();
    }, [isOnline, connectionState, queuedRequests, removeFromQueue, incrementRetryCount, queryClient]);
}
