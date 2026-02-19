import { useEffect, useState } from 'react';
import { getMobileConfig, type MobileConfig, DEFAULT_MOBILE_CONFIG } from '@/lib/mobile';

/**
 * Hook to fetch and manage mobile configuration
 */
export function useMobileConfig() {
    const [config, setConfig] = useState<MobileConfig>(DEFAULT_MOBILE_CONFIG);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        let mounted = true;

        async function loadConfig() {
            try {
                setIsLoading(true);
                const mobileConfig = await getMobileConfig();

                if (mounted) {
                    setConfig(mobileConfig);
                    setError(null);
                }
            } catch (err) {
                if (mounted) {
                    setError(err instanceof Error ? err : new Error('Failed to load mobile config'));
                    // Keep using default config on error
                }
            } finally {
                if (mounted) {
                    setIsLoading(false);
                }
            }
        }

        loadConfig();

        return () => {
            mounted = false;
        };
    }, []);

    return {
        config,
        isLoading,
        error,
    };
}
