import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface QueuedRequest {
    id: string;
    url: string;
    method: string;
    body?: unknown;
    headers?: Record<string, string>;
    timestamp: number;
    retryCount: number;
}

interface OfflineState {
    // State
    isOnline: boolean;
    queuedRequests: QueuedRequest[];

    // Actions
    setOnline: (online: boolean) => void;
    addToQueue: (request: Omit<QueuedRequest, 'id' | 'timestamp' | 'retryCount'>) => void;
    removeFromQueue: (id: string) => void;
    incrementRetryCount: (id: string) => void;
    clearQueue: () => void;
    getNextRequest: () => QueuedRequest | undefined;
}

export const useOfflineStore = create<OfflineState>()(
    persist(
        (set, get) => ({
            isOnline: navigator.onLine,
            queuedRequests: [],

            setOnline: (online) => set({ isOnline: online }),

            addToQueue: (request) =>
                set((state) => ({
                    queuedRequests: [
                        ...state.queuedRequests,
                        {
                            ...request,
                            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                            timestamp: Date.now(),
                            retryCount: 0,
                        },
                    ],
                })),

            removeFromQueue: (id) =>
                set((state) => ({
                    queuedRequests: state.queuedRequests.filter((req) => req.id !== id),
                })),

            incrementRetryCount: (id) =>
                set((state) => ({
                    queuedRequests: state.queuedRequests.map((req) =>
                        req.id === id ? { ...req, retryCount: req.retryCount + 1 } : req
                    ),
                })),

            clearQueue: () => set({ queuedRequests: [] }),

            getNextRequest: () => {
                const state = get();
                // Get oldest request that hasn't exceeded retry limit (max 3 retries)
                return state.queuedRequests
                    .filter((req) => req.retryCount < 3)
                    .sort((a, b) => a.timestamp - b.timestamp)[0];
            },
        }),
        {
            name: 'offline-storage',
            partialize: (state) => ({
                queuedRequests: state.queuedRequests,
                // Don't persist isOnline - it should be determined at runtime
            }),
        }
    )
);
