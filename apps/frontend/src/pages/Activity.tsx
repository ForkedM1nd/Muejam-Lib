import { ActivityFeed } from "@/components/shared/ActivityFeed";

export default function Activity() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
          Activity
        </h1>
        <p className="text-muted-foreground mt-2">
          Recent updates from writers and readers you follow.
        </p>
      </div>

      <ActivityFeed />
    </div>
  );
}
