import { useState } from "react";
import { NewAndNoteworthyFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function NewAndNoteworthyPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="space-y-6">
            <PageHeader title="New & Noteworthy" eyebrow="Discover" description="Fresh stories worth your attention." />

            <SurfacePanel className="p-4">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </SurfacePanel>

            <div className="transition-opacity duration-300">
                <NewAndNoteworthyFeed filters={filters} />
            </div>
        </div>
    );
}
