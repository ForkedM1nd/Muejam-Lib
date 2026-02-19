import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useUser } from "@clerk/clerk-react";
import { Shield, Filter, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { ModerationQueueItem } from "@/components/moderation/ModerationQueueItem";
import { ModerationMetrics } from "@/components/moderation/ModerationMetrics";
import { useModerationQueue } from "@/hooks/useModerationQueue";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { Button } from "@/components/ui/button";

export default function ModerationQueue() {
    const { user, isLoaded } = useUser();
    const navigate = useNavigate();
    const [contentTypeFilter, setContentTypeFilter] = useState<string>("all");
    const [severityFilter, setSeverityFilter] = useState<string>("all");
    const [statusFilter, setStatusFilter] = useState<string>("pending");

    // Check if user has moderator role
    const isModerator = user?.publicMetadata?.role === "moderator" || user?.publicMetadata?.role === "admin";

    // Build query params for the moderation queue
    const queueParams = {
        content_type: contentTypeFilter !== "all" ? contentTypeFilter : undefined,
        severity: severityFilter !== "all" ? severityFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        page_size: 20,
    };

    // Fetch moderation queue with infinite scroll
    const {
        data,
        isLoading,
        isError,
        error,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        invalidateQueue,
    } = useModerationQueue(queueParams);

    // Set up infinite scroll
    const sentinelRef = useInfiniteScroll({
        onLoadMore: fetchNextPage,
        hasMore: hasNextPage ?? false,
        isLoading: isFetchingNextPage,
    });

    // Handle review action
    const handleReview = (itemId: string) => {
        // Navigate to a review detail page (to be implemented in task 8.3)
        navigate(`/moderation/review/${itemId}`);
    };

    // Flatten all pages into a single array of items
    const allItems = data?.pages.flatMap((page) => page.results) ?? [];

    // Show loading state while checking auth
    if (!isLoaded) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Redirect non-moderator users
    if (!isModerator) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <aside className="hidden md:flex md:w-80 md:flex-col border-r">
                <div className="flex h-16 items-center border-b px-6">
                    <Shield className="h-6 w-6 mr-2 text-primary" />
                    <h1 className="text-xl font-bold">Moderation</h1>
                </div>
                <nav className="flex-1 space-y-1 p-4 overflow-y-auto">
                    {/* Metrics Section */}
                    <div className="mb-6">
                        <h3 className="text-sm font-medium text-muted-foreground mb-3 px-4">Metrics</h3>
                        <ModerationMetrics />
                    </div>

                    {/* Filters Section */}
                    <div className="px-4 py-2">
                        <h3 className="text-sm font-medium text-muted-foreground mb-2">Queue Filters</h3>

                        {/* Content Type Filter */}
                        <div className="space-y-2 mb-4">
                            <label className="text-xs font-medium">Content Type</label>
                            <Select value={contentTypeFilter} onValueChange={setContentTypeFilter}>
                                <SelectTrigger className="w-full">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Types</SelectItem>
                                    <SelectItem value="story">Stories</SelectItem>
                                    <SelectItem value="chapter">Chapters</SelectItem>
                                    <SelectItem value="whisper">Whispers</SelectItem>
                                    <SelectItem value="user">Users</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Severity Filter */}
                        <div className="space-y-2 mb-4">
                            <label className="text-xs font-medium">Severity</label>
                            <Select value={severityFilter} onValueChange={setSeverityFilter}>
                                <SelectTrigger className="w-full">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Severities</SelectItem>
                                    <SelectItem value="low">Low</SelectItem>
                                    <SelectItem value="medium">Medium</SelectItem>
                                    <SelectItem value="high">High</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Status Filter */}
                        <div className="space-y-2">
                            <label className="text-xs font-medium">Status</label>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-full">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Statuses</SelectItem>
                                    <SelectItem value="pending">Pending</SelectItem>
                                    <SelectItem value="reviewing">Reviewing</SelectItem>
                                    <SelectItem value="resolved">Resolved</SelectItem>
                                    <SelectItem value="escalated">Escalated</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="container mx-auto p-6 space-y-6">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight">Moderation Queue</h2>
                            <p className="text-muted-foreground">
                                Review and manage flagged content
                            </p>
                        </div>
                        <Button
                            variant="outline"
                            onClick={() => invalidateQueue()}
                            disabled={isLoading}
                        >
                            Refresh Queue
                        </Button>
                    </div>

                    {/* Metrics - Mobile View */}
                    <div className="md:hidden">
                        <ModerationMetrics />
                    </div>

                    {/* Mobile Filters */}
                    <div className="md:hidden">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Filter className="h-5 w-5" />
                                    Filters
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Content Type Filter */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Content Type</label>
                                    <Select value={contentTypeFilter} onValueChange={setContentTypeFilter}>
                                        <SelectTrigger className="w-full">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Types</SelectItem>
                                            <SelectItem value="story">Stories</SelectItem>
                                            <SelectItem value="chapter">Chapters</SelectItem>
                                            <SelectItem value="whisper">Whispers</SelectItem>
                                            <SelectItem value="user">Users</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Severity Filter */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Severity</label>
                                    <Select value={severityFilter} onValueChange={setSeverityFilter}>
                                        <SelectTrigger className="w-full">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Severities</SelectItem>
                                            <SelectItem value="low">Low</SelectItem>
                                            <SelectItem value="medium">Medium</SelectItem>
                                            <SelectItem value="high">High</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Status Filter */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Status</label>
                                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                                        <SelectTrigger className="w-full">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Statuses</SelectItem>
                                            <SelectItem value="pending">Pending</SelectItem>
                                            <SelectItem value="reviewing">Reviewing</SelectItem>
                                            <SelectItem value="resolved">Resolved</SelectItem>
                                            <SelectItem value="escalated">Escalated</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Queue Content */}
                    {isLoading && allItems.length === 0 ? (
                        <Card>
                            <CardContent className="flex flex-col items-center justify-center py-12">
                                <Loader2 className="h-12 w-12 text-muted-foreground mb-4 animate-spin" />
                                <p className="text-lg font-medium">Loading moderation queue...</p>
                            </CardContent>
                        </Card>
                    ) : isError ? (
                        <Card>
                            <CardContent className="flex flex-col items-center justify-center py-12">
                                <AlertCircle className="h-12 w-12 text-destructive mb-4" />
                                <p className="text-lg font-medium mb-2">Failed to load queue</p>
                                <p className="text-sm text-muted-foreground text-center max-w-md mb-4">
                                    {(error as any)?.error?.message || "An error occurred while loading the moderation queue."}
                                </p>
                                <Button onClick={() => invalidateQueue()}>
                                    Try Again
                                </Button>
                            </CardContent>
                        </Card>
                    ) : allItems.length === 0 ? (
                        <Card>
                            <CardContent className="flex flex-col items-center justify-center py-12">
                                <Shield className="h-12 w-12 text-muted-foreground mb-4" />
                                <p className="text-lg font-medium mb-2">No items in queue</p>
                                <p className="text-sm text-muted-foreground text-center max-w-md">
                                    There are no flagged items matching your current filters.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="space-y-4">
                            {/* Queue Items */}
                            {allItems.map((item) => (
                                <ModerationQueueItem
                                    key={item.id}
                                    item={item}
                                    onReview={handleReview}
                                />
                            ))}

                            {/* Infinite Scroll Sentinel */}
                            <div ref={sentinelRef} className="h-4" />

                            {/* Loading More Indicator */}
                            {isFetchingNextPage && (
                                <Card>
                                    <CardContent className="flex items-center justify-center py-6">
                                        <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
                                        <span className="text-sm text-muted-foreground">
                                            Loading more items...
                                        </span>
                                    </CardContent>
                                </Card>
                            )}

                            {/* End of Queue Indicator */}
                            {!hasNextPage && allItems.length > 0 && (
                                <Card>
                                    <CardContent className="flex items-center justify-center py-6">
                                        <p className="text-sm text-muted-foreground">
                                            You've reached the end of the queue
                                        </p>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
