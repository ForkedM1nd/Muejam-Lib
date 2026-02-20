import { ReactNode, useState, useRef, useEffect, useCallback, useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Bell,
  Bookmark,
  Compass,
  Flame,
  Home,
  LibraryBig,
  LogOut,
  Menu,
  MessageCircle,
  Moon,
  PenSquare,
  Search,
  Settings,
  Sun,
  User,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { useAuthContext } from "@/contexts/AuthContext";
import { useTheme } from "@/hooks/useTheme";
import { useDebounce } from "@/hooks/useDebounce";
import { getTotalNewMatches } from "@/lib/savedSearches";
import { useSavedSearchNotifications } from "@/hooks/useSavedSearchNotifications";
import { ConnectionStatus } from "@/components/shared/ConnectionStatus";
import FloatingFooter, { type FooterNavLink } from "@/components/layout/FloatingFooter";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

const NAV_LINKS: FooterNavLink[] = [
  { to: "/", label: "Home", icon: Home },
  { to: "/discover", label: "Discover", icon: Compass },
  { to: "/activity", label: "Activity", icon: Flame },
  { to: "/library", label: "Library", icon: LibraryBig },
  { to: "/write", label: "Write", icon: PenSquare },
  { to: "/whispers", label: "Whispers", icon: MessageCircle },
];

const AUTH_ONLY_LINKS = new Set(["/activity", "/library", "/write"]);

const UTILITY_LINKS = [
  { to: "/about", label: "About" },
  { to: "/community", label: "Community" },
  { to: "/help", label: "Help" },
  { to: "/status", label: "Status" },
  { to: "/legal/terms", label: "Terms" },
];

function isPathActive(pathname: string, to: string) {
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(`${to}/`);
}

function SearchBar() {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const [newMatchesCount, setNewMatchesCount] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useSavedSearchNotifications();

  useEffect(() => {
    const updateCount = () => {
      setNewMatchesCount(getTotalNewMatches());
    };

    updateCount();
    const interval = setInterval(updateCount, 30000);

    return () => clearInterval(interval);
  }, []);

  const debouncedQuery = useDebounce(query, 300);

  const { data: suggestions } = useQuery({
    queryKey: ["search-suggest", debouncedQuery],
    queryFn: () => api.searchSuggest(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 30000,
  });

  type SearchItem =
    | { type: "story"; label: string; slug: string }
    | { type: "author"; label: string; handle: string }
    | { type: "tag"; label: string; slug: string };

  const allItems: SearchItem[] = useMemo(
    () => [
      ...(suggestions?.stories?.map((story) => ({ type: "story" as const, label: story.title, slug: story.slug })) ?? []),
      ...(suggestions?.authors?.map((author) => ({ type: "author" as const, label: author.display_name, handle: author.handle })) ?? []),
      ...(suggestions?.tags?.map((tag) => ({ type: "tag" as const, label: tag.name, slug: tag.slug })) ?? []),
    ],
    [suggestions]
  );

  const submit = useCallback(() => {
    if (selectedIdx >= 0 && selectedIdx < allItems.length) {
      const item = allItems[selectedIdx];
      if (item.type === "story") navigate(`/story/${item.slug}`);
      else if (item.type === "author") navigate(`/u/${item.handle}`);
      else navigate(`/search?q=${encodeURIComponent(item.label)}`);
    } else if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }

    setOpen(false);
    inputRef.current?.blur();
  }, [allItems, navigate, query, selectedIdx]);

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelectedIdx((idx) => Math.min(idx + 1, allItems.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelectedIdx((idx) => Math.max(idx - 1, -1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      submit();
    } else if (event.key === "Escape") {
      setOpen(false);
      inputRef.current?.blur();
    }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
            setSelectedIdx(-1);
          }}
          onFocus={() => query.length >= 2 && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search stories, authors, tags…"
          className="h-9 w-full rounded-full border border-border/80 bg-background/90 pl-9 pr-9 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />

        {newMatchesCount > 0 && (
          <Link
            to="/search"
            className="absolute right-2 top-1/2 -translate-y-1/2"
            title={`${newMatchesCount} new matches in saved searches`}
          >
            <div className="relative">
              <Bookmark className="h-4 w-4 text-muted-foreground transition-colors hover:text-foreground" />
              <Badge
                variant="destructive"
                className="absolute -right-2 -top-2 flex h-4 min-w-4 items-center justify-center px-1 text-[10px]"
              >
                {newMatchesCount > 9 ? "9+" : newMatchesCount}
              </Badge>
            </div>
          </Link>
        )}
      </div>

      {open && allItems.length > 0 && (
        <div className="absolute top-full z-50 mt-2 w-full overflow-hidden rounded-2xl border border-border/80 bg-popover/95 py-1 shadow-2xl backdrop-blur">
          {suggestions?.stories && suggestions.stories.length > 0 && (
            <div className="px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">Stories</div>
          )}

          {suggestions?.stories?.map((story, index) => (
            <button
              key={story.id}
              className={cn(
                "w-full px-3 py-2 text-left text-sm transition-colors hover:bg-accent",
                selectedIdx === index && "bg-accent"
              )}
              onMouseEnter={() => setSelectedIdx(index)}
              onClick={() => {
                navigate(`/story/${story.slug}`);
                setOpen(false);
              }}
            >
              <span className="font-medium">{story.title}</span>
              <span className="ml-2 text-xs text-muted-foreground">by {story.author.display_name}</span>
            </button>
          ))}

          {suggestions?.authors && suggestions.authors.length > 0 && (
            <div className="border-t border-border/70 px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Authors
            </div>
          )}

          {suggestions?.authors?.map((author, index) => {
            const idx = (suggestions?.stories?.length ?? 0) + index;
            return (
              <button
                key={author.id}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm transition-colors hover:bg-accent",
                  selectedIdx === idx && "bg-accent"
                )}
                onMouseEnter={() => setSelectedIdx(idx)}
                onClick={() => {
                  navigate(`/u/${author.handle}`);
                  setOpen(false);
                }}
              >
                {author.display_name} <span className="text-muted-foreground">@{author.handle}</span>
              </button>
            );
          })}

          {suggestions?.tags && suggestions.tags.length > 0 && (
            <div className="border-t border-border/70 px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Tags
            </div>
          )}

          {suggestions?.tags?.map((tag, index) => {
            const idx = (suggestions?.stories?.length ?? 0) + (suggestions?.authors?.length ?? 0) + index;
            return (
              <button
                key={tag.id}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm transition-colors hover:bg-accent",
                  selectedIdx === idx && "bg-accent"
                )}
                onMouseEnter={() => setSelectedIdx(idx)}
                onClick={() => {
                  navigate(`/search?q=${encodeURIComponent(tag.name)}`);
                  setOpen(false);
                }}
              >
                #{tag.name}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function AuthButtons() {
  const { isSignedIn } = useSafeAuth();
  const { signOut } = useAuthContext();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
  };

  if (!CLERK_KEY) {
    return (
      <Button size="sm" variant="outline" disabled>
        Auth not configured
      </Button>
    );
  }

  if (isSignedIn) {
    return (
      <>
        <Button
          variant="ghost"
          size="icon"
          className="rounded-xl"
          onClick={toggleTheme}
          title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>

        <Link to="/notifications">
          <Button variant="ghost" size="icon" className="rounded-xl">
            <Bell className="h-4 w-4" />
          </Button>
        </Link>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-xl">
              <User className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => navigate("/settings/profile")}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </>
    );
  }

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="rounded-xl"
        onClick={toggleTheme}
        title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      >
        {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      </Button>
      <Button size="sm" variant="outline" onClick={() => navigate("/sign-in")}>
        Sign In
      </Button>
      <Button size="sm" onClick={() => navigate("/sign-up")}>
        Sign Up
      </Button>
    </>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { isSignedIn } = useSafeAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const visibleNavLinks = useMemo(
    () => NAV_LINKS.filter((link) => !AUTH_ONLY_LINKS.has(link.to) || isSignedIn),
    [isSignedIn]
  );

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="relative min-h-screen overflow-x-clip bg-background">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[linear-gradient(180deg,hsl(var(--background))_0%,hsl(var(--secondary)/0.9)_24%,hsl(var(--background))_68%)]" />

      <header className="pointer-events-none fixed inset-x-0 top-0 z-50">
        <div className="pointer-events-auto mx-auto mt-3 w-[min(1120px,calc(100%-1rem))] rounded-2xl border border-border bg-background/95 shadow-[0_14px_32px_-24px_hsl(var(--foreground)/0.45)] backdrop-blur">
          <div className="flex h-14 items-center gap-2 px-3 sm:px-4">
            <Link to="/" className="rounded-xl px-2 py-1 text-xl font-semibold tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
              MueJam
            </Link>

            <nav className="hidden items-center gap-1 lg:flex">
              {visibleNavLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    "rounded-xl px-3 py-1.5 text-sm font-medium transition-all",
                    isPathActive(location.pathname, link.to)
                      ? "bg-primary/15 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            <div className="ml-auto hidden items-center gap-2 md:flex">
              <ConnectionStatus />
              <SearchBar />
              <AuthButtons />
            </div>

            <button
              className="ml-auto rounded-xl p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground md:hidden"
              onClick={() => setMobileMenuOpen((open) => !open)}
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="pointer-events-auto mx-auto mt-2 w-[min(1120px,calc(100%-1rem))] rounded-2xl border border-border/70 bg-background/95 p-3 shadow-2xl backdrop-blur-xl md:hidden">
            <div className="mb-3">
              <SearchBar />
            </div>

            <nav className="grid grid-cols-2 gap-2">
              {visibleNavLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                    isPathActive(location.pathname, link.to)
                      ? "bg-primary/15 text-primary"
                      : "bg-accent/40 text-foreground"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            <div className="mt-3 flex items-center gap-2 border-t border-border/70 pt-3">
              <AuthButtons />
            </div>
          </div>
        )}
      </header>

      <main className="relative mx-auto w-full max-w-6xl px-4 pb-44 pt-24 sm:px-6 sm:pt-28 lg:px-10">{children}</main>

      <FloatingFooter navLinks={visibleNavLinks} utilityLinks={UTILITY_LINKS} pathname={location.pathname} />
    </div>
  );
}
