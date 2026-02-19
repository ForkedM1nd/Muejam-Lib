import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { ConsentHistory } from "./ConsentHistory";
import type { ConsentRecord } from "@/types";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        gdpr: {
            getConsentHistory: vi.fn(),
            withdrawConsent: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: vi.fn(() => ({
        toast: vi.fn(),
    })),
}));

const mockConsentRecords: ConsentRecord[] = [
    {
        consent_type: "story_recommendations",
        granted: true,
        granted_at: "2024-01-15T10:30:00Z",
        ip_address: "192.168.1.1",
    },
    {
        consent_type: "personalized_ads",
        granted: true,
        granted_at: "2024-01-15T10:30:00Z",
        ip_address: "192.168.1.1",
    },
    {
        consent_type: "analytics_tracking",
        granted: false,
        granted_at: "2024-01-15T10:30:00Z",
        withdrawn_at: "2024-02-01T14:20:00Z",
        ip_address: "192.168.1.1",
    },
];

describe("ConsentHistory", () => {
    let queryClient: QueryClient;

    beforeEach(async () => {
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
                <BrowserRouter>{component}</BrowserRouter>
            </QueryClientProvider>
        );
    };

    it("should display loading state initially", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockImplementation(
            () => new Promise(() => { }) // Never resolves
        );

        renderWithProviders(<ConsentHistory />);

        // Should show skeleton loaders
        const skeletons = document.querySelectorAll(".animate-pulse");
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it("should load and display consent history", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Check that consent records are displayed
        expect(screen.getByText("Story Recommendations")).toBeInTheDocument();
        expect(screen.getByText("Personalized Advertising")).toBeInTheDocument();
        expect(screen.getByText("Analytics Tracking")).toBeInTheDocument();

        // Check that descriptions are displayed
        expect(
            screen.getByText(/Allow us to recommend stories based on your reading history/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Show ads tailored to your interests/i)
        ).toBeInTheDocument();
    });

    it("should display consent records with timestamps", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Check that timestamps are displayed (formatted dates)
        const grantedDates = screen.getAllByText(/January 15, 2024/i);
        expect(grantedDates.length).toBeGreaterThan(0);

        // Check that withdrawn date is displayed for withdrawn consent
        expect(screen.getByText(/February 1, 2024/i)).toBeInTheDocument();
    });

    it("should display active and withdrawn status correctly", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Check for active status
        const activeStatuses = screen.getAllByText("Active");
        expect(activeStatuses.length).toBe(2); // Two active consents

        // Check for withdrawn status
        expect(screen.getByText("Withdrawn")).toBeInTheDocument();
    });

    it("should show withdraw button only for active consents", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Should have 2 withdraw buttons (for the 2 active consents)
        const withdrawButtons = screen.getAllByRole("button", { name: /Withdraw/i });
        expect(withdrawButtons.length).toBe(2);
    });

    it("should open confirmation dialog when withdraw is clicked", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Click the first withdraw button
        const withdrawButtons = screen.getAllByRole("button", { name: /^Withdraw$/i });
        fireEvent.click(withdrawButtons[0]);

        // Check that confirmation dialog appears
        await waitFor(() => {
            expect(screen.getByRole("alertdialog")).toBeInTheDocument();
            expect(
                screen.getByText(/Are you sure you want to withdraw your consent/i)
            ).toBeInTheDocument();
        });
    });

    it("should withdraw consent when confirmed", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );
        vi.mocked(services.gdpr.withdrawConsent).mockResolvedValue(undefined);

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Click the first withdraw button
        const withdrawButtons = screen.getAllByRole("button", { name: /^Withdraw$/i });
        fireEvent.click(withdrawButtons[0]);

        // Confirm withdrawal
        await waitFor(() => {
            expect(screen.getByRole("alertdialog")).toBeInTheDocument();
        });

        const confirmButtons = screen.getAllByRole("button", { name: "Withdraw Consent" });
        // The last button should be the confirm button in the dialog
        fireEvent.click(confirmButtons[confirmButtons.length - 1]);

        // Check that API was called
        await waitFor(() => {
            expect(services.gdpr.withdrawConsent).toHaveBeenCalledWith(
                "story_recommendations"
            );
        });

        // Check that success toast was shown
        await waitFor(() => {
            expect(mockToast).toHaveBeenCalledWith(
                expect.objectContaining({
                    title: "Consent withdrawn",
                })
            );
        });
    });

    it("should handle withdrawal errors gracefully", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );
        vi.mocked(services.gdpr.withdrawConsent).mockRejectedValue(
            new Error("Withdrawal failed")
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Click withdraw and confirm
        const withdrawButtons = screen.getAllByRole("button", { name: /^Withdraw$/i });
        fireEvent.click(withdrawButtons[0]);

        await waitFor(() => {
            expect(screen.getByRole("alertdialog")).toBeInTheDocument();
        });

        const confirmButtons = screen.getAllByRole("button", { name: "Withdraw Consent" });
        // The last button should be the confirm button in the dialog
        fireEvent.click(confirmButtons[confirmButtons.length - 1]);

        // Check that error toast was shown
        await waitFor(() => {
            expect(mockToast).toHaveBeenCalledWith(
                expect.objectContaining({
                    title: "Error",
                    variant: "destructive",
                })
            );
        });
    });

    it("should display empty state when no consents exist", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue([]);

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Check for empty state message
        expect(
            screen.getByText(/No consent records found/i)
        ).toBeInTheDocument();
    });

    it("should display error when loading fails", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.getConsentHistory).mockRejectedValue(
            new Error("Failed to load")
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(mockToast).toHaveBeenCalledWith(
                expect.objectContaining({
                    title: "Error",
                    description: "Failed to load consent history. Please try again.",
                    variant: "destructive",
                })
            );
        });
    });

    it("should display IP addresses for consent records", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getConsentHistory).mockResolvedValue(
            mockConsentRecords
        );

        renderWithProviders(<ConsentHistory />);

        await waitFor(() => {
            expect(screen.getByText("Consent History")).toBeInTheDocument();
        });

        // Check that IP addresses are displayed
        const ipAddresses = screen.getAllByText("192.168.1.1");
        expect(ipAddresses.length).toBe(3); // One for each consent record
    });
});
