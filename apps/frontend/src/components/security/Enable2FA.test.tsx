import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Enable2FA } from "./Enable2FA";
import { services } from "@/lib/api";

// Mock the API services
vi.mock("@/lib/api", () => ({
    services: {
        security: {
            enable2FA: vi.fn(),
            verify2FA: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: () => ({
        toast: vi.fn(),
    }),
}));

describe("Enable2FA", () => {
    const mockOnOpenChange = vi.fn();
    const mockOnSuccess = vi.fn();

    const mockSetupData = {
        secret: "JBSWY3DPEHPK3PXP",
        qr_code_url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        backup_codes: [
            "12345678",
            "23456789",
            "34567890",
            "45678901",
            "56789012",
            "67890123",
            "78901234",
            "89012345",
        ],
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should fetch QR code when dialog opens", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        await waitFor(() => {
            expect(services.security.enable2FA).toHaveBeenCalled();
        });
    });

    it("should display QR code for authenticator app", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        await waitFor(() => {
            const qrImage = screen.getByAltText("2FA QR Code");
            expect(qrImage).toBeInTheDocument();
            expect(qrImage).toHaveAttribute("src", mockSetupData.qr_code_url);
        });

        expect(screen.getByText(/Scan this QR code/i)).toBeInTheDocument();
        expect(screen.getByText(mockSetupData.secret)).toBeInTheDocument();
    });

    it("should have verification code input", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        // Wait for QR code to load
        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        // Click continue to verification
        const continueButton = screen.getByText("Continue to Verification");
        await userEvent.click(continueButton);

        // Should show verification code input
        expect(screen.getByLabelText("Verification Code")).toBeInTheDocument();
        expect(screen.getByPlaceholderText("000000")).toBeInTheDocument();
    });

    it("should verify code before enabling", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);
        vi.mocked(services.security.verify2FA).mockResolvedValue();

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        // Wait for QR code and navigate to verification
        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        // Enter verification code
        const codeInput = screen.getByLabelText("Verification Code");
        await userEvent.type(codeInput, "123456");

        // Click verify
        const verifyButton = screen.getByText("Verify");
        await userEvent.click(verifyButton);

        await waitFor(() => {
            expect(services.security.verify2FA).toHaveBeenCalledWith("123456");
        });
    });

    it("should display backup codes after enabling", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);
        vi.mocked(services.security.verify2FA).mockResolvedValue();

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        // Navigate through the flow
        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        const codeInput = screen.getByLabelText("Verification Code");
        await userEvent.type(codeInput, "123456");

        await userEvent.click(screen.getByText("Verify"));

        // Should show backup codes
        await waitFor(() => {
            expect(screen.getByText("Backup Codes")).toBeInTheDocument();
        });

        // Check all backup codes are displayed
        mockSetupData.backup_codes.forEach((code) => {
            expect(screen.getByText(code)).toBeInTheDocument();
        });

        expect(screen.getByText(/Save these codes in a safe place/i)).toBeInTheDocument();
    });

    it("should validate verification code format", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        // Verify button should be disabled with invalid code
        const verifyButton = screen.getByText("Verify");
        expect(verifyButton).toBeDisabled();

        // Enter partial code
        const codeInput = screen.getByLabelText("Verification Code");
        await userEvent.type(codeInput, "123");
        expect(verifyButton).toBeDisabled();

        // Enter full code
        await userEvent.type(codeInput, "456");
        expect(verifyButton).not.toBeDisabled();
    });

    it("should handle verification errors", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);
        vi.mocked(services.security.verify2FA).mockRejectedValue(new Error("Invalid code"));

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        const codeInput = screen.getByLabelText("Verification Code");
        await userEvent.type(codeInput, "123456");

        await userEvent.click(screen.getByText("Verify"));

        await waitFor(() => {
            expect(screen.getByText(/Invalid verification code/i)).toBeInTheDocument();
        });
    });

    it("should allow copying backup codes", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);
        vi.mocked(services.security.verify2FA).mockResolvedValue();

        // Mock clipboard API
        Object.assign(navigator, {
            clipboard: {
                writeText: vi.fn().mockResolvedValue(undefined),
            },
        });

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        // Navigate to backup codes
        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        const codeInput = screen.getByLabelText("Verification Code");
        await userEvent.type(codeInput, "123456");

        await userEvent.click(screen.getByText("Verify"));

        await waitFor(() => {
            expect(screen.getByText("Backup Codes")).toBeInTheDocument();
        });

        // Click copy button
        const copyButton = screen.getByText("Copy Codes");
        await userEvent.click(copyButton);

        await waitFor(() => {
            expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
                mockSetupData.backup_codes.join("\n")
            );
        });
    });

    it("should call onSuccess when setup is complete", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);
        vi.mocked(services.security.verify2FA).mockResolvedValue();

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        // Navigate through the entire flow
        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        const codeInput = screen.getByLabelText("Verification Code");
        await userEvent.type(codeInput, "123456");

        await userEvent.click(screen.getByText("Verify"));

        await waitFor(() => {
            expect(screen.getByText("Backup Codes")).toBeInTheDocument();
        });

        // Click done
        const doneButton = screen.getByText("Done");
        await userEvent.click(doneButton);

        expect(mockOnSuccess).toHaveBeenCalled();
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    it("should allow going back from verification to setup", async () => {
        vi.mocked(services.security.enable2FA).mockResolvedValue(mockSetupData);

        render(
            <Enable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });

        await userEvent.click(screen.getByText("Continue to Verification"));

        // Should be on verification step
        expect(screen.getByLabelText("Verification Code")).toBeInTheDocument();

        // Click back
        const backButton = screen.getByText("Back");
        await userEvent.click(backButton);

        // Should be back on setup step
        await waitFor(() => {
            expect(screen.getByAltText("2FA QR Code")).toBeInTheDocument();
        });
    });
});
