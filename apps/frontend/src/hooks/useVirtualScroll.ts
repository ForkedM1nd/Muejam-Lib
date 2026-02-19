import { useRef, useState, useEffect, useCallback } from 'react';

interface VirtualScrollOptions {
    itemHeight: number;
    containerHeight: number;
    overscan?: number;
}

interface VirtualScrollResult {
    virtualItems: Array<{
        index: number;
        start: number;
        size: number;
    }>;
    totalHeight: number;
    scrollToIndex: (index: number) => void;
    containerRef: React.RefObject<HTMLDivElement>;
}

/**
 * Custom hook for virtual scrolling implementation
 * Renders only visible items plus overscan for better performance with large lists
 */
export function useVirtualScroll<T>(
    items: T[],
    options: VirtualScrollOptions
): VirtualScrollResult {
    const { itemHeight, containerHeight, overscan = 3 } = options;
    const containerRef = useRef<HTMLDivElement>(null);
    const [scrollTop, setScrollTop] = useState(0);

    // Calculate visible range
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
        items.length - 1,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );

    // Generate virtual items
    const virtualItems = [];
    for (let i = startIndex; i <= endIndex; i++) {
        virtualItems.push({
            index: i,
            start: i * itemHeight,
            size: itemHeight,
        });
    }

    const totalHeight = items.length * itemHeight;

    // Handle scroll events
    const handleScroll = useCallback(() => {
        if (containerRef.current) {
            setScrollTop(containerRef.current.scrollTop);
        }
    }, []);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        container.addEventListener('scroll', handleScroll, { passive: true });
        return () => container.removeEventListener('scroll', handleScroll);
    }, [handleScroll]);

    // Scroll to specific index
    const scrollToIndex = useCallback((index: number) => {
        if (containerRef.current) {
            containerRef.current.scrollTop = index * itemHeight;
        }
    }, [itemHeight]);

    return {
        virtualItems,
        totalHeight,
        scrollToIndex,
        containerRef,
    };
}
