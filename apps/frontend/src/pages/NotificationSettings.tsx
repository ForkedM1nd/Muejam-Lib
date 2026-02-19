// ── Notification Settings Page ──
// Allows users to manage notification preferences and devices

import { Bell } from "lucide-react";
import { NotificationPreferences } from "@/components/settings/NotificationPreferences";

export default function NotificationSettings() {
    return (
        <div className="container max-w-4xl py-8">
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Bell className="h-8 w-8" />
                        Notification Settings
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Manage your notification preferences and registered devices.
                    </p>
                </div>

                {/* Notification Preferences */}
                <NotificationPreferences />
            </div>
        </div>
    );
}
