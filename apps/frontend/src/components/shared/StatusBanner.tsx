import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { X, AlertCircle, Info, Clock } from 'lucide-react';
import { services } from '@/lib/api';

interface StatusBannerProps {
    checkInterval?: number; // in milliseconds
}

export function StatusBanner({ checkInterval = 60000 }: StatusBannerProps) {
    const [status, setStatus] = useState<'operational' | 'degraded' | 'maintenance' | 'major_outage' | null>(null);
    const [message, setMessage] = useState<string>('');
    const [dismissed, setDismissed] = useState(false);

    useEffect(() => {
        checkStatus();
        const interval = setInterval(checkStatus, checkInterval);
        return () => clearInterval(interval);
    }, [checkInterval]);

    const checkStatus = async () => {
        try {
            const data = await services.status.getHealth();
            const systemStatus = (data as any).overall_status;

            if (systemStatus !== 'operational') {
                setStatus(systemStatus);
                setMessage(getStatusMessage(systemStatus));
                setDismissed(false);
            } else {
                setStatus('operational');
                setDismissed(true);
            }
        } catch (error) {
            console.error('Failed to check system status:', error);
        }
    };

    const getStatusMessage = (status: string): string => {
        switch (status) {
            case 'degraded':
                return 'Some services are experiencing issues. We are working to resolve them.';
            case 'maintenance':
                return 'Scheduled maintenance is in progress. Some features may be temporarily unavailable.';
            case 'major_outage':
                return 'We are experiencing a major service disruption. Our team is working to restore services.';
            default:
                return 'System status update available.';
        }
    };

    const getIcon = () => {
        switch (status) {
            case 'degraded':
                return <AlertCircle className="h-4 w-4" />;
            case 'maintenance':
                return <Clock className="h-4 w-4" />;
            case 'major_outage':
                return <AlertCircle className="h-4 w-4" />;
            default:
                return <Info className="h-4 w-4" />;
        }
    };

    const getVariant = (): 'default' | 'destructive' => {
        switch (status) {
            case 'major_outage':
                return 'destructive';
            default:
                return 'default';
        }
    };

    if (!status || status === 'operational' || dismissed) {
        return null;
    }

    return (
        <Alert variant={getVariant()} className="mb-4">
            <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                    {getIcon()}
                    <div>
                        <AlertTitle>System Status Update</AlertTitle>
                        <AlertDescription>{message}</AlertDescription>
                        <Button
                            variant="link"
                            size="sm"
                            className="px-0 h-auto mt-2"
                            onClick={() => window.location.href = '/status'}
                        >
                            View status page →
                        </Button>
                    </div>
                </div>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => setDismissed(true)}
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>
        </Alert>
    );
}
