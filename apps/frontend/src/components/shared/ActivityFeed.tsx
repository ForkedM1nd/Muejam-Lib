// ── Activity Feed Component ──
// Displays followed users' actions with infinite scroll and real-time updates

import { useEffect, useRef, useState } from "react";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ActivityFeedItem, ApiError } from "@/types";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDistanceToNow } from "date-fns";
import { BookOpen, MessageCircle, UserPlus, FileText } from "lucide-react";
import { Link } from "react-router-dom";

export function ActivityFeed() {
    const queryClient = useQueryClient();
    const observerTarget = useRef<HTMLDivElement>(null);
    const [isVisible, setIsVisible] = useState(false);

    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading,
        isError,
        error,
        refetch,
    } = useInfiniteQuery({
        queryKey: ["activity-feed"],
        queryFn: ({ pageParam }) =>
            api.getActivityFeed({ cursor: pageParam, page_size: 20 }),
        getNextPageParam: (lastPage) => lastPage.next_cursor,
        initialPageParam: undefined as string | undefined,
        staleTime: 30 * 1000, // 30 seconds
    });

    // Infinite scroll observer
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    setIsVisible(true);
                }
            },
            { threshold: 0.1 }
        );

        const currentTarget = observerTarget.current;
        if (currentTarget) {
            observer.observe(currentTarget);
        }

        return () => {
            if (currentTarget) {
                observer.unobserve(currentTarget);
            }
        };
    }, []);

    // Fetch next page when observer target is visible
    useEffect(() => {
        if (isVisible && hasNextPage && !isFetchingNextPage) {
            fetchNextPage();
            setIsVisible(false);
        }
    }, [isVisible, hasNextPage, isFetchingNextPage, fetchNextPage]);

    // Real-time updates via WebSocket (placeholder for future implementation)
    useEffect(() => {
        const handleNewActivity = () => {
            // Invalidate query to refetch with new activity
            queryClient.invalidateQueries({ queryKey: ["activity-feed"] });
        };

        window.addEventListener("activity:new", handleNewActivity as EventListener);

        return () => {
            window.removeEventListener("activity:new", handleNewActivity as EventListener);
        };
    }, [queryClient]);

    if (isLoading) {
        return (
            <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                    <Card key={i}>
                        <CardContent className="p-4">
                            <div className="flex items-start gap-3">
                                <Skeleton className="h-10 w-10 rounded-full" />
                                <div className="flex-1 space-y-2">
                                    <Skeleton className="h-4 w-3/4" />
                                    <Skeleton className="h-3 w-1/2" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    if (isError) {
        return (
            <Card>
                <CardContent className="p-6 text-center">
                    <p className="text-sm text-muted-foreground">
                        Failed to load activity feed. Please try again later.
                    </p>
                    {error && (
                        <p className="text-xs text-muted-foreground mt-2">
                            {(error as ApiError).error?.message || "Unknown error"}
                        </p>
                    )}
                    <Button variant="outline" size="sm" className="mt-4" onClick={() => refetch()}>
                        Try again
                    </Button>
                </CardContent>
            </Card>
        );
    }

    const activities = data?.pages.flatMap((page) => page.results) || [];

    // Filter out activities from blocked users
    const filteredActivities = activities.filter(
        (activity) => !activity.actor.is_blocked
    );

    if (filteredActivities.length === 0) {
        return (
            <Card>
                <CardContent className="p-6 text-center">
                    <p className="text-sm text-muted-foreground">
                        No activity yet. Follow some users to see their updates here!
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            {filteredActivities.map((activity) => (
                <ActivityFeedItemCard key={activity.id} activity={activity} />
            ))}

            {/* Infinite scroll trigger */}
            <div ref={observerTarget} className="h-4" />

            {isFetchingNextPage && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                            <Skeleton className="h-10 w-10 rounded-full" />
                            <div className="flex-1 space-y-2">
                                <Skeleton className="h-4 w-3/4" />
                                <Skeleton className="h-3 w-1/2" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {!hasNextPage && filteredActivities.length > 0 && (
                <p className="text-center text-sm text-muted-foreground py-4">
                    You've reached the end of the activity feed
                </p>
            )}
        </div>
    );
}

function ActivityFeedItemCard({ activity }: { activity: ActivityFeedItem }) {
    const icon = getActivityIcon(activity.type);
    const message = getActivityMessage(activity);
    const link = getActivityLink(activity);

    return (
        <Card className="hover:bg-accent/50 transition-colors">
            <CardContent className="p-4">
                <div className="flex items-start gap-3">
                    <Link to={`/u/${activity.actor.handle}`}>
                        <Avatar className="h-10 w-10">
                            <AvatarImage src={activity.actor.avatar_url} />
                            <AvatarFallback>
                                {activity.actor.display_name.charAt(0).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                    </Link>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-2">
                            <div className="flex-shrink-0 mt-1">{icon}</div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm">
                                    <Link
                                        to={`/u/${activity.actor.handle}`}
                                        className="font-medium hover:underline"
                                    >
                                        {activity.actor.display_name}
                                    </Link>{" "}
                                    {message}
                                </p>

                                {activity.target && link && (
                                    <Link
                                        to={link}
                                        className="text-sm text-muted-foreground hover:text-foreground hover:underline mt-1 block truncate"
                                    >
                                        {activity.target.title || activity.target.content}
                                    </Link>
                                )}

                                <p className="text-xs text-muted-foreground mt-1">
                                    {formatDistanceToNow(new Date(activity.created_at), {
                                        addSuffix: true,
                                    })}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function getActivityIcon(type: ActivityFeedItem["type"]) {
    switch (type) {
        case "story_published":
            return <BookOpen className="h-4 w-4 text-blue-500" />;
        case "chapter_published":
            return <FileText className="h-4 w-4 text-green-500" />;
        case "whisper_created":
            return <MessageCircle className="h-4 w-4 text-cyan-600" />;
        case "user_followed":
            return <UserPlus className="h-4 w-4 text-orange-500" />;
        default:
            return null;
    }
}

function getActivityMessage(activity: ActivityFeedItem): string {
    switch (activity.type) {
        case "story_published":
            return "published a new story";
        case "chapter_published":
            return "published a new chapter";
        case "whisper_created":
            return "posted a whisper";
        case "user_followed":
            return "followed a user";
        default:
            return "did something";
    }
}

function getActivityLink(activity: ActivityFeedItem): string | null {
    if (!activity.target) return null;

    switch (activity.target.type) {
        case "story":
            return activity.target.slug ? `/story/${activity.target.slug}` : null;
        case "chapter":
            return activity.target.id ? `/read/${activity.target.id}` : null;
        case "whisper":
            return "/whispers"; // Could be more specific if we have whisper detail pages
        case "user":
            return null;
        default:
            return null;
    }
}
