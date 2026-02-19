import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RegenerateBackupCodes } from "./RegenerateBackupCodes";
import { services } from "@/lib/api";

// Mock the API services
vi.mock("@/lib/api", () => ({
    services: {
        security: {
            regenerateBackupCodes: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: () => ({
        toast: vi.fn(),
    }),
}));

describe("RegenerateBackupCodes", () => {
    const mockOnOpenChange = vi.fn();
    const mockOnSuccess = vi.fn();

    const mockBackupCodes = [
        "12345678",
        "23456789",
        "34567890",
        "45678901",
        "56789012",
        "67890123",
        "78901234",
        "89012345",
    ];

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should display confirmation dialog initially", () => {
        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByText("Regenerate Backup Codes")).toBeInTheDocument();
        expect(screen.getByText(/Generate new backup codes for your account/i)).toBeInTheDocument();
    });

    it("should display warning about invalidating old codes", () => {
        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByText(/Regenerating backup codes will invalidate all your existing backup codes/i)).toBeInTheDocument();
    });

    it("should call regenerateBackupCodes API when confirmed", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockResolvedValue(mockBackupCodes);

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(services.security.regenerateBackupCodes).toHaveBeenCalled();
        });
    });

    it("should display new backup codes after regeneration", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockResolvedValue(mockBackupCodes);

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(screen.getByText("New Backup Codes")).toBeInTheDocument();
        });

        // Check all backup codes are displayed
        mockBackupCodes.forEach((code) => {
            expect(screen.getByText(code)).toBeInTheDocument();
        });
    });

    it("should display success message after regeneration", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockResolvedValue(mockBackupCodes);

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(screen.getByText(/New backup codes have been generated successfully/i)).toBeInTheDocument();
        });
    });

    it("should allow copying backup codes", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockResolvedValue(mockBackupCodes);

        // Mock clipboard API
        Object.assign(navigator, {
            clipboard: {
                writeText: vi.fn().mockResolvedValue(undefined),
            },
        });

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(screen.getByText("New Backup Codes")).toBeInTheDocument();
        });

        const copyButton = screen.getByText("Copy Codes");
        await userEvent.click(copyButton);

        await waitFor(() => {
            expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
                mockBackupCodes.join("\n")
            );
        });
    });

    it("should call onSuccess when done", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockResolvedValue(mockBackupCodes);

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(screen.getByText("New Backup Codes")).toBeInTheDocument();
        });

        const doneButton = screen.getByText("Done");
        await userEvent.click(doneButton);

        expect(mockOnSuccess).toHaveBeenCalled();
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    it("should handle regeneration errors", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockRejectedValue(
            new Error("Failed to regenerate")
        );

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(screen.getByText(/Failed to regenerate backup codes/i)).toBeInTheDocument();
        });

        expect(mockOnSuccess).not.toHaveBeenCalled();
    });

    it("should allow canceling from confirmation step", async () => {
        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const cancelButton = screen.getByText("Cancel");
        await userEvent.click(cancelButton);

        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
        expect(mockOnSuccess).not.toHaveBeenCalled();
    });

    it("should show loading state while regenerating", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockImplementation(
            () => new Promise((resolve) => setTimeout(() => resolve(mockBackupCodes), 100))
        );

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        expect(screen.getByText("Generating...")).toBeInTheDocument();
    });

    it("should display warning about old codes being invalidated", async () => {
        vi.mocked(services.security.regenerateBackupCodes).mockResolvedValue(mockBackupCodes);

        render(
            <RegenerateBackupCodes
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const regenerateButton = screen.getByText("Regenerate Codes");
        await userEvent.click(regenerateButton);

        await waitFor(() => {
            expect(screen.getByText(/Your old backup codes have been invalidated/i)).toBeInTheDocument();
        });
    });
});
