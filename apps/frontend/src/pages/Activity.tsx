import { ActivityFeed } from "@/components/shared/ActivityFeed";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function Activity() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Activity"
        eyebrow="Social feed"
        description="Recent updates from writers and readers you follow."
      />

      <SurfacePanel className="p-5 sm:p-6">
        <ActivityFeed />
      </SurfacePanel>
    </div>
  );
}
