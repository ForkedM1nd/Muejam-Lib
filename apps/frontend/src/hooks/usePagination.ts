/**
 * usePagination Hook
 * 
 * Custom hook for cursor-based pagination with infinite scroll support.
 * Works with TanStack Query's useInfiniteQuery for efficient data fetching.
 * 
 * @example
 * ```tsx
 * const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = usePagination({
 *   queryKey: ['stories', { tag: 'fantasy' }],
 *   queryFn: ({ pageParam }) => api.getStories({ tag: 'fantasy', cursor: pageParam }),
 * });
 * 
 * // Flatten results
 * const stories = data?.pages.flatMap(page => page.results) ?? [];
 * ```
 */

import { useInfiniteQuery, type UseInfiniteQueryOptions } from '@tanstack/react-query';
import type { CursorPage } from '@/types';

interface UsePaginationOptions<T> extends Omit<UseInfiniteQueryOptions<CursorPage<T>>, 'getNextPageParam' | 'initialPageParam'> {
    queryKey: unknown[];
    queryFn: (context: { pageParam?: string }) => Promise<CursorPage<T>>;
    enabled?: boolean;
    staleTime?: number;
}

export function usePagination<T>({
    queryKey,
    queryFn,
    enabled = true,
    staleTime = 30_000, // 30 seconds default
    ...options
}: UsePaginationOptions<T>) {
    return useInfiniteQuery({
        queryKey,
        queryFn: ({ pageParam }) => queryFn({ pageParam }),
        getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
        initialPageParam: undefined as string | undefined,
        enabled,
        staleTime,
        ...options,
    });
}

/**
 * useInfiniteScroll Hook
 * 
 * Automatically triggers fetchNextPage when user scrolls near the bottom.
 * 
 * @example
 * ```tsx
 * const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = usePagination({...});
 * const { ref } = useInfiniteScroll({ fetchNextPage, hasNextPage, isFetchingNextPage });
 * 
 * return (
 *   <div>
 *     {stories.map(story => <StoryCard key={story.id} story={story} />)}
 *     <div ref={ref} />
 *   </div>
 * );
 * ```
 */

import { useEffect, useRef } from 'react';

interface UseInfiniteScrollOptions {
    fetchNextPage: () => void;
    hasNextPage?: boolean;
    isFetchingNextPage: boolean;
    threshold?: number; // Distance from bottom in pixels
}

export function useInfiniteScroll({
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    threshold = 500,
}: UseInfiniteScrollOptions) {
    const observerRef = useRef<IntersectionObserver | null>(null);
    const elementRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (!hasNextPage || isFetchingNextPage) return;

        // Create intersection observer
        observerRef.current = new IntersectionObserver(
            (entries) => {
                const [entry] = entries;
                if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
                    fetchNextPage();
                }
            },
            {
                rootMargin: `${threshold}px`,
            }
        );

        // Observe the element
        const currentElement = elementRef.current;
        if (currentElement) {
            observerRef.current.observe(currentElement);
        }

        // Cleanup
        return () => {
            if (observerRef.current && currentElement) {
                observerRef.current.unobserve(currentElement);
            }
        };
    }, [fetchNextPage, hasNextPage, isFetchingNextPage, threshold]);

    return { ref: elementRef };
}

/**
 * Flatten paginated results into a single array
 * 
 * @example
 * ```tsx
 * const { data } = usePagination({...});
 * const stories = flattenPages(data);
 * ```
 */
export function flattenPages<T>(data: { pages: CursorPage<T>[] } | undefined): T[] {
    return data?.pages.flatMap((page) => page.results) ?? [];
}

/**
 * Get total count from paginated data
 */
export function getTotalCount<T>(data: { pages: CursorPage<T>[] } | undefined): number {
    return data?.pages.reduce((total, page) => total + page.results.length, 0) ?? 0;
}
