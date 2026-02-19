import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { DataExport } from "./DataExport";
import type { ExportRequest, ExportStatus } from "@/types";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        gdpr: {
            requestDataExport: vi.fn(),
            getExportStatus: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: vi.fn(() => ({
        toast: vi.fn(),
    })),
}));

const mockExportRequest: ExportRequest = {
    export_id: "export-123",
    status: "pending",
    requested_at: "2024-01-15T10:30:00Z",
};

const mockExportStatusPending: ExportStatus = {
    export_id: "export-123",
    status: "pending",
};

const mockExportStatusProcessing: ExportStatus = {
    export_id: "export-123",
    status: "processing",
    progress: 45,
};

const mockExportStatusCompleted: ExportStatus = {
    export_id: "export-123",
    status: "completed",
    download_url: "https://example.com/download/export-123.zip",
    expires_at: "2024-01-22T10:30:00Z",
};

const mockExportStatusFailed: ExportStatus = {
    export_id: "export-123",
    status: "failed",
};

describe("DataExport", () => {
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
                <BrowserRouter>{component}</BrowserRouter>
            </QueryClientProvider>
        );
    };

    it("should display initial state with request button", () => {
        renderWithProviders(<DataExport />);

        expect(screen.getByText("Data Export")).toBeInTheDocument();
        expect(
            screen.getByText(/Request a copy of all your personal data/i)
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /Request Data Export/i })
        ).toBeInTheDocument();
    });

    it("should display information about what will be exported", () => {
        renderWithProviders(<DataExport />);

        expect(
            screen.getByText(/Your export will include all your stories/i)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/available for download for 7 days/i)
        ).toBeInTheDocument();
    });

    it("should request data export when button is clicked", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusPending
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        await waitFor(
            () => {
                expect(mockToast).toHaveBeenCalledWith(
                    expect.objectContaining({
                        title: "Export requested",
                    })
                );
            },
            { timeout: 10000 }
        );
    });

    it("should display export status after request", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusPending
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(screen.getByText(/Export Status: Pending/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        expect(screen.getByText(/Export ID:/i)).toBeInTheDocument();
        expect(screen.getByText("export-123")).toBeInTheDocument();
    });

    it("should poll for export status after request", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusPending
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for at least one poll
        await waitFor(
            () => {
                expect(services.gdpr.getExportStatus).toHaveBeenCalledWith("export-123");
            },
            { timeout: 10000 }
        );
    });

    it("should display progress bar when processing", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusProcessing
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for status update
        await waitFor(
            () => {
                expect(screen.getByText(/Export Status: Processing/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        expect(screen.getByText("45%")).toBeInTheDocument();
        expect(screen.getByText(/Progress/i)).toBeInTheDocument();
    }, 15000);

    it("should display download link when export is completed", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusCompleted
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for completed status
        await waitFor(
            () => {
                expect(screen.getByText(/Export Status: Completed/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        const downloadLink = screen.getByRole("link", { name: /Download Export/i });
        expect(downloadLink).toBeInTheDocument();
        expect(downloadLink).toHaveAttribute(
            "href",
            "https://example.com/download/export-123.zip"
        );
    }, 15000);

    it("should display expiration time when export is completed", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusCompleted
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for completed status
        await waitFor(
            () => {
                expect(screen.getByText(/Expires:/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        expect(screen.getByText(/January 22, 2024/i)).toBeInTheDocument();
    }, 15000);

    it("should stop polling when export is completed", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusCompleted
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for completed status
        await waitFor(
            () => {
                expect(screen.getByText(/Export Status: Completed/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        const callCount = vi.mocked(services.gdpr.getExportStatus).mock.calls.length;

        // Wait a bit more - should not poll again since completed
        await new Promise(resolve => setTimeout(resolve, 6000));

        expect(vi.mocked(services.gdpr.getExportStatus).mock.calls.length).toBe(
            callCount
        );
    }, 15000);

    it("should display error message when export fails", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusFailed
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for failed status
        await waitFor(
            () => {
                expect(screen.getByText(/Export Status: Failed/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        expect(
            screen.getByText(/The export failed to complete/i)
        ).toBeInTheDocument();
    }, 15000);

    it("should allow requesting new export after completion", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusCompleted
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for completed status
        await waitFor(
            () => {
                expect(screen.getByText(/Export Status: Completed/i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );

        const newExportButton = screen.getByRole("button", {
            name: /Request New Export/i,
        });
        expect(newExportButton).toBeInTheDocument();
    }, 15000);

    it("should handle request errors gracefully", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.requestDataExport).mockRejectedValue(
            new Error("Request failed")
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(mockToast).toHaveBeenCalledWith(
                    expect.objectContaining({
                        title: "Error",
                        description: "Failed to request data export. Please try again.",
                        variant: "destructive",
                    })
                );
            },
            { timeout: 10000 }
        );
    });

    it("should handle status polling errors gracefully", async () => {
        const { services } = await import("@/lib/api");
        const { useToast } = await import("@/hooks/use-toast");
        const mockToast = vi.fn();
        vi.mocked(useToast).mockReturnValue({
            toast: mockToast,
            dismiss: vi.fn(),
            toasts: [],
        });

        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockRejectedValue(
            new Error("Status check failed")
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for polling error
        await waitFor(
            () => {
                expect(mockToast).toHaveBeenCalledWith(
                    expect.objectContaining({
                        title: "Error",
                        description: "Failed to check export status. Please refresh the page.",
                        variant: "destructive",
                    })
                );
            },
            { timeout: 10000 }
        );
    }, 15000);

    it("should display loading state while requesting", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockImplementation(
            () => new Promise(() => { }) // Never resolves
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(screen.getByText(/Requesting.../i)).toBeInTheDocument();
            },
            { timeout: 10000 }
        );
    });

    it("should display auto-update message while processing", async () => {
        const { services } = await import("@/lib/api");
        vi.mocked(services.gdpr.requestDataExport).mockResolvedValue(
            mockExportRequest
        );
        vi.mocked(services.gdpr.getExportStatus).mockResolvedValue(
            mockExportStatusProcessing
        );

        renderWithProviders(<DataExport />);

        const requestButton = screen.getByRole("button", {
            name: /Request Data Export/i,
        });
        fireEvent.click(requestButton);

        await waitFor(
            () => {
                expect(services.gdpr.requestDataExport).toHaveBeenCalled();
            },
            { timeout: 10000 }
        );

        // Wait for processing status
        await waitFor(
            () => {
                expect(
                    screen.getByText(/This page will update automatically/i)
                ).toBeInTheDocument();
            },
            { timeout: 10000 }
        );
    });
});
