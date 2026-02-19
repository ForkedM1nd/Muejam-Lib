// ── WebSocket Handlers Hook Tests ──
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWebSocketHandlers } from './useWebSocketHandlers';
import { WebSocketManager } from '@/lib/websocket';
import { useNotificationsStore } from '@/stores/useNotificationsStore';
import type { NotificationEvent } from '@/lib/websocketHandlers';

// Mock WebSocket
class MockWebSocket {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    readyState = MockWebSocket.CONNECTING;
    url: string;
    onopen: ((event: Event) => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;

    constructor(url: string) {
        this.url = url;
        setTimeout(() => {
            this.readyState = MockWebSocket.OPEN;
            this.onopen?.(new Event('open'));
        }, 0);
    }

    send(data: string) {
        if (this.readyState !== MockWebSocket.OPEN) {
            throw new Error('WebSocket is not open');
        }
    }

    close(code?: number, reason?: string) {
        this.readyState = MockWebSocket.CLOSED;
        this.onclose?.(new CloseEvent('close', { code: code ?? 1000, reason: reason ?? '' }));
    }
}

global.WebSocket = MockWebSocket as any;

describe('useWebSocketHandlers', () => {
    let queryClient: QueryClient;
    let wsManager: WebSocketManager;
    const mockGetToken = vi.fn();

    beforeEach(() => {
        mockGetToken.mockReset();
        mockGetToken.mockResolvedValue('test-token-123');

        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });

        // Reset notification store
        useNotificationsStore.setState({
            unreadCount: 0,
            items: [],
        });

        wsManager = new WebSocketManager({
            getToken: mockGetToken,
        });
    });

    afterEach(() => {
        if (wsManager) {
            wsManager.disconnect();
        }
        vi.clearAllTimers();
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    it('should set up event handlers when wsManager is provided', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        const { result } = renderHook(() => useWebSocketHandlers(wsManager), { wrapper });

        // Hook should not return anything
        expect(result.current).toBeUndefined();

        // Verify handlers are subscribed by checking internal state
        const eventHandlers = (wsManager as any).eventHandlers;
        expect(eventHandlers.has('notification')).toBe(true);
        expect(eventHandlers.has('whisper_reply')).toBe(true);
        expect(eventHandlers.has('story_update')).toBe(true);
        expect(eventHandlers.has('follow')).toBe(true);
    });

    it('should handle notification events', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        renderHook(() => useWebSocketHandlers(wsManager), { wrapper });

        const notification: NotificationEvent = {
            id: 'notif-123',
            type: 'follow',
            title: 'New Follower',
            message: 'John Doe started following you',
            read: false,
            created_at: '2024-01-01T00:00:00Z',
        };

        // Simulate incoming notification
        const ws = (wsManager as any).ws;
        const message = {
            type: 'notification',
            payload: notification,
            timestamp: new Date().toISOString(),
        };
        ws.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }));

        await waitFor(() => {
            const store = useNotificationsStore.getState();
            expect(store.items).toHaveLength(1);
            expect(store.items[0].id).toBe('notif-123');
        });
    });

    it('should handle whisper reply events', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

        renderHook(() => useWebSocketHandlers(wsManager), { wrapper });

        const reply = {
            whisper_id: 'whisper-123',
            reply_id: 'reply-456',
            reply: {
                id: 'reply-456',
                content: 'Great whisper!',
                author: {
                    id: 'user-789',
                    handle: 'janedoe',
                    display_name: 'Jane Doe',
                },
                created_at: '2024-01-01T00:00:00Z',
            },
        };

        // Simulate incoming whisper reply
        const ws = (wsManager as any).ws;
        const message = {
            type: 'whisper_reply',
            payload: reply,
            timestamp: new Date().toISOString(),
        };
        ws.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }));

        await waitFor(() => {
            expect(invalidateSpy).toHaveBeenCalled();
        });
    });

    it('should handle story update events', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

        renderHook(() => useWebSocketHandlers(wsManager), { wrapper });

        const update = {
            story_id: 'story-123',
            story_slug: 'my-story',
            update_type: 'published',
            author_id: 'author-456',
        };

        // Simulate incoming story update
        const ws = (wsManager as any).ws;
        const message = {
            type: 'story_update',
            payload: update,
            timestamp: new Date().toISOString(),
        };
        ws.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }));

        await waitFor(() => {
            expect(invalidateSpy).toHaveBeenCalled();
        });
    });

    it('should handle follow events', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        renderHook(() => useWebSocketHandlers(wsManager), { wrapper });

        const follow = {
            follower_id: 'user-123',
            following_id: 'user-456',
            follower: {
                id: 'user-123',
                handle: 'johndoe',
                display_name: 'John Doe',
            },
        };

        // Simulate incoming follow event
        const ws = (wsManager as any).ws;
        const message = {
            type: 'follow',
            payload: follow,
            timestamp: new Date().toISOString(),
        };
        ws.onmessage?.(new MessageEvent('message', { data: JSON.stringify(message) }));

        await waitFor(() => {
            const store = useNotificationsStore.getState();
            expect(store.items).toHaveLength(1);
            expect(store.items[0].type).toBe('follow');
        });
    });

    it('should unsubscribe from events on unmount', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        const { unmount } = renderHook(() => useWebSocketHandlers(wsManager), { wrapper });

        // Verify handlers are subscribed
        let eventHandlers = (wsManager as any).eventHandlers;
        expect(eventHandlers.get('notification')?.size).toBe(1);

        // Unmount the hook
        unmount();

        // Verify handlers are unsubscribed (Set is deleted when empty)
        eventHandlers = (wsManager as any).eventHandlers;
        expect(eventHandlers.get('notification')).toBeUndefined();
    });

    it('should handle undefined wsManager gracefully', () => {
        const { result } = renderHook(() => useWebSocketHandlers(undefined), { wrapper });

        // Should not throw and should return undefined
        expect(result.current).toBeUndefined();
    });

    it('should re-subscribe when wsManager changes', async () => {
        await wsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        const { rerender } = renderHook(
            ({ manager }) => useWebSocketHandlers(manager),
            {
                wrapper,
                initialProps: { manager: wsManager },
            }
        );

        // Create a new manager
        const newWsManager = new WebSocketManager({
            getToken: mockGetToken,
        });
        await newWsManager.connect();
        await new Promise(resolve => setTimeout(resolve, 10));

        // Rerender with new manager
        rerender({ manager: newWsManager });

        // Old manager should have no handlers (Set is deleted when empty)
        const oldEventHandlers = (wsManager as any).eventHandlers;
        expect(oldEventHandlers.get('notification')).toBeUndefined();

        // New manager should have handlers
        const newEventHandlers = (newWsManager as any).eventHandlers;
        expect(newEventHandlers.get('notification')?.size).toBe(1);

        newWsManager.disconnect();
    });
});
