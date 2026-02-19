import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import ProfilePage from "./Profile";
import { api } from "@/lib/api";

// Mock the API
vi.mock("@/lib/api", () => ({
    api: {
        getProfile: vi.fn(),
        getMe: vi.fn(),
        getStories: vi.fn(),
        getWhispers: vi.fn(),
        getFollowers: vi.fn(),
        getFollowing: vi.fn(),
        followUser: vi.fn(),
        unfollowUser: vi.fn(),
        blockUser: vi.fn(),
        unblockUser: vi.fn(),
    },
}));

// Mock the auth hook
vi.mock("@/hooks/useSafeAuth", () => ({
    useSafeAuth: () => ({ isSignedIn: true, user: { id: "user1" } }),
}));

// Mock toast
vi.mock("@/hooks/use-toast", () => ({
    toast: vi.fn(),
    useToast: () => ({ toast: vi.fn() }),
}));

const mockProfile = {
    id: "user2",
    handle: "testauthor",
    display_name: "Test Author",
    avatar_url: "https://example.com/avatar.jpg",
    bio: "A test author bio",
    follower_count: 150,
    following_count: 75,
    is_following: false,
    is_blocked: false,
    created_at: "2024-01-01T00:00:00Z",
};

const mockCurrentUser = {
    id: "user1",
    handle: "currentuser",
    display_name: "Current User",
    follower_count: 50,
    following_count: 100,
    created_at: "2024-01-01T00:00:00Z",
};

const mockStories = {
    results: [
        {
            id: "story1",
            slug: "test-story",
            title: "Test Story",
            blurb: "A test story",
            author: {
                id: "user2",
                handle: "testauthor",
                display_name: "Test Author",
            },
            tags: [],
            chapter_count: 5,
            status: "published" as const,
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T00:00:00Z",
        },
    ],
    next_cursor: null,
};

const mockMutualFollowers = {
    results: [
        {
            id: "user3",
            handle: "mutualfriend",
            display_name: "Mutual Friend",
            follower_count: 200,
            following_count: 150,
            created_at: "2024-01-01T00:00:00Z",
        },
    ],
    next_cursor: null,
};

describe("Profile - Enhanced Social Features", () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });
        vi.clearAllMocks();

        // Setup default mocks
        vi.mocked(api.getProfile).mockResolvedValue(mockProfile);
        vi.mocked(api.getMe).mockResolvedValue(mockCurrentUser);
        vi.mocked(api.getStories).mockResolvedValue(mockStories);
        vi.mocked(api.getFollowers).mockResolvedValue(mockMutualFollowers);
        vi.mocked(api.getFollowing).mockResolvedValue(mockMutualFollowers);

        // Mock fetch for statistics
        global.fetch = vi.fn((url) => {
            if (url.includes("/statistics/")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        total_stories: 3,
                        total_chapters: 15,
                        total_whispers: 42,
                        follower_count: 150,
                        total_likes_received: 500,
                    }),
                });
            }
            return Promise.resolve({
                ok: false,
                json: () => Promise.resolve(null),
            });
        }) as any;
    });

    const renderComponent = (handle = "testauthor") => {
        return render(
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <Routes>
                        <Route path="/u/:handle" element={<ProfilePage />} />
                    </Routes>
                </BrowserRouter>
            </QueryClientProvider>,
            { wrapper: ({ children }) => <div>{children}</div> }
        );
    };

    it("displays user stats including followers, following, stories, and whispers", async () => {
        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Check that all stats are displayed
        expect(screen.getByText("150")).toBeInTheDocument(); // Followers
        expect(screen.getByText("75")).toBeInTheDocument(); // Following
        expect(screen.getByText("3")).toBeInTheDocument(); // Stories
        expect(screen.getByText("42")).toBeInTheDocument(); // Whispers

        expect(screen.getByText("Followers")).toBeInTheDocument();
        expect(screen.getByText("Following")).toBeInTheDocument();
        expect(screen.getByText("Stories")).toBeInTheDocument();
        expect(screen.getByText("Whispers")).toBeInTheDocument();
    });

    it("displays follow button for other users", async () => {
        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Check that follow button is present
        const followButton = screen.getByRole("button", { name: /follow/i });
        expect(followButton).toBeInTheDocument();
    });

    it("displays unfollow button when already following", async () => {
        vi.mocked(api.getProfile).mockResolvedValue({
            ...mockProfile,
            is_following: true,
        });

        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Check that unfollow button is present
        const unfollowButton = screen.getByRole("button", { name: /unfollow/i });
        expect(unfollowButton).toBeInTheDocument();
    });

    it("calls followUser API when follow button is clicked", async () => {
        const user = userEvent.setup();
        vi.mocked(api.followUser).mockResolvedValue(undefined);

        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Click follow button
        const followButton = screen.getByRole("button", { name: /follow/i });
        await user.click(followButton);

        // Verify API was called
        await waitFor(() => {
            expect(api.followUser).toHaveBeenCalledWith("user2");
        });
    });

    it("displays block/unblock button", async () => {
        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Check that block button is present
        const blockButton = screen.getByRole("button", { name: /block/i });
        expect(blockButton).toBeInTheDocument();

        // Note: The block confirmation dialog is tested separately in integration tests
        // as it requires portal rendering which is complex to test in unit tests
    });

    it("displays social proof with mutual followers", async () => {
        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Wait for mutual followers to load
        await waitFor(() => {
            expect(screen.getByText(/Followed by/)).toBeInTheDocument();
            expect(screen.getByText("Mutual Friend")).toBeInTheDocument();
        });
    });

    it("makes followers and following stats clickable links", async () => {
        window.history.pushState({}, "", "/u/testauthor");
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole("heading", { name: "Test Author" })).toBeInTheDocument();
        });

        // Find the links by checking parent elements
        const followersCard = screen.getByText("Followers").closest("a");
        const followingCard = screen.getByText("Following").closest("a");

        expect(followersCard).toHaveAttribute("href", "/users/testauthor/followers");
        expect(followingCard).toHaveAttribute("href", "/users/testauthor/following");
    });

    it("displays edit profile button for own profile", async () => {
        const ownProfile = {
            ...mockProfile,
            id: "user1",
            handle: "currentuser",
            display_name: "Current User",
        };

        vi.mocked(api.getProfile).mockResolvedValue(ownProfile);

        window.history.pushState({}, "", "/u/currentuser");
        renderComponent("currentuser");

        await waitFor(() => {
            expect(screen.getByText("@currentuser")).toBeInTheDocument();
        });

        // Check that edit profile button is present instead of follow/block
        const editButton = screen.getByRole("button", { name: /edit profile/i });
        expect(editButton).toBeInTheDocument();

        // Follow and block buttons should not be present
        expect(screen.queryByRole("button", { name: /follow/i })).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: /block/i })).not.toBeInTheDocument();
    });
});
