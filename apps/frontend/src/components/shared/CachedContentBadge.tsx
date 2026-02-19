import { Badge } from '@/components/ui/badge';
import { Download } from 'lucide-react';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

interface CachedContentBadgeProps {
    isCached: boolean;
    className?: string;
}

/**
 * Badge to indicate if content is available offline
 */
export function CachedContentBadge({ isCached, className }: CachedContentBadgeProps) {
    const isOnline = useOnlineStatus();

    // Only show when offline or when explicitly cached
    if (isOnline && !isCached) {
        return null;
    }

    if (!isCached) {
        return null;
    }

    return (
        <Badge variant="secondary" className={className}>
            <Download className="h-3 w-3 mr-1" />
            Available offline
        </Badge>
    );
}
