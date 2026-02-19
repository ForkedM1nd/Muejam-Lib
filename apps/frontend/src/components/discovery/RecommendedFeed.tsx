import { usePagination, useInfiniteScroll, flattenPages } from "@/hooks/usePagination";
import { services } from "@/lib/api";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import type { DiscoveryParams, Story } from "@/types";
import StoryCard from "@/components/shared/StoryCard";
import { StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";

interface RecommendedFeedProps {
    filters?: Omit<DiscoveryParams, "cursor" | "page_size">;
}

export function RecommendedFeed({ filters = {} }: RecommendedFeedProps) {
    const { isSignedIn } = useSafeAuth();

    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading,
        isError,
        refetch,
    } = usePagination<Story>({
        queryKey: ["discover", "recommended", filters],
        queryFn: ({ pageParam }) =>
            services.discovery.getRecommended({
                ...filters,
                cursor: pageParam,
                page_size: 20,
            }),
        staleTime: 5 * 60 * 1000, // 5 minutes for personalized content
        enabled: isSignedIn, // Only fetch if user is signed in
    });

    const { ref } = useInfiniteScroll({
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        threshold: 500,
    });

    // Show sign-in prompt if not authenticated
    if (!isSignedIn) {
        return (
            <div className="animate-in fade-in duration-300">
                <EmptyState
                    title="Personalized recommendations"
                    description="Sign in to get story recommendations based on your reading history and preferences."
                />
            </div>
        );
    }

    const stories = flattenPages<Story>(data);

    // Filter out stories from blocked authors
    const filteredStories = stories.filter((story) => !story.author.is_blocked);

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-in fade-in duration-300">
                {Array.from({ length: 6 }).map((_, i) => (
                    <StoryCardSkeleton key={i} />
                ))}
            </div>
        );
    }

    if (isError) {
        return (
            <div className="animate-in fade-in duration-300">
                <EmptyState
                    title="Something went wrong"
                    description="Could not load recommended stories."
                    action={
                        <Button variant="outline" onClick={() => refetch()}>
                            Retry
                        </Button>
                    }
                />
            </div>
        );
    }

    if (filteredStories.length === 0) {
        return (
            <div className="animate-in fade-in duration-300">
                <EmptyState
                    title="No recommendations yet"
                    description="Start reading stories to get personalized recommendations."
                />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in duration-300">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredStories.map((story) => (
                    <StoryCard key={story.id} story={story} />
                ))}
            </div>

            {/* Infinite scroll sentinel */}
            <div ref={ref} className="h-10 flex items-center justify-center">
                {isFetchingNextPage && (
                    <div className="text-sm text-muted-foreground">Loading more...</div>
                )}
            </div>

            {!hasNextPage && filteredStories.length > 0 && (
                <div className="text-center text-sm text-muted-foreground py-4">
                    You've reached the end
                </div>
            )}
        </div>
    );
}
