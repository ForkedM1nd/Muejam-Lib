import { useState } from "react";
import { TrendingFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function TrendingStoriesPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="space-y-6">
            <PageHeader title="Trending Stories" eyebrow="Discover" description="Discover what is popular right now." />

            <SurfacePanel className="p-4">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </SurfacePanel>

            <div className="transition-opacity duration-300">
                <TrendingFeed filters={filters} />
            </div>
        </div>
    );
}
