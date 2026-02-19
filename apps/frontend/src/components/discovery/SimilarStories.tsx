import { usePagination, useInfiniteScroll, flattenPages } from "@/hooks/usePagination";
import { services } from "@/lib/api";
import type { PaginationParams, Story } from "@/types";
import StoryCard from "@/components/shared/StoryCard";
import { StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";

interface SimilarStoriesProps {
    storyId: string;
    filters?: Omit<PaginationParams, "cursor" | "page_size">;
}

export function SimilarStories({ storyId, filters = {} }: SimilarStoriesProps) {
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading,
        isError,
        refetch,
    } = usePagination<Story>({
        queryKey: ["discover", "similar", storyId, filters],
        queryFn: ({ pageParam }) =>
            services.discovery.getSimilar(storyId, {
                ...filters,
                cursor: pageParam,
                page_size: 20,
            }),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });

    const { ref } = useInfiniteScroll({
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        threshold: 500,
    });

    const stories = flattenPages<Story>(data);

    // Filter out stories from blocked authors
    const filteredStories = stories.filter((story) => !story.author.is_blocked);

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                    <StoryCardSkeleton key={i} />
                ))}
            </div>
        );
    }

    if (isError) {
        return (
            <EmptyState
                title="Something went wrong"
                description="Could not load similar stories."
                action={
                    <Button variant="outline" onClick={() => refetch()}>
                        Retry
                    </Button>
                }
            />
        );
    }

    if (filteredStories.length === 0) {
        return (
            <EmptyState
                title="No similar stories"
                description="We couldn't find any similar stories at this time."
            />
        );
    }

    return (
        <div className="space-y-6">
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
