import { useEffect, useCallback, RefObject } from 'react';

interface KeyboardNavigationOptions {
    onArrowUp?: () => void;
    onArrowDown?: () => void;
    onArrowLeft?: () => void;
    onArrowRight?: () => void;
    onEnter?: () => void;
    onEscape?: () => void;
    onHome?: () => void;
    onEnd?: () => void;
    enabled?: boolean;
}

/**
 * Hook for implementing keyboard navigation
 */
export function useKeyboardNavigation(
    ref: RefObject<HTMLElement>,
    options: KeyboardNavigationOptions
) {
    const {
        onArrowUp,
        onArrowDown,
        onArrowLeft,
        onArrowRight,
        onEnter,
        onEscape,
        onHome,
        onEnd,
        enabled = true,
    } = options;

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            if (!enabled) return;

            switch (event.key) {
                case 'ArrowUp':
                    event.preventDefault();
                    onArrowUp?.();
                    break;
                case 'ArrowDown':
                    event.preventDefault();
                    onArrowDown?.();
                    break;
                case 'ArrowLeft':
                    event.preventDefault();
                    onArrowLeft?.();
                    break;
                case 'ArrowRight':
                    event.preventDefault();
                    onArrowRight?.();
                    break;
                case 'Enter':
                    onEnter?.();
                    break;
                case 'Escape':
                    onEscape?.();
                    break;
                case 'Home':
                    event.preventDefault();
                    onHome?.();
                    break;
                case 'End':
                    event.preventDefault();
                    onEnd?.();
                    break;
            }
        },
        [enabled, onArrowUp, onArrowDown, onArrowLeft, onArrowRight, onEnter, onEscape, onHome, onEnd]
    );

    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        element.addEventListener('keydown', handleKeyDown);

        return () => {
            element.removeEventListener('keydown', handleKeyDown);
        };
    }, [ref, handleKeyDown]);
}

/**
 * Hook for list keyboard navigation
 */
export function useListKeyboardNavigation(
    items: unknown[],
    selectedIndex: number,
    onSelect: (index: number) => void,
    onActivate?: (index: number) => void
) {
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            switch (event.key) {
                case 'ArrowUp':
                    event.preventDefault();
                    if (selectedIndex > 0) {
                        onSelect(selectedIndex - 1);
                    }
                    break;
                case 'ArrowDown':
                    event.preventDefault();
                    if (selectedIndex < items.length - 1) {
                        onSelect(selectedIndex + 1);
                    }
                    break;
                case 'Home':
                    event.preventDefault();
                    onSelect(0);
                    break;
                case 'End':
                    event.preventDefault();
                    onSelect(items.length - 1);
                    break;
                case 'Enter':
                case ' ':
                    event.preventDefault();
                    onActivate?.(selectedIndex);
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [items.length, selectedIndex, onSelect, onActivate]);
}
