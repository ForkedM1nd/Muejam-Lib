import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAsyncOperation } from './useAsyncOperation';
import * as errorToast from '@/lib/errorToast';
import * as errors from '@/lib/errors';

// Mock the toast and error logging functions
vi.mock('@/lib/errorToast', () => ({
    showSuccessToast: vi.fn(),
    showErrorToast: vi.fn(),
}));

vi.mock('@/lib/errors', () => ({
    logErrorToService: vi.fn(),
}));

describe('useAsyncOperation', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should initialize with idle state', () => {
        const { result } = renderHook(() => useAsyncOperation());

        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSuccess).toBe(false);
        expect(result.current.isError).toBe(false);
        expect(result.current.data).toBe(null);
        expect(result.current.error).toBe(null);
    });

    it('should handle successful operation', async () => {
        const { result } = renderHook(() => useAsyncOperation());

        const operation = vi.fn().mockResolvedValue('success data');

        let returnedData: string | null = null;
        await act(async () => {
            returnedData = await result.current.execute(operation);
        });

        expect(operation).toHaveBeenCalledTimes(1);
        expect(returnedData).toBe('success data');
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.isError).toBe(false);
        expect(result.current.data).toBe('success data');
        expect(result.current.error).toBe(null);
    });

    it('should handle failed operation', async () => {
        const { result } = renderHook(() => useAsyncOperation());

        const error = new Error('Operation failed');
        const operation = vi.fn().mockRejectedValue(error);

        let returnedData: unknown = undefined;
        await act(async () => {
            returnedData = await result.current.execute(operation);
        });

        expect(operation).toHaveBeenCalledTimes(1);
        expect(returnedData).toBe(null);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSuccess).toBe(false);
        expect(result.current.isError).toBe(true);
        expect(result.current.data).toBe(null);
        expect(result.current.error).toBe(error);
    });

    it('should show success toast when configured', async () => {
        const { result } = renderHook(() =>
            useAsyncOperation({
                showSuccessMessage: true,
                successMessage: 'Operation completed!',
            })
        );

        const operation = vi.fn().mockResolvedValue('data');

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(errorToast.showSuccessToast).toHaveBeenCalledWith(
            'Operation completed!',
            'Success'
        );
    });

    it('should not show success toast when not configured', async () => {
        const { result } = renderHook(() =>
            useAsyncOperation({
                showSuccessMessage: false,
            })
        );

        const operation = vi.fn().mockResolvedValue('data');

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(errorToast.showSuccessToast).not.toHaveBeenCalled();
    });

    it('should show error toast when configured', async () => {
        const { result } = renderHook(() =>
            useAsyncOperation({
                showErrorToast: true,
            })
        );

        const error = new Error('Operation failed');
        const operation = vi.fn().mockRejectedValue(error);

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(errorToast.showErrorToast).toHaveBeenCalledWith(error);
    });

    it('should log errors when configured', async () => {
        const { result } = renderHook(() =>
            useAsyncOperation({
                logErrors: true,
                errorContext: {
                    component: 'TestComponent',
                    action: 'testAction',
                },
            })
        );

        const error = new Error('Operation failed');
        const operation = vi.fn().mockRejectedValue(error);

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(errors.logErrorToService).toHaveBeenCalledWith(error, {
            component: 'TestComponent',
            action: 'testAction',
        });
    });

    it('should not log errors when disabled', async () => {
        const { result } = renderHook(() =>
            useAsyncOperation({
                logErrors: false,
            })
        );

        const error = new Error('Operation failed');
        const operation = vi.fn().mockRejectedValue(error);

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(errors.logErrorToService).not.toHaveBeenCalled();
    });

    it('should call onSuccess callback', async () => {
        const onSuccess = vi.fn();
        const { result } = renderHook(() =>
            useAsyncOperation({
                onSuccess,
            })
        );

        const operation = vi.fn().mockResolvedValue('data');

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(onSuccess).toHaveBeenCalledWith('data');
    });

    it('should call onError callback', async () => {
        const onError = vi.fn();
        const { result } = renderHook(() =>
            useAsyncOperation({
                onError,
            })
        );

        const error = new Error('Operation failed');
        const operation = vi.fn().mockRejectedValue(error);

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(onError).toHaveBeenCalledWith(error);
    });

    it('should reset state', async () => {
        const { result } = renderHook(() => useAsyncOperation());

        const operation = vi.fn().mockResolvedValue('data');

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toBe('data');

        act(() => {
            result.current.reset();
        });

        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSuccess).toBe(false);
        expect(result.current.isError).toBe(false);
        expect(result.current.data).toBe(null);
        expect(result.current.error).toBe(null);
    });

    it('should complete operation successfully', async () => {
        const { result } = renderHook(() => useAsyncOperation());

        const operation = vi.fn().mockResolvedValue('data');

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(operation).toHaveBeenCalledTimes(1);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSuccess).toBe(true);
        expect(result.current.data).toBe('data');
    });

    it('should handle minimum loading time', async () => {
        const { result } = renderHook(() =>
            useAsyncOperation({
                minLoadingTime: 100,
            })
        );

        const operation = vi.fn().mockResolvedValue('data');

        const start = Date.now();
        await act(async () => {
            await result.current.execute(operation);
        });
        const elapsed = Date.now() - start;

        expect(elapsed).toBeGreaterThanOrEqual(95); // Allow small margin
        expect(result.current.isSuccess).toBe(true);
    });

    it('should handle non-Error rejections', async () => {
        const { result } = renderHook(() => useAsyncOperation());

        const operation = vi.fn().mockRejectedValue('string error');

        await act(async () => {
            await result.current.execute(operation);
        });

        expect(result.current.isError).toBe(true);
        expect(result.current.error).toBeInstanceOf(Error);
        expect(result.current.error?.message).toBe('string error');
    });
});
