import { sanitizeHtml } from '@/lib/sanitize';
import { useMemo } from 'react';

interface SafeHtmlProps {
    html: string;
    className?: string;
    as?: keyof JSX.IntrinsicElements;
}

/**
 * Component to safely render HTML content
 * 
 * IMPORTANT: This uses basic sanitization. For production,
 * install DOMPurify for more robust HTML sanitization.
 */
export function SafeHtml({ html, className, as: Component = 'div' }: SafeHtmlProps) {
    const sanitized = useMemo(() => sanitizeHtml(html), [html]);

    return (
        <Component
            className={className}
            dangerouslySetInnerHTML={{ __html: sanitized }}
        />
    );
}
