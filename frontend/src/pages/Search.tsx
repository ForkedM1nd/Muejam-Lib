import { useSearchParams } from "react-router-dom";
import { usePagination, useInfiniteScroll, flattenPages } from "@/hooks/usePagination";
import { api } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import StoryCard from "@/components/shared/StoryCard";
import { StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Link } from "react-router-dom";
import type { Story, UserProfile } from "@/types";

function SearchResults({ q, type }: { q: string; type: string }) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    refetch,
  } = usePagination({
    queryKey: ["search", q, type],
    queryFn: ({ pageParam }) => api.search({ q, type, cursor: pageParam, page_size: 20 }),
    enabled: !!q,
    staleTime: 30_000, // 30 seconds
  });

  const { ref } = useInfiniteScroll({
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    threshold: 500,
  });

  const results = flattenPages(data);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <StoryCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="Search failed"
        description="Something went wrong while searching."
        action={
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        }
      />
    );
  }

  if (results.length === 0) {
    return (
      <EmptyState
        title="No results"
        description={`Nothing found for "${q}".`}
      />
    );
  }

  // Type guard: if result has 'slug' it's a story, if 'handle' it's a user
  const stories = results.filter(
    (r): r is Story => "slug" in r && "chapter_count" in r
  );
  const users = results.filter(
    (r): r is UserProfile => "handle" in r && !("slug" in r)
  );

  return (
    <div className="space-y-6">
      {/* Stories */}
      {stories.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Stories ({stories.length})
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {stories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        </div>
      )}

      {/* Authors */}
      {users.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Authors ({users.length})
          </h2>
          <div className="space-y-2">
            {users.map((user) => (
              <Link
                key={user.id}
                to={`/u/${user.handle}`}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors"
              >
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-sm font-medium">
                    {user.display_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium">{user.display_name}</p>
                  <p className="text-xs text-muted-foreground">
                    @{user.handle}
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{user.follower_count} followers</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Infinite scroll sentinel */}
      <div ref={ref} className="h-10 flex items-center justify-center">
        {isFetchingNextPage && (
          <div className="text-sm text-muted-foreground">Loading more...</div>
        )}
      </div>

      {!hasNextPage && results.length > 0 && (
        <div className="text-center text-sm text-muted-foreground py-4">
          You've reached the end
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const currentType = searchParams.get("type") || "all";

  if (!q) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1
          className="text-2xl font-semibold mb-6"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Search
        </h1>
        <EmptyState
          title="Start searching"
          description="Type something in the search bar above to find stories, authors, and tags."
        />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1
          className="text-2xl font-semibold mb-2"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Search Results
        </h1>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">for</span>
          <Badge variant="secondary" className="text-base">
            {q}
          </Badge>
        </div>
      </div>

      <Tabs value={currentType} onValueChange={(value) => {
        const newParams = new URLSearchParams(searchParams);
        newParams.set("type", value);
        window.history.pushState({}, "", `?${newParams.toString()}`);
      }}>
        <TabsList className="mb-6">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="stories">Stories</TabsTrigger>
          <TabsTrigger value="users">Authors</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <SearchResults q={q} type="all" />
        </TabsContent>

        <TabsContent value="stories">
          <SearchResults q={q} type="stories" />
        </TabsContent>

        <TabsContent value="users">
          <SearchResults q={q} type="users" />
        </TabsContent>
      </Tabs>
    </div>
  );
}
