// ── WebSocket Handlers Hook ──
// Hook to set up WebSocket event handlers with query cache integration

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketManager } from '@/lib/websocket';
import { createWebSocketHandlers } from '@/lib/websocketHandlers';
import type {
    NotificationEvent,
    WhisperReplyEvent,
    StoryUpdateEvent,
    FollowEvent,
} from '@/lib/websocketHandlers';

/**
 * Hook to set up WebSocket event handlers
 * Subscribes to WebSocket events and updates query cache accordingly
 * 
 * @param wsManager - WebSocket manager instance
 */
export function useWebSocketHandlers(wsManager: WebSocketManager | undefined) {
    const queryClient = useQueryClient();

    useEffect(() => {
        if (!wsManager) return;

        // Create handlers with query client
        const handlers = createWebSocketHandlers(queryClient);

        // Subscribe to notification events
        const unsubscribeNotification = wsManager.subscribe(
            'notification',
            (data) => handlers.onNotification(data as NotificationEvent)
        );

        // Subscribe to whisper reply events
        const unsubscribeWhisperReply = wsManager.subscribe(
            'whisper_reply',
            (data) => handlers.onWhisperReply(data as WhisperReplyEvent)
        );

        // Subscribe to story update events
        const unsubscribeStoryUpdate = wsManager.subscribe(
            'story_update',
            (data) => handlers.onStoryUpdate(data as StoryUpdateEvent)
        );

        // Subscribe to follow events
        const unsubscribeFollow = wsManager.subscribe(
            'follow',
            (data) => handlers.onFollow(data as FollowEvent)
        );

        // Cleanup: unsubscribe from all events
        return () => {
            unsubscribeNotification();
            unsubscribeWhisperReply();
            unsubscribeStoryUpdate();
            unsubscribeFollow();
        };
    }, [wsManager, queryClient]);
}
