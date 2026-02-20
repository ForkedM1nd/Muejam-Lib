import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, AlertCircle, Clock, Activity } from 'lucide-react';
import { services } from '@/lib/api';
import PageHeader from '@/components/shared/PageHeader';
import SurfacePanel from '@/components/shared/SurfacePanel';

interface ComponentStatus {
    name: string;
    status: 'operational' | 'degraded' | 'down';
    response_time?: number;
    error?: string;
}

interface SystemStatus {
    overall_status: 'operational' | 'degraded' | 'maintenance' | 'major_outage';
    components: ComponentStatus[];
    last_updated: string;
}

export default function StatusPage() {
    const [status, setStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStatus();
        // Refresh every 30 seconds
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const data = await services.status.getHealth();
            setStatus(data as SystemStatus);
        } catch (error) {
            console.error('Failed to fetch status:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'operational':
                return <CheckCircle className="h-5 w-5 text-green-600" />;
            case 'degraded':
                return <AlertCircle className="h-5 w-5 text-yellow-600" />;
            case 'down':
            case 'major_outage':
                return <XCircle className="h-5 w-5 text-red-600" />;
            case 'maintenance':
                return <Clock className="h-5 w-5 text-blue-600" />;
            default:
                return <Activity className="h-5 w-5 text-gray-600" />;
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'operational':
                return <Badge className="bg-green-600">Operational</Badge>;
            case 'degraded':
                return <Badge className="bg-yellow-600">Degraded</Badge>;
            case 'down':
                return <Badge className="bg-red-600">Down</Badge>;
            case 'major_outage':
                return <Badge className="bg-red-600">Major Outage</Badge>;
            case 'maintenance':
                return <Badge className="bg-blue-600">Maintenance</Badge>;
            default:
                return <Badge>Unknown</Badge>;
        }
    };

    if (loading) {
        return (
            <SurfacePanel className="p-8 text-center">Loading system status...</SurfacePanel>
        );
    }

    if (!status) {
        return (
            <SurfacePanel className="p-6">
                <Alert variant="destructive">
                    <AlertDescription>
                        Failed to load system status. Please try again later.
                    </AlertDescription>
                </Alert>
            </SurfacePanel>
        );
    }

    return (
        <div className="space-y-6">
            <PageHeader
                title="System Status"
                eyebrow="Operations"
                description="Current operational status of MueJam Library services."
            />

            {/* Overall Status */}
            <Card className="mb-6">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {getStatusIcon(status.overall_status)}
                            <div>
                                <CardTitle>Overall Status</CardTitle>
                                <CardDescription>
                                    Last updated: {new Date(status.last_updated).toLocaleString()}
                                </CardDescription>
                            </div>
                        </div>
                        {getStatusBadge(status.overall_status)}
                    </div>
                </CardHeader>
                {status.overall_status !== 'operational' && (
                    <CardContent>
                        <Alert>
                            <AlertDescription>
                                {status.overall_status === 'degraded' &&
                                    'Some services are experiencing issues. We are working to resolve them.'}
                                {status.overall_status === 'maintenance' &&
                                    'Scheduled maintenance is in progress. Services may be temporarily unavailable.'}
                                {status.overall_status === 'major_outage' &&
                                    'We are experiencing a major service disruption. Our team is working to restore services as quickly as possible.'}
                            </AlertDescription>
                        </Alert>
                    </CardContent>
                )}
            </Card>

            {/* Component Status */}
            <Card>
                <CardHeader>
                    <CardTitle>Service Components</CardTitle>
                    <CardDescription>
                        Status of individual system components
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {status.components.map((component) => (
                            <div
                                key={component.name}
                                className="flex items-center justify-between p-4 border rounded-lg"
                            >
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(component.status)}
                                    <div>
                                        <h3 className="font-medium">{component.name}</h3>
                                        {component.response_time && (
                                            <p className="text-sm text-muted-foreground">
                                                Response time: {component.response_time}ms
                                            </p>
                                        )}
                                        {component.error && (
                                            <p className="text-sm text-red-600">{component.error}</p>
                                        )}
                                    </div>
                                </div>
                                {getStatusBadge(component.status)}
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Auto-refresh notice */}
            <div className="mt-6 text-center text-sm text-muted-foreground">
                Status updates automatically every 30 seconds
            </div>
        </div>
    );
}
