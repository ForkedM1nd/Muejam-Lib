// ── Offline Sync Hook Tests ──
// Tests for offline sync functionality

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useOfflineSync } from './useOfflineSync';
import { useOfflineStore } from '@/stores/useOfflineStore';
import { useWebSocketStore } from '@/stores/useWebSocketStore';
import { ReactNode } from 'react';

// Mock fetch
global.fetch = vi.fn();

describe('useOfflineSync', () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });

        // Reset stores
        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [],
        });

        useWebSocketStore.setState({
            connectionState: 'connected',
            connected: true,
        });

        // Reset fetch mock
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    it('should not process queue when offline', async () => {
        useOfflineStore.setState({
            isOnline: false,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).not.toHaveBeenCalled();
        });
    });

    it('should not process queue when not connected', async () => {
        useWebSocketStore.setState({ connectionState: 'disconnected', connected: false });
        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [
                { id: '1', url: '/api/test', method: 'POST', timestamp: Date.now(), retryCount: 0 },
            ],
        });

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).not.toHaveBeenCalled();
        });
    });

    it('should process queue when online and connected', async () => {
        const mockRequest = {
            id: '1',
            url: 'https://api.muejam.com/v1/stories',
            method: 'POST',
            body: { title: 'Test Story' },
            headers: { 'Content-Type': 'application/json' },
            timestamp: Date.now(),
            retryCount: 0,
        };

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [mockRequest],
        });

        (fetch as any).mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ id: '123', title: 'Test Story' }),
        });

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledWith(
                mockRequest.url,
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json',
                    }),
                    body: JSON.stringify(mockRequest.body),
                })
            );
        });

        // Request should be removed from queue after successful sync
        await waitFor(() => {
            const state = useOfflineStore.getState();
            expect(state.queuedRequests).toHaveLength(0);
        });
    });

    it('should increment retry count on failed sync', async () => {
        const mockRequest = {
            id: '1',
            url: 'https://api.muejam.com/v1/stories',
            method: 'POST',
            body: { title: 'Test Story' },
            timestamp: Date.now(),
            retryCount: 0,
        };

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [mockRequest],
        });

        (fetch as any).mockResolvedValueOnce({
            ok: false,
            status: 500,
        });

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).toHaveBeenCalled();
        });

        // Retry count should be incremented
        await waitFor(() => {
            const state = useOfflineStore.getState();
            expect(state.queuedRequests[0]?.retryCount).toBe(1);
        });
    });

    it('should remove request after max retries', async () => {
        const mockRequest = {
            id: '1',
            url: 'https://api.muejam.com/v1/stories',
            method: 'POST',
            body: { title: 'Test Story' },
            timestamp: Date.now(),
            retryCount: 2, // Already at max retries
        };

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [mockRequest],
        });

        (fetch as any).mockResolvedValueOnce({
            ok: false,
            status: 500,
        });

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).toHaveBeenCalled();
        });

        // Request should be removed after exceeding max retries
        await waitFor(() => {
            const state = useOfflineStore.getState();
            expect(state.queuedRequests).toHaveLength(0);
        });
    });

    it('should invalidate related queries after successful sync', async () => {
        const mockRequest = {
            id: '1',
            url: 'https://api.muejam.com/v1/stories',
            method: 'POST',
            body: { title: 'Test Story' },
            timestamp: Date.now(),
            retryCount: 0,
        };

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [mockRequest],
        });

        (fetch as any).mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ id: '123', title: 'Test Story' }),
        });

        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).toHaveBeenCalled();
        });

        // Should invalidate stories queries
        await waitFor(() => {
            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['stories'] });
        });
    });

    it('should handle network errors gracefully', async () => {
        const mockRequest = {
            id: '1',
            url: 'https://api.muejam.com/v1/stories',
            method: 'POST',
            body: { title: 'Test Story' },
            timestamp: Date.now(),
            retryCount: 0,
        };

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: [mockRequest],
        });

        (fetch as any).mockRejectedValueOnce(new Error('Network error'));

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).toHaveBeenCalled();
        });

        // Retry count should be incremented
        await waitFor(() => {
            const state = useOfflineStore.getState();
            expect(state.queuedRequests[0]?.retryCount).toBe(1);
        });
    });

    it('should process multiple requests in sequence', async () => {
        const mockRequests = [
            {
                id: '1',
                url: 'https://api.muejam.com/v1/stories',
                method: 'POST',
                body: { title: 'Story 1' },
                timestamp: Date.now(),
                retryCount: 0,
            },
            {
                id: '2',
                url: 'https://api.muejam.com/v1/whispers',
                method: 'POST',
                body: { content: 'Whisper 1' },
                timestamp: Date.now() + 1000,
                retryCount: 0,
            },
        ];

        useOfflineStore.setState({
            isOnline: true,
            queuedRequests: mockRequests,
        });

        (fetch as any)
            .mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => ({ id: '123' }),
            })
            .mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => ({ id: '456' }),
            });

        renderHook(() => useOfflineSync(), { wrapper });

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledTimes(2);
        });

        // All requests should be removed from queue
        await waitFor(() => {
            const state = useOfflineStore.getState();
            expect(state.queuedRequests).toHaveLength(0);
        });
    });
});
