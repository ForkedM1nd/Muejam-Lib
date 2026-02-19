import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import PrivacySettings from "./PrivacySettings";
import type { PrivacySettings as PrivacySettingsType } from "@/types";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        gdpr: {
            getPrivacySettings: vi.fn(),
            updatePrivacySettings: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: vi.fn(() => ({
        toast: vi.fn(),
    })),
}));

const mockPrivacySettings: PrivacySettingsType = {
    profile_visibility: "public",
    show_reading_activity: true,
    show_followers: true,
    show_following: true,
    allow_story_recommendations: true,
    allow_personalized_ads: false,
    allow_analytics_tracking: true,
    allow_email_notifications: true,
};

describe("PrivacySettings", () => {
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
        vi.mocked(services.gdpr.getPrivacySettings).mockImplementation(
            () => new Promise(() => { }) // Never resolves
        );

        renderWithProviders(<PrivacySettings />);

        // Should show skeleton loaders (check for animate-pulse class)
        const skeletons = document.querySelectorAll(".animate-pulse");
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it("should load and display privacy settings", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getPrivacySettings).mockResolvedValue(
            mockPrivacySettings
        );

        renderWithProviders(<PrivacySettings />);

        await waitFor(() => {
            expect(screen.getByText("Privacy Settings")).toBeInTheDocument();
        });

        // Check that all settings sections are displayed
        expect(screen.getByText("Profile Visibility")).toBeInTheDocument();
        expect(screen.getByText("Personalization")).toBeInTheDocument();
        expect(screen.getByText("Communications")).toBeInTheDocument();

        // Check that specific settings are displayed
        expect(screen.getByText("Show reading activity")).toBeInTheDocument();
        expect(screen.getByText("Show followers")).toBeInTheDocument();
        expect(screen.getByText("Story recommendations")).toBeInTheDocument();
        expect(screen.getByText("Email notifications")).toBeInTheDocument();
    });

    it("should display error when loading fails", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getPrivacySettings).mockRejectedValue(
            new Error("Failed to load")
        );

        renderWithProviders(<PrivacySettings />);

        await waitFor(() => {
            expect(
                screen.getByText(/Failed to load privacy settings/i)
            ).toBeInTheDocument();
        });
    });

    it("should toggle boolean settings", async () => {
        const { services } = await import("@/lib/api");

        vi.mocked(services.gdpr.getPrivacySettings).mockResolvedValue(
            mockPrivacySettings
        );

        const updatedSettings = {
            ...mockPrivacySettings,
            show_reading_activity: false,
        };
        vi.mocked(services.gdpr.updatePrivacySettings).mockResolvedValue(
            updatedSettings
        );

        renderWithProviders(<PrivacySettings />);

        await waitFor(() => {
            expect(screen.getByText("Privacy Settings")).toBeInTheDocument();
        });

        // Find and toggle the "Show reading activity" switch
        const readingActivitySwitch = screen.getByRole("switch", {
            name: /Show reading activity/i,
        });
        fireEvent.click(readingActivitySwitch);

        await waitFor(() => {
            expect(services.gdpr.updatePrivacySettings).toHaveBeenCalledWith({
                show_reading_activity: false,
            });
        });
    });

    it("should display all privacy options with explanations", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.getPrivacySettings).mockResolvedValue(
            mockPrivacySettings
        );

        renderWithProviders(<PrivacySettings />);

        await waitFor(() => {
            expect(screen.getByText("Privacy Settings")).toBeInTheDocument();
        });

        // Check that explanations are present
        expect(
            screen.getByText(/Allow others to see what stories you're reading/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Display your followers list on your profile/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Allow us to recommend stories based on your reading history/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Show ads tailored to your interests/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Help us improve by tracking how you use the platform/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Receive email notifications about your account activity/i)
        ).toBeInTheDocument();
    });

    it("should handle update errors gracefully", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({ toast: mockToast });

        vi.mocked(services.gdpr.getPrivacySettings).mockResolvedValue(
            mockPrivacySettings
        );

        vi.mocked(services.gdpr.updatePrivacySettings).mockRejectedValue(
            new Error("Update failed")
        );

        renderWithProviders(<PrivacySettings />);

        await waitFor(() => {
            expect(screen.getByText("Privacy Settings")).toBeInTheDocument();
        });

        // Try to toggle a setting
        const readingActivitySwitch = screen.getByRole("switch", {
            name: /Show reading activity/i,
        });
        fireEvent.click(readingActivitySwitch);

        await waitFor(() => {
            expect(mockToast).toHaveBeenCalledWith(
                expect.objectContaining({
                    title: "Error",
                    variant: "destructive",
                })
            );
        });
    });
});
