import { ReactNode } from 'react';
import { useVirtualScroll } from '@/hooks/useVirtualScroll';
import { cn } from '@/lib/utils';

interface VirtualListProps<T> {
    items: T[];
    itemHeight: number;
    containerHeight: number;
    renderItem: (item: T, index: number) => ReactNode;
    className?: string;
    overscan?: number;
}

/**
 * Virtual scrolling list component for rendering large lists efficiently
 * Only renders visible items plus overscan buffer
 */
export function VirtualList<T>({
    items,
    itemHeight,
    containerHeight,
    renderItem,
    className,
    overscan = 3,
}: VirtualListProps<T>) {
    const { virtualItems, totalHeight, containerRef } = useVirtualScroll(items, {
        itemHeight,
        containerHeight,
        overscan,
    });

    return (
        <div
            ref={containerRef}
            className={cn('overflow-auto', className)}
            style={{ height: containerHeight }}
        >
            <div style={{ height: totalHeight, position: 'relative' }}>
                {virtualItems.map(({ index, start }) => (
                    <div
                        key={index}
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: itemHeight,
                            transform: `translateY(${start}px)`,
                        }}
                    >
                        {renderItem(items[index], index)}
                    </div>
                ))}
            </div>
        </div>
    );
}
