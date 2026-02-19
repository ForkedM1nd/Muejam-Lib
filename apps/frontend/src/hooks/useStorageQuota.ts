import { useState, useEffect } from 'react';

interface StorageQuota {
    usage: number;
    quota: number;
    percentUsed: number;
    isSupported: boolean;
}

/**
 * Hook to monitor storage quota usage
 */
export function useStorageQuota(): StorageQuota {
    const [quota, setQuota] = useState<StorageQuota>({
        usage: 0,
        quota: 0,
        percentUsed: 0,
        isSupported: false,
    });

    useEffect(() => {
        const checkQuota = async () => {
            if ('storage' in navigator && 'estimate' in navigator.storage) {
                try {
                    const estimate = await navigator.storage.estimate();
                    const usage = estimate.usage || 0;
                    const quota = estimate.quota || 0;
                    const percentUsed = quota > 0 ? (usage / quota) * 100 : 0;

                    setQuota({
                        usage,
                        quota,
                        percentUsed,
                        isSupported: true,
                    });
                } catch (error) {
                    console.error('Failed to estimate storage quota:', error);
                }
            }
        };

        checkQuota();

        // Check quota every 30 seconds
        const interval = setInterval(checkQuota, 30000);

        return () => clearInterval(interval);
    }, []);

    return quota;
}

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
