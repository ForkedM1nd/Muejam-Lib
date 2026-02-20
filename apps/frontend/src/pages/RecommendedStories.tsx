import { useState } from "react";
import { RecommendedFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function RecommendedStoriesPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="space-y-6">
            <PageHeader
                title="Recommended for You"
                eyebrow="Discover"
                description="Personalized story recommendations based on your reading history."
            />

            <SurfacePanel className="p-4">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </SurfacePanel>

            <div className="transition-opacity duration-300">
                <RecommendedFeed filters={filters} />
            </div>
        </div>
    );
}
