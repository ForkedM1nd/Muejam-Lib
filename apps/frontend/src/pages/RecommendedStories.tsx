import { useState } from "react";
import { RecommendedFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";

export default function RecommendedStoriesPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1
                    className="text-3xl font-semibold mb-2"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Recommended for You
                </h1>
                <p className="text-muted-foreground">
                    Personalized story recommendations based on your reading history
                </p>
            </div>

            <div className="mb-6">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </div>

            <div className="transition-opacity duration-300">
                <RecommendedFeed filters={filters} />
            </div>
        </div>
    );
}
