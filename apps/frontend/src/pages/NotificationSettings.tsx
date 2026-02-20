import { Bell } from "lucide-react";
import { NotificationPreferences } from "@/components/settings/NotificationPreferences";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function NotificationSettings() {
    return (
        <div className="mx-auto max-w-4xl space-y-5">
            <PageHeader
                title="Notification Settings"
                eyebrow="Settings"
                description="Manage your notification preferences and registered devices."
                action={<Bell className="h-5 w-5 text-primary" />}
            />

            <SurfacePanel className="p-5 sm:p-6">
                <NotificationPreferences />
            </SurfacePanel>
        </div>
    );
}
