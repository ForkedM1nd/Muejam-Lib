import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle, XCircle, Clock } from "lucide-react";
import { services } from "@/lib/api";
import type { HealthStatus, ComponentStatus } from "@/types";

const REFRESH_INTERVAL = 30000; // 30 seconds

function getStatusIcon(status: ComponentStatus["status"]) {
    switch (status) {
        case "operational":
            return <CheckCircle className="h-5 w-5 text-green-500" />;
        case "degraded":
            return <AlertCircle className="h-5 w-5 text-yellow-500" />;
        case "down":
            return <XCircle className="h-5 w-5 text-red-500" />;
        default:
            return <Clock className="h-5 w-5 text-gray-500" />;
    }
}

function getStatusBadge(status: ComponentStatus["status"]) {
    switch (status) {
        case "operational":
            return <Badge className="bg-green-500">Operational</Badge>;
        case "degraded":
            return <Badge className="bg-yellow-500">Degraded</Badge>;
        case "down":
            return <Badge className="bg-red-500">Down</Badge>;
        default:
            return <Badge variant="secondary">Unknown</Badge>;
    }
}

function getOverallStatusBadge(status: HealthStatus["status"]) {
    switch (status) {
        case "healthy":
            return <Badge className="bg-green-500 text-lg px-4 py-1">Healthy</Badge>;
        case "degraded":
            return <Badge className="bg-yellow-500 text-lg px-4 py-1">Degraded</Badge>;
        case "down":
            return <Badge className="bg-red-500 text-lg px-4 py-1">Down</Badge>;
        default:
            return <Badge variant="secondary" className="text-lg px-4 py-1">Unknown</Badge>;
    }
}

export function HealthMetrics() {
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const fetchHealth = async () => {
        try {
            setError(null);
            const data = await services.admin.getHealth();
            setHealth(data);
            setLastUpdated(new Date());
            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch health metrics");
            setLoading(false);
        }
    };

    useEffect(() => {
        // Initial fetch
        fetchHealth();

        // Set up auto-refresh
        const interval = setInterval(fetchHealth, REFRESH_INTERVAL);

        // Cleanup
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>System Health</CardTitle>
                    <CardDescription>Loading health metrics...</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>System Health</CardTitle>
                    <CardDescription>Error loading health metrics</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-500">
                        <XCircle className="h-5 w-5" />
                        <p>{error}</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!health) {
        return null;
    }

    const components = [
        { name: "Database", status: health.database },
        { name: "Cache", status: health.cache },
        { name: "Storage", status: health.storage },
        { name: "WebSocket", status: health.websocket },
    ];

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>System Health</CardTitle>
                            <CardDescription>
                                Real-time system health information
                                {lastUpdated && (
                                    <span className="ml-2 text-xs">
                                        (Last updated: {lastUpdated.toLocaleTimeString()})
                                    </span>
                                )}
                            </CardDescription>
                        </div>
                        {getOverallStatusBadge(health.status)}
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                        {components.map((component) => (
                            <div
                                key={component.name}
                                className="flex items-center justify-between p-4 border rounded-lg"
                            >
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(component.status.status)}
                                    <div>
                                        <p className="font-medium">{component.name}</p>
                                        {component.status.response_time !== undefined && (
                                            <p className="text-sm text-muted-foreground">
                                                {component.status.response_time}ms
                                            </p>
                                        )}
                                        {component.status.error && (
                                            <p className="text-sm text-red-500">{component.status.error}</p>
                                        )}
                                    </div>
                                </div>
                                {getStatusBadge(component.status.status)}
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
