import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Eye, BookOpen, Users, Activity } from "lucide-react";
import type { AnalyticsDashboard } from "@/types";

interface OverviewMetricsProps {
    data: AnalyticsDashboard;
    isLoading?: boolean;
}

export function OverviewMetrics({ data, isLoading }: OverviewMetricsProps) {
    if (isLoading) {
        return (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                    <Card key={i}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                            <div className="h-4 w-4 bg-muted animate-pulse rounded" />
                        </CardHeader>
                        <CardContent>
                            <div className="h-8 w-32 bg-muted animate-pulse rounded mb-2" />
                            <div className="h-3 w-40 bg-muted animate-pulse rounded" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    const metrics = [
        {
            title: "Total Views",
            value: data.total_views.toLocaleString(),
            description: "Total story views",
            icon: Eye,
            trend: "+12.5% from last month",
        },
        {
            title: "Total Reads",
            value: data.total_reads.toLocaleString(),
            description: "Completed chapter reads",
            icon: BookOpen,
            trend: "+8.2% from last month",
        },
        {
            title: "Followers",
            value: data.total_followers.toLocaleString(),
            description: "Total followers",
            icon: Users,
            trend: "+5.1% from last month",
        },
        {
            title: "Engagement Rate",
            value: `${(data.engagement_rate * 100).toFixed(1)}%`,
            description: "Reader engagement",
            icon: Activity,
            trend: "+2.3% from last month",
        },
    ];

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {metrics.map((metric) => {
                const Icon = metric.icon;
                return (
                    <Card key={metric.title}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                {metric.title}
                            </CardTitle>
                            <Icon className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{metric.value}</div>
                            <p className="text-xs text-muted-foreground mt-1">
                                {metric.description}
                            </p>
                            <div className="flex items-center mt-2 text-xs text-green-600">
                                <TrendingUp className="h-3 w-3 mr-1" />
                                {metric.trend}
                            </div>
                        </CardContent>
                    </Card>
                );
            })}
        </div>
    );
}
