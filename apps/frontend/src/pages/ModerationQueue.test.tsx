import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { ClerkProvider } from "@clerk/clerk-react";
import ModerationQueue from "./ModerationQueue";
import type { ModerationItem, CursorPage } from "@/types";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        moderation: {
            getQueue: vi.fn(),
        },
    },
}));

// Mock Clerk
vi.mock("@clerk/clerk-react", async () => {
    const actual = await vi.importActual("@clerk/clerk-react");
    return {
        ...actual,
        useUser: vi.fn(),
        ClerkProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    };
});

const mockModerationItems: ModerationItem[] = [
    {
        id: "1",
        content_type: "story",
        content_id: "story-123",
        content_preview: "This is a test story content that has been flagged.",
        reporter_id: "user-456",
        report_reason: "Inappropriate content",
        report_details: "This story contains offensive language.",
        severity: "high",
        status: "pending",
        created_at: new Date().toISOString(),
    },
    {
        id: "2",
        content_type: "whisper",
        content_id: "whisper-789",
        content_preview: "This is a test whisper that has been reported.",
        reporter_id: "user-101",
        report_reason: "Spam",
        report_details: "This whisper is spam.",
        severity: "low",
        status: "pending",
        created_at: new Date().toISOString(),
    },
];

describe("ModerationQueue", () => {
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

    const renderWithProviders = (component: React.ReactElement) => {
        return render(
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    {component}
                </BrowserRouter>
            </QueryClientProvider>
        );
    };

    it("should redirect non-moderator users", async () => {
        const { useUser } = await import("@clerk/clerk-react");
        vi.mocked(useUser).mockReturnValue({
            isLoaded: true,
            user: {
                publicMetadata: { role: "user" },
            } as any,
            isSignedIn: true,
        });

        renderWithProviders(<ModerationQueue />);

        // Should redirect, so the main content should not be visible
        expect(screen.queryByText("Moderation Queue")).not.toBeInTheDocument();
    });

    it("should display loading state while checking auth", async () => {
        const { useUser } = await import("@clerk/clerk-react");
        vi.mocked(useUser).mockReturnValue({
            isLoaded: false,
            user: null,
            isSignedIn: false,
        });

        renderWithProviders(<ModerationQueue />);

        // Should show loading spinner (it's an SVG, not an img)
        expect(screen.getByText((content, element) => {
            return element?.tagName.toLowerCase() === 'svg' &&
                element?.classList.contains('lucide-loader-circle');
        })).toBeInTheDocument();
    });

    it("should display moderation queue for moderators", async () => {
        const { useUser } = await import("@clerk/clerk-react");
        const { services } = await import("@/lib/api");

        vi.mocked(useUser).mockReturnValue({
            isLoaded: true,
            user: {
                publicMetadata: { role: "moderator" },
            } as any,
            isSignedIn: true,
        });

        const mockResponse: CursorPage<ModerationItem> = {
            results: mockModerationItems,
            next_cursor: null,
            has_more: false,
        };

        vi.mocked(services.moderation.getQueue).mockResolvedValue(mockResponse);

        renderWithProviders(<ModerationQueue />);

        // Should display the page title
        await waitFor(() => {
            expect(screen.getByText("Moderation Queue")).toBeInTheDocument();
        });

        // Should display the queue items - use regex to match partial text
        await waitFor(() => {
            expect(screen.getByText(/Inappropriate content/i)).toBeInTheDocument();
            expect(screen.getByText(/Spam/i)).toBeInTheDocument();
        }, { timeout: 3000 });
    });

    it("should display empty state when queue is empty", async () => {
        const { useUser } = await import("@clerk/clerk-react");
        const { services } = await import("@/lib/api");

        vi.mocked(useUser).mockReturnValue({
            isLoaded: true,
            user: {
                publicMetadata: { role: "admin" },
            } as any,
            isSignedIn: true,
        });

        const mockResponse: CursorPage<ModerationItem> = {
            results: [],
            next_cursor: null,
            has_more: false,
        };

        vi.mocked(services.moderation.getQueue).mockResolvedValue(mockResponse);

        renderWithProviders(<ModerationQueue />);

        await waitFor(() => {
            expect(screen.getByText("No items in queue")).toBeInTheDocument();
        });
    });

    it("should display error state when fetch fails", async () => {
        const { useUser } = await import("@clerk/clerk-react");
        const { services } = await import("@/lib/api");

        vi.mocked(useUser).mockReturnValue({
            isLoaded: true,
            user: {
                publicMetadata: { role: "moderator" },
            } as any,
            isSignedIn: true,
        });

        vi.mocked(services.moderation.getQueue).mockRejectedValue({
            error: {
                code: "INTERNAL_SERVER_ERROR",
                message: "Failed to fetch queue",
            },
        });

        renderWithProviders(<ModerationQueue />);

        await waitFor(() => {
            expect(screen.getByText("Failed to load queue")).toBeInTheDocument();
        });
    });
});
