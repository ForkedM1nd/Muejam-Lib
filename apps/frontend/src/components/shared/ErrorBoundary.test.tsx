// ── Error Boundary Component Tests ──
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBoundary, useErrorBoundary } from "./ErrorBoundary";
import * as errors from "@/lib/errors";

// Component that throws an error
function ThrowError({ error }: { error: Error }) {
    throw error;
}

// Component that uses useErrorBoundary hook
function ComponentWithHook({ error }: { error: Error }) {
    const throwError = useErrorBoundary();

    return (
        <button onClick={() => throwError(error)}>
            Trigger Error
        </button>
    );
}

describe("ErrorBoundary", () => {
    beforeEach(() => {
        // Suppress console.error for cleaner test output
        vi.spyOn(console, "error").mockImplementation(() => { });
        vi.spyOn(errors, "logErrorToService").mockImplementation(() => { });
    });

    describe("Error Catching", () => {
        it("should catch and display errors from child components", () => {
            const error = new Error("Test error");

            render(
                <ErrorBoundary>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            expect(screen.getByText("Something went wrong")).toBeInTheDocument();
        });

        it("should display error message in fallback UI", () => {
            const error = new Error("Test error message");

            render(
                <ErrorBoundary>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            expect(screen.getByText("Something went wrong")).toBeInTheDocument();
            expect(
                screen.getByText(/We encountered an unexpected error/)
            ).toBeInTheDocument();
        });

        it("should log errors to monitoring service", () => {
            const error = new Error("Test error");
            const logSpy = vi.spyOn(errors, "logErrorToService");

            render(
                <ErrorBoundary>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            expect(logSpy).toHaveBeenCalledWith(
                error,
                expect.objectContaining({
                    componentStack: expect.any(String),
                    errorBoundary: true,
                })
            );
        });

        it("should call custom onError handler if provided", () => {
            const error = new Error("Test error");
            const onError = vi.fn();

            render(
                <ErrorBoundary onError={onError}>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            expect(onError).toHaveBeenCalledWith(
                error,
                expect.objectContaining({
                    componentStack: expect.any(String),
                })
            );
        });
    });

    describe("Fallback UI", () => {
        it("should display default fallback UI", () => {
            const error = new Error("Test error");

            render(
                <ErrorBoundary>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            expect(screen.getByText("Something went wrong")).toBeInTheDocument();
            expect(screen.getByText("Try again")).toBeInTheDocument();
            expect(screen.getByText("Refresh page")).toBeInTheDocument();
        });

        it("should display custom fallback UI if provided", () => {
            const error = new Error("Test error");
            const customFallback = (err: Error, reset: () => void) => (
                <div>
                    <h1>Custom Error</h1>
                    <p>{err.message}</p>
                    <button onClick={reset}>Reset</button>
                </div>
            );

            render(
                <ErrorBoundary fallback={customFallback}>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            expect(screen.getByText("Custom Error")).toBeInTheDocument();
            expect(screen.getByText("Test error")).toBeInTheDocument();
            expect(screen.getByText("Reset")).toBeInTheDocument();
        });

        it("should display error details in development mode", () => {
            const error = new Error("Test error with stack");
            error.stack = "Error: Test error\n  at Component";

            render(
                <ErrorBoundary>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            // Error details should be in a details element
            const details = screen.getByText(/Error details/);
            expect(details).toBeInTheDocument();
        });
    });

    describe("Reset Functionality", () => {
        it("should reset error state when Try again button is clicked", async () => {
            const user = userEvent.setup();
            let shouldThrow = true;

            function ConditionalError() {
                if (shouldThrow) {
                    throw new Error("Test error");
                }
                return <div>Success</div>;
            }

            render(
                <ErrorBoundary>
                    <ConditionalError />
                </ErrorBoundary>
            );

            expect(screen.getByText("Something went wrong")).toBeInTheDocument();

            // Stop throwing error
            shouldThrow = false;

            // Click Try again
            const tryAgainButton = screen.getByText("Try again");
            await user.click(tryAgainButton);

            expect(screen.getByText("Success")).toBeInTheDocument();
        });

        it("should call custom reset function in custom fallback", async () => {
            const user = userEvent.setup();
            const error = new Error("Test error");
            const resetSpy = vi.fn();

            const customFallback = (_err: Error, reset: () => void) => (
                <button
                    onClick={() => {
                        resetSpy();
                        reset();
                    }}
                >
                    Custom Reset
                </button>
            );

            render(
                <ErrorBoundary fallback={customFallback}>
                    <ThrowError error={error} />
                </ErrorBoundary>
            );

            const resetButton = screen.getByText("Custom Reset");
            await user.click(resetButton);

            expect(resetSpy).toHaveBeenCalled();
        });
    });

    describe("Normal Rendering", () => {
        it("should render children when no error occurs", () => {
            render(
                <ErrorBoundary>
                    <div>Normal content</div>
                </ErrorBoundary>
            );

            expect(screen.getByText("Normal content")).toBeInTheDocument();
            expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
        });

        it("should render multiple children", () => {
            render(
                <ErrorBoundary>
                    <div>Child 1</div>
                    <div>Child 2</div>
                    <div>Child 3</div>
                </ErrorBoundary>
            );

            expect(screen.getByText("Child 1")).toBeInTheDocument();
            expect(screen.getByText("Child 2")).toBeInTheDocument();
            expect(screen.getByText("Child 3")).toBeInTheDocument();
        });
    });

    describe("useErrorBoundary Hook", () => {
        it("should allow manually triggering error boundary", async () => {
            const user = userEvent.setup();
            const error = new Error("Manual error");

            render(
                <ErrorBoundary>
                    <ComponentWithHook error={error} />
                </ErrorBoundary>
            );

            // Initially, no error
            expect(screen.getByText("Trigger Error")).toBeInTheDocument();

            // Click button to trigger error
            await user.click(screen.getByText("Trigger Error"));

            // Error boundary should catch it
            expect(screen.getByText("Something went wrong")).toBeInTheDocument();
        });

        it("should work with async errors", async () => {
            const user = userEvent.setup();
            const error = new Error("Async error");

            function AsyncComponent() {
                const throwError = useErrorBoundary();

                const handleClick = async () => {
                    // Simulate async operation
                    await new Promise((resolve) => setTimeout(resolve, 0));
                    throwError(error);
                };

                return <button onClick={handleClick}>Async Error</button>;
            }

            render(
                <ErrorBoundary>
                    <AsyncComponent />
                </ErrorBoundary>
            );

            await user.click(screen.getByText("Async Error"));

            // Wait for async operation
            await screen.findByText("Something went wrong");
            expect(screen.getByText("Something went wrong")).toBeInTheDocument();
        });
    });

    describe("Error Boundary Nesting", () => {
        it("should catch errors at the nearest boundary", () => {
            const innerError = new Error("Inner error");
            const outerError = new Error("Outer error");

            const innerFallback = () => <div>Inner Fallback</div>;
            const outerFallback = () => <div>Outer Fallback</div>;

            render(
                <ErrorBoundary fallback={outerFallback}>
                    <div>Outer content</div>
                    <ErrorBoundary fallback={innerFallback}>
                        <ThrowError error={innerError} />
                    </ErrorBoundary>
                </ErrorBoundary>
            );

            // Inner boundary should catch the error
            expect(screen.getByText("Inner Fallback")).toBeInTheDocument();
            expect(screen.getByText("Outer content")).toBeInTheDocument();
            expect(screen.queryByText("Outer Fallback")).not.toBeInTheDocument();
        });
    });
});
