import { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { usePagination, useInfiniteScroll, flattenPages } from "@/hooks/usePagination";
import { api } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { X, Search, TrendingUp, Sparkles, Star, Award, ArrowRight } from "lucide-react";
import StoryCard from "@/components/shared/StoryCard";
import { StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

interface StoryFeedProps {
  tab: "trending" | "new" | "for-you";
  tag?: string;
  searchQuery?: string;
}

function StoryFeed({ tab, tag, searchQuery }: StoryFeedProps) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    refetch,
  } = usePagination({
    queryKey: ["discover", tab, tag, searchQuery],
    queryFn: ({ pageParam }) =>
      api.getDiscoverFeed({
        tab,
        tag,
        q: searchQuery,
        cursor: pageParam,
        page_size: 20,
      }),
    staleTime: tab === "for-you" ? 5 * 60 * 1000 : 3 * 60 * 1000, // 5 min for personalized, 3 min for others
  });

  const { ref } = useInfiniteScroll({
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    threshold: 500,
  });

  const stories = flattenPages(data);

  // Filter out stories from blocked authors
  const filteredStories = stories.filter((story) => !story.author.is_blocked);

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
        title="Something went wrong"
        description="Could not load stories."
        action={
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        }
      />
    );
  }

  if (filteredStories.length === 0) {
    if (searchQuery) {
      return (
        <EmptyState
          title="No results found"
          description={`No stories found for "${searchQuery}"`}
        />
      );
    }
    if (tag) {
      return (
        <EmptyState
          title="No stories found"
          description={`No stories found with tag "${tag}"`}
        />
      );
    }
    return (
      <EmptyState
        title="No stories yet"
        description="Check back soon for new stories."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStories.map((story) => (
          <StoryCard key={story.id} story={story} />
        ))}
      </div>

      {/* Infinite scroll sentinel */}
      <div ref={ref} className="h-10 flex items-center justify-center">
        {isFetchingNextPage && (
          <div className="text-sm text-muted-foreground">Loading more...</div>
        )}
      </div>

      {!hasNextPage && filteredStories.length > 0 && (
        <div className="text-center text-sm text-muted-foreground py-4">
          You've reached the end
        </div>
      )}
    </div>
  );
}

function ForYouTab({ tag, searchQuery }: { tag?: string; searchQuery?: string }) {
  const { isSignedIn } = useSafeAuth();

  if (!isSignedIn) {
    return (
      <EmptyState
        title="Personalized for you"
        description="Sign in to get story recommendations based on your reading history."
      />
    );
  }

  return <StoryFeed tab="for-you" tag={tag} searchQuery={searchQuery} />;
}

export default function DiscoverPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get("q") || "");

  const currentTab = (searchParams.get("tab") || "trending") as "trending" | "new" | "for-you";
  const currentTag = searchParams.get("tag") || undefined;
  const currentSearch = searchParams.get("q") || undefined;

  const handleTabChange = (tab: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("tab", tab);
    setSearchParams(newParams);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams = new URLSearchParams(searchParams);
    if (searchInput.trim()) {
      newParams.set("q", searchInput.trim());
    } else {
      newParams.delete("q");
    }
    setSearchParams(newParams);
  };

  const clearSearch = () => {
    setSearchInput("");
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("q");
    setSearchParams(newParams);
  };

  const clearTag = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("tag");
    setSearchParams(newParams);
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Discover"
        eyebrow="Reader feed"
        description="A clean feed of trending, fresh, and personalized stories."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/discover/trending">
          <SurfacePanel className="h-full p-4 transition-colors hover:bg-secondary/60">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-semibold">Trending</h3>
                <p className="text-xs text-muted-foreground">What is hot now</p>
              </div>
              <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
            </div>
          </SurfacePanel>
        </Link>

        <Link to="/discover/new">
          <SurfacePanel className="h-full p-4 transition-colors hover:bg-secondary/60">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-semibold">New & Noteworthy</h3>
                <p className="text-xs text-muted-foreground">Fresh stories</p>
              </div>
              <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
            </div>
          </SurfacePanel>
        </Link>

        <Link to="/discover/recommended">
          <SurfacePanel className="h-full p-4 transition-colors hover:bg-secondary/60">
            <div className="flex items-center gap-3">
              <Star className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-semibold">For You</h3>
                <p className="text-xs text-muted-foreground">Personalized</p>
              </div>
              <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
            </div>
          </SurfacePanel>
        </Link>

        <Link to="/discover/staff-picks">
          <SurfacePanel className="h-full p-4 transition-colors hover:bg-secondary/60">
            <div className="flex items-center gap-3">
              <Award className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-semibold">Staff Picks</h3>
                <p className="text-xs text-muted-foreground">Curated by us</p>
              </div>
              <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
            </div>
          </SurfacePanel>
        </Link>
      </div>

      <SurfacePanel className="p-4 sm:p-5">
        <form onSubmit={handleSearch} className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search stories..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="border-border/80 bg-background/80 pl-9 pr-10"
            />
            {searchInput && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </form>

        {(currentTag || currentSearch) && (
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground">Filters:</span>
            {currentTag && (
              <Badge variant="secondary" className="gap-1">
                Tag: {currentTag}
                <button
                  onClick={clearTag}
                  className="ml-1 hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
            {currentSearch && (
              <Badge variant="secondary" className="gap-1">
                Search: {currentSearch}
                <button
                  onClick={clearSearch}
                  className="ml-1 hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
          </div>
        )}
      </SurfacePanel>

      <Tabs value={currentTab} onValueChange={handleTabChange} className="space-y-4">
        <SurfacePanel className="p-1.5">
          <TabsList className="h-auto w-full justify-start rounded-xl bg-transparent p-0">
            <TabsTrigger
              value="trending"
              className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              Trending
            </TabsTrigger>
            <TabsTrigger
              value="new"
              className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              New
            </TabsTrigger>
            <TabsTrigger
              value="for-you"
              className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              For You
            </TabsTrigger>
          </TabsList>
        </SurfacePanel>

        <TabsContent value="trending" className="mt-0">
          <SurfacePanel className="p-4 sm:p-5">
            <StoryFeed tab="trending" tag={currentTag} searchQuery={currentSearch} />
          </SurfacePanel>
        </TabsContent>

        <TabsContent value="new" className="mt-0">
          <SurfacePanel className="p-4 sm:p-5">
            <StoryFeed tab="new" tag={currentTag} searchQuery={currentSearch} />
          </SurfacePanel>
        </TabsContent>

        <TabsContent value="for-you" className="mt-0">
          <SurfacePanel className="p-4 sm:p-5">
            <ForYouTab tag={currentTag} searchQuery={currentSearch} />
          </SurfacePanel>
        </TabsContent>
      </Tabs>
    </div>
  );
}
