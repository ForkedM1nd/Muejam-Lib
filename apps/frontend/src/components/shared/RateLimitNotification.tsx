// ── Rate Limit Notification Component ──
// Displays rate limit exceeded notifications with retry time

import { useEffect, useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RateLimitNotificationProps {
    retryAfter: number; // seconds until retry is allowed
    onDismiss?: () => void;
    className?: string;
}

/**
 * Rate limit notification component
 * Shows countdown until user can retry the request
 */
export function RateLimitNotification({
    retryAfter,
    onDismiss,
    className,
}: RateLimitNotificationProps) {
    const [timeRemaining, setTimeRemaining] = useState(retryAfter);

    useEffect(() => {
        if (timeRemaining <= 0) {
            onDismiss?.();
            return;
        }

        const timer = setInterval(() => {
            setTimeRemaining((prev) => {
                const next = prev - 1;
                if (next <= 0) {
                    onDismiss?.();
                }
                return next;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [timeRemaining, onDismiss]);

    const formatTime = (seconds: number): string => {
        if (seconds < 60) {
            return `${seconds} second${seconds === 1 ? '' : 's'}`;
        }
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        if (remainingSeconds === 0) {
            return `${minutes} minute${minutes === 1 ? '' : 's'}`;
        }
        return `${minutes}m ${remainingSeconds}s`;
    };

    return (
        <Alert variant="destructive" className={cn('mb-4', className)}>
            <div className="flex items-start gap-3">
                <AlertTriangle className="h-4 w-4 mt-0.5" />
                <div className="flex-1">
                    <div className="font-semibold">Rate Limit Exceeded</div>
                    <AlertDescription className="mt-1">
                        You've made too many requests. Please wait before trying again.
                    </AlertDescription>
                    <div className="mt-2 flex items-center gap-2 text-sm">
                        <Clock className="h-3.5 w-3.5" />
                        <span>Retry in {formatTime(timeRemaining)}</span>
                    </div>
                </div>
            </div>
        </Alert>
    );
}

/**
 * Floating rate limit notification (for bottom-right corner)
 */
export function FloatingRateLimitNotification({
    retryAfter,
    onDismiss,
}: Omit<RateLimitNotificationProps, 'className'>) {
    return (
        <div className="fixed bottom-4 right-4 z-50 max-w-md">
            <RateLimitNotification retryAfter={retryAfter} onDismiss={onDismiss} />
        </div>
    );
}
