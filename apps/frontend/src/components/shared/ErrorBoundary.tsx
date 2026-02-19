// ── Error Boundary Component ──
// Catches and displays component errors with fallback UI

import React, { Component, type ErrorInfo, type ReactNode } from "react";
import { logErrorToService } from "@/lib/errors";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface Props {
    children: ReactNode;
    fallback?: (error: Error, reset: () => void) => ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
        };
    }

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error,
        };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        // Log to monitoring service
        logErrorToService(error, {
            componentStack: errorInfo.componentStack,
            errorBoundary: true,
        });

        // Call custom error handler if provided
        this.props.onError?.(error, errorInfo);
    }

    reset = (): void => {
        this.setState({
            hasError: false,
            error: null,
        });
    };

    render(): ReactNode {
        if (this.state.hasError && this.state.error) {
            // Use custom fallback if provided
            if (this.props.fallback) {
                return this.props.fallback(this.state.error, this.reset);
            }

            // Default fallback UI
            return <ErrorFallback error={this.state.error} reset={this.reset} />;
        }

        return this.props.children;
    }
}

// ── Default Error Fallback UI ──

interface ErrorFallbackProps {
    error: Error;
    reset: () => void;
}

function ErrorFallback({ error, reset }: ErrorFallbackProps): ReactNode {
    return (
        <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center">
            <div className="mb-4 rounded-full bg-red-100 p-3 dark:bg-red-900/20">
                <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>

            <h2 className="mb-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                Something went wrong
            </h2>

            <p className="mb-6 max-w-md text-gray-600 dark:text-gray-400">
                We encountered an unexpected error. Please try refreshing the page or contact support if the problem persists.
            </p>

            {import.meta.env.DEV && (
                <details className="mb-6 max-w-2xl text-left">
                    <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300">
                        Error details (development only)
                    </summary>
                    <pre className="mt-2 overflow-auto rounded-md bg-gray-100 p-4 text-xs text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                        {error.message}
                        {"\n\n"}
                        {error.stack}
                    </pre>
                </details>
            )}

            <div className="flex gap-3">
                <Button onClick={reset} variant="default">
                    Try again
                </Button>
                <Button
                    onClick={() => window.location.reload()}
                    variant="outline"
                >
                    Refresh page
                </Button>
            </div>
        </div>
    );
}

// ── Convenience Hook for Error Boundaries ──

/**
 * Hook to manually trigger error boundary
 * Useful for async errors that occur outside of render
 */
export function useErrorBoundary(): (error: Error) => void {
    const [, setError] = React.useState<Error | null>(null);

    return React.useCallback((error: Error) => {
        setError(() => {
            throw error;
        });
    }, []);
}
