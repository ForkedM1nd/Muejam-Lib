import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useUser } from "@clerk/clerk-react";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, TrendingUp, Users, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { api, services } from "@/lib/api";
import { OverviewMetrics, FollowerGrowthChart, MobileMetrics, StoryAnalytics } from "@/components/analytics";

export default function AnalyticsDashboard() {
    const { user, isLoaded } = useUser();
    const [activeTab, setActiveTab] = useState("overview");
    const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
    const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);

    // Check if user is a content creator (has published stories)
    // For now, we'll check if user is authenticated
    // In production, this should check if user has any published stories
    const isContentCreator = !!user;

    // Fetch user's stories for the story selector
    const { data: storiesData } = useQuery({
        queryKey: ["stories", "user"],
        queryFn: () => api.getStories({ sort: "updated" }),
        enabled: isContentCreator && activeTab === "stories",
    });

    // Fetch analytics data
    const { data: dashboardData, isLoading: isDashboardLoading } = useQuery({
        queryKey: ["analytics", "dashboard"],
        queryFn: () => services.analytics.getDashboard(),
        enabled: isContentCreator && activeTab === "overview",
    });

    const { data: followerGrowthData, isLoading: isFollowerGrowthLoading } = useQuery({
        queryKey: ["analytics", "follower-growth", dateRange],
        queryFn: () => services.analytics.getFollowerGrowth({
            start_date: dateRange.from ? format(dateRange.from, "yyyy-MM-dd") : undefined,
            end_date: dateRange.to ? format(dateRange.to, "yyyy-MM-dd") : undefined,
        }),
        enabled: isContentCreator && (activeTab === "overview" || activeTab === "followers"),
    });

    const { data: mobileMetricsData, isLoading: isMobileMetricsLoading } = useQuery({
        queryKey: ["analytics", "mobile"],
        queryFn: () => services.analytics.getMobileMetrics(),
        enabled: isContentCreator && activeTab === "overview",
    });

    // Fetch story-specific analytics
    const { data: storyAnalyticsData, isLoading: isStoryAnalyticsLoading } = useQuery({
        queryKey: ["analytics", "story", selectedStoryId],
        queryFn: () => services.analytics.getStoryAnalytics(selectedStoryId!),
        enabled: isContentCreator && activeTab === "stories" && !!selectedStoryId,
    });

    // Handle CSV export
    const handleExportStoryAnalytics = async () => {
        if (!selectedStoryId) return;

        try {
            const blob = await services.analytics.exportStoryAnalytics(selectedStoryId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `story-analytics-${selectedStoryId}-${format(new Date(), "yyyy-MM-dd")}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error("Failed to export analytics:", error);
        }
    };

    // Show loading state while checking auth
    if (!isLoaded) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    // Redirect non-authenticated users
    if (!isContentCreator) {
        return <Navigate to="/sign-in" replace />;
    }

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <aside className="hidden md:flex md:w-64 md:flex-col border-r">
                <div className="flex h-16 items-center border-b px-6">
                    <BarChart3 className="h-6 w-6 mr-2 text-primary" />
                    <h1 className="text-xl font-bold">Analytics</h1>
                </div>
                <nav className="flex-1 space-y-1 p-4">
                    <button
                        onClick={() => setActiveTab("overview")}
                        className={`flex items-center w-full px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "overview"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            }`}
                    >
                        <TrendingUp className="mr-3 h-5 w-5" />
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab("stories")}
                        className={`flex items-center w-full px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "stories"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            }`}
                    >
                        <BarChart3 className="mr-3 h-5 w-5" />
                        Story Analytics
                    </button>
                    <button
                        onClick={() => setActiveTab("followers")}
                        className={`flex items-center w-full px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === "followers"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            }`}
                    >
                        <Users className="mr-3 h-5 w-5" />
                        Followers
                    </button>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="container mx-auto p-6 space-y-6">
                    {/* Header with Date Range Selector */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight">
                                {activeTab === "overview" && "Overview"}
                                {activeTab === "stories" && "Story Analytics"}
                                {activeTab === "followers" && "Follower Growth"}
                            </h2>
                            <p className="text-muted-foreground">
                                {activeTab === "overview" && "Your content performance at a glance"}
                                {activeTab === "stories" && "Detailed analytics for your stories"}
                                {activeTab === "followers" && "Track your audience growth"}
                            </p>
                        </div>

                        {/* Date Range Selector */}
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button
                                    variant="outline"
                                    className={cn(
                                        "w-[280px] justify-start text-left font-normal",
                                        !dateRange.from && "text-muted-foreground"
                                    )}
                                >
                                    <Calendar className="mr-2 h-4 w-4" />
                                    {dateRange.from ? (
                                        dateRange.to ? (
                                            <>
                                                {format(dateRange.from, "LLL dd, y")} -{" "}
                                                {format(dateRange.to, "LLL dd, y")}
                                            </>
                                        ) : (
                                            format(dateRange.from, "LLL dd, y")
                                        )
                                    ) : (
                                        <span>Pick a date range</span>
                                    )}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="end">
                                <CalendarComponent
                                    mode="range"
                                    selected={dateRange}
                                    onSelect={(range) => setDateRange(range || {})}
                                    numberOfMonths={2}
                                />
                            </PopoverContent>
                        </Popover>
                    </div>

                    {/* Mobile Navigation */}
                    <div className="md:hidden">
                        <Tabs value={activeTab} onValueChange={setActiveTab}>
                            <TabsList className="grid w-full grid-cols-3">
                                <TabsTrigger value="overview">
                                    <TrendingUp className="h-4 w-4 mr-2" />
                                    Overview
                                </TabsTrigger>
                                <TabsTrigger value="stories">
                                    <BarChart3 className="h-4 w-4 mr-2" />
                                    Stories
                                </TabsTrigger>
                                <TabsTrigger value="followers">
                                    <Users className="h-4 w-4 mr-2" />
                                    Followers
                                </TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>

                    {/* Content Sections */}
                    {activeTab === "overview" && (
                        <div className="space-y-6">
                            {dashboardData && (
                                <OverviewMetrics
                                    data={dashboardData}
                                    isLoading={isDashboardLoading}
                                />
                            )}

                            {followerGrowthData && (
                                <FollowerGrowthChart
                                    data={followerGrowthData}
                                    isLoading={isFollowerGrowthLoading}
                                />
                            )}

                            {mobileMetricsData && (
                                <MobileMetrics
                                    data={mobileMetricsData}
                                    isLoading={isMobileMetricsLoading}
                                />
                            )}

                            {/* Top Stories Section */}
                            {dashboardData && dashboardData.top_stories.length > 0 && (
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Top Performing Stories</CardTitle>
                                        <CardDescription>
                                            Your most popular stories this period
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-4">
                                            {dashboardData.top_stories.map((story) => (
                                                <div
                                                    key={story.story_id}
                                                    className="flex items-center justify-between p-4 border rounded-lg"
                                                >
                                                    <div>
                                                        <h4 className="font-medium">{story.story_title}</h4>
                                                        <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                                                            <span>{story.views.toLocaleString()} views</span>
                                                            <span>{story.reads.toLocaleString()} reads</span>
                                                            <span>{(story.engagement * 100).toFixed(1)}% engagement</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    )}

                    {activeTab === "stories" && (
                        <div className="space-y-6">
                            {/* Story Selector */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Select a Story</CardTitle>
                                    <CardDescription>
                                        Choose a story to view detailed analytics
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <Select
                                        value={selectedStoryId || ""}
                                        onValueChange={(value) => setSelectedStoryId(value)}
                                    >
                                        <SelectTrigger className="w-full">
                                            <SelectValue placeholder="Select a story..." />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {storiesData?.results.map((story) => (
                                                <SelectItem key={story.id} value={story.id}>
                                                    {story.title}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </CardContent>
                            </Card>

                            {/* Story Analytics */}
                            {selectedStoryId && storyAnalyticsData && (
                                <StoryAnalytics
                                    data={storyAnalyticsData}
                                    isLoading={isStoryAnalyticsLoading}
                                    onExport={handleExportStoryAnalytics}
                                />
                            )}

                            {/* Empty State */}
                            {!selectedStoryId && (
                                <Card>
                                    <CardContent className="flex flex-col items-center justify-center py-12">
                                        <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                                        <p className="text-lg font-medium mb-2">No Story Selected</p>
                                        <p className="text-sm text-muted-foreground text-center max-w-md">
                                            Select a story from the dropdown above to view detailed analytics including views, engagement, demographics, and more.
                                        </p>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    )}

                    {activeTab === "followers" && (
                        <div className="space-y-6">
                            {followerGrowthData && (
                                <FollowerGrowthChart
                                    data={followerGrowthData}
                                    isLoading={isFollowerGrowthLoading}
                                />
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
