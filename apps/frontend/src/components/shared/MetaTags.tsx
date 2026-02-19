import { useEffect } from 'react';
import { updateMetaTags, clearMetaTags, type MetaTagsConfig } from '@/lib/seo';

interface MetaTagsProps extends MetaTagsConfig { }

/**
 * Component for managing page meta tags
 * Automatically updates meta tags when props change and cleans up on unmount
 */
export function MetaTags(props: MetaTagsProps) {
    useEffect(() => {
        updateMetaTags(props);

        return () => {
            clearMetaTags();
        };
    }, [props]);

    return null;
}
