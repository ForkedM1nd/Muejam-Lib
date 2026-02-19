import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { GenreDiscovery as GenreDiscoveryComponent } from "@/components/discovery/GenreDiscovery";
import { DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

// Common genres - this could be fetched from the backend in a real implementation
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

export default function GenreDiscoveryPage() {
    const { genre } = useParams<{ genre: string }>();
    const navigate = useNavigate();
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    if (!genre) {
        return (
            <div className="max-w-5xl mx-auto px-4 py-8">
                <h1
                    className="text-3xl font-semibold mb-6"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Browse by Genre
                </h1>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                    {GENRES.map((g) => (
                        <Button
                            key={g}
                            variant="outline"
                            className="h-20 text-lg"
                            onClick={() => navigate(`/discover/genre/${g.toLowerCase().replace(/\s+/g, "-")}`)}
                        >
                            {g}
                        </Button>
                    ))}
                </div>
            </div>
        );
    }

    // Format genre for display (e.g., "science-fiction" -> "Science Fiction")
    const displayGenre = genre
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="mb-6">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate("/discover/genre")}
                    className="mb-4"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    All Genres
                </Button>
                <h1
                    className="text-3xl font-semibold mb-2"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    {displayGenre}
                </h1>
                <p className="text-muted-foreground">
                    Explore stories in the {displayGenre.toLowerCase()} genre
                </p>
            </div>

            <div className="mb-6">
                <DiscoveryFilters
                    filters={filters}
                    onFiltersChange={setFilters}
                    showGenreFilter={false}
                />
            </div>

            <div className="transition-opacity duration-300">
                <GenreDiscoveryComponent genre={genre} filters={filters} />
            </div>
        </div>
    );
}
