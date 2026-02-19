// ── Device Management Page ──
// Allows users to view and manage their registered devices

import { usePushNotifications } from "@/hooks/usePushNotifications";
import { services } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Smartphone, Monitor, Tablet, Trash2, Bell } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

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
        <div className="container max-w-4xl py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold">Device Management</h1>
                <p className="text-muted-foreground mt-2">
                    Manage devices registered for push notifications
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Registered Devices</CardTitle>
                    <CardDescription>
                        Devices that can receive push notifications from MueJam
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoadingDevices ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin" />
                        </div>
                    ) : devices && devices.length > 0 ? (
                        <div className="space-y-4">
                            {devices.map((device) => (
                                <div
                                    key={device.device_id}
                                    className="flex items-center justify-between p-4 border rounded-lg"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="text-muted-foreground">
                                            {getDeviceIcon(device.platform)}
                                        </div>
                                        <div>
                                            <h3 className="font-medium">{device.device_name}</h3>
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                <span>{getPlatformLabel(device.platform)}</span>
                                                <span>•</span>
                                                <span>
                                                    Last active{" "}
                                                    {formatDistanceToNow(new Date(device.last_active), {
                                                        addSuffix: true,
                                                    })}
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1">
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
                                                    console.error('Failed to send test notification:', error);
                                                }
                                            }}
                                        >
                                            <Bell className="h-4 w-4 mr-1" />
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
                </CardContent>
            </Card>

            <div className="mt-6">
                <Alert>
                    <AlertDescription>
                        <strong>Note:</strong> Revoking device access will stop push notifications on that device.
                        You can re-register the device at any time from the notification settings.
                    </AlertDescription>
                </Alert>
            </div>
        </div>
    );
}
