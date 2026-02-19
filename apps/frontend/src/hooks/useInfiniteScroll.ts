import { useEffect, useRef, useCallback } from "react";

interface UseInfiniteScrollOptions {
    onLoadMore: () => void;
    hasMore: boolean;
    isLoading: boolean;
    threshold?: number;
}

export function useInfiniteScroll({
    onLoadMore,
    hasMore,
    isLoading,
    threshold = 0.8,
}: UseInfiniteScrollOptions) {
    const observerRef = useRef<IntersectionObserver | null>(null);
    const sentinelRef = useRef<HTMLDivElement | null>(null);

    const handleObserver = useCallback(
        (entries: IntersectionObserverEntry[]) => {
            const [entry] = entries;
            if (entry.isIntersecting && hasMore && !isLoading) {
                onLoadMore();
            }
        },
        [hasMore, isLoading, onLoadMore]
    );

    useEffect(() => {
        const options = {
            root: null,
            rootMargin: "0px",
            threshold,
        };

        observerRef.current = new IntersectionObserver(handleObserver, options);

        const currentSentinel = sentinelRef.current;
        if (currentSentinel) {
            observerRef.current.observe(currentSentinel);
        }

        return () => {
            if (observerRef.current && currentSentinel) {
                observerRef.current.unobserve(currentSentinel);
            }
        };
    }, [handleObserver, threshold]);

    return sentinelRef;
}
