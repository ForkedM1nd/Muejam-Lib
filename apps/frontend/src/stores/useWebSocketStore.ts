import { create } from 'zustand';

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

interface WebSocketState {
    // State
    connected: boolean;
    reconnecting: boolean;
    connectionState: ConnectionState;
    lastConnectedAt: number | null;
    reconnectAttempts: number;

    // Actions
    setConnected: (connected: boolean) => void;
    setReconnecting: (reconnecting: boolean) => void;
    setConnectionState: (state: ConnectionState) => void;
    setLastConnectedAt: (timestamp: number) => void;
    incrementReconnectAttempts: () => void;
    resetReconnectAttempts: () => void;
}

export const useWebSocketStore = create<WebSocketState>((set) => ({
    connected: false,
    reconnecting: false,
    connectionState: 'disconnected',
    lastConnectedAt: null,
    reconnectAttempts: 0,

    setConnected: (connected) =>
        set((state) => ({
            connected,
            connectionState: connected ? 'connected' : state.connectionState,
            lastConnectedAt: connected ? Date.now() : state.lastConnectedAt,
            reconnectAttempts: connected ? 0 : state.reconnectAttempts,
        })),

    setReconnecting: (reconnecting) =>
        set({
            reconnecting,
            connectionState: reconnecting ? 'reconnecting' : 'disconnected',
        }),

    setConnectionState: (connectionState) =>
        set({
            connectionState,
            connected: connectionState === 'connected',
            reconnecting: connectionState === 'reconnecting',
        }),

    setLastConnectedAt: (timestamp) => set({ lastConnectedAt: timestamp }),

    incrementReconnectAttempts: () =>
        set((state) => ({
            reconnectAttempts: state.reconnectAttempts + 1,
        })),

    resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),
}));
