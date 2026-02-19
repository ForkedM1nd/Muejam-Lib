import { useEffect } from 'react';
import { injectStructuredData, removeStructuredData } from '@/lib/structuredData';

interface StructuredDataProps {
    data: object;
    id?: string;
}

/**
 * Component for injecting JSON-LD structured data into the page
 */
export function StructuredData({ data, id = 'structured-data' }: StructuredDataProps) {
    useEffect(() => {
        injectStructuredData(data, id);

        return () => {
            removeStructuredData(id);
        };
    }, [data, id]);

    return null;
}
