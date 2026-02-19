import { useEffect } from 'react';
import { updateMetaTags, clearMetaTags, type MetaTagsConfig } from '@/lib/seo';

/**
 * Hook for managing page meta tags
 * Automatically updates meta tags when config changes and cleans up on unmount
 */
export function useMetaTags(config: MetaTagsConfig) {
    useEffect(() => {
        updateMetaTags(config);

        return () => {
            clearMetaTags();
        };
    }, [config]);
}
