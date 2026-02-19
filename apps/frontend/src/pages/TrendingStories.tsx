import { useState } from "react";
import { TrendingFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";

export default function TrendingStoriesPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1
                    className="text-3xl font-semibold mb-2"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Trending Stories
                </h1>
                <p className="text-muted-foreground">
                    Discover what's popular right now
                </p>
            </div>

            <div className="mb-6">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </div>

            <div className="transition-opacity duration-300">
                <TrendingFeed filters={filters} />
            </div>
        </div>
    );
}
