import { useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { services } from "@/lib/api";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Flag, Calendar, Filter, AlertCircle, CheckCircle, Clock, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import type { Report, ReportStatus, ReportableContentType } from "@/types";

const STATUS_CONFIG: Record<
    ReportStatus,
    { label: string; icon: typeof Clock; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
    pending: { label: "Pending", icon: Clock, variant: "secondary" },
    under_review: { label: "Under Review", icon: AlertCircle, variant: "default" },
    resolved: { label: "Resolved", icon: CheckCircle, variant: "outline" },
    dismissed: { label: "Dismissed", icon: XCircle, variant: "destructive" },
};

const CONTENT_TYPE_LABELS: Record<ReportableContentType, string> = {
    story: "Story",
    whisper: "Whisper",
    user: "User",
    comment: "Comment",
};

export default function MyReportsPage() {
    const { isSignedIn } = useSafeAuth();
    const navigate = useNavigate();

    const [statusFilter, setStatusFilter] = useState<ReportStatus | "all">("all");
    const [contentTypeFilter, setContentTypeFilter] = useState<ReportableContentType | "all">("all");
    const [showFilters, setShowFilters] = useState(false);

    // Fetch reports with filters
    const {
        data,
        isLoading,
        isError,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
    } = useInfiniteQuery({
        queryKey: ["my-reports", statusFilter, contentTypeFilter],
        queryFn: async ({ pageParam }) => {
            const params: any = {
                cursor: pageParam,
                limit: 20,
            };
            if (statusFilter !== "all") params.status = statusFilter;
            if (contentTypeFilter !== "all") params.content_type = contentTypeFilter;
            return services.reports.getMyReports(params);
        },
        getNextPageParam: (lastPage) => lastPage.next_cursor,
        initialPageParam: undefined as string | undefined,
        enabled: !!isSignedIn,
    });

    const reports = data?.pages.flatMap((page) => page.results) ?? [];

    // Infinite scroll
    const sentinelRef = useInfiniteScroll({
        onLoadMore: () => {
            if (hasNextPage && !isFetchingNextPage) {
                fetchNextPage();
            }
        },
        hasMore: hasNextPage ?? false,
        isLoading: isFetchingNextPage,
    });

    // Format reason for display
    const formatReason = (reason: string) => {
        return reason
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    };

    if (!isSignedIn) {
        return (
            <div className="container max-w-4xl mx-auto px-4 py-12">
                <EmptyState
                    title="Sign in to view reports"
                    description="Create an account to report content and track your submissions"
                />
            </div>
        );
    }

    if (isLoading) return <PageSkeleton />;

    if (isError) {
        return (
            <div className="container max-w-4xl mx-auto px-4 py-12">
                <EmptyState
                    title="Failed to load reports"
                    description="There was an error loading your reports. Please try again."
                />
            </div>
        );
    }

    return (
        <div className="container max-w-4xl mx-auto px-4 py-12">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <Flag className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold" style={{ fontFamily: "var(--font-display)" }}>
                                My Reports
                            </h1>
                            <p className="text-muted-foreground">
                                {reports.length} report{reports.length !== 1 ? "s" : ""} submitted
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowFilters(!showFilters)}
                    >
                        <Filter className="h-4 w-4 mr-2" />
                        Filters
                    </Button>
                </div>

                {/* Filters */}
                {showFilters && (
                    <div className="bg-muted/50 border border-border rounded-lg p-4 space-y-4">
                        {/* Status filter */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">Filter by Status</label>
                            <div className="flex flex-wrap gap-2">
                                <Button
                                    variant={statusFilter === "all" ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setStatusFilter("all")}
                                >
                                    All
                                </Button>
                                {(Object.keys(STATUS_CONFIG) as ReportStatus[]).map((status) => (
                                    <Button
                                        key={status}
                                        variant={statusFilter === status ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => setStatusFilter(status)}
                                    >
                                        {STATUS_CONFIG[status].label}
                                    </Button>
                                ))}
                            </div>
                        </div>

                        {/* Content type filter */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">Filter by Content Type</label>
                            <div className="flex flex-wrap gap-2">
                                <Button
                                    variant={contentTypeFilter === "all" ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setContentTypeFilter("all")}
                                >
                                    All
                                </Button>
                                {(Object.keys(CONTENT_TYPE_LABELS) as ReportableContentType[]).map((type) => (
                                    <Button
                                        key={type}
                                        variant={contentTypeFilter === type ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => setContentTypeFilter(type)}
                                    >
                                        {CONTENT_TYPE_LABELS[type]}
                                    </Button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Reports list */}
            {reports.length === 0 ? (
                <EmptyState
                    title="No reports submitted"
                    description="When you report content that violates community guidelines, it will appear here"
                />
            ) : (
                <div className="space-y-4">
                    {reports.map((report) => {
                        const statusConfig = STATUS_CONFIG[report.status];
                        const StatusIcon = statusConfig.icon;

                        return (
                            <div
                                key={report.id}
                                className="p-4 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors"
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline">
                                            {CONTENT_TYPE_LABELS[report.content_type]}
                                        </Badge>
                                        <Badge variant={statusConfig.variant}>
                                            <StatusIcon className="h-3 w-3 mr-1" />
                                            {statusConfig.label}
                                        </Badge>
                                    </div>
                                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                                        <Calendar className="h-3 w-3" />
                                        {new Date(report.created_at).toLocaleDateString()}
                                    </span>
                                </div>

                                {/* Reason */}
                                <div className="mb-2">
                                    <span className="text-sm font-medium">Reason: </span>
                                    <span className="text-sm text-muted-foreground">
                                        {formatReason(report.reason)}
                                    </span>
                                </div>

                                {/* Additional context */}
                                {report.additional_context && (
                                    <div className="mb-3">
                                        <p className="text-sm text-muted-foreground italic">
                                            "{report.additional_context}"
                                        </p>
                                    </div>
                                )}

                                {/* Resolution info */}
                                {report.status === "resolved" && report.resolved_at && (
                                    <div className="mt-3 pt-3 border-t border-border">
                                        <div className="flex items-start gap-2">
                                            <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-green-600">
                                                    Resolved on {new Date(report.resolved_at).toLocaleDateString()}
                                                </p>
                                                {report.resolution_note && (
                                                    <p className="text-sm text-muted-foreground mt-1">
                                                        {report.resolution_note}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Dismissal info */}
                                {report.status === "dismissed" && report.resolved_at && (
                                    <div className="mt-3 pt-3 border-t border-border">
                                        <div className="flex items-start gap-2">
                                            <XCircle className="h-4 w-4 text-muted-foreground mt-0.5" />
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-muted-foreground">
                                                    Dismissed on {new Date(report.resolved_at).toLocaleDateString()}
                                                </p>
                                                {report.resolution_note && (
                                                    <p className="text-sm text-muted-foreground mt-1">
                                                        {report.resolution_note}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {/* Infinite scroll sentinel */}
                    <div ref={sentinelRef} className="h-4" />

                    {/* Loading more indicator */}
                    {isFetchingNextPage && (
                        <div className="text-center py-4">
                            <p className="text-sm text-muted-foreground">Loading more reports...</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
