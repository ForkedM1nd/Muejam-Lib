import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { services } from "@/lib/api";

export function ModerationMetrics() {
    const { data: metrics, isLoading, isError } = useQuery({
        queryKey: ["admin", "metrics", "moderation"],
        queryFn: () => services.admin.getModerationMetrics(),
        refetchInterval: 30000, // Refresh every 30 seconds
    });

    if (isLoading) {
        return (
            <Card>
                <CardContent className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </CardContent>
            </Card>
        );
    }

    if (isError || !metrics) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center py-8">
                    <AlertCircle className="h-8 w-8 text-destructive mb-2" />
                    <p className="text-sm text-muted-foreground">Failed to load metrics</p>
                </CardContent>
            </Card>
        );
    }

    // Format resolution time (in minutes)
    const formatResolutionTime = (minutes: number) => {
        if (minutes < 60) {
            return `${Math.round(minutes)}m`;
        }
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    };

    return (
        <div className="space-y-4">
            {/* Overview Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Pending Items</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{metrics.pending_items}</div>
                        <p className="text-xs text-muted-foreground">
                            Awaiting review
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Resolved Today</CardTitle>
                        <CheckCircle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{metrics.resolved_today}</div>
                        <p className="text-xs text-muted-foreground">
                            Completed actions
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Resolution Time</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {formatResolutionTime(metrics.average_resolution_time)}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Time to resolve
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Items by Severity */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium">Items by Severity</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {Object.entries(metrics.items_by_severity).map(([severity, count]) => (
                            <div key={severity} className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <div
                                        className={`h-2 w-2 rounded-full ${severity === "high"
                                            ? "bg-red-500"
                                            : severity === "medium"
                                                ? "bg-yellow-500"
                                                : "bg-blue-500"
                                            }`}
                                    />
                                    <span className="text-sm capitalize">{severity}</span>
                                </div>
                                <span className="text-sm font-medium">{count}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Items by Type */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium">Items by Type</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {Object.entries(metrics.items_by_type).map(([type, count]) => (
                            <div key={type} className="flex items-center justify-between">
                                <span className="text-sm capitalize">{type}</span>
                                <span className="text-sm font-medium">{count}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
