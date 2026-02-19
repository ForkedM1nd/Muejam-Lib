import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bookmark, X, Bell, BellOff, Trash2 } from "lucide-react";
import {
    getSavedSearches,
    removeSavedSearch,
    clearNewMatchesCount,
    clearSavedSearches,
    type SavedSearch,
} from "@/lib/savedSearches";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface SavedSearchesProps {
    onSearchSelect?: (search: SavedSearch) => void;
}

export function SavedSearches({ onSearchSelect }: SavedSearchesProps) {
    const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        setSavedSearches(getSavedSearches());
    }, []);

    const handleRemove = (id: string) => {
        removeSavedSearch(id);
        setSavedSearches(getSavedSearches());
    };

    const handleClearAll = () => {
        clearSavedSearches();
        setSavedSearches([]);
    };

    const handleSearchClick = (search: SavedSearch) => {
        // Clear new matches count when user clicks on a saved search
        clearNewMatchesCount(search.id);
        setSavedSearches(getSavedSearches());

        if (onSearchSelect) {
            onSearchSelect(search);
        } else {
            // Build URL with query and filters
            const params = new URLSearchParams();
            params.set("q", search.query);

            if (search.filters.type) {
                params.set("type", search.filters.type);
            }

            navigate(`/search?${params.toString()}`);
        }
    };

    const formatFilters = (search: SavedSearch): string => {
        const parts: string[] = [];

        if (search.filters.type && search.filters.type !== "all") {
            parts.push(search.filters.type);
        }

        if (search.filters.genres && search.filters.genres.length > 0) {
            parts.push(`${search.filters.genres.length} genre${search.filters.genres.length > 1 ? "s" : ""}`);
        }

        if (search.filters.status && search.filters.status.length > 0) {
            parts.push(search.filters.status.join(", "));
        }

        if (search.filters.minWordCount || search.filters.maxWordCount) {
            parts.push("word count filter");
        }

        if (search.filters.sort && search.filters.sort !== "relevance") {
            parts.push(`sorted by ${search.filters.sort}`);
        }

        return parts.length > 0 ? parts.join(" • ") : "No filters";
    };

    if (savedSearches.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Bookmark className="h-5 w-5" />
                        Saved Searches
                    </CardTitle>
                    <CardDescription>
                        Save your searches to quickly access them later and get notified of new matches.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No saved searches yet. Save a search from the search page to see it here.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Bookmark className="h-5 w-5" />
                            Saved Searches
                        </CardTitle>
                        <CardDescription>
                            {savedSearches.length} saved search{savedSearches.length !== 1 ? "es" : ""}
                        </CardDescription>
                    </div>
                    <AlertDialog>
                        <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="sm">
                                <Trash2 className="h-4 w-4 mr-1" />
                                Clear All
                            </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                            <AlertDialogHeader>
                                <AlertDialogTitle>Clear all saved searches?</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This will remove all {savedSearches.length} saved searches. This action cannot be undone.
                                </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={handleClearAll}>Clear All</AlertDialogAction>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialog>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    {savedSearches.map((search) => (
                        <div
                            key={search.id}
                            className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors group"
                        >
                            <Bookmark className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                            <div className="flex-1 min-w-0">
                                <button
                                    onClick={() => handleSearchClick(search)}
                                    className="text-left w-full"
                                >
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-medium hover:underline">
                                            {search.query}
                                        </span>
                                        {search.newMatchesCount && search.newMatchesCount > 0 && (
                                            <Badge variant="default" className="text-xs">
                                                {search.newMatchesCount} new
                                            </Badge>
                                        )}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {formatFilters(search)}
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Saved {new Date(search.createdAt).toLocaleDateString()}
                                    </p>
                                </button>
                            </div>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0"
                                    onClick={() => handleRemove(search.id)}
                                    aria-label="Remove saved search"
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
