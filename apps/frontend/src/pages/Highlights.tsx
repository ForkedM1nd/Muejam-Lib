import { useState } from "react";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { Button } from "@/components/ui/button";
import { PageSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Highlighter, Trash2, Calendar, BookOpen, Filter, MessageCircle, Download } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import WhisperComposer from "@/components/shared/WhisperComposer";
import type { Highlight } from "@/types";

interface HighlightWithMeta extends Highlight {
    chapter_title: string;
    story_title: string;
    story_id: string;
}

export default function HighlightsPage() {
    const { isSignedIn } = useSafeAuth();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const [storyFilter, setStoryFilter] = useState<string>("");
    const [dateFilter, setDateFilter] = useState<"all" | "week" | "month" | "year">("all");
    const [showFilters, setShowFilters] = useState(false);
    const [whisperModalOpen, setWhisperModalOpen] = useState(false);
    const [selectedHighlight, setSelectedHighlight] = useState<HighlightWithMeta | null>(null);
    const [exportFormat, setExportFormat] = useState<"markdown" | "text">("markdown");

    // Calculate date range based on filter
    const getDateRange = () => {
        if (dateFilter === "all") return {};

        const now = new Date();
        const startDate = new Date();

        switch (dateFilter) {
            case "week":
                startDate.setDate(now.getDate() - 7);
                break;
            case "month":
                startDate.setMonth(now.getMonth() - 1);
                break;
            case "year":
                startDate.setFullYear(now.getFullYear() - 1);
                break;
        }

        return {
            start_date: startDate.toISOString().split('T')[0],
            end_date: now.toISOString().split('T')[0],
        };
    };

    // Fetch highlights with filters
    const {
        data,
        isLoading,
        isError,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
    } = useInfiniteQuery({
        queryKey: ["highlights", storyFilter, dateFilter],
        queryFn: async ({ pageParam }) => {
            const params = {
                ...(storyFilter && { story_id: storyFilter }),
                ...getDateRange(),
                cursor: pageParam,
                page_size: 20,
            };
            return api.getHighlights(params);
        },
        getNextPageParam: (lastPage) => lastPage.next_cursor,
        initialPageParam: undefined as string | undefined,
        enabled: !!isSignedIn,
    });

    const highlights = data?.pages.flatMap((page) => page.results) ?? [];

    // Delete highlight mutation
    const deleteMutation = useMutation({
        mutationFn: (highlightId: string) => api.deleteHighlight(highlightId),
        onSuccess: () => {
            toast({ title: "Highlight deleted" });
            queryClient.invalidateQueries({ queryKey: ["highlights"] });
        },
        onError: () => {
            toast({ title: "Failed to delete highlight", variant: "destructive" });
        },
    });

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

    // Navigate to chapter with highlight
    const handleHighlightClick = (highlight: HighlightWithMeta) => {
        navigate(`/read/${highlight.chapter_id}#highlight-${highlight.id}`);
    };

    // Open whisper modal for a highlight
    const handleCreateWhisper = (highlight: HighlightWithMeta) => {
        setSelectedHighlight(highlight);
        setWhisperModalOpen(true);
    };

    // Export highlights as markdown
    const exportAsMarkdown = () => {
        if (highlights.length === 0) return;

        let markdown = "# My Highlights\n\n";
        markdown += `Exported on ${new Date().toLocaleDateString()}\n\n`;
        markdown += `Total highlights: ${highlights.length}\n\n`;
        markdown += "---\n\n";

        Object.entries(highlightsByStory).forEach(([, { story_title, highlights: storyHighlights }]) => {
            markdown += `## ${story_title}\n\n`;
            markdown += `${storyHighlights.length} highlight${storyHighlights.length !== 1 ? "s" : ""}\n\n`;

            storyHighlights.forEach((highlight) => {
                markdown += `### ${highlight.chapter_title}\n\n`;
                markdown += `> ${highlight.quote_text}\n\n`;
                markdown += `*Highlighted on ${new Date(highlight.created_at).toLocaleDateString()}*\n\n`;
                markdown += "---\n\n";
            });
        });

        downloadFile(markdown, "highlights.md", "text/markdown");
    };

    // Export highlights as plain text
    const exportAsText = () => {
        if (highlights.length === 0) return;

        let text = "MY HIGHLIGHTS\n\n";
        text += `Exported on ${new Date().toLocaleDateString()}\n`;
        text += `Total highlights: ${highlights.length}\n\n`;
        text += "=".repeat(50) + "\n\n";

        Object.entries(highlightsByStory).forEach(([, { story_title, highlights: storyHighlights }]) => {
            text += `${story_title.toUpperCase()}\n`;
            text += `${storyHighlights.length} highlight${storyHighlights.length !== 1 ? "s" : ""}\n\n`;

            storyHighlights.forEach((highlight, index) => {
                text += `${index + 1}. ${highlight.chapter_title}\n\n`;
                text += `"${highlight.quote_text}"\n\n`;
                text += `Highlighted on ${new Date(highlight.created_at).toLocaleDateString()}\n\n`;
                text += "-".repeat(50) + "\n\n";
            });
        });

        downloadFile(text, "highlights.txt", "text/plain");
    };

    // Helper function to download file
    const downloadFile = (content: string, filename: string, mimeType: string) => {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        toast({ title: `Highlights exported as ${filename}` });
    };

    // Handle export based on selected format
    const handleExport = () => {
        if (exportFormat === "markdown") {
            exportAsMarkdown();
        } else {
            exportAsText();
        }
    };

    // Group highlights by story
    const highlightsByStory = highlights.reduce((acc, highlight) => {
        const storyId = highlight.story_id;
        if (!acc[storyId]) {
            acc[storyId] = {
                story_title: highlight.story_title,
                highlights: [],
            };
        }
        acc[storyId].highlights.push(highlight);
        return acc;
    }, {} as Record<string, { story_title: string; highlights: HighlightWithMeta[] }>);

    // Get unique stories for filter
    const uniqueStories = Array.from(
        new Set(highlights.map((h) => JSON.stringify({ id: h.story_id, title: h.story_title })))
    ).map((s) => JSON.parse(s) as { id: string; title: string });

    if (!isSignedIn) {
        return (
            <div className="container max-w-4xl mx-auto px-4 py-12">
                <EmptyState
                    title="Sign in to view highlights"
                    description="Create an account to save and manage your story highlights"
                />
            </div>
        );
    }

    if (isLoading) return <PageSkeleton />;

    if (isError) {
        return (
            <div className="container max-w-4xl mx-auto px-4 py-12">
                <EmptyState
                    title="Failed to load highlights"
                    description="There was an error loading your highlights. Please try again."
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
                            <Highlighter className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold" style={{ fontFamily: "var(--font-display)" }}>
                                My Highlights
                            </h1>
                            <p className="text-muted-foreground">
                                {highlights.length} highlight{highlights.length !== 1 ? "s" : ""} saved
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {highlights.length > 0 && (
                            <div className="flex items-center gap-2">
                                <select
                                    className="px-3 py-2 bg-background border border-border rounded-md text-sm"
                                    value={exportFormat}
                                    onChange={(e) => setExportFormat(e.target.value as "markdown" | "text")}
                                >
                                    <option value="markdown">Markdown</option>
                                    <option value="text">Text</option>
                                </select>
                                <Button
                                    variant="default"
                                    size="sm"
                                    onClick={handleExport}
                                >
                                    <Download className="h-4 w-4 mr-2" />
                                    Export
                                </Button>
                            </div>
                        )}
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowFilters(!showFilters)}
                        >
                            <Filter className="h-4 w-4 mr-2" />
                            Filters
                        </Button>
                    </div>
                </div>

                {/* Filters */}
                {showFilters && (
                    <div className="bg-muted/50 border border-border rounded-lg p-4 space-y-4">
                        {/* Story filter */}
                        {uniqueStories.length > 1 && (
                            <div>
                                <label className="text-sm font-medium mb-2 block">Filter by Story</label>
                                <select
                                    className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm"
                                    value={storyFilter}
                                    onChange={(e) => setStoryFilter(e.target.value)}
                                >
                                    <option value="">All Stories</option>
                                    {uniqueStories.map((story) => (
                                        <option key={story.id} value={story.id}>
                                            {story.title}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* Date filter */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">Filter by Date</label>
                            <div className="flex gap-2">
                                {(["all", "week", "month", "year"] as const).map((filter) => (
                                    <Button
                                        key={filter}
                                        variant={dateFilter === filter ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => setDateFilter(filter)}
                                    >
                                        {filter === "all" ? "All Time" : `Past ${filter.charAt(0).toUpperCase() + filter.slice(1)}`}
                                    </Button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Highlights list */}
            {highlights.length === 0 ? (
                <EmptyState
                    title="No highlights yet"
                    description="Start reading and highlight passages that resonate with you"
                    action={
                        <Button onClick={() => navigate("/discover")}>
                            <BookOpen className="h-4 w-4 mr-2" />
                            Discover Stories
                        </Button>
                    }
                />
            ) : (
                <div className="space-y-8">
                    {Object.entries(highlightsByStory).map(([storyId, { story_title, highlights: storyHighlights }]) => (
                        <div key={storyId} className="space-y-4">
                            {/* Story header */}
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                                    {story_title}
                                </h2>
                                <span className="text-sm text-muted-foreground">
                                    {storyHighlights.length} highlight{storyHighlights.length !== 1 ? "s" : ""}
                                </span>
                            </div>

                            {/* Highlights for this story */}
                            <div className="space-y-3">
                                {storyHighlights.map((highlight, index) => {
                                    const isLast = index === storyHighlights.length - 1;
                                    return (
                                        <div
                                            key={highlight.id}
                                            className={cn(
                                                "group relative p-4 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors"
                                            )}
                                        >
                                            {/* Highlight content */}
                                            <div
                                                className="cursor-pointer"
                                                onClick={() => handleHighlightClick(highlight)}
                                            >
                                                <p className="text-sm italic mb-3 leading-relaxed">
                                                    "{highlight.quote_text}"
                                                </p>
                                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                    <span className="flex items-center gap-1">
                                                        <BookOpen className="h-3 w-3" />
                                                        {highlight.chapter_title}
                                                    </span>
                                                    <span className="flex items-center gap-1">
                                                        <Calendar className="h-3 w-3" />
                                                        {new Date(highlight.created_at).toLocaleDateString()}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Action buttons */}
                                            <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleCreateWhisper(highlight);
                                                    }}
                                                    title="Create whisper from highlight"
                                                >
                                                    <MessageCircle className="h-4 w-4 text-primary" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (confirm("Delete this highlight?")) {
                                                            deleteMutation.mutate(highlight.id);
                                                        }
                                                    }}
                                                    title="Delete highlight"
                                                >
                                                    <Trash2 className="h-4 w-4 text-destructive" />
                                                </Button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}

                    {/* Infinite scroll sentinel */}
                    <div ref={sentinelRef} className="h-4" />

                    {/* Loading more indicator */}
                    {isFetchingNextPage && (
                        <div className="text-center py-4">
                            <p className="text-sm text-muted-foreground">Loading more highlights...</p>
                        </div>
                    )}
                </div>
            )}

            {/* Whisper from highlight modal */}
            {whisperModalOpen && selectedHighlight && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setWhisperModalOpen(false)}>
                    <div className="bg-popover border border-border rounded-lg shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
                        <h3 className="text-lg font-medium mb-4" style={{ fontFamily: "var(--font-display)" }}>
                            Whisper about this highlight
                        </h3>
                        <WhisperComposer
                            quoteText={selectedHighlight.quote_text}
                            highlightId={selectedHighlight.id}
                            scope="HIGHLIGHT"
                            placeholder="Share your thoughts on this passage…"
                            onSubmit={async (content, mediaFile, scope, storyId, highlightId) => {
                                await api.createWhisper({
                                    content,
                                    scope: scope || "HIGHLIGHT",
                                    highlight_id: highlightId,
                                });
                                setWhisperModalOpen(false);
                                setSelectedHighlight(null);
                                toast({ title: "Whisper posted!" });
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
