import { useState } from "react";
import { NewAndNoteworthyFeed, DiscoveryFilters, type DiscoveryFilterValues } from "@/components/discovery";

export default function NewAndNoteworthyPage() {
    const [filters, setFilters] = useState<DiscoveryFilterValues>({});

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1
                    className="text-3xl font-semibold mb-2"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    New & Noteworthy
                </h1>
                <p className="text-muted-foreground">
                    Fresh stories worth your attention
                </p>
            </div>

            <div className="mb-6">
                <DiscoveryFilters filters={filters} onFiltersChange={setFilters} />
            </div>

            <div className="transition-opacity duration-300">
                <NewAndNoteworthyFeed filters={filters} />
            </div>
        </div>
    );
}
