import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X, Filter, ChevronDown } from "lucide-react";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible";

export interface DiscoveryFilterValues {
    genre?: string;
    tags?: string;
    length?: string;
}

interface DiscoveryFiltersProps {
    filters: DiscoveryFilterValues;
    onFiltersChange: (filters: DiscoveryFilterValues) => void;
    showGenreFilter?: boolean;
}

// Common genres - could be fetched from backend
const GENRES = [
    "Fantasy",
    "Science Fiction",
    "Romance",
    "Mystery",
    "Thriller",
    "Horror",
    "Adventure",
    "Historical Fiction",
    "Contemporary",
    "Young Adult",
    "Poetry",
    "Non-Fiction",
];

const LENGTH_OPTIONS = [
    { value: "short", label: "Short (< 10k words)" },
    { value: "medium", label: "Medium (10k-50k words)" },
    { value: "long", label: "Long (50k-100k words)" },
    { value: "epic", label: "Epic (> 100k words)" },
];

export function DiscoveryFilters({
    filters,
    onFiltersChange,
    showGenreFilter = true,
}: DiscoveryFiltersProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [tagsInput, setTagsInput] = useState(filters.tags || "");

    const hasActiveFilters = !!(filters.genre || filters.tags || filters.length);

    const handleGenreChange = (value: string) => {
        onFiltersChange({
            ...filters,
            genre: value === "all" ? undefined : value,
        });
    };

    const handleLengthChange = (value: string) => {
        onFiltersChange({
            ...filters,
            length: value === "all" ? undefined : value,
        });
    };

    const handleTagsSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onFiltersChange({
            ...filters,
            tags: tagsInput.trim() || undefined,
        });
    };

    const clearFilter = (filterKey: keyof DiscoveryFilterValues) => {
        const newFilters = { ...filters };
        delete newFilters[filterKey];
        onFiltersChange(newFilters);
        if (filterKey === "tags") {
            setTagsInput("");
        }
    };

    const clearAllFilters = () => {
        onFiltersChange({});
        setTagsInput("");
    };

    return (
        <div className="space-y-4">
            {/* Active Filters Display */}
            {hasActiveFilters && (
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm text-muted-foreground">Active filters:</span>
                    {filters.genre && (
                        <Badge variant="secondary" className="gap-1">
                            Genre: {filters.genre}
                            <button
                                onClick={() => clearFilter("genre")}
                                className="ml-1 hover:text-foreground"
                                aria-label="Clear genre filter"
                            >
                                <X className="h-3 w-3" />
                            </button>
                        </Badge>
                    )}
                    {filters.tags && (
                        <Badge variant="secondary" className="gap-1">
                            Tags: {filters.tags}
                            <button
                                onClick={() => clearFilter("tags")}
                                className="ml-1 hover:text-foreground"
                                aria-label="Clear tags filter"
                            >
                                <X className="h-3 w-3" />
                            </button>
                        </Badge>
                    )}
                    {filters.length && (
                        <Badge variant="secondary" className="gap-1">
                            Length: {LENGTH_OPTIONS.find((opt) => opt.value === filters.length)?.label}
                            <button
                                onClick={() => clearFilter("length")}
                                className="ml-1 hover:text-foreground"
                                aria-label="Clear length filter"
                            >
                                <X className="h-3 w-3" />
                            </button>
                        </Badge>
                    )}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearAllFilters}
                        className="h-6 text-xs"
                    >
                        Clear all
                    </Button>
                </div>
            )}

            {/* Filter Controls */}
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
                <CollapsibleTrigger asChild>
                    <Button variant="outline" className="w-full sm:w-auto">
                        <Filter className="h-4 w-4 mr-2" />
                        Filters
                        <ChevronDown
                            className={`h-4 w-4 ml-2 transition-transform ${isOpen ? "rotate-180" : ""
                                }`}
                        />
                    </Button>
                </CollapsibleTrigger>

                <CollapsibleContent className="mt-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4 border rounded-lg bg-muted/50">
                        {/* Genre Filter */}
                        {showGenreFilter && (
                            <div className="space-y-2">
                                <Label htmlFor="genre-filter">Genre</Label>
                                <Select
                                    value={filters.genre || "all"}
                                    onValueChange={handleGenreChange}
                                >
                                    <SelectTrigger id="genre-filter">
                                        <SelectValue placeholder="All genres" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All genres</SelectItem>
                                        {GENRES.map((genre) => (
                                            <SelectItem
                                                key={genre}
                                                value={genre.toLowerCase().replace(/\s+/g, "-")}
                                            >
                                                {genre}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {/* Length Filter */}
                        <div className="space-y-2">
                            <Label htmlFor="length-filter">Story Length</Label>
                            <Select
                                value={filters.length || "all"}
                                onValueChange={handleLengthChange}
                            >
                                <SelectTrigger id="length-filter">
                                    <SelectValue placeholder="Any length" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">Any length</SelectItem>
                                    {LENGTH_OPTIONS.map((option) => (
                                        <SelectItem key={option.value} value={option.value}>
                                            {option.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Tags Filter */}
                        <div className="space-y-2">
                            <Label htmlFor="tags-filter">Tags</Label>
                            <form onSubmit={handleTagsSubmit} className="flex gap-2">
                                <Input
                                    id="tags-filter"
                                    type="text"
                                    placeholder="e.g., magic, dragons"
                                    value={tagsInput}
                                    onChange={(e) => setTagsInput(e.target.value)}
                                />
                                <Button type="submit" size="sm">
                                    Apply
                                </Button>
                            </form>
                            <p className="text-xs text-muted-foreground">
                                Comma-separated tags
                            </p>
                        </div>
                    </div>
                </CollapsibleContent>
            </Collapsible>
        </div>
    );
}
