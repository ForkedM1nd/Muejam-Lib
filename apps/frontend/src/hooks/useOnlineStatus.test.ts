// ── Online Status Hook Tests ──
// Tests for online/offline detection

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useOnlineStatus } from './useOnlineStatus';
import { useOfflineStore } from '@/stores/useOfflineStore';

describe('useOnlineStatus', () => {
    beforeEach(() => {
        // Reset store
        useOfflineStore.setState({ isOnline: true });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('should set initial online status', () => {
        // Mock navigator.onLine
        Object.defineProperty(navigator, 'onLine', {
            writable: true,
            value: true,
        });

        renderHook(() => useOnlineStatus());

        const state = useOfflineStore.getState();
        expect(state.isOnline).toBe(true);
    });

    it('should set initial offline status', () => {
        // Mock navigator.onLine
        Object.defineProperty(navigator, 'onLine', {
            writable: true,
            value: false,
        });

        renderHook(() => useOnlineStatus());

        const state = useOfflineStore.getState();
        expect(state.isOnline).toBe(false);
    });

    it('should update status when going online', () => {
        Object.defineProperty(navigator, 'onLine', {
            writable: true,
            value: false,
        });

        renderHook(() => useOnlineStatus());

        // Initially offline
        expect(useOfflineStore.getState().isOnline).toBe(false);

        // Simulate going online
        act(() => {
            Object.defineProperty(navigator, 'onLine', {
                writable: true,
                value: true,
            });
            window.dispatchEvent(new Event('online'));
        });

        // Should be online now
        expect(useOfflineStore.getState().isOnline).toBe(true);
    });

    it('should update status when going offline', () => {
        Object.defineProperty(navigator, 'onLine', {
            writable: true,
            value: true,
        });

        renderHook(() => useOnlineStatus());

        // Initially online
        expect(useOfflineStore.getState().isOnline).toBe(true);

        // Simulate going offline
        act(() => {
            Object.defineProperty(navigator, 'onLine', {
                writable: true,
                value: false,
            });
            window.dispatchEvent(new Event('offline'));
        });

        // Should be offline now
        expect(useOfflineStore.getState().isOnline).toBe(false);
    });

    it('should clean up event listeners on unmount', () => {
        const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

        const { unmount } = renderHook(() => useOnlineStatus());

        unmount();

        expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
        expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    });
});
