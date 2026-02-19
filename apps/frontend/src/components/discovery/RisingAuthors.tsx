import { usePagination, useInfiniteScroll, flattenPages } from "@/hooks/usePagination";
import { services } from "@/lib/api";
import type { PaginationParams, UserProfile } from "@/types";
import UserCard from "@/components/shared/UserCard";
import { StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";

interface RisingAuthorsProps {
    filters?: Omit<PaginationParams, "cursor" | "page_size">;
}

export function RisingAuthors({ filters = {} }: RisingAuthorsProps) {
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading,
        isError,
        refetch,
    } = usePagination<UserProfile>({
        queryKey: ["discover", "rising-authors", filters],
        queryFn: ({ pageParam }) =>
            services.discovery.getRisingAuthors({
                ...filters,
                cursor: pageParam,
                page_size: 20,
            }),
        staleTime: 10 * 60 * 1000, // 10 minutes
    });

    const { ref } = useInfiniteScroll({
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        threshold: 500,
    });

    const authors = flattenPages<UserProfile>(data);

    // Filter out blocked authors
    const filteredAuthors = authors.filter((author) => !author.is_blocked);

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                description="Could not load rising authors."
                action={
                    <Button variant="outline" onClick={() => refetch()}>
                        Retry
                    </Button>
                }
            />
        );
    }

    if (filteredAuthors.length === 0) {
        return (
            <EmptyState
                title="No rising authors"
                description="Check back soon for up-and-coming writers."
            />
        );
    }

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredAuthors.map((author) => (
                    <UserCard key={author.id} user={author} />
                ))}
            </div>

            {/* Infinite scroll sentinel */}
            <div ref={ref} className="h-10 flex items-center justify-center">
                {isFetchingNextPage && (
                    <div className="text-sm text-muted-foreground">Loading more...</div>
                )}
            </div>

            {!hasNextPage && filteredAuthors.length > 0 && (
                <div className="text-center text-sm text-muted-foreground py-4">
                    You've reached the end
                </div>
            )}
        </div>
    );
}
