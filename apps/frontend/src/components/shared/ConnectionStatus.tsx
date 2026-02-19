// ── Connection Status Indicator ──
// Displays WebSocket connection status and offline queue information

import { useWebSocketStore } from '@/stores/useWebSocketStore';
import { useOfflineStore } from '@/stores/useOfflineStore';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
    className?: string;
    showDetails?: boolean;
}

/**
 * Connection status indicator component
 * Shows WebSocket connection state and offline queue status
 */
export function ConnectionStatus({ className, showDetails = false }: ConnectionStatusProps) {
    const { connectionState, reconnectAttempts } = useWebSocketStore();
    const { isOnline, queuedRequests } = useOfflineStore();

    // Don't show anything if everything is normal
    if (connectionState === 'connected' && isOnline && queuedRequests.length === 0) {
        return null;
    }

    // Determine status message and styling
    const getStatusInfo = () => {
        if (!isOnline) {
            return {
                icon: <WifiOff className="h-4 w-4" />,
                label: 'Offline',
                description: queuedRequests.length > 0
                    ? `${queuedRequests.length} update${queuedRequests.length === 1 ? '' : 's'} queued`
                    : 'You are currently offline',
                variant: 'destructive' as const,
                showQueue: true,
            };
        }

        if (connectionState === 'reconnecting') {
            return {
                icon: <RefreshCw className="h-4 w-4 animate-spin" />,
                label: 'Reconnecting',
                description: reconnectAttempts > 0
                    ? `Attempt ${reconnectAttempts}...`
                    : 'Reconnecting to server...',
                variant: 'default' as const,
                showQueue: false,
            };
        }

        if (connectionState === 'connecting') {
            return {
                icon: <RefreshCw className="h-4 w-4 animate-spin" />,
                label: 'Connecting',
                description: 'Establishing connection...',
                variant: 'default' as const,
                showQueue: false,
            };
        }

        if (connectionState === 'disconnected') {
            return {
                icon: <AlertCircle className="h-4 w-4" />,
                label: 'Disconnected',
                description: 'Connection lost',
                variant: 'destructive' as const,
                showQueue: false,
            };
        }

        // Connected but has queued requests (syncing)
        if (queuedRequests.length > 0) {
            return {
                icon: <RefreshCw className="h-4 w-4 animate-spin" />,
                label: 'Syncing',
                description: `Syncing ${queuedRequests.length} update${queuedRequests.length === 1 ? '' : 's'}...`,
                variant: 'default' as const,
                showQueue: true,
            };
        }

        return null;
    };

    const statusInfo = getStatusInfo();

    if (!statusInfo) {
        return null;
    }

    // Compact badge view (for header/navbar)
    if (!showDetails) {
        return (
            <Badge
                variant={statusInfo.variant}
                className={cn('flex items-center gap-1.5', className)}
            >
                {statusInfo.icon}
                <span className="text-xs">{statusInfo.label}</span>
            </Badge>
        );
    }

    // Detailed alert view (for full-width notification)
    return (
        <Alert variant={statusInfo.variant} className={cn('mb-4', className)}>
            <div className="flex items-start gap-3">
                {statusInfo.icon}
                <div className="flex-1">
                    <div className="font-semibold">{statusInfo.label}</div>
                    <AlertDescription className="mt-1">
                        {statusInfo.description}
                    </AlertDescription>
                    {statusInfo.showQueue && queuedRequests.length > 0 && (
                        <div className="mt-2 text-sm text-muted-foreground">
                            Your changes will be synced automatically when connection is restored.
                        </div>
                    )}
                </div>
            </div>
        </Alert>
    );
}

/**
 * Floating connection status indicator (for bottom-right corner)
 */
export function FloatingConnectionStatus() {
    const { connectionState } = useWebSocketStore();
    const { isOnline, queuedRequests } = useOfflineStore();

    // Don't show if everything is normal
    if (connectionState === 'connected' && isOnline && queuedRequests.length === 0) {
        return null;
    }

    return (
        <div className="fixed bottom-4 right-4 z-50">
            <ConnectionStatus showDetails />
        </div>
    );
}
