import { RisingAuthors as RisingAuthorsComponent } from "@/components/discovery/RisingAuthors";

export default function RisingAuthorsPage() {
    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1
                    className="text-3xl font-semibold mb-2"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Rising Authors
                </h1>
                <p className="text-muted-foreground">
                    Discover up-and-coming writers making waves on the platform
                </p>
            </div>

            <RisingAuthorsComponent />
        </div>
    );
}
