import { useState } from "react";
import { StaffPicksFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function StaffPicksPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="space-y-6">
            <PageHeader title="Staff Picks" eyebrow="Discover" description="Curated stories handpicked by our team." />

            <SurfacePanel className="p-4">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </SurfacePanel>

            <div className="transition-opacity duration-300">
                <StaffPicksFeed filters={filters} />
            </div>
        </div>
    );
}
