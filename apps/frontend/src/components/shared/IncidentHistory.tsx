import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { services } from '@/lib/api';
import type { Incident } from '@/types';
import { formatDistanceToNow } from 'date-fns';

export function IncidentHistory() {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchIncidents();
    }, []);

    const fetchIncidents = async () => {
        try {
            const data = await services.status.getIncidents();
            setIncidents(data);
        } catch (error) {
            console.error('Failed to fetch incidents:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'resolved':
                return <CheckCircle className="h-4 w-4 text-green-600" />;
            case 'monitoring':
                return <Clock className="h-4 w-4 text-blue-600" />;
            default:
                return <AlertCircle className="h-4 w-4 text-yellow-600" />;
        }
    };

    const getSeverityBadge = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <Badge className="bg-red-600">Critical</Badge>;
            case 'major':
                return <Badge className="bg-orange-600">Major</Badge>;
            case 'minor':
                return <Badge className="bg-yellow-600">Minor</Badge>;
            default:
                return <Badge>Unknown</Badge>;
        }
    };

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Recent Incidents</CardTitle>
                    <CardDescription>Loading...</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    if (incidents.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Recent Incidents</CardTitle>
                    <CardDescription>No recent incidents</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle className="h-5 w-5" />
                        <p>All systems operational</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Recent Incidents</CardTitle>
                <CardDescription>Past incidents and their resolutions</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {incidents.map((incident) => (
                        <div key={incident.id} className="border rounded-lg p-4">
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    {getStatusIcon(incident.status)}
                                    <h3 className="font-medium">{incident.title}</h3>
                                </div>
                                {getSeverityBadge(incident.severity)}
                            </div>
                            <p className="text-sm text-muted-foreground mb-3">
                                {incident.description}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                <span>
                                    Started {formatDistanceToNow(new Date(incident.started_at), { addSuffix: true })}
                                </span>
                                {incident.resolved_at && (
                                    <span>
                                        Resolved {formatDistanceToNow(new Date(incident.resolved_at), { addSuffix: true })}
                                    </span>
                                )}
                            </div>
                            {incident.updates && incident.updates.length > 0 && (
                                <div className="mt-3 pt-3 border-t">
                                    <p className="text-xs font-medium mb-2">Updates:</p>
                                    <div className="space-y-2">
                                        {incident.updates.slice(0, 3).map((update, index) => (
                                            <div key={index} className="text-xs">
                                                <span className="text-muted-foreground">
                                                    {formatDistanceToNow(new Date(update.created_at), { addSuffix: true })}:
                                                </span>{' '}
                                                {update.message}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
