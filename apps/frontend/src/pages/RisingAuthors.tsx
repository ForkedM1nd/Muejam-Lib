import { RisingAuthors as RisingAuthorsComponent } from "@/components/discovery/RisingAuthors";
import PageHeader from "@/components/shared/PageHeader";

export default function RisingAuthorsPage() {
    return (
        <div className="space-y-6">
            <PageHeader
                title="Rising Authors"
                eyebrow="Discover"
                description="Discover up-and-coming writers making waves on the platform."
            />

            <RisingAuthorsComponent />
        </div>
    );
}
