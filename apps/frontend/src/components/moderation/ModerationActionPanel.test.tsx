import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ModerationActionPanel } from "./ModerationActionPanel";
import type { ModerationItem } from "@/types";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        moderation: {
            reviewItem: vi.fn(),
            getItemHistory: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: () => ({
        toast: vi.fn(),
    }),
}));

const mockItem: ModerationItem = {
    id: "item-1",
    content_type: "whisper",
    content_id: "content-123",
    content_preview: "This is flagged content",
    reporter_id: "reporter-456",
    report_reason: "Spam",
    report_details: "This looks like spam content",
    severity: "medium",
    status: "pending",
    created_at: new Date().toISOString(),
};

describe("ModerationActionPanel", () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });
        vi.clearAllMocks();
    });

    const renderComponent = (item: ModerationItem = mockItem) => {
        const onActionComplete = vi.fn();
        return {
            ...render(
                <QueryClientProvider client={queryClient}>
                    <ModerationActionPanel item={item} onActionComplete={onActionComplete} />
                </QueryClientProvider>
            ),
            onActionComplete,
        };
    };

    it("should render all action buttons", () => {
        renderComponent();

        expect(screen.getByText("Approve")).toBeInTheDocument();
        expect(screen.getByText("Hide Content")).toBeInTheDocument();
        expect(screen.getByText("Warn User")).toBeInTheDocument();
        expect(screen.getByText("Ban User")).toBeInTheDocument();
        expect(screen.getByText("Escalate")).toBeInTheDocument();
    });

    it("should show action form when an action is selected", async () => {
        renderComponent();

        // Click the Approve button
        fireEvent.click(screen.getByText("Approve"));

        // Form fields should appear
        await waitFor(() => {
            expect(screen.getByLabelText(/Reason/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/Additional Notes/i)).toBeInTheDocument();
            expect(screen.getByText("Submit Action")).toBeInTheDocument();
        });
    });

    it("should show duration field for ban action", async () => {
        renderComponent();

        // Click the Ban User button
        fireEvent.click(screen.getByText("Ban User"));

        // Duration field should appear
        await waitFor(() => {
            expect(screen.getByLabelText(/Ban Duration/i)).toBeInTheDocument();
        });
    });

    it("should allow canceling action selection", async () => {
        renderComponent();

        // Select an action
        fireEvent.click(screen.getByText("Approve"));

        // Form should appear
        await waitFor(() => {
            expect(screen.getByText("Submit Action")).toBeInTheDocument();
        });

        // Click cancel
        fireEvent.click(screen.getByText("Cancel"));

        // Form should disappear
        await waitFor(() => {
            expect(screen.queryByText("Submit Action")).not.toBeInTheDocument();
        });
    });

    it("should toggle moderation history visibility", async () => {
        const { services } = await import("@/lib/api");

        // Mock history response
        vi.mocked(services.moderation.getItemHistory).mockResolvedValue([
            {
                action: "reviewed",
                moderator_id: "mod-1",
                moderator_handle: "moderator1",
                reason: "Previous review",
                created_at: new Date().toISOString(),
            },
        ]);

        renderComponent();

        // Initially history should be hidden
        expect(screen.queryByText("Previous review")).not.toBeInTheDocument();

        // Click Show button
        const showButton = screen.getByText("Show");
        fireEvent.click(showButton);

        // History should load and display
        await waitFor(() => {
            expect(screen.getByText("Previous review")).toBeInTheDocument();
        });

        // Click Hide button
        const hideButton = screen.getByText("Hide");
        fireEvent.click(hideButton);

        // History should be hidden again
        await waitFor(() => {
            expect(screen.queryByText("Previous review")).not.toBeInTheDocument();
        });
    });

    it("should display empty state when no history exists", async () => {
        const { services } = await import("@/lib/api");

        // Mock empty history response
        vi.mocked(services.moderation.getItemHistory).mockResolvedValue([]);

        renderComponent();

        // Show history
        fireEvent.click(screen.getByText("Show"));

        // Empty state should display
        await waitFor(() => {
            expect(screen.getByText(/No moderation history/i)).toBeInTheDocument();
        });
    });
});
