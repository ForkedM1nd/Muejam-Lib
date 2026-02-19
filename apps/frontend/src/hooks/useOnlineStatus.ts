// ── Online Status Hook ──
// Detects and tracks online/offline status

import { useEffect } from 'react';
import { useOfflineStore } from '@/stores/useOfflineStore';

/**
 * Hook to detect and track online/offline status
 * Updates the offline store when network status changes
 */
export function useOnlineStatus() {
    const { setOnline } = useOfflineStore();

    useEffect(() => {
        // Set initial status
        setOnline(navigator.onLine);

        // Handle online event
        const handleOnline = () => {
            console.log('[OnlineStatus] Network connection restored');
            setOnline(true);
        };

        // Handle offline event
        const handleOffline = () => {
            console.log('[OnlineStatus] Network connection lost');
            setOnline(false);
        };

        // Add event listeners
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Cleanup
        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, [setOnline]);
}
