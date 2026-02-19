import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useDebounce } from "./useDebounce";

describe("useDebounce", () => {
    it("should return the initial value immediately", () => {
        const { result } = renderHook(() => useDebounce("test", 300));
        expect(result.current).toBe("test");
    });

    it("should debounce value changes", async () => {
        const { result, rerender } = renderHook(
            ({ value, delay }) => useDebounce(value, delay),
            { initialProps: { value: "initial", delay: 300 } }
        );

        expect(result.current).toBe("initial");

        // Update the value
        rerender({ value: "updated", delay: 300 });

        // Value should still be the initial value immediately after update
        expect(result.current).toBe("initial");

        // Wait for debounce delay
        await waitFor(
            () => {
                expect(result.current).toBe("updated");
            },
            { timeout: 500 }
        );
    });

    it("should cancel previous timeout on rapid changes", async () => {
        const { result, rerender } = renderHook(
            ({ value }) => useDebounce(value, 300),
            { initialProps: { value: "first" } }
        );

        expect(result.current).toBe("first");

        // Rapidly change values
        rerender({ value: "second" });
        rerender({ value: "third" });
        rerender({ value: "fourth" });

        // Should still be the initial value
        expect(result.current).toBe("first");

        // Wait for debounce delay
        await waitFor(
            () => {
                expect(result.current).toBe("fourth");
            },
            { timeout: 500 }
        );
    });

    it("should use custom delay", async () => {
        const { result, rerender } = renderHook(
            ({ value, delay }) => useDebounce(value, delay),
            { initialProps: { value: "initial", delay: 100 } }
        );

        rerender({ value: "updated", delay: 100 });

        // Wait for shorter delay
        await waitFor(
            () => {
                expect(result.current).toBe("updated");
            },
            { timeout: 200 }
        );
    });
});
