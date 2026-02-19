import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { format, parseISO } from "date-fns";
import type { FollowerGrowthData } from "@/types";

interface FollowerGrowthChartProps {
    data: FollowerGrowthData;
    isLoading?: boolean;
}

export function FollowerGrowthChart({ data, isLoading }: FollowerGrowthChartProps) {
    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <div className="h-6 w-48 bg-muted animate-pulse rounded mb-2" />
                    <div className="h-4 w-64 bg-muted animate-pulse rounded" />
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] bg-muted animate-pulse rounded" />
                </CardContent>
            </Card>
        );
    }

    // Transform data for recharts
    const chartData = data.data_points.map((point) => ({
        date: format(parseISO(point.date), "MMM dd"),
        followers: point.followers,
        newFollowers: point.new_followers,
        unfollows: point.unfollows,
    }));

    return (
        <Card>
            <CardHeader>
                <CardTitle>Follower Growth</CardTitle>
                <CardDescription>
                    Track your audience growth over time
                </CardDescription>
                <div className="flex gap-6 mt-4">
                    <div>
                        <p className="text-sm text-muted-foreground">Total Growth</p>
                        <p className="text-2xl font-bold">
                            {data.total_growth > 0 ? "+" : ""}
                            {data.total_growth.toLocaleString()}
                        </p>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground">Growth Rate</p>
                        <p className="text-2xl font-bold">
                            {data.growth_rate > 0 ? "+" : ""}
                            {(data.growth_rate * 100).toFixed(1)}%
                        </p>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey="date"
                            className="text-xs"
                            tick={{ fill: "hsl(var(--muted-foreground))" }}
                        />
                        <YAxis
                            className="text-xs"
                            tick={{ fill: "hsl(var(--muted-foreground))" }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "hsl(var(--background))",
                                border: "1px solid hsl(var(--border))",
                                borderRadius: "var(--radius)",
                            }}
                            labelStyle={{ color: "hsl(var(--foreground))" }}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="followers"
                            stroke="hsl(var(--primary))"
                            strokeWidth={2}
                            name="Total Followers"
                            dot={{ fill: "hsl(var(--primary))" }}
                        />
                        <Line
                            type="monotone"
                            dataKey="newFollowers"
                            stroke="hsl(var(--chart-2))"
                            strokeWidth={2}
                            name="New Followers"
                            dot={{ fill: "hsl(var(--chart-2))" }}
                        />
                        <Line
                            type="monotone"
                            dataKey="unfollows"
                            stroke="hsl(var(--destructive))"
                            strokeWidth={2}
                            name="Unfollows"
                            dot={{ fill: "hsl(var(--destructive))" }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
