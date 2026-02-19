import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerDeepLinkHandler } from '@/lib/deepLinks';

/**
 * Hook to handle deep links in the application
 * Automatically registers and cleans up deep link handlers
 */
export function useDeepLinks() {
    const navigate = useNavigate();

    useEffect(() => {
        const cleanup = registerDeepLinkHandler((path) => {
            navigate(path);
        });

        return cleanup;
    }, [navigate]);
}
