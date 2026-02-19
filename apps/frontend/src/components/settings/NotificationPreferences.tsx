// ── Notification Preferences Component ──
// Allows users to configure their notification preferences

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { usePushNotifications } from "@/hooks/usePushNotifications";
import { services } from "@/lib/api";
import type { NotificationPreferences as NotificationPreferencesType } from "@/types";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Bell, BellOff, Check, Loader2 } from "lucide-react";

export function NotificationPreferences() {
    const {
        permission,
        isSupported,
        isRegistered,
        requestPermission,
        registerDevice,
        unregisterDevice,
        updatePreferences,
        isRegistering,
        isUnregistering,
        isUpdatingPreferences,
        registerError,
    } = usePushNotifications();

    // Fetch current preferences
    const { data: preferences, isLoading } = useQuery<NotificationPreferencesType>({
        queryKey: ["notification-preferences"],
        queryFn: async () => {
            // This would typically come from a dedicated endpoint
            // For now, we'll use a default structure
            return {
                enabled: true,
                follows: true,
                likes: true,
                replies: true,
                chapters: true,
                stories: true,
            };
        },
        staleTime: 5 * 60 * 1000,
    });

    const [localPreferences, setLocalPreferences] = useState<NotificationPreferencesType | null>(null);

    // Use local preferences if available, otherwise use fetched preferences
    const currentPreferences = localPreferences || preferences;

    const handleToggle = (key: keyof NotificationPreferencesType) => {
        if (!currentPreferences) return;

        const updated = {
            ...currentPreferences,
            [key]: !currentPreferences[key],
        };

        setLocalPreferences(updated);
        updatePreferences(updated);
    };

    const handleEnableNotifications = async () => {
        try {
            const perm = await requestPermission();
            if (perm === "granted") {
                registerDevice(undefined);
            }
        } catch (error) {
            console.error("Failed to enable notifications:", error);
        }
    };

    const handleDisableNotifications = () => {
        unregisterDevice(undefined);
    };

    if (!isSupported) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Push Notifications</CardTitle>
                    <CardDescription>
                        Push notifications are not supported in your browser
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Alert>
                        <BellOff className="h-4 w-4" />
                        <AlertDescription>
                            Your browser doesn't support push notifications. Please use a modern browser like Chrome, Firefox, or Safari.
                        </AlertDescription>
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Permission Status */}
            <Card>
                <CardHeader>
                    <CardTitle>Push Notifications</CardTitle>
                    <CardDescription>
                        Receive real-time notifications for updates and activity
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {permission === "denied" && (
                        <Alert variant="destructive">
                            <BellOff className="h-4 w-4" />
                            <AlertDescription>
                                Notifications are blocked. Please enable them in your browser settings.
                            </AlertDescription>
                        </Alert>
                    )}

                    {permission === "default" && (
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <Label>Enable Push Notifications</Label>
                                <p className="text-sm text-muted-foreground">
                                    Get notified about new followers, likes, and replies
                                </p>
                            </div>
                            <Button
                                onClick={handleEnableNotifications}
                                disabled={isRegistering}
                            >
                                {isRegistering ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Enabling...
                                    </>
                                ) : (
                                    <>
                                        <Bell className="mr-2 h-4 w-4" />
                                        Enable
                                    </>
                                )}
                            </Button>
                        </div>
                    )}

                    {permission === "granted" && !isRegistered && (
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <Label>Register Device</Label>
                                <p className="text-sm text-muted-foreground">
                                    Register this device to receive notifications
                                </p>
                            </div>
                            <Button
                                onClick={() => registerDevice(undefined)}
                                disabled={isRegistering}
                            >
                                {isRegistering ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Registering...
                                    </>
                                ) : (
                                    "Register Device"
                                )}
                            </Button>
                        </div>
                    )}

                    {permission === "granted" && isRegistered && (
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Check className="h-4 w-4 text-green-600" />
                                <div className="space-y-0.5">
                                    <Label>Notifications Enabled</Label>
                                    <p className="text-sm text-muted-foreground">
                                        This device is registered for push notifications
                                    </p>
                                </div>
                            </div>
                            <Button
                                variant="outline"
                                onClick={handleDisableNotifications}
                                disabled={isUnregistering}
                            >
                                {isUnregistering ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Disabling...
                                    </>
                                ) : (
                                    "Disable"
                                )}
                            </Button>
                        </div>
                    )}

                    {registerError && (
                        <Alert variant="destructive">
                            <AlertDescription>
                                Failed to register device: {registerError.message}
                            </AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {/* Notification Preferences */}
            {isRegistered && (
                <Card>
                    <CardHeader>
                        <CardTitle>Notification Preferences</CardTitle>
                        <CardDescription>
                            Choose which notifications you want to receive
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {isLoading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin" />
                            </div>
                        ) : currentPreferences ? (
                            <>
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="follows">New Followers</Label>
                                        <p className="text-sm text-muted-foreground">
                                            When someone follows you
                                        </p>
                                    </div>
                                    <Switch
                                        id="follows"
                                        checked={currentPreferences.follows}
                                        onCheckedChange={() => handleToggle("follows")}
                                        disabled={isUpdatingPreferences}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="likes">Likes</Label>
                                        <p className="text-sm text-muted-foreground">
                                            When someone likes your content
                                        </p>
                                    </div>
                                    <Switch
                                        id="likes"
                                        checked={currentPreferences.likes}
                                        onCheckedChange={() => handleToggle("likes")}
                                        disabled={isUpdatingPreferences}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="replies">Replies</Label>
                                        <p className="text-sm text-muted-foreground">
                                            When someone replies to your whispers
                                        </p>
                                    </div>
                                    <Switch
                                        id="replies"
                                        checked={currentPreferences.replies}
                                        onCheckedChange={() => handleToggle("replies")}
                                        disabled={isUpdatingPreferences}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="chapters">New Chapters</Label>
                                        <p className="text-sm text-muted-foreground">
                                            When authors you follow publish new chapters
                                        </p>
                                    </div>
                                    <Switch
                                        id="chapters"
                                        checked={currentPreferences.chapters}
                                        onCheckedChange={() => handleToggle("chapters")}
                                        disabled={isUpdatingPreferences}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="stories">New Stories</Label>
                                        <p className="text-sm text-muted-foreground">
                                            When authors you follow publish new stories
                                        </p>
                                    </div>
                                    <Switch
                                        id="stories"
                                        checked={currentPreferences.stories}
                                        onCheckedChange={() => handleToggle("stories")}
                                        disabled={isUpdatingPreferences}
                                    />
                                </div>

                                {/* Quiet Hours */}
                                <div className="pt-4 border-t">
                                    <div className="space-y-0.5 mb-4">
                                        <Label>Quiet Hours</Label>
                                        <p className="text-sm text-muted-foreground">
                                            Mute notifications during specific hours
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="quiet-start" className="text-sm">
                                                Start Time
                                            </Label>
                                            <input
                                                id="quiet-start"
                                                type="time"
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                value={currentPreferences.quiet_hours_start || ""}
                                                onChange={(e) => {
                                                    const updated = {
                                                        ...currentPreferences,
                                                        quiet_hours_start: e.target.value,
                                                    };
                                                    setLocalPreferences(updated);
                                                    updatePreferences(updated);
                                                }}
                                                disabled={isUpdatingPreferences}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="quiet-end" className="text-sm">
                                                End Time
                                            </Label>
                                            <input
                                                id="quiet-end"
                                                type="time"
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                value={currentPreferences.quiet_hours_end || ""}
                                                onChange={(e) => {
                                                    const updated = {
                                                        ...currentPreferences,
                                                        quiet_hours_end: e.target.value,
                                                    };
                                                    setLocalPreferences(updated);
                                                    updatePreferences(updated);
                                                }}
                                                disabled={isUpdatingPreferences}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </>
                        ) : null}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
