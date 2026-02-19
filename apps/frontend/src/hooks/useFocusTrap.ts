import { useEffect, useRef, RefObject } from 'react';

/**
 * Hook to trap focus within a container (useful for modals and dialogs)
 */
export function useFocusTrap<T extends HTMLElement>(
    isActive: boolean = true
): RefObject<T> {
    const containerRef = useRef<T>(null);
    const previousFocusRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        if (!isActive || !containerRef.current) return;

        const container = containerRef.current;

        // Store the currently focused element
        previousFocusRef.current = document.activeElement as HTMLElement;

        // Get all focusable elements within the container
        const getFocusableElements = (): HTMLElement[] => {
            const selector = [
                'a[href]',
                'button:not([disabled])',
                'textarea:not([disabled])',
                'input:not([disabled])',
                'select:not([disabled])',
                '[tabindex]:not([tabindex="-1"])',
            ].join(', ');

            return Array.from(container.querySelectorAll(selector));
        };

        // Focus the first focusable element
        const focusableElements = getFocusableElements();
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }

        // Handle tab key to trap focus
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key !== 'Tab') return;

            const focusableElements = getFocusableElements();
            if (focusableElements.length === 0) return;

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    event.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    event.preventDefault();
                    firstElement.focus();
                }
            }
        };

        container.addEventListener('keydown', handleKeyDown);

        // Cleanup: restore focus to previous element
        return () => {
            container.removeEventListener('keydown', handleKeyDown);

            if (previousFocusRef.current) {
                previousFocusRef.current.focus();
            }
        };
    }, [isActive]);

    return containerRef;
}

/**
 * Hook to restore focus to a previous element
 */
export function useFocusRestore() {
    const previousFocusRef = useRef<HTMLElement | null>(null);

    const saveFocus = () => {
        previousFocusRef.current = document.activeElement as HTMLElement;
    };

    const restoreFocus = () => {
        if (previousFocusRef.current) {
            previousFocusRef.current.focus();
            previousFocusRef.current = null;
        }
    };

    return { saveFocus, restoreFocus };
}

/**
 * Hook to manage focus visibility (show focus indicators only for keyboard users)
 */
export function useFocusVisible() {
    useEffect(() => {
        let isUsingKeyboard = false;

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Tab') {
                isUsingKeyboard = true;
                document.body.classList.add('keyboard-navigation');
            }
        };

        const handleMouseDown = () => {
            isUsingKeyboard = false;
            document.body.classList.remove('keyboard-navigation');
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('mousedown', handleMouseDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('mousedown', handleMouseDown);
        };
    }, []);
}
