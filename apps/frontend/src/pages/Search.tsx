import { useSearchParams, useNavigate } from "react-router-dom";
import { usePagination, useInfiniteScroll, flattenPages } from "@/hooks/usePagination";
import { api } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import StoryCard from "@/components/shared/StoryCard";
import { StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Link } from "react-router-dom";
import { Filter, X, Clock, Trash2, Bookmark, BookmarkCheck } from "lucide-react";
import type { Story, UserProfile } from "@/types";
import { useState, useEffect } from "react";
import { highlightText } from "@/lib/highlightText";
import {
  getSearchHistory,
  addToSearchHistory,
  removeFromSearchHistory,
  clearSearchHistory,
  type SearchHistoryItem,
} from "@/lib/searchHistory";
import {
  getSavedSearches,
  saveSearch,
  removeSavedSearch,
  type SavedSearch,
} from "@/lib/savedSearches";
import { SavedSearches } from "@/components/shared/SavedSearches";
import { useToast } from "@/hooks/use-toast";

// Available genres for filtering
const GENRES = [
  "Fantasy",
  "Science Fiction",
  "Romance",
  "Mystery",
  "Thriller",
  "Horror",
  "Adventure",
  "Historical",
  "Contemporary",
  "Young Adult",
  "Poetry",
  "Non-Fiction",
];

// Story status options
const STATUS_OPTIONS = [
  { value: "published", label: "Published" },
  { value: "draft", label: "Draft" },
  { value: "completed", label: "Completed" },
  { value: "ongoing", label: "Ongoing" },
];

// Sorting options
const SORT_OPTIONS = [
  { value: "relevance", label: "Relevance" },
  { value: "date", label: "Date" },
  { value: "popularity", label: "Popularity" },
  { value: "rating", label: "Rating" },
];

interface SearchFilters {
  genres: string[];
  tags: string[];
  status: string[];
  minWordCount?: number;
  maxWordCount?: number;
  sort: string;
}

interface FilterPanelProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  onClearFilters: () => void;
}

function FilterPanel({ filters, onFiltersChange, onClearFilters }: FilterPanelProps) {
  const [wordCountRange, setWordCountRange] = useState<[number, number]>([
    filters.minWordCount || 0,
    filters.maxWordCount || 500000,
  ]);

  const handleGenreToggle = (genre: string) => {
    const newGenres = filters.genres.includes(genre)
      ? filters.genres.filter((g) => g !== genre)
      : [...filters.genres, genre];
    onFiltersChange({ ...filters, genres: newGenres });
  };

  const handleStatusToggle = (status: string) => {
    const newStatus = filters.status.includes(status)
      ? filters.status.filter((s) => s !== status)
      : [...filters.status, status];
    onFiltersChange({ ...filters, status: newStatus });
  };

  const handleWordCountChange = (value: number[]) => {
    setWordCountRange([value[0], value[1]]);
  };

  const handleWordCountCommit = () => {
    onFiltersChange({
      ...filters,
      minWordCount: wordCountRange[0] > 0 ? wordCountRange[0] : undefined,
      maxWordCount: wordCountRange[1] < 500000 ? wordCountRange[1] : undefined,
    });
  };

  const hasActiveFilters =
    filters.genres.length > 0 ||
    filters.status.length > 0 ||
    filters.minWordCount !== undefined ||
    filters.maxWordCount !== undefined;

  return (
    <div className="space-y-6">
      {/* Clear Filters */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Active Filters</span>
          <Button variant="ghost" size="sm" onClick={onClearFilters}>
            <X className="h-4 w-4 mr-1" />
            Clear All
          </Button>
        </div>
      )}

      {/* Sort */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Sort By</Label>
        <Select
          value={filters.sort}
          onValueChange={(value) => onFiltersChange({ ...filters, sort: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Separator />

      {/* Genres */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Genres</Label>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {GENRES.map((genre) => (
            <div key={genre} className="flex items-center space-x-2">
              <Checkbox
                id={`genre-${genre}`}
                checked={filters.genres.includes(genre)}
                onCheckedChange={() => handleGenreToggle(genre)}
              />
              <label
                htmlFor={`genre-${genre}`}
                className="text-sm cursor-pointer flex-1"
              >
                {genre}
              </label>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Status */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Status</Label>
        <div className="space-y-2">
          {STATUS_OPTIONS.map((option) => (
            <div key={option.value} className="flex items-center space-x-2">
              <Checkbox
                id={`status-${option.value}`}
                checked={filters.status.includes(option.value)}
                onCheckedChange={() => handleStatusToggle(option.value)}
              />
              <label
                htmlFor={`status-${option.value}`}
                className="text-sm cursor-pointer flex-1"
              >
                {option.label}
              </label>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Word Count */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Word Count</Label>
        <div className="space-y-4">
          <Slider
            min={0}
            max={500000}
            step={1000}
            value={wordCountRange}
            onValueChange={handleWordCountChange}
            onValueCommit={handleWordCountCommit}
            className="w-full"
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{wordCountRange[0].toLocaleString()}</span>
            <span>{wordCountRange[1].toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function SearchResults({ q, type, filters }: { q: string; type: string; filters: SearchFilters }) {
  // Build search params with filters
  const searchParams: any = {
    q,
    type,
    sort: filters.sort,
  };

  // Add genre filter (comma-separated)
  if (filters.genres.length > 0) {
    searchParams.genre = filters.genres.join(",");
  }

  // Add status filter (comma-separated)
  if (filters.status.length > 0) {
    searchParams.status = filters.status.join(",");
  }

  // Add word count filters
  if (filters.minWordCount !== undefined) {
    searchParams.min_word_count = filters.minWordCount;
  }
  if (filters.maxWordCount !== undefined) {
    searchParams.max_word_count = filters.maxWordCount;
  }

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    refetch,
  } = usePagination({
    queryKey: ["search", q, type, filters],
    queryFn: ({ pageParam }) => api.search({ ...searchParams, cursor: pageParam, page_size: 20 }),
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

  // Filter out blocked users
  const filteredUsers = users.filter((user) => !user.is_blocked);

  // Filter out stories from blocked authors
  const filteredStories = stories.filter((story) => !story.author.is_blocked);

  return (
    <div className="space-y-6">
      {/* Stories */}
      {filteredStories.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Stories ({filteredStories.length})
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredStories.map((story) => (
              <div key={story.id}>
                <StoryCard story={story} />
                {/* Highlight matching terms in title and description */}
                <div className="mt-2 px-2">
                  <h3 className="text-sm font-medium line-clamp-2">
                    {highlightText(story.title, q)}
                  </h3>
                  {story.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {highlightText(story.description, q)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Authors */}
      {filteredUsers.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Authors ({filteredUsers.length})
          </h2>
          <div className="space-y-2">
            {filteredUsers.map((user) => (
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
                  <p className="text-sm font-medium">
                    {highlightText(user.display_name, q)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    @{highlightText(user.handle, q)}
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
  const navigate = useNavigate();
  const { toast } = useToast();
  const q = searchParams.get("q") ?? "";
  const currentType = searchParams.get("type") || "all";

  // Initialize filters state
  const [filters, setFilters] = useState<SearchFilters>({
    genres: [],
    tags: [],
    status: [],
    sort: "relevance",
  });

  // Search history state
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);

  // Saved searches state
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [isSearchSaved, setIsSearchSaved] = useState(false);

  // Load search history and saved searches on mount
  useEffect(() => {
    setSearchHistory(getSearchHistory());
    setSavedSearches(getSavedSearches());
  }, []);

  // Check if current search is saved
  useEffect(() => {
    if (q.trim()) {
      const saved = getSavedSearches();
      const exists = saved.some(
        (s) => s.query === q && JSON.stringify(s.filters) === JSON.stringify({
          type: currentType !== "all" ? currentType : undefined,
          genres: filters.genres,
          tags: filters.tags,
          status: filters.status,
          minWordCount: filters.minWordCount,
          maxWordCount: filters.maxWordCount,
          sort: filters.sort !== "relevance" ? filters.sort : undefined,
        })
      );
      setIsSearchSaved(exists);
    }
  }, [q, currentType, filters]);

  // Add current query to history when it changes
  useEffect(() => {
    if (q.trim()) {
      addToSearchHistory(q);
      setSearchHistory(getSearchHistory());
    }
  }, [q]);

  const handleClearFilters = () => {
    setFilters({
      genres: [],
      tags: [],
      status: [],
      sort: "relevance",
    });
  };

  const handleClearHistory = () => {
    clearSearchHistory();
    setSearchHistory([]);
  };

  const handleRemoveHistoryItem = (query: string) => {
    removeFromSearchHistory(query);
    setSearchHistory(getSearchHistory());
  };

  const handleHistoryItemClick = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  const handleSaveSearch = () => {
    if (!q.trim()) return;

    try {
      const searchFilters: SavedSearch["filters"] = {
        type: currentType !== "all" ? currentType : undefined,
        genres: filters.genres.length > 0 ? filters.genres : undefined,
        tags: filters.tags.length > 0 ? filters.tags : undefined,
        status: filters.status.length > 0 ? filters.status : undefined,
        minWordCount: filters.minWordCount,
        maxWordCount: filters.maxWordCount,
        sort: filters.sort !== "relevance" ? filters.sort : undefined,
      };

      saveSearch(q, searchFilters);
      setSavedSearches(getSavedSearches());
      setIsSearchSaved(true);

      toast({
        title: "Search saved",
        description: "You'll be notified when new matches are found.",
      });
    } catch (error) {
      toast({
        title: "Failed to save search",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    }
  };

  const handleUnsaveSearch = () => {
    if (!q.trim()) return;

    const saved = getSavedSearches();
    const searchToRemove = saved.find(
      (s) => s.query === q && JSON.stringify(s.filters) === JSON.stringify({
        type: currentType !== "all" ? currentType : undefined,
        genres: filters.genres,
        tags: filters.tags,
        status: filters.status,
        minWordCount: filters.minWordCount,
        maxWordCount: filters.maxWordCount,
        sort: filters.sort !== "relevance" ? filters.sort : undefined,
      })
    );

    if (searchToRemove) {
      removeSavedSearch(searchToRemove.id);
      setSavedSearches(getSavedSearches());
      setIsSearchSaved(false);

      toast({
        title: "Search removed",
        description: "This search has been removed from your saved searches.",
      });
    }
  };

  const handleSavedSearchSelect = (search: SavedSearch) => {
    // Navigate to search with saved filters
    const params = new URLSearchParams();
    params.set("q", search.query);

    if (search.filters.type) {
      params.set("type", search.filters.type);
    }

    navigate(`/search?${params.toString()}`);

    // Apply saved filters
    setFilters({
      genres: search.filters.genres || [],
      tags: search.filters.tags || [],
      status: search.filters.status || [],
      minWordCount: search.filters.minWordCount,
      maxWordCount: search.filters.maxWordCount,
      sort: search.filters.sort || "relevance",
    });
  };

  if (!q) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1
          className="text-2xl font-semibold mb-6"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Search
        </h1>

        {/* Saved Searches */}
        <div className="mb-8">
          <SavedSearches onSearchSelect={handleSavedSearchSelect} />
        </div>

        {/* Search History */}
        {searchHistory.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium flex items-center gap-2">
                <Clock className="h-5 w-5 text-muted-foreground" />
                Recent Searches
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearHistory}
                className="text-muted-foreground hover:text-foreground"
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Clear History
              </Button>
            </div>

            <div className="space-y-2">
              {searchHistory.map((item) => (
                <div
                  key={item.timestamp}
                  className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors group"
                >
                  <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <button
                    onClick={() => handleHistoryItemClick(item.query)}
                    className="flex-1 text-left text-sm hover:underline"
                  >
                    {item.query}
                  </button>
                  <button
                    onClick={() => handleRemoveHistoryItem(item.query)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-destructive/10 rounded"
                    aria-label="Remove from history"
                  >
                    <X className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <EmptyState
            title="Start searching"
            description="Type something in the search bar above to find stories, authors, and tags."
          />
        )}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1
            className="text-2xl font-semibold"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Search Results
          </h1>
          <Button
            variant={isSearchSaved ? "secondary" : "outline"}
            size="sm"
            onClick={isSearchSaved ? handleUnsaveSearch : handleSaveSearch}
          >
            {isSearchSaved ? (
              <>
                <BookmarkCheck className="h-4 w-4 mr-2" />
                Saved
              </>
            ) : (
              <>
                <Bookmark className="h-4 w-4 mr-2" />
                Save Search
              </>
            )}
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">for</span>
          <Badge variant="secondary" className="text-base">
            {q}
          </Badge>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Desktop Filter Panel */}
        <aside className="hidden lg:block w-64 flex-shrink-0">
          <div className="sticky top-4 space-y-4">
            <h2 className="text-lg font-semibold">Filters</h2>
            <FilterPanel
              filters={filters}
              onFiltersChange={setFilters}
              onClearFilters={handleClearFilters}
            />
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          {/* Mobile Filter Button */}
          <div className="lg:hidden mb-4">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="w-full">
                  <Filter className="h-4 w-4 mr-2" />
                  Filters & Sort
                  {(filters.genres.length > 0 ||
                    filters.status.length > 0 ||
                    filters.minWordCount !== undefined ||
                    filters.maxWordCount !== undefined) && (
                      <Badge variant="secondary" className="ml-2">
                        {filters.genres.length +
                          filters.status.length +
                          (filters.minWordCount !== undefined ? 1 : 0) +
                          (filters.maxWordCount !== undefined ? 1 : 0)}
                      </Badge>
                    )}
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 overflow-y-auto">
                <SheetHeader>
                  <SheetTitle>Filters</SheetTitle>
                </SheetHeader>
                <div className="mt-6">
                  <FilterPanel
                    filters={filters}
                    onFiltersChange={setFilters}
                    onClearFilters={handleClearFilters}
                  />
                </div>
              </SheetContent>
            </Sheet>
          </div>

          <Tabs
            value={currentType}
            onValueChange={(value) => {
              const newParams = new URLSearchParams(searchParams);
              newParams.set("type", value);
              window.history.pushState({}, "", `?${newParams.toString()}`);
            }}
          >
            <TabsList className="mb-6">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="stories">Stories</TabsTrigger>
              <TabsTrigger value="users">Authors</TabsTrigger>
              <TabsTrigger value="whispers">Whispers</TabsTrigger>
            </TabsList>

            <TabsContent value="all">
              <SearchResults q={q} type="all" filters={filters} />
            </TabsContent>

            <TabsContent value="stories">
              <SearchResults q={q} type="stories" filters={filters} />
            </TabsContent>

            <TabsContent value="users">
              <SearchResults q={q} type="users" filters={filters} />
            </TabsContent>

            <TabsContent value="whispers">
              <SearchResults q={q} type="whispers" filters={filters} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
