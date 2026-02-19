import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ShareButton from "./ShareButton";
import type { ShareOptions } from "@/hooks/useShare";

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
    toast: vi.fn(),
    useToast: () => ({ toast: vi.fn() }),
}));

describe("ShareButton", () => {
    const mockShareOptions: ShareOptions = {
        url: "https://example.com/story/test-story",
        title: "Test Story",
        text: "A test story description",
    };

    beforeEach(() => {
        // Mock window.open
        vi.stubGlobal("open", vi.fn());
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("renders share button", () => {
        render(<ShareButton shareOptions={mockShareOptions} />);
        const button = screen.getByRole("button");
        expect(button).toBeInTheDocument();
    });

    it("opens dropdown menu when clicked", async () => {
        const user = userEvent.setup();
        render(<ShareButton shareOptions={mockShareOptions} />);

        const button = screen.getByRole("button");
        await user.click(button);

        await waitFor(() => {
            expect(screen.getByText("Copy link")).toBeInTheDocument();
        });
    });

    it("shows copy link option in dropdown menu", async () => {
        const user = userEvent.setup();
        render(<ShareButton shareOptions={mockShareOptions} />);

        const button = screen.getByRole("button");
        await user.click(button);

        await waitFor(() => {
            expect(screen.getByText("Copy link")).toBeInTheDocument();
            expect(screen.getByText("Share on Twitter")).toBeInTheDocument();
            expect(screen.getByText("Share on Facebook")).toBeInTheDocument();
            expect(screen.getByText("Share on Reddit")).toBeInTheDocument();
        });
    });

    it("opens Twitter share window when 'Share on Twitter' is clicked", async () => {
        const user = userEvent.setup();
        render(<ShareButton shareOptions={mockShareOptions} />);

        const button = screen.getByRole("button");
        await user.click(button);

        const twitterShare = await screen.findByText("Share on Twitter");
        await user.click(twitterShare);

        await waitFor(() => {
            expect(window.open).toHaveBeenCalledWith(
                expect.stringContaining("twitter.com/intent/tweet"),
                "_blank",
                "noopener,noreferrer"
            );
        });
    });

    it("opens Facebook share window when 'Share on Facebook' is clicked", async () => {
        const user = userEvent.setup();
        render(<ShareButton shareOptions={mockShareOptions} />);

        const button = screen.getByRole("button");
        await user.click(button);

        const facebookShare = await screen.findByText("Share on Facebook");
        await user.click(facebookShare);

        await waitFor(() => {
            expect(window.open).toHaveBeenCalledWith(
                expect.stringContaining("facebook.com/sharer"),
                "_blank",
                "noopener,noreferrer"
            );
        });
    });

    it("opens Reddit share window when 'Share on Reddit' is clicked", async () => {
        const user = userEvent.setup();
        render(<ShareButton shareOptions={mockShareOptions} />);

        const button = screen.getByRole("button");
        await user.click(button);

        const redditShare = await screen.findByText("Share on Reddit");
        await user.click(redditShare);

        await waitFor(() => {
            expect(window.open).toHaveBeenCalledWith(
                expect.stringContaining("reddit.com/submit"),
                "_blank",
                "noopener,noreferrer"
            );
        });
    });

    it("shows native share option when navigator.share is available", async () => {
        // Mock navigator.share
        Object.defineProperty(navigator, "share", {
            value: vi.fn().mockResolvedValue(undefined),
            writable: true,
            configurable: true,
        });

        const user = userEvent.setup();
        render(<ShareButton shareOptions={mockShareOptions} />);

        const button = screen.getByRole("button");
        await user.click(button);

        await waitFor(() => {
            expect(screen.getByText("Share...")).toBeInTheDocument();
        });
    });

    it("renders with icon only when iconOnly prop is true", () => {
        render(<ShareButton shareOptions={mockShareOptions} iconOnly />);
        const button = screen.getByRole("button");
        expect(button).toBeInTheDocument();
        expect(screen.queryByText("Share")).not.toBeInTheDocument();
    });

    it("renders with text when iconOnly prop is false", () => {
        render(<ShareButton shareOptions={mockShareOptions} iconOnly={false} />);
        const button = screen.getByRole("button");
        expect(button).toBeInTheDocument();
        expect(screen.getByText("Share")).toBeInTheDocument();
    });
});
