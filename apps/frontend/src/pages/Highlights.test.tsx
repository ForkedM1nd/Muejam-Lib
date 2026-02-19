import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import HighlightsPage from "./Highlights";
import { api } from "@/lib/api";

// Mock the API
vi.mock("@/lib/api", () => ({
    api: {
        getHighlights: vi.fn(),
        deleteHighlight: vi.fn(),
        createWhisper: vi.fn(),
    },
}));

// Mock the auth hook
vi.mock("@/hooks/useSafeAuth", () => ({
    useSafeAuth: () => ({ isSignedIn: true, user: { id: "user1" } }),
}));

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
    toast: vi.fn(),
}));

// Mock reCAPTCHA
vi.mock("@/hooks/useRecaptchaToken", () => ({
    useRecaptchaToken: () => vi.fn().mockResolvedValue("mock-token"),
}));

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => "mock-url");
global.URL.revokeObjectURL = vi.fn();

const mockHighlights = {
    results: [
        {
            id: "h1",
            chapter_id: "ch1",
            user_id: "user1",
            quote_text: "This is a test highlight",
            start_offset: 0,
            end_offset: 24,
            created_at: "2024-01-01T00:00:00Z",
            chapter_title: "Chapter 1",
            story_title: "Test Story",
            story_id: "story1",
        },
        {
            id: "h2",
            chapter_id: "ch2",
            user_id: "user1",
            quote_text: "Another highlight from the same story",
            start_offset: 100,
            end_offset: 138,
            created_at: "2024-01-02T00:00:00Z",
            chapter_title: "Chapter 2",
            story_title: "Test Story",
            story_id: "story1",
        },
    ],
    next_cursor: null,
};

describe("Highlights - Whisper Creation", () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });
        vi.clearAllMocks();
        vi.mocked(api.getHighlights).mockResolvedValue(mockHighlights);
    });

    const renderComponent = () => {
        return render(
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <HighlightsPage />
                </BrowserRouter>
            </QueryClientProvider>
        );
    };

    it("displays create whisper button on highlights", async () => {
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Find all whisper buttons (there should be one per highlight)
        const whisperButtons = screen.getAllByTitle("Create whisper from highlight");
        expect(whisperButtons.length).toBeGreaterThan(0);
    });

    it("opens whisper modal when create whisper button is clicked", async () => {
        const user = userEvent.setup();
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Find and click the first whisper button
        const whisperButtons = screen.getAllByTitle("Create whisper from highlight");
        await user.click(whisperButtons[0]);

        // Check that the modal opened
        await waitFor(() => {
            expect(screen.getByText("Whisper about this highlight")).toBeInTheDocument();
        });

        // Check that the textarea is present (quote is pre-filled in the composer)
        const textarea = screen.getByPlaceholderText("Share your thoughts on this passage…");
        expect(textarea).toBeInTheDocument();
    });

    it("creates a whisper linked to the highlight", async () => {
        const user = userEvent.setup();
        vi.mocked(api.createWhisper).mockResolvedValue({
            id: "w1",
            author: {
                id: "user1",
                handle: "testuser",
                display_name: "Test User",
                avatar_url: null,
            },
            body: "My thoughts on this",
            scope: "HIGHLIGHT",
            highlight_id: "h1",
            quote_text: "This is a test highlight",
            like_count: 0,
            reply_count: 0,
            created_at: "2024-01-01T00:00:00Z",
        });

        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Click the whisper button
        const whisperButtons = screen.getAllByTitle("Create whisper from highlight");
        await user.click(whisperButtons[0]);

        // Wait for modal
        await waitFor(() => {
            expect(screen.getByText("Whisper about this highlight")).toBeInTheDocument();
        });

        // Type in the whisper content
        const textarea = screen.getByPlaceholderText("Share your thoughts on this passage…");
        await user.type(textarea, "My thoughts on this");

        // Submit the whisper
        const postButton = screen.getByRole("button", { name: /post/i });
        await user.click(postButton);

        // Verify the API was called with the correct parameters
        await waitFor(() => {
            expect(api.createWhisper).toHaveBeenCalledWith({
                content: "My thoughts on this",
                scope: "HIGHLIGHT",
                highlight_id: "h1",
            });
        });
    });
});

describe("Highlights - Export Functionality", () => {
    let queryClient: QueryClient;
    let createElementSpy: any;
    let appendChildSpy: any;
    let removeChildSpy: any;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });
        vi.clearAllMocks();
        vi.mocked(api.getHighlights).mockResolvedValue(mockHighlights);

        // Restore any previous spies
        if (createElementSpy) createElementSpy.mockRestore();
        if (appendChildSpy) appendChildSpy.mockRestore();
        if (removeChildSpy) removeChildSpy.mockRestore();
    });

    const renderComponent = () => {
        return render(
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <HighlightsPage />
                </BrowserRouter>
            </QueryClientProvider>
        );
    };

    it("displays export button when highlights exist", async () => {
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Check that export button is present
        const exportButton = screen.getByRole("button", { name: /export/i });
        expect(exportButton).toBeInTheDocument();
    });

    it("does not display export button when no highlights exist", async () => {
        vi.mocked(api.getHighlights).mockResolvedValue({ results: [], next_cursor: null });
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/No highlights yet/)).toBeInTheDocument();
        });

        // Check that export button is not present
        const exportButton = screen.queryByRole("button", { name: /export/i });
        expect(exportButton).not.toBeInTheDocument();
    });

    it("displays format selector with markdown and text options", async () => {
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Find the format selector
        const formatSelector = screen.getByRole("combobox");
        expect(formatSelector).toBeInTheDocument();

        // Check that it has markdown and text options
        const options = Array.from(formatSelector.querySelectorAll("option")).map(
            (opt) => opt.value
        );
        expect(options).toContain("markdown");
        expect(options).toContain("text");
    });

    it("exports highlights as markdown when markdown format is selected", async () => {
        const user = userEvent.setup();

        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Mock document.createElement and appendChild AFTER rendering
        const mockLink = {
            href: "",
            download: "",
            click: vi.fn(),
        };
        createElementSpy = vi.spyOn(document, "createElement").mockReturnValue(mockLink as any);
        appendChildSpy = vi.spyOn(document.body, "appendChild").mockImplementation(() => mockLink as any);
        removeChildSpy = vi.spyOn(document.body, "removeChild").mockImplementation(() => mockLink as any);

        // Select markdown format (should be default)
        const formatSelector = screen.getByRole("combobox");
        expect(formatSelector).toHaveValue("markdown");

        // Click export button
        const exportButton = screen.getByRole("button", { name: /export/i });
        await user.click(exportButton);

        // Verify that a link was created and clicked
        await waitFor(() => {
            expect(mockLink.download).toBe("highlights.md");
            expect(mockLink.click).toHaveBeenCalled();
        });

        // Verify cleanup
        expect(appendChildSpy).toHaveBeenCalled();
        expect(removeChildSpy).toHaveBeenCalled();
        expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    });

    it("exports highlights as text when text format is selected", async () => {
        const user = userEvent.setup();

        renderComponent();

        await waitFor(() => {
            expect(screen.getByText(/This is a test highlight/)).toBeInTheDocument();
        });

        // Mock document.createElement and appendChild AFTER rendering
        const mockLink = {
            href: "",
            download: "",
            click: vi.fn(),
        };
        createElementSpy = vi.spyOn(document, "createElement").mockReturnValue(mockLink as any);
        appendChildSpy = vi.spyOn(document.body, "appendChild").mockImplementation(() => mockLink as any);
        removeChildSpy = vi.spyOn(document.body, "removeChild").mockImplementation(() => mockLink as any);

        // Select text format
        const formatSelector = screen.getByRole("combobox");
        await user.selectOptions(formatSelector, "text");
        expect(formatSelector).toHaveValue("text");

        // Click export button
        const exportButton = screen.getByRole("button", { name: /export/i });
        await user.click(exportButton);

        // Verify that a link was created with .txt extension
        await waitFor(() => {
            expect(mockLink.download).toBe("highlights.txt");
            expect(mockLink.click).toHaveBeenCalled();
        });
    });
});
