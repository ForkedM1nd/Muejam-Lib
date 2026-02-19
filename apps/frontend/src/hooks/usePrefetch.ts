import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

/**
 * Hook for prefetching data for likely next navigation
 * Uses TanStack Query's prefetchQuery to load data in the background
 */
export function usePrefetch() {
    const queryClient = useQueryClient();

    /**
     * Prefetch data for a query
     * @param queryKey - The query key to prefetch
     * @param queryFn - The function to fetch the data
     * @param staleTime - How long the data should be considered fresh (default: 5 minutes)
     */
    const prefetch = useCallback(
        async <T>(
            queryKey: unknown[],
            queryFn: () => Promise<T>,
            staleTime: number = 5 * 60 * 1000
        ) => {
            await queryClient.prefetchQuery({
                queryKey,
                queryFn,
                staleTime,
            });
        },
        [queryClient]
    );

    /**
     * Prefetch data on hover (for links)
     * Returns event handlers to attach to elements
     */
    const prefetchOnHover = useCallback(
        <T>(queryKey: unknown[], queryFn: () => Promise<T>) => {
            let timeoutId: NodeJS.Timeout;

            return {
                onMouseEnter: () => {
                    // Delay prefetch slightly to avoid prefetching on accidental hovers
                    timeoutId = setTimeout(() => {
                        prefetch(queryKey, queryFn);
                    }, 100);
                },
                onMouseLeave: () => {
                    clearTimeout(timeoutId);
                },
            };
        },
        [prefetch]
    );

    /**
     * Prefetch data on focus (for keyboard navigation)
     * Returns event handlers to attach to elements
     */
    const prefetchOnFocus = useCallback(
        <T>(queryKey: unknown[], queryFn: () => Promise<T>) => {
            return {
                onFocus: () => {
                    prefetch(queryKey, queryFn);
                },
            };
        },
        [prefetch]
    );

    return {
        prefetch,
        prefetchOnHover,
        prefetchOnFocus,
    };
}
