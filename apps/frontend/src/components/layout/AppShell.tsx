import { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { UserButton } from "@clerk/clerk-react";
import { Search, Menu, X, Bell, Moon, Sun } from "lucide-react";
import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { useTheme } from "@/hooks/useTheme";

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";

const NAV_LINKS = [
  { to: "/discover", label: "Discover" },
  { to: "/library", label: "Library", auth: true },
  { to: "/write", label: "Write", auth: true },
  { to: "/whispers", label: "Whispers" },
];

function SearchBar() {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: suggestions } = useQuery({
    queryKey: ["search-suggest", query],
    queryFn: () => api.searchSuggest(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  });

  const allItems = [
    ...(suggestions?.stories?.map((s) => ({ type: "story" as const, label: s.title, slug: s.slug })) ?? []),
    ...(suggestions?.authors?.map((a) => ({ type: "author" as const, label: a.display_name, handle: a.handle })) ?? []),
    ...(suggestions?.tags?.map((t) => ({ type: "tag" as const, label: t.name, slug: t.slug })) ?? []),
  ];

  const submit = useCallback(() => {
    if (selectedIdx >= 0 && selectedIdx < allItems.length) {
      const item = allItems[selectedIdx];
      if (item.type === "story") navigate(`/story/${item.slug}`);
      else if (item.type === "author") navigate(`/u/${(item as any).handle}`);
      else navigate(`/search?q=${encodeURIComponent(item.label)}`);
    } else if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
    setOpen(false);
    inputRef.current?.blur();
  }, [query, selectedIdx, allItems, navigate]);

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSelectedIdx((i) => Math.min(i + 1, allItems.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSelectedIdx((i) => Math.max(i - 1, -1)); }
    else if (e.key === "Enter") { e.preventDefault(); submit(); }
    else if (e.key === "Escape") { setOpen(false); inputRef.current?.blur(); }
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); setSelectedIdx(-1); }}
          onFocus={() => query.length >= 2 && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search stories, authors, tags…"
          className="w-full h-9 pl-9 pr-3 rounded-full border border-input bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      {open && allItems.length > 0 && (
        <div className="absolute top-full mt-1 w-full bg-popover border border-border rounded-lg shadow-lg z-50 py-1 overflow-hidden">
          {suggestions?.stories && suggestions.stories.length > 0 && (
            <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">Stories</div>
          )}
          {suggestions?.stories?.map((s, i) => (
            <button
              key={s.id}
              className={cn("w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors", selectedIdx === i && "bg-accent")}
              onMouseEnter={() => setSelectedIdx(i)}
              onClick={() => { navigate(`/story/${s.slug}`); setOpen(false); }}
            >
              <span className="font-medium">{s.title}</span>
              <span className="text-muted-foreground ml-2 text-xs">by {s.author.display_name}</span>
            </button>
          ))}
          {suggestions?.authors && suggestions.authors.length > 0 && (
            <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider border-t border-border">Authors</div>
          )}
          {suggestions?.authors?.map((a, i) => {
            const idx = (suggestions?.stories?.length ?? 0) + i;
            return (
              <button
                key={a.id}
                className={cn("w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors", selectedIdx === idx && "bg-accent")}
                onMouseEnter={() => setSelectedIdx(idx)}
                onClick={() => { navigate(`/u/${a.handle}`); setOpen(false); }}
              >
                {a.display_name} <span className="text-muted-foreground">@{a.handle}</span>
              </button>
            );
          })}
          {suggestions?.tags && suggestions.tags.length > 0 && (
            <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider border-t border-border">Tags</div>
          )}
          {suggestions?.tags?.map((t, i) => {
            const idx = (suggestions?.stories?.length ?? 0) + (suggestions?.authors?.length ?? 0) + i;
            return (
              <button
                key={t.id}
                className={cn("w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors", selectedIdx === idx && "bg-accent")}
                onMouseEnter={() => setSelectedIdx(idx)}
                onClick={() => { navigate(`/search?q=${encodeURIComponent(t.name)}`); setOpen(false); }}
              >
                #{t.name}
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
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  if (!CLERK_KEY) {
    return <Button size="sm" variant="outline" disabled>Auth not configured</Button>;
  }

  if (isSignedIn) {
    return (
      <>
        <Button variant="ghost" size="icon" onClick={toggleTheme} title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
        <Link to="/notifications">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-4 w-4" />
          </Button>
        </Link>
        <UserButton afterSignOutUrl="/" />
      </>
    );
  }

  return (
    <>
      <Button variant="ghost" size="icon" onClick={toggleTheme} title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
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

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto max-w-5xl flex items-center justify-between h-14 px-4">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-xl font-semibold tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
              MueJam
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              {NAV_LINKS.filter((l) => !l.auth || isSignedIn).map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  className={cn(
                    "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    location.pathname.startsWith(l.to)
                      ? "text-foreground bg-accent"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  )}
                >
                  {l.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="hidden md:flex items-center gap-3">
            <SearchBar />
            <AuthButtons />
          </div>

          <button className="md:hidden p-2" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border px-4 py-3 space-y-3">
            <SearchBar />
            <nav className="flex flex-col gap-1">
              {NAV_LINKS.filter((l) => !l.auth || isSignedIn).map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "px-3 py-2 rounded-md text-sm font-medium",
                    location.pathname.startsWith(l.to) ? "bg-accent text-foreground" : "text-muted-foreground"
                  )}
                >
                  {l.label}
                </Link>
              ))}
            </nav>
            <div className="flex items-center gap-2 pt-2 border-t border-border">
              <AuthButtons />
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} MueJam · A home for serial stories
      </footer>
    </div>
  );
}
