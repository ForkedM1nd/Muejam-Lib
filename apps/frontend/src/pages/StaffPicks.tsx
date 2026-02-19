import { useState } from "react";
import { StaffPicksFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";

export default function StaffPicksPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1
                    className="text-3xl font-semibold mb-2"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Staff Picks
                </h1>
                <p className="text-muted-foreground">
                    Curated stories handpicked by our team
                </p>
            </div>

            <div className="mb-6">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </div>

            <div className="transition-opacity duration-300">
                <StaffPicksFeed filters={filters} />
            </div>
        </div>
    );
}
