import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { AccountDeletion } from "./AccountDeletion";
import type { DeletionRequest } from "@/types";
import { services } from "@/lib/api";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        gdpr: {
            requestAccountDeletion: vi.fn(),
            getDeletionStatus: vi.fn(),
            cancelDeletion: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: () => ({
        toast: vi.fn(),
    }),
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });

    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>{children}</BrowserRouter>
        </QueryClientProvider>
    );
};

describe("AccountDeletion", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("renders initial state with deletion information", () => {
        render(<AccountDeletion />, { wrapper: createWrapper() });

        expect(screen.getByText("Account Deletion")).toBeInTheDocument();
        expect(screen.getByText(/permanently delete your account/i)).toBeInTheDocument();
        expect(screen.getByText(/What will be deleted:/)).toBeInTheDocument();
        expect(screen.getByText(/Grace period:/)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /request account deletion/i })).toBeInTheDocument();
    });

    it("displays warning about permanent deletion", () => {
        render(<AccountDeletion />, { wrapper: createWrapper() });

        expect(screen.getByText(/Warning:/)).toBeInTheDocument();
        expect(screen.getByText(/Account deletion is permanent and cannot be undone/i)).toBeInTheDocument();
    });

    it("lists all data that will be deleted", () => {
        render(<AccountDeletion />, { wrapper: createWrapper() });

        expect(screen.getByText(/Your profile and account information/)).toBeInTheDocument();
        expect(screen.getByText(/All stories and chapters you've written/)).toBeInTheDocument();
        expect(screen.getByText(/All whispers and comments/)).toBeInTheDocument();
        expect(screen.getByText(/All highlights and bookmarks/)).toBeInTheDocument();
        expect(screen.getByText(/Your reading history and preferences/)).toBeInTheDocument();
        expect(screen.getByText(/All followers and following relationships/)).toBeInTheDocument();
    });

    it("explains the grace period", () => {
        render(<AccountDeletion />, { wrapper: createWrapper() });

        expect(screen.getByText(/30 days to cancel the request/i)).toBeInTheDocument();
        expect(screen.getByText(/your account will remain active but will be scheduled for deletion/i)).toBeInTheDocument();
    });

    it("shows confirmation dialog when requesting deletion", async () => {
        render(<AccountDeletion />, { wrapper: createWrapper() });

        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByText(/Are you absolutely sure?/)).toBeInTheDocument();
        });
        expect(screen.getByText(/This action will schedule your account for permanent deletion/i)).toBeInTheDocument();
    });

    it("requests account deletion via API when confirmed", async () => {
        const mockDeletionRequest: DeletionRequest = {
            deletion_id: "del_123",
            status: "pending",
            requested_at: "2024-01-01T00:00:00Z",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        };

        vi.mocked(services.gdpr.requestAccountDeletion).mockResolvedValue(mockDeletionRequest);
        vi.mocked(services.gdpr.getDeletionStatus).mockResolvedValue({
            deletion_id: "del_123",
            status: "pending",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        });

        render(<AccountDeletion />, { wrapper: createWrapper() });

        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, delete my account/i })).toBeInTheDocument();
        });

        const confirmButton = screen.getByRole("button", { name: /yes, delete my account/i });
        fireEvent.click(confirmButton);

        await waitFor(() => {
            expect(services.gdpr.requestAccountDeletion).toHaveBeenCalledTimes(1);
        });
    });

    it("displays deletion status after requesting", async () => {
        const mockDeletionRequest: DeletionRequest = {
            deletion_id: "del_123",
            status: "pending",
            requested_at: "2024-01-01T00:00:00Z",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        };

        vi.mocked(services.gdpr.requestAccountDeletion).mockResolvedValue(mockDeletionRequest);
        vi.mocked(services.gdpr.getDeletionStatus).mockResolvedValue({
            deletion_id: "del_123",
            status: "pending",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        });

        render(<AccountDeletion />, { wrapper: createWrapper() });

        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, delete my account/i })).toBeInTheDocument();
        });

        const confirmButton = screen.getByRole("button", { name: /yes, delete my account/i });
        fireEvent.click(confirmButton);

        await waitFor(() => {
            expect(screen.getByText(/Deletion Status: Pending/)).toBeInTheDocument();
        });

        expect(screen.getByText(/Deletion ID:/)).toBeInTheDocument();
        expect(screen.getByText("del_123")).toBeInTheDocument();
        expect(screen.getByText(/Scheduled for:/)).toBeInTheDocument();
    });

    it("displays scheduled deletion date", async () => {
        const scheduledDate = new Date("2024-01-31T00:00:00Z");
        const mockDeletionRequest: DeletionRequest = {
            deletion_id: "del_123",
            status: "pending",
            requested_at: "2024-01-01T00:00:00Z",
            scheduled_for: scheduledDate.toISOString(),
            can_cancel: true,
        };

        vi.mocked(services.gdpr.requestAccountDeletion).mockResolvedValue(mockDeletionRequest);
        vi.mocked(services.gdpr.getDeletionStatus).mockResolvedValue({
            deletion_id: "del_123",
            status: "pending",
            scheduled_for: scheduledDate.toISOString(),
            can_cancel: true,
        });

        render(<AccountDeletion />, { wrapper: createWrapper() });

        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, delete my account/i })).toBeInTheDocument();
        });

        const confirmButton = screen.getByRole("button", { name: /yes, delete my account/i });
        fireEvent.click(confirmButton);

        await waitFor(() => {
            expect(screen.getByText(/Scheduled for:/)).toBeInTheDocument();
        });
    });

    it("displays grace period information when deletion is pending", async () => {
        const mockDeletionRequest: DeletionRequest = {
            deletion_id: "del_123",
            status: "pending",
            requested_at: "2024-01-01T00:00:00Z",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        };

        vi.mocked(services.gdpr.requestAccountDeletion).mockResolvedValue(mockDeletionRequest);
        vi.mocked(services.gdpr.getDeletionStatus).mockResolvedValue({
            deletion_id: "del_123",
            status: "pending",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        });

        render(<AccountDeletion />, { wrapper: createWrapper() });

        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, delete my account/i })).toBeInTheDocument();
        });

        const confirmButton = screen.getByRole("button", { name: /yes, delete my account/i });
        fireEvent.click(confirmButton);

        await waitFor(() => {
            expect(screen.getByText(/days remaining to cancel/)).toBeInTheDocument();
        });

        expect(screen.getByText(/You can cancel this request at any time during the grace period/i)).toBeInTheDocument();
    });

    it("shows cancel deletion button when deletion is pending and can be cancelled", async () => {
        const mockDeletionRequest: DeletionRequest = {
            deletion_id: "del_123",
            status: "pending",
            requested_at: "2024-01-01T00:00:00Z",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        };

        vi.mocked(services.gdpr.requestAccountDeletion).mockResolvedValue(mockDeletionRequest);
        vi.mocked(services.gdpr.getDeletionStatus).mockResolvedValue({
            deletion_id: "del_123",
            status: "pending",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        });

        render(<AccountDeletion />, { wrapper: createWrapper() });

        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, delete my account/i })).toBeInTheDocument();
        });

        const confirmButton = screen.getByRole("button", { name: /yes, delete my account/i });
        fireEvent.click(confirmButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /cancel deletion request/i })).toBeInTheDocument();
        });
    });

    it("calls cancelDeletion API when cancel button is clicked", async () => {
        const mockDeletionRequest: DeletionRequest = {
            deletion_id: "del_123",
            status: "pending",
            requested_at: "2024-01-01T00:00:00Z",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        };

        vi.mocked(services.gdpr.requestAccountDeletion).mockResolvedValue(mockDeletionRequest);
        vi.mocked(services.gdpr.getDeletionStatus).mockResolvedValue({
            deletion_id: "del_123",
            status: "pending",
            scheduled_for: "2024-01-31T00:00:00Z",
            can_cancel: true,
        });
        vi.mocked(services.gdpr.cancelDeletion).mockResolvedValue();

        render(<AccountDeletion />, { wrapper: createWrapper() });

        // Request deletion
        const requestButton = screen.getByRole("button", { name: /request account deletion/i });
        fireEvent.click(requestButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, delete my account/i })).toBeInTheDocument();
        });

        const confirmButton = screen.getByRole("button", { name: /yes, delete my account/i });
        fireEvent.click(confirmButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /cancel deletion request/i })).toBeInTheDocument();
        });

        // Cancel deletion
        const cancelButton = screen.getByRole("button", { name: /cancel deletion request/i });
        fireEvent.click(cancelButton);

        await waitFor(() => {
            expect(screen.getByRole("button", { name: /yes, cancel deletion/i })).toBeInTheDocument();
        });

        const confirmCancelButton = screen.getByRole("button", { name: /yes, cancel deletion/i });
        fireEvent.click(confirmCancelButton);

        await waitFor(() => {
            expect(services.gdpr.cancelDeletion).toHaveBeenCalledWith("del_123");
        });
    });
});
