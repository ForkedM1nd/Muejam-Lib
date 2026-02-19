import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getOfflineQueue } from '@/lib/offlineQueue';
import { useState, useEffect } from 'react';

export function OfflineIndicator() {
    const isOnline = useOnlineStatus();
    const [queueSize, setQueueSize] = useState(0);

    useEffect(() => {
        const updateQueueSize = () => {
            const queue = getOfflineQueue();
            setQueueSize(queue.size());
        };

        updateQueueSize();

        // Update queue size periodically
        const interval = setInterval(updateQueueSize, 1000);

        return () => clearInterval(interval);
    }, []);

    if (isOnline) {
        return null;
    }

    return (
        <Alert variant="destructive" className="mb-4">
            <WifiOff className="h-4 w-4" />
            <AlertTitle>You're offline</AlertTitle>
            <AlertDescription className="flex items-center justify-between">
                <span>
                    Some features may not be available.
                    {queueSize > 0 && ` ${queueSize} action${queueSize > 1 ? 's' : ''} queued for when you're back online.`}
                </span>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.location.reload()}
                    className="ml-4"
                >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Retry
                </Button>
            </AlertDescription>
        </Alert>
    );
}
