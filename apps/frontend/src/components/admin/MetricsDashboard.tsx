import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Users,
    FileText,
    MessageSquare,
    TrendingUp,
    Activity,
    AlertTriangle,
    Clock,
    BarChart3
} from "lucide-react";
import { services } from "@/lib/api";
import type { BusinessMetrics, ModerationMetrics, RealTimeMetrics } from "@/types";

export function MetricsDashboard() {
    const [businessMetrics, setBusinessMetrics] = useState<BusinessMetrics | null>(null);
    const [moderationMetrics, setModerationMetrics] = useState<ModerationMetrics | null>(null);
    const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchMetrics();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchMetrics, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchMetrics = async () => {
        try {
            setError(null);
            const [business, moderation, realTime] = await Promise.all([
                services.admin.getBusinessMetrics(),
                services.admin.getModerationMetrics(),
                services.admin.getRealTimeMetrics(),
            ]);
            setBusinessMetrics(business);
            setModerationMetrics(moderation);
            setRealTimeMetrics(realTime);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch metrics");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                    {[...Array(4)].map((_, i) => (
                        <Card key={i}>
                            <CardHeader className="pb-2">
                                <Skeleton className="h-4 w-24" />
                            </CardHeader>
                            <CardContent>
                                <Skeleton className="h-8 w-16 mb-2" />
                                <Skeleton className="h-3 w-32" />
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
            </Alert>
        );
    }

    return (
        <div className="space-y-6">
            {/* Business Metrics */}
            <div>
                <h3 className="text-lg font-semibold mb-4">Business Metrics</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <MetricCard
                        title="Total Users"
                        value={businessMetrics?.total_users.toLocaleString() ?? "0"}
                        subtitle={`${businessMetrics?.active_users_today.toLocaleString() ?? "0"} active today`}
                        icon={<Users className="h-4 w-4 text-muted-foreground" />}
                        trend={businessMetrics?.user_growth_rate}
                    />
                    <MetricCard
                        title="Total Stories"
                        value={businessMetrics?.total_stories.toLocaleString() ?? "0"}
                        subtitle={`${businessMetrics?.stories_published_today.toLocaleString() ?? "0"} published today`}
                        icon={<FileText className="h-4 w-4 text-muted-foreground" />}
                        trend={businessMetrics?.content_growth_rate}
                    />
                    <MetricCard
                        title="Total Chapters"
                        value={businessMetrics?.total_chapters.toLocaleString() ?? "0"}
                        subtitle={`${businessMetrics?.chapters_published_today.toLocaleString() ?? "0"} published today`}
                        icon={<FileText className="h-4 w-4 text-muted-foreground" />}
                    />
                    <MetricCard
                        title="Total Whispers"
                        value={businessMetrics?.total_whispers.toLocaleString() ?? "0"}
                        subtitle={`${businessMetrics?.whispers_today.toLocaleString() ?? "0"} today`}
                        icon={<MessageSquare className="h-4 w-4 text-muted-foreground" />}
                    />
                </div>
            </div>

            {/* Real-Time Metrics */}
            <div>
                <h3 className="text-lg font-semibold mb-4">Real-Time Activity</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <MetricCard
                        title="Active Users Now"
                        value={realTimeMetrics?.active_users_now.toLocaleString() ?? "0"}
                        subtitle={`${realTimeMetrics?.active_readers.toLocaleString() ?? "0"} readers, ${realTimeMetrics?.active_writers.toLocaleString() ?? "0"} writers`}
                        icon={<Activity className="h-4 w-4 text-muted-foreground" />}
                    />
                    <MetricCard
                        title="Requests/Min"
                        value={realTimeMetrics?.requests_per_minute.toLocaleString() ?? "0"}
                        subtitle={`${realTimeMetrics?.average_response_time.toFixed(0) ?? "0"}ms avg response`}
                        icon={<BarChart3 className="h-4 w-4 text-muted-foreground" />}
                    />
                    <MetricCard
                        title="Error Rate"
                        value={`${((realTimeMetrics?.error_rate ?? 0) * 100).toFixed(2)}%`}
                        subtitle="Last 5 minutes"
                        icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
                        isError={(realTimeMetrics?.error_rate ?? 0) > 0.05}
                    />
                </div>
            </div>

            {/* Moderation Metrics */}
            <div>
                <h3 className="text-lg font-semibold mb-4">Moderation Metrics</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <MetricCard
                        title="Pending Items"
                        value={moderationMetrics?.pending_items.toLocaleString() ?? "0"}
                        subtitle="Awaiting review"
                        icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
                        isWarning={(moderationMetrics?.pending_items ?? 0) > 10}
                    />
                    <MetricCard
                        title="Resolved Today"
                        value={moderationMetrics?.resolved_today.toLocaleString() ?? "0"}
                        subtitle={`${moderationMetrics?.average_resolution_time.toFixed(1) ?? "0"} min avg time`}
                        icon={<Clock className="h-4 w-4 text-muted-foreground" />}
                    />
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium">Items by Severity</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {moderationMetrics && Object.entries(moderationMetrics.items_by_severity).map(([severity, count]) => (
                                    <div key={severity} className="flex justify-between items-center">
                                        <span className="text-sm capitalize">{severity}</span>
                                        <span className="text-sm font-semibold">{count}</span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
                <Card className="mt-4">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Items by Type</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {moderationMetrics && Object.entries(moderationMetrics.items_by_type).map(([type, count]) => (
                                <div key={type} className="text-center">
                                    <div className="text-2xl font-bold">{count}</div>
                                    <div className="text-xs text-muted-foreground capitalize">{type}</div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

interface MetricCardProps {
    title: string;
    value: string;
    subtitle: string;
    icon: React.ReactNode;
    trend?: number;
    isWarning?: boolean;
    isError?: boolean;
}

function MetricCard({ title, value, subtitle, icon, trend, isWarning, isError }: MetricCardProps) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{title}</CardTitle>
                {icon}
            </CardHeader>
            <CardContent>
                <div className={`text-2xl font-bold ${isError ? "text-destructive" : isWarning ? "text-yellow-600" : ""}`}>
                    {value}
                </div>
                <div className="flex items-center gap-2">
                    <p className="text-xs text-muted-foreground">{subtitle}</p>
                    {trend !== undefined && (
                        <div className={`flex items-center text-xs ${trend >= 0 ? "text-green-600" : "text-red-600"}`}>
                            <TrendingUp className={`h-3 w-3 ${trend < 0 ? "rotate-180" : ""}`} />
                            <span>{Math.abs(trend).toFixed(1)}%</span>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
