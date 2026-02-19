import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Eye, BookOpen, TrendingUp, Users, Clock, MapPin, ExternalLink } from "lucide-react";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { format, parseISO } from "date-fns";
import type { StoryAnalytics as StoryAnalyticsType } from "@/types";

interface StoryAnalyticsProps {
    data: StoryAnalyticsType;
    isLoading?: boolean;
    onExport?: () => void;
}

const COLORS = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))", "hsl(var(--chart-5))"];

export function StoryAnalytics({ data, isLoading, onExport }: StoryAnalyticsProps) {
    if (isLoading) {
        return (
            <div className="space-y-6">
                {[...Array(4)].map((_, i) => (
                    <Card key={i}>
                        <CardHeader>
                            <div className="h-6 w-48 bg-muted animate-pulse rounded mb-2" />
                            <div className="h-4 w-64 bg-muted animate-pulse rounded" />
                        </CardHeader>
                        <CardContent>
                            <div className="h-[300px] bg-muted animate-pulse rounded" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    // Transform time series data for charts
    const timeSeriesData = data.time_series.map((point) => ({
        date: format(parseISO(point.date), "MMM dd"),
        value: point.value,
    }));

    // Transform traffic sources for pie chart
    const trafficSourceData = data.traffic_sources.map((source) => ({
        name: source.source,
        value: source.visits,
        percentage: source.percentage,
    }));

    // Transform demographics for charts
    const ageGroupData = Object.entries(data.demographics.age_groups).map(([age, count]) => ({
        age,
        count,
    }));

    const locationData = Object.entries(data.demographics.locations)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([location, count]) => ({
            location,
            count,
        }));

    return (
        <div className="space-y-6">
            {/* Header with Export Button */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-2xl font-bold">Story Analytics</h3>
                    <p className="text-sm text-muted-foreground">
                        Detailed performance metrics for your story
                    </p>
                </div>
                {onExport && (
                    <Button onClick={onExport} variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        Export CSV
                    </Button>
                )}
            </div>

            {/* Key Metrics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Views</CardTitle>
                        <Eye className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.views.toLocaleString()}</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Story page visits
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Unique Readers</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.unique_readers.toLocaleString()}</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Individual readers
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
                        <BookOpen className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {(data.completion_rate * 100).toFixed(1)}%
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Readers who finished
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg. Read Time</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {Math.round(data.average_read_time)} min
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Per reading session
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Engagement Score */}
            <Card>
                <CardHeader>
                    <CardTitle>Engagement Score</CardTitle>
                    <CardDescription>
                        Overall reader engagement with your story
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-4">
                        <div className="text-4xl font-bold text-primary">
                            {(data.engagement_score * 100).toFixed(0)}
                        </div>
                        <div className="flex-1">
                            <div className="h-4 bg-muted rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary transition-all"
                                    style={{ width: `${data.engagement_score * 100}%` }}
                                />
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">
                                Based on views, reads, completion rate, and interaction metrics
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Time Series Chart */}
            <Card>
                <CardHeader>
                    <CardTitle>Views Over Time</CardTitle>
                    <CardDescription>
                        Track how your story views have changed over time
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeSeriesData}>
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
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke="hsl(var(--primary))"
                                strokeWidth={2}
                                name="Views"
                                dot={{ fill: "hsl(var(--primary))" }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Chapter Performance */}
            <Card>
                <CardHeader>
                    <CardTitle>Chapter Performance</CardTitle>
                    <CardDescription>
                        See how each chapter is performing
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data.chapter_performance}>
                            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                            <XAxis
                                dataKey="chapter_title"
                                className="text-xs"
                                tick={{ fill: "hsl(var(--muted-foreground))" }}
                                angle={-45}
                                textAnchor="end"
                                height={100}
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
                            <Bar
                                dataKey="views"
                                fill="hsl(var(--primary))"
                                name="Views"
                            />
                            <Bar
                                dataKey="completion_rate"
                                fill="hsl(var(--chart-2))"
                                name="Completion Rate (%)"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Traffic Sources */}
            <Card>
                <CardHeader>
                    <CardTitle>Traffic Sources</CardTitle>
                    <CardDescription>
                        Where your readers are coming from
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">
                        <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                                <Pie
                                    data={trafficSourceData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {trafficSourceData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "hsl(var(--background))",
                                        border: "1px solid hsl(var(--border))",
                                        borderRadius: "var(--radius)",
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>

                        <div className="space-y-3">
                            {trafficSourceData.map((source, index) => (
                                <div key={source.name} className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div
                                            className="w-3 h-3 rounded-full"
                                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                                        />
                                        <span className="text-sm font-medium">{source.name}</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm font-bold">{source.value.toLocaleString()}</div>
                                        <div className="text-xs text-muted-foreground">
                                            {source.percentage.toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Demographics */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Age Groups */}
                <Card>
                    <CardHeader>
                        <CardTitle>Reader Age Groups</CardTitle>
                        <CardDescription>
                            Age distribution of your readers
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={ageGroupData}>
                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                <XAxis
                                    dataKey="age"
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
                                />
                                <Bar
                                    dataKey="count"
                                    fill="hsl(var(--primary))"
                                    name="Readers"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                {/* Top Locations */}
                <Card>
                    <CardHeader>
                        <CardTitle>Top Locations</CardTitle>
                        <CardDescription>
                            Where your readers are located
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {locationData.map((location, index) => (
                                <div key={location.location} className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <MapPin className="h-4 w-4 text-muted-foreground" />
                                        <span className="text-sm font-medium">{location.location}</span>
                                    </div>
                                    <div className="text-sm font-bold">{location.count.toLocaleString()}</div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
