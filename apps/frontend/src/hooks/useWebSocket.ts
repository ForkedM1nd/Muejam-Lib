// ── useWebSocket Hook ──
// React hook for managing WebSocket connection and subscriptions

import { useEffect, useRef, useCallback } from "react";
import { createWebSocketManager, WebSocketManager, WebSocketEventHandler } from "@/lib/websocket";
import { useWebSocketStore } from "@/stores/useWebSocketStore";

interface UseWebSocketConfig {
    getToken: () => Promise<string | null>;
    autoConnect?: boolean;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
    manager: WebSocketManager | null;
    connected: boolean;
    reconnecting: boolean;
    connectionState: "connecting" | "connected" | "disconnected" | "reconnecting";
    connect: () => void;
    disconnect: () => void;
    subscribe: (event: string, handler: WebSocketEventHandler) => () => void;
    send: (event: string, data: unknown) => void;
}

/**
 * Hook for managing WebSocket connection
 * 
 * @example
 * ```tsx
 * const { connected, subscribe } = useWebSocket({
 *   getToken: async () => await getToken(),
 *   autoConnect: true,
 * });
 * 
 * useEffect(() => {
 *   const unsubscribe = subscribe('notification', (data) => {
 *     console.log('New notification:', data);
 *   });
 *   return unsubscribe;
 * }, [subscribe]);
 * ```
 */
export function useWebSocket(config: UseWebSocketConfig): UseWebSocketReturn {
    const managerRef = useRef<WebSocketManager | null>(null);
    const { connected, reconnecting, connectionState } = useWebSocketStore();

    // Initialize WebSocket manager
    useEffect(() => {
        if (!managerRef.current) {
            managerRef.current = createWebSocketManager({
                getToken: config.getToken,
                onConnect: config.onConnect,
                onDisconnect: config.onDisconnect,
                onError: config.onError,
            });

            // Auto-connect if enabled
            if (config.autoConnect !== false) {
                managerRef.current.connect();
            }
        }

        // Cleanup on unmount
        return () => {
            if (managerRef.current) {
                managerRef.current.disconnect();
                managerRef.current = null;
            }
        };
    }, [config.getToken, config.autoConnect, config.onConnect, config.onDisconnect, config.onError]);

    const connect = useCallback(() => {
        managerRef.current?.connect();
    }, []);

    const disconnect = useCallback(() => {
        managerRef.current?.disconnect();
    }, []);

    const subscribe = useCallback((event: string, handler: WebSocketEventHandler) => {
        if (!managerRef.current) {
            console.warn("[useWebSocket] Manager not initialized");
            return () => { };
        }
        return managerRef.current.subscribe(event, handler);
    }, []);

    const send = useCallback((event: string, data: unknown) => {
        managerRef.current?.send(event, data);
    }, []);

    return {
        manager: managerRef.current,
        connected,
        reconnecting,
        connectionState,
        connect,
        disconnect,
        subscribe,
        send,
    };
}
