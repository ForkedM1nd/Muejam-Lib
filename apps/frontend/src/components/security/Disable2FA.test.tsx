import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Disable2FA } from "./Disable2FA";
import { services } from "@/lib/api";

// Mock the API services
vi.mock("@/lib/api", () => ({
    services: {
        security: {
            disable2FA: vi.fn(),
        },
    },
}));

// Mock the toast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: () => ({
        toast: vi.fn(),
    }),
}));

describe("Disable2FA", () => {
    const mockOnOpenChange = vi.fn();
    const mockOnSuccess = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should display password confirmation dialog", () => {
        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByText("Disable Two-Factor Authentication")).toBeInTheDocument();
        expect(screen.getByText(/Enter your password to confirm/i)).toBeInTheDocument();
        expect(screen.getByLabelText("Password")).toBeInTheDocument();
    });

    it("should display warning about security implications", () => {
        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByText(/Disabling two-factor authentication will make your account less secure/i)).toBeInTheDocument();
    });

    it("should require password to disable 2FA", async () => {
        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const disableButton = screen.getByText("Disable 2FA");
        expect(disableButton).toBeDisabled();

        const passwordInput = screen.getByLabelText("Password");
        await userEvent.type(passwordInput, "mypassword");

        expect(disableButton).not.toBeDisabled();
    });

    it("should call disable2FA API with password", async () => {
        vi.mocked(services.security.disable2FA).mockResolvedValue();

        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const passwordInput = screen.getByLabelText("Password");
        await userEvent.type(passwordInput, "mypassword");

        const disableButton = screen.getByText("Disable 2FA");
        await userEvent.click(disableButton);

        await waitFor(() => {
            expect(services.security.disable2FA).toHaveBeenCalledWith("mypassword");
        });
    });

    it("should call onSuccess when 2FA is disabled successfully", async () => {
        vi.mocked(services.security.disable2FA).mockResolvedValue();

        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const passwordInput = screen.getByLabelText("Password");
        await userEvent.type(passwordInput, "mypassword");

        const disableButton = screen.getByText("Disable 2FA");
        await userEvent.click(disableButton);

        await waitFor(() => {
            expect(mockOnSuccess).toHaveBeenCalled();
            expect(mockOnOpenChange).toHaveBeenCalledWith(false);
        });
    });

    it("should handle disable errors", async () => {
        vi.mocked(services.security.disable2FA).mockRejectedValue(new Error("Invalid password"));

        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const passwordInput = screen.getByLabelText("Password");
        await userEvent.type(passwordInput, "wrongpassword");

        const disableButton = screen.getByText("Disable 2FA");
        await userEvent.click(disableButton);

        await waitFor(() => {
            expect(screen.getByText(/Failed to disable 2FA/i)).toBeInTheDocument();
        });

        expect(mockOnSuccess).not.toHaveBeenCalled();
    });

    it("should allow canceling the operation", async () => {
        render(
            <Disable2FA
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

    it("should support Enter key to submit", async () => {
        vi.mocked(services.security.disable2FA).mockResolvedValue();

        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const passwordInput = screen.getByLabelText("Password");
        await userEvent.type(passwordInput, "mypassword{Enter}");

        await waitFor(() => {
            expect(services.security.disable2FA).toHaveBeenCalledWith("mypassword");
        });
    });

    it("should show loading state while disabling", async () => {
        vi.mocked(services.security.disable2FA).mockImplementation(
            () => new Promise((resolve) => setTimeout(resolve, 100))
        );

        render(
            <Disable2FA
                open={true}
                onOpenChange={mockOnOpenChange}
                onSuccess={mockOnSuccess}
            />
        );

        const passwordInput = screen.getByLabelText("Password");
        await userEvent.type(passwordInput, "mypassword");

        const disableButton = screen.getByText("Disable 2FA");
        await userEvent.click(disableButton);

        expect(screen.getByText("Disabling...")).toBeInTheDocument();

        // Wait for the operation to complete to avoid state updates after teardown
        await waitFor(() => {
            expect(mockOnSuccess).toHaveBeenCalled();
        });
    });
});
