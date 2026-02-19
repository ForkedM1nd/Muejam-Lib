import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ModerationMetrics } from "./ModerationMetrics";
import { services } from "@/lib/api";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        admin: {
            getModerationMetrics: vi.fn(),
        },
    },
}));

describe("ModerationMetrics", () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: {
                    retry: false,
                },
            },
        });
        vi.clearAllMocks();
    });

    const renderWithClient = (component: React.ReactElement) => {
        return render(
            <QueryClientProvider client={queryClient}>
                {component}
            </QueryClientProvider>
        );
    };

    it("displays loading state initially", () => {
        vi.mocked(services.admin.getModerationMetrics).mockImplementation(
            () => new Promise(() => { }) // Never resolves
        );

        const { container } = renderWithClient(<ModerationMetrics />);

        // Check for the loading spinner by class
        const spinner = container.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
    });

    it("displays error state when fetch fails", async () => {
        vi.mocked(services.admin.getModerationMetrics).mockRejectedValue(
            new Error("Failed to fetch")
        );

        renderWithClient(<ModerationMetrics />);

        await waitFor(() => {
            expect(screen.getByText("Failed to load metrics")).toBeInTheDocument();
        });
    });

    it("displays metrics data when fetch succeeds", async () => {
        const mockMetrics = {
            pending_items: 15,
            resolved_today: 42,
            average_resolution_time: 125, // 2h 5m
            items_by_severity: {
                low: 5,
                medium: 7,
                high: 3,
            },
            items_by_type: {
                story: 8,
                chapter: 4,
                whisper: 2,
                user: 1,
            },
        };

        vi.mocked(services.admin.getModerationMetrics).mockResolvedValue(mockMetrics);

        renderWithClient(<ModerationMetrics />);

        await waitFor(() => {
            // Check overview metrics
            expect(screen.getByText("15")).toBeInTheDocument(); // Pending items
            expect(screen.getByText("42")).toBeInTheDocument(); // Resolved today
            expect(screen.getByText("2h 5m")).toBeInTheDocument(); // Avg resolution time

            // Check severity breakdown
            expect(screen.getByText("low")).toBeInTheDocument();
            expect(screen.getByText("5")).toBeInTheDocument();
            expect(screen.getByText("medium")).toBeInTheDocument();
            expect(screen.getByText("7")).toBeInTheDocument();
            expect(screen.getByText("high")).toBeInTheDocument();
            expect(screen.getByText("3")).toBeInTheDocument();

            // Check type breakdown
            expect(screen.getByText("story")).toBeInTheDocument();
            expect(screen.getByText("8")).toBeInTheDocument();
            expect(screen.getByText("chapter")).toBeInTheDocument();
            expect(screen.getByText("4")).toBeInTheDocument();
            expect(screen.getByText("whisper")).toBeInTheDocument();
            expect(screen.getByText("2")).toBeInTheDocument();
            expect(screen.getByText("user")).toBeInTheDocument();
            expect(screen.getByText("1")).toBeInTheDocument();
        });
    });

    it("formats resolution time correctly for minutes", async () => {
        const mockMetrics = {
            pending_items: 10,
            resolved_today: 20,
            average_resolution_time: 45, // 45 minutes
            items_by_severity: {},
            items_by_type: {},
        };

        vi.mocked(services.admin.getModerationMetrics).mockResolvedValue(mockMetrics);

        renderWithClient(<ModerationMetrics />);

        await waitFor(() => {
            expect(screen.getByText("45m")).toBeInTheDocument();
        });
    });

    it("formats resolution time correctly for hours only", async () => {
        const mockMetrics = {
            pending_items: 10,
            resolved_today: 20,
            average_resolution_time: 120, // 2 hours exactly
            items_by_severity: {},
            items_by_type: {},
        };

        vi.mocked(services.admin.getModerationMetrics).mockResolvedValue(mockMetrics);

        renderWithClient(<ModerationMetrics />);

        await waitFor(() => {
            expect(screen.getByText("2h")).toBeInTheDocument();
        });
    });

    it("displays all metric cards with correct titles", async () => {
        const mockMetrics = {
            pending_items: 0,
            resolved_today: 0,
            average_resolution_time: 0,
            items_by_severity: {},
            items_by_type: {},
        };

        vi.mocked(services.admin.getModerationMetrics).mockResolvedValue(mockMetrics);

        renderWithClient(<ModerationMetrics />);

        await waitFor(() => {
            expect(screen.getByText("Pending Items")).toBeInTheDocument();
            expect(screen.getByText("Resolved Today")).toBeInTheDocument();
            expect(screen.getByText("Avg Resolution Time")).toBeInTheDocument();
            expect(screen.getByText("Items by Severity")).toBeInTheDocument();
            expect(screen.getByText("Items by Type")).toBeInTheDocument();
        });
    });
});
