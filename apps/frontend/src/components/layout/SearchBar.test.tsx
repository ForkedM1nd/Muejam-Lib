import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { api } from "@/lib/api";
import AppShell from "./AppShell";

// Mock the API
vi.mock("@/lib/api", () => ({
    api: {
        searchSuggest: vi.fn(),
    },
}));

// Mock Clerk
vi.mock("@clerk/clerk-react", () => ({
    UserButton: () => <div>UserButton</div>,
    useAuth: () => ({ isSignedIn: false, isLoaded: true }),
}));

// Mock contexts
vi.mock("@/hooks/useSafeAuth", () => ({
    useSafeAuth: () => ({ isSignedIn: false, isLoaded: true }),
}));

vi.mock("@/contexts/AuthContext", () => ({
    useAuthContext: () => ({
        signOut: vi.fn(),
    }),
}));

vi.mock("@/hooks/useTheme", () => ({
    useTheme: () => ({
        theme: "light",
        toggleTheme: vi.fn(),
    }),
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });

    return ({ children }: { children: React.ReactNode }) => (
        <BrowserRouter>
            <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        </BrowserRouter>
    );
};

describe("SearchBar", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should render search input", () => {
        render(<AppShell>Test Content</AppShell>, { wrapper: createWrapper() });

        const searchInput = screen.getByPlaceholderText(/search stories, authors, tags/i);
        expect(searchInput).toBeInTheDocument();
    });

    it("should debounce search input and fetch suggestions", async () => {
        const mockSuggestions = {
            stories: [
                {
                    id: "1",
                    slug: "test-story",
                    title: "Test Story",
                    cover_url: null,
                    author: { id: "1", display_name: "Test Author", handle: "testauthor" },
                },
            ],
            authors: [
                {
                    id: "2",
                    handle: "author2",
                    display_name: "Author Two",
                    avatar_url: null,
                },
            ],
            tags: [
                {
                    id: "3",
                    name: "fantasy",
                    slug: "fantasy",
                    story_count: 10,
                },
            ],
        };

        vi.mocked(api.searchSuggest).mockResolvedValue(mockSuggestions);

        render(<AppShell>Test Content</AppShell>, { wrapper: createWrapper() });

        const searchInput = screen.getByPlaceholderText(/search stories, authors, tags/i);

        // Type in the search input
        fireEvent.change(searchInput, { target: { value: "te" } });

        // API should not be called immediately (debounced)
        expect(api.searchSuggest).not.toHaveBeenCalled();

        // Wait for debounce delay (300ms)
        await waitFor(
            () => {
                expect(api.searchSuggest).toHaveBeenCalledWith("te");
            },
            { timeout: 500 }
        );
    });

    it("should display suggestions when query is at least 2 characters", async () => {
        const mockSuggestions = {
            stories: [
                {
                    id: "1",
                    slug: "test-story",
                    title: "Test Story",
                    cover_url: null,
                    author: { id: "1", display_name: "Test Author", handle: "testauthor" },
                },
            ],
            authors: [],
            tags: [],
        };

        vi.mocked(api.searchSuggest).mockResolvedValue(mockSuggestions);

        render(<AppShell>Test Content</AppShell>, { wrapper: createWrapper() });

        const searchInput = screen.getByPlaceholderText(/search stories, authors, tags/i);

        // Type in the search input
        fireEvent.change(searchInput, { target: { value: "test" } });

        // Wait for suggestions to appear
        await waitFor(
            () => {
                expect(screen.getByText("Test Story")).toBeInTheDocument();
            },
            { timeout: 500 }
        );
    });

    it("should not fetch suggestions for queries shorter than 2 characters", async () => {
        render(<AppShell>Test Content</AppShell>, { wrapper: createWrapper() });

        const searchInput = screen.getByPlaceholderText(/search stories, authors, tags/i);

        // Type a single character
        fireEvent.change(searchInput, { target: { value: "t" } });

        // Wait to ensure API is not called
        await new Promise((resolve) => setTimeout(resolve, 400));

        expect(api.searchSuggest).not.toHaveBeenCalled();
    });

    it("should group suggestions by type (stories, authors, tags)", async () => {
        const mockSuggestions = {
            stories: [
                {
                    id: "1",
                    slug: "test-story",
                    title: "Test Story",
                    cover_url: null,
                    author: { id: "1", display_name: "Test Author", handle: "testauthor" },
                },
            ],
            authors: [
                {
                    id: "2",
                    handle: "author2",
                    display_name: "Author Two",
                    avatar_url: null,
                },
            ],
            tags: [
                {
                    id: "3",
                    name: "fantasy",
                    slug: "fantasy",
                    story_count: 10,
                },
            ],
        };

        vi.mocked(api.searchSuggest).mockResolvedValue(mockSuggestions);

        render(<AppShell>Test Content</AppShell>, { wrapper: createWrapper() });

        const searchInput = screen.getByPlaceholderText(/search stories, authors, tags/i);

        fireEvent.change(searchInput, { target: { value: "test" } });

        // Wait for suggestions to appear
        await waitFor(
            () => {
                expect(screen.getByText("Stories")).toBeInTheDocument();
                expect(screen.getByText("Authors")).toBeInTheDocument();
                expect(screen.getByText("Tags")).toBeInTheDocument();
            },
            { timeout: 500 }
        );
    });

    it("should cancel previous API call on rapid input changes", async () => {
        const mockSuggestions = {
            stories: [],
            authors: [],
            tags: [],
        };

        vi.mocked(api.searchSuggest).mockResolvedValue(mockSuggestions);

        render(<AppShell>Test Content</AppShell>, { wrapper: createWrapper() });

        const searchInput = screen.getByPlaceholderText(/search stories, authors, tags/i);

        // Rapidly change input
        fireEvent.change(searchInput, { target: { value: "te" } });
        fireEvent.change(searchInput, { target: { value: "tes" } });
        fireEvent.change(searchInput, { target: { value: "test" } });

        // Wait for debounce
        await waitFor(
            () => {
                // Should only call API once with the final value
                expect(api.searchSuggest).toHaveBeenCalledTimes(1);
                expect(api.searchSuggest).toHaveBeenCalledWith("test");
            },
            { timeout: 500 }
        );
    });
});
