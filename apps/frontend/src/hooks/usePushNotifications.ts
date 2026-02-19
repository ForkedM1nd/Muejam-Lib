// ── Push Notifications Hook ──
// Handles device registration, notification preferences, and push notification permissions

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { services } from "@/lib/api";
import type { DeviceToken, NotificationPreferences, RegisteredDevice } from "@/types";

interface PushNotificationState {
    permission: NotificationPermission;
    isSupported: boolean;
    isRegistered: boolean;
    deviceToken: string | null;
}

export function usePushNotifications() {
    const queryClient = useQueryClient();
    const [state, setState] = useState<PushNotificationState>({
        permission: typeof Notification !== "undefined" ? Notification.permission : "default",
        isSupported: typeof Notification !== "undefined" && "serviceWorker" in navigator,
        isRegistered: false,
        deviceToken: null,
    });

    // Check if push notifications are supported
    useEffect(() => {
        if (!state.isSupported) {
            console.warn("[Push Notifications] Not supported in this browser");
        }
    }, [state.isSupported]);

    // Request notification permission
    const requestPermission = async (): Promise<NotificationPermission> => {
        if (!state.isSupported) {
            throw new Error("Push notifications are not supported");
        }

        try {
            const permission = await Notification.requestPermission();
            setState((prev) => ({ ...prev, permission }));
            return permission;
        } catch (error) {
            console.error("[Push Notifications] Permission request failed:", error);
            throw error;
        }
    };

    // Register device for push notifications
    const registerDeviceMutation = useMutation({
        mutationFn: async (deviceName?: string) => {
            if (!state.isSupported) {
                throw new Error("Push notifications are not supported");
            }

            // Request permission if not already granted
            if (state.permission !== "granted") {
                const permission = await requestPermission();
                if (permission !== "granted") {
                    throw new Error("Notification permission denied");
                }
            }

            // Register service worker if not already registered
            let registration = await navigator.serviceWorker.getRegistration();
            if (!registration) {
                registration = await navigator.serviceWorker.register("/sw.js");
            }

            // Subscribe to push notifications
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY,
            });

            // Extract the token from the subscription
            const token = btoa(JSON.stringify(subscription.toJSON()));

            // Detect platform
            const userAgent = navigator.userAgent.toLowerCase();
            let platform: "ios" | "android" | "web" = "web";
            if (userAgent.includes("android")) {
                platform = "android";
            } else if (userAgent.includes("iphone") || userAgent.includes("ipad")) {
                platform = "ios";
            }

            // Prepare device token
            const deviceToken: DeviceToken = {
                token,
                platform,
                device_name: deviceName || `${platform} device`,
            };

            // Register with backend
            await services.device.registerDevice(deviceToken);

            setState((prev) => ({
                ...prev,
                isRegistered: true,
                deviceToken: token,
            }));

            return token;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["devices"] });
        },
    });

    // Unregister device
    const unregisterDeviceMutation = useMutation({
        mutationFn: async (token?: string) => {
            const tokenToUnregister = token || state.deviceToken;
            if (!tokenToUnregister) {
                throw new Error("No device token to unregister");
            }

            await services.device.unregisterDevice(tokenToUnregister);

            // Unsubscribe from push notifications
            if (state.isSupported) {
                const registration = await navigator.serviceWorker.getRegistration();
                if (registration) {
                    const subscription = await registration.pushManager.getSubscription();
                    if (subscription) {
                        await subscription.unsubscribe();
                    }
                }
            }

            setState((prev) => ({
                ...prev,
                isRegistered: false,
                deviceToken: null,
            }));
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["devices"] });
        },
    });

    // Update notification preferences
    const updatePreferencesMutation = useMutation({
        mutationFn: (preferences: NotificationPreferences) =>
            services.device.updatePreferences(preferences),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
        },
    });

    // Get registered devices
    const { data: devices, isLoading: isLoadingDevices } = useQuery<RegisteredDevice[]>({
        queryKey: ["devices"],
        queryFn: () => services.device.getDevices(),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });

    // Check if current device is registered
    useEffect(() => {
        if (devices && state.deviceToken) {
            const isRegistered = devices.some((device) =>
                device.device_id === state.deviceToken
            );
            setState((prev) => ({ ...prev, isRegistered }));
        }
    }, [devices, state.deviceToken]);

    return {
        // State
        permission: state.permission,
        isSupported: state.isSupported,
        isRegistered: state.isRegistered,
        deviceToken: state.deviceToken,
        devices,
        isLoadingDevices,

        // Actions
        requestPermission,
        registerDevice: registerDeviceMutation.mutate,
        unregisterDevice: unregisterDeviceMutation.mutate,
        updatePreferences: updatePreferencesMutation.mutate,

        // Mutation states
        isRegistering: registerDeviceMutation.isPending,
        isUnregistering: unregisterDeviceMutation.isPending,
        isUpdatingPreferences: updatePreferencesMutation.isPending,
        registerError: registerDeviceMutation.error,
        unregisterError: unregisterDeviceMutation.error,
        updatePreferencesError: updatePreferencesMutation.error,
    };
}
