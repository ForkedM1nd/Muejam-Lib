// ── useAsyncOperation Hook ──
// Provides consistent handling of async operations with loading, success, and error states

import { useState, useCallback } from 'react';
import { showSuccessToast, showErrorToast } from '@/lib/errorToast';
import { logErrorToService, type ErrorLogContext } from '@/lib/errors';
import {
    type LoadingConfig,
    DEFAULT_LOADING_CONFIG,
    withMinLoadingTime
} from '@/lib/loadingStates';

/**
 * State for async operations
 */
export interface AsyncOperationState<T> {
    isLoading: boolean;
    isSuccess: boolean;
    isError: boolean;
    data: T | null;
    error: Error | null;
}

/**
 * Options for async operation hook
 */
export interface UseAsyncOperationOptions extends LoadingConfig {
    /**
     * Callback on success
     */
    onSuccess?: (data: unknown) => void;

    /**
     * Callback on error
     */
    onError?: (error: Error) => void;

    /**
     * Log errors to monitoring service
     */
    logErrors?: boolean;

    /**
     * Error logging context
     */
    errorContext?: ErrorLogContext;

    /**
     * Show error toast on failure
     */
    showErrorToast?: boolean;
}

/**
 * Default options
 */
const DEFAULT_OPTIONS: Required<Omit<UseAsyncOperationOptions, 'errorContext' | 'onSuccess' | 'onError'>> = {
    ...DEFAULT_LOADING_CONFIG,
    logErrors: true,
    showErrorToast: true,
};

/**
 * Hook for managing async operations with loading, success, and error states
 * 
 * @example
 * ```tsx
 * const { execute, isLoading, isSuccess, error } = useAsyncOperation({
 *   showSuccessMessage: true,
 *   successMessage: 'Story created successfully!',
 * });
 * 
 * const handleCreate = async () => {
 *   await execute(async () => {
 *     return await api.createStory({ title, description });
 *   });
 * };
 * ```
 */
export function useAsyncOperation<T = unknown>(
    options: UseAsyncOperationOptions = {}
) {
    const finalOptions = { ...DEFAULT_OPTIONS, ...options };

    const [state, setState] = useState<AsyncOperationState<T>>({
        isLoading: false,
        isSuccess: false,
        isError: false,
        data: null,
        error: null,
    });

    /**
     * Execute an async operation
     */
    const execute = useCallback(
        async (operation: () => Promise<T>): Promise<T | null> => {
            // Reset state
            setState({
                isLoading: true,
                isSuccess: false,
                isError: false,
                data: null,
                error: null,
            });

            try {
                // Execute operation with minimum loading time
                const data = await withMinLoadingTime(
                    operation(),
                    finalOptions.minLoadingTime
                );

                // Update state with success
                setState({
                    isLoading: false,
                    isSuccess: true,
                    isError: false,
                    data,
                    error: null,
                });

                // Show success message if configured
                if (finalOptions.showSuccessMessage) {
                    showSuccessToast(
                        finalOptions.successMessage,
                        'Success'
                    );
                }

                // Call success callback
                options.onSuccess?.(data);

                return data;
            } catch (error) {
                const err = error instanceof Error ? error : new Error(String(error));

                // Update state with error
                setState({
                    isLoading: false,
                    isSuccess: false,
                    isError: true,
                    data: null,
                    error: err,
                });

                // Log error to monitoring service
                if (finalOptions.logErrors) {
                    logErrorToService(err, options.errorContext);
                }

                // Show error toast if configured
                if (finalOptions.showErrorToast) {
                    showErrorToast(err);
                }

                // Call error callback
                options.onError?.(err);

                return null;
            }
        },
        [finalOptions, options]
    );

    /**
     * Reset state
     */
    const reset = useCallback(() => {
        setState({
            isLoading: false,
            isSuccess: false,
            isError: false,
            data: null,
            error: null,
        });
    }, []);

    return {
        ...state,
        execute,
        reset,
    };
}

/**
 * Hook for managing multiple async operations
 * Useful for forms with multiple submit actions
 */
export function useAsyncOperations<T extends Record<string, unknown>>(
    operations: Record<keyof T, UseAsyncOperationOptions> = {} as Record<keyof T, UseAsyncOperationOptions>
) {
    const [states, setStates] = useState<Record<keyof T, AsyncOperationState<unknown>>>(() => {
        const initialStates = {} as Record<keyof T, AsyncOperationState<unknown>>;
        for (const key in operations) {
            initialStates[key] = {
                isLoading: false,
                isSuccess: false,
                isError: false,
                data: null,
                error: null,
            };
        }
        return initialStates;
    });

    /**
     * Execute a specific operation
     */
    const execute = useCallback(
        async <K extends keyof T>(
            key: K,
            operation: () => Promise<T[K]>
        ): Promise<T[K] | null> => {
            const options = { ...DEFAULT_OPTIONS, ...operations[key] };

            // Update state to loading
            setStates((prev) => ({
                ...prev,
                [key]: {
                    isLoading: true,
                    isSuccess: false,
                    isError: false,
                    data: null,
                    error: null,
                },
            }));

            try {
                // Execute operation with minimum loading time
                const data = await withMinLoadingTime(
                    operation(),
                    options.minLoadingTime
                );

                // Update state with success
                setStates((prev) => ({
                    ...prev,
                    [key]: {
                        isLoading: false,
                        isSuccess: true,
                        isError: false,
                        data,
                        error: null,
                    },
                }));

                // Show success message if configured
                if (options.showSuccessMessage) {
                    showSuccessToast(options.successMessage, 'Success');
                }

                // Call success callback
                operations[key]?.onSuccess?.(data);

                return data;
            } catch (error) {
                const err = error instanceof Error ? error : new Error(String(error));

                // Update state with error
                setStates((prev) => ({
                    ...prev,
                    [key]: {
                        isLoading: false,
                        isSuccess: false,
                        isError: true,
                        data: null,
                        error: err,
                    },
                }));

                // Log error to monitoring service
                if (options.logErrors) {
                    logErrorToService(err, operations[key]?.errorContext);
                }

                // Show error toast if configured
                if (options.showErrorToast) {
                    showErrorToast(err);
                }

                // Call error callback
                operations[key]?.onError?.(err);

                return null;
            }
        },
        [operations]
    );

    /**
     * Reset a specific operation state
     */
    const reset = useCallback((key: keyof T) => {
        setStates((prev) => ({
            ...prev,
            [key]: {
                isLoading: false,
                isSuccess: false,
                isError: false,
                data: null,
                error: null,
            },
        }));
    }, []);

    /**
     * Reset all operation states
     */
    const resetAll = useCallback(() => {
        const resetStates = {} as Record<keyof T, AsyncOperationState<unknown>>;
        for (const key in operations) {
            resetStates[key] = {
                isLoading: false,
                isSuccess: false,
                isError: false,
                data: null,
                error: null,
            };
        }
        setStates(resetStates);
    }, [operations]);

    return {
        states,
        execute,
        reset,
        resetAll,
    };
}
