import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Smartphone, Apple, TabletSmartphone } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import type { MobileMetrics as MobileMetricsType } from "@/types";

interface MobileMetricsProps {
    data: MobileMetricsType;
    isLoading?: boolean;
}

const COLORS = {
    ios: "hsl(var(--chart-1))",
    android: "hsl(var(--chart-2))",
};

export function MobileMetrics({ data, isLoading }: MobileMetricsProps) {
    if (isLoading) {
        return (
            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <div className="h-6 w-48 bg-muted animate-pulse rounded mb-2" />
                        <div className="h-4 w-64 bg-muted animate-pulse rounded" />
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px] bg-muted animate-pulse rounded" />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <div className="h-6 w-48 bg-muted animate-pulse rounded mb-2" />
                        <div className="h-4 w-64 bg-muted animate-pulse rounded" />
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px] bg-muted animate-pulse rounded" />
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Platform distribution data
    const platformData = [
        { name: "iOS", value: data.ios_users, color: COLORS.ios },
        { name: "Android", value: data.android_users, color: COLORS.android },
    ];

    // Device types data
    const deviceTypesData = Object.entries(data.device_types).map(([name, value]) => ({
        name,
        value,
    }));

    // App versions data
    const appVersionsData = Object.entries(data.app_version_distribution)
        .map(([version, count]) => ({
            version,
            count,
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5); // Top 5 versions

    return (
        <div className="space-y-4">
            {/* Platform Overview */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">iOS Users</CardTitle>
                        <Apple className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.ios_users.toLocaleString()}</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {((data.ios_users / (data.ios_users + data.android_users)) * 100).toFixed(1)}% of mobile users
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Android Users</CardTitle>
                        <Smartphone className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.android_users.toLocaleString()}</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {((data.android_users / (data.ios_users + data.android_users)) * 100).toFixed(1)}% of mobile users
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Mobile Engagement</CardTitle>
                        <TabletSmartphone className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {(data.mobile_engagement_rate * 100).toFixed(1)}%
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Average engagement rate
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Platform Distribution Chart */}
            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Platform Distribution</CardTitle>
                        <CardDescription>iOS vs Android breakdown</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={platformData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {platformData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Device Types */}
                <Card>
                    <CardHeader>
                        <CardTitle>Device Types</CardTitle>
                        <CardDescription>Distribution by device category</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {deviceTypesData.map((device) => {
                                const total = deviceTypesData.reduce((sum, d) => sum + d.value, 0);
                                const percentage = (device.value / total) * 100;
                                return (
                                    <div key={device.name} className="space-y-1">
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="font-medium capitalize">{device.name}</span>
                                            <span className="text-muted-foreground">
                                                {device.value.toLocaleString()} ({percentage.toFixed(1)}%)
                                            </span>
                                        </div>
                                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-primary transition-all"
                                                style={{ width: `${percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* App Versions */}
            <Card>
                <CardHeader>
                    <CardTitle>App Version Distribution</CardTitle>
                    <CardDescription>Top 5 app versions in use</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {appVersionsData.map((version) => {
                            const total = Object.values(data.app_version_distribution).reduce((sum, count) => sum + count, 0);
                            const percentage = (version.count / total) * 100;
                            return (
                                <div key={version.version} className="space-y-1">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="font-medium">Version {version.version}</span>
                                        <span className="text-muted-foreground">
                                            {version.count.toLocaleString()} users ({percentage.toFixed(1)}%)
                                        </span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-chart-2 transition-all"
                                            style={{ width: `${percentage}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
