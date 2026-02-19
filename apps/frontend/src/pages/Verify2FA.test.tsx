import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Verify2FA from "./Verify2FA";
import { services } from "@/lib/api";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        security: {
            verify2FALogin: vi.fn(),
            verifyBackupCode: vi.fn(),
        },
    },
}));

// Mock the useSafeAuth hook
vi.mock("@/hooks/useSafeAuth", () => ({
    useSafeAuth: () => ({
        isSignedIn: true,
        isLoaded: true,
        userId: "test-user-id",
    }),
}));

// Mock the useToast hook
vi.mock("@/hooks/use-toast", () => ({
    useToast: () => ({
        toast: vi.fn(),
    }),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return {
        ...actual,
        useNavigate: () => mockNavigate,
        useSearchParams: () => [new URLSearchParams()],
    };
});

describe("Verify2FA", () => {
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

    const renderComponent = () => {
        return render(
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <Verify2FA />
                </BrowserRouter>
            </QueryClientProvider>
        );
    };

    it("renders the 2FA verification page", () => {
        renderComponent();
        expect(screen.getByText("Two-Factor Authentication")).toBeInTheDocument();
        expect(screen.getByText("Enter your authentication code to continue")).toBeInTheDocument();
    });

    it("displays TOTP code input by default", () => {
        renderComponent();
        expect(screen.getByLabelText("Authentication Code")).toBeInTheDocument();
        expect(screen.getByPlaceholderText("000000")).toBeInTheDocument();
    });

    it("allows switching to backup code tab", async () => {
        const user = userEvent.setup();
        renderComponent();

        const backupTab = screen.getByRole("tab", { name: /backup code/i });
        await user.click(backupTab);

        // Wait for tab content to be visible
        await waitFor(() => {
            expect(screen.getByPlaceholderText("XXXX-XXXX")).toBeInTheDocument();
        });
    });

    it("validates TOTP code length", async () => {
        const user = userEvent.setup();
        renderComponent();

        const input = screen.getByLabelText("Authentication Code");
        const verifyButton = screen.getByRole("button", { name: /verify code/i });

        // Button should be disabled with empty input
        expect(verifyButton).toBeDisabled();

        // Enter partial code
        await user.type(input, "123");
        expect(verifyButton).toBeDisabled();

        // Enter full code
        await user.clear(input);
        await user.type(input, "123456");
        expect(verifyButton).not.toBeDisabled();
    });

    it("successfully verifies TOTP code", async () => {
        const user = userEvent.setup();
        vi.mocked(services.security.verify2FALogin).mockResolvedValue({
            message: "2FA verification successful",
            verified: true,
        });

        renderComponent();

        const input = screen.getByLabelText("Authentication Code");
        const verifyButton = screen.getByRole("button", { name: /verify code/i });

        await user.type(input, "123456");
        await user.click(verifyButton);

        await waitFor(() => {
            expect(services.security.verify2FALogin).toHaveBeenCalledWith("123456");
            expect(mockNavigate).toHaveBeenCalledWith("/discover", { replace: true });
        });
    });

    it("displays error for invalid TOTP code", async () => {
        const user = userEvent.setup();
        vi.mocked(services.security.verify2FALogin).mockRejectedValue({
            error: { message: "Invalid verification code" },
        });

        renderComponent();

        const input = screen.getByLabelText("Authentication Code");
        const verifyButton = screen.getByRole("button", { name: /verify code/i });

        await user.type(input, "000000");
        await user.click(verifyButton);

        await waitFor(() => {
            expect(screen.getByText("Invalid verification code")).toBeInTheDocument();
        });
    });

    it("successfully verifies backup code", async () => {
        const user = userEvent.setup();
        vi.mocked(services.security.verifyBackupCode).mockResolvedValue({
            message: "Backup code verified successfully",
            verified: true,
            remaining_codes: 9,
        });

        renderComponent();

        // Switch to backup code tab
        const backupTab = screen.getByRole("tab", { name: /backup code/i });
        await user.click(backupTab);

        // Wait for tab content to be visible
        await waitFor(() => {
            expect(screen.getByPlaceholderText("XXXX-XXXX")).toBeInTheDocument();
        });

        const input = screen.getByPlaceholderText("XXXX-XXXX");
        const verifyButton = screen.getByRole("button", { name: /verify backup code/i });

        await user.type(input, "ABCD1234");
        await user.click(verifyButton);

        await waitFor(() => {
            expect(services.security.verifyBackupCode).toHaveBeenCalledWith("ABCD1234");
            expect(mockNavigate).toHaveBeenCalledWith("/discover", { replace: true });
        });
    });

    it("displays error for invalid backup code", async () => {
        const user = userEvent.setup();
        vi.mocked(services.security.verifyBackupCode).mockRejectedValue({
            error: { message: "Invalid backup code" },
        });

        renderComponent();

        // Switch to backup code tab
        const backupTab = screen.getByRole("tab", { name: /backup code/i });
        await user.click(backupTab);

        // Wait for tab content to be visible
        await waitFor(() => {
            expect(screen.getByPlaceholderText("XXXX-XXXX")).toBeInTheDocument();
        });

        const input = screen.getByPlaceholderText("XXXX-XXXX");
        const verifyButton = screen.getByRole("button", { name: /verify backup code/i });

        await user.type(input, "INVALID1");
        await user.click(verifyButton);

        await waitFor(() => {
            expect(screen.getByText("Invalid backup code")).toBeInTheDocument();
        });
    });

    it("only accepts numeric input for TOTP code", async () => {
        const user = userEvent.setup();
        renderComponent();

        const input = screen.getByLabelText("Authentication Code") as HTMLInputElement;

        await user.type(input, "abc123def");

        // Should only contain numeric characters
        expect(input.value).toBe("123");
    });

    it("converts backup code to uppercase", async () => {
        const user = userEvent.setup();
        renderComponent();

        // Switch to backup code tab
        const backupTab = screen.getByRole("tab", { name: /backup code/i });
        await user.click(backupTab);

        // Wait for tab content to be visible
        await waitFor(() => {
            expect(screen.getByPlaceholderText("XXXX-XXXX")).toBeInTheDocument();
        });

        const input = screen.getByPlaceholderText("XXXX-XXXX") as HTMLInputElement;

        await user.type(input, "abcd1234");

        expect(input.value).toBe("ABCD1234");
    });
});
