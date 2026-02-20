import { formatDistanceToNow } from "date-fns";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Loader2, Smartphone, Monitor, Tablet, Trash2, Bell } from "lucide-react";
import { usePushNotifications } from "@/hooks/usePushNotifications";
import { services } from "@/lib/api";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function DeviceManagement() {
    const {
        devices,
        isLoadingDevices,
        unregisterDevice,
        isUnregistering,
    } = usePushNotifications();

    const getDeviceIcon = (deviceType: string) => {
        switch (deviceType.toLowerCase()) {
            case "mobile":
                return <Smartphone className="h-5 w-5" />;
            case "tablet":
                return <Tablet className="h-5 w-5" />;
            case "desktop":
            default:
                return <Monitor className="h-5 w-5" />;
        }
    };

    const getPlatformLabel = (platform: string) => {
        switch (platform.toLowerCase()) {
            case "ios":
                return "iOS";
            case "android":
                return "Android";
            case "web":
                return "Web";
            default:
                return platform;
        }
    };

    return (
        <div className="mx-auto max-w-4xl space-y-5">
            <PageHeader
                title="Device Management"
                eyebrow="Settings"
                description="Manage devices registered for push notifications."
                action={<Smartphone className="h-5 w-5 text-primary" />}
            />

            <SurfacePanel className="p-5 sm:p-6">
                {isLoadingDevices ? (
                    <div className="flex items-center justify-center py-10">
                        <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                ) : devices && devices.length > 0 ? (
                    <div className="space-y-3">
                        {devices.map((device) => (
                            <div
                                key={device.device_id}
                                className="flex items-center justify-between gap-3 rounded-xl border border-border p-4"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="text-muted-foreground">
                                        {getDeviceIcon(device.platform)}
                                    </div>
                                    <div>
                                        <h3 className="font-medium">{device.device_name}</h3>
                                        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                                            <span>{getPlatformLabel(device.platform)}</span>
                                            <span>•</span>
                                            <span>
                                                Last active{" "}
                                                {formatDistanceToNow(new Date(device.last_active), {
                                                    addSuffix: true,
                                                })}
                                            </span>
                                        </div>
                                        <p className="mt-1 text-xs text-muted-foreground">
                                            Registered{" "}
                                            {formatDistanceToNow(new Date(device.registered_at), {
                                                addSuffix: true,
                                            })}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={async () => {
                                            try {
                                                await services.device.testNotification(device.device_id);
                                            } catch (error) {
                                                console.error("Failed to send test notification:", error);
                                            }
                                        }}
                                    >
                                        <Bell className="mr-1 h-4 w-4" />
                                        Test
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => unregisterDevice(device.device_id)}
                                        disabled={isUnregistering}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <Alert>
                        <AlertDescription>
                            No devices registered. Enable push notifications in your settings to register this device.
                        </AlertDescription>
                    </Alert>
                )}
            </SurfacePanel>

            <SurfacePanel className="p-4">
                <Alert>
                    <AlertDescription>
                        <strong>Note:</strong> Revoking device access stops push notifications on that device. You can
                        re-register it anytime from notification settings.
                    </AlertDescription>
                </Alert>
            </SurfacePanel>
        </div>
    );
}
