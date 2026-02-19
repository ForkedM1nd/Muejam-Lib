// ── Push Notifications Hook Tests ──

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePushNotifications } from "./usePushNotifications";
import { services } from "@/lib/api";

// Mock the services
vi.mock("@/lib/api", () => ({
    services: {
        device: {
            registerDevice: vi.fn(),
            unregisterDevice: vi.fn(),
            updatePreferences: vi.fn(),
            getDevices: vi.fn(),
        },
    },
}));

// Mock Notification API
const mockNotification = {
    permission: "default" as NotificationPermission,
    requestPermission: vi.fn(),
};

Object.defineProperty(global, "Notification", {
    value: mockNotification,
    writable: true,
});

// Mock navigator.serviceWorker
const mockServiceWorker = {
    getRegistration: vi.fn(),
    register: vi.fn(),
};

Object.defineProperty(navigator, "serviceWorker", {
    value: mockServiceWorker,
    writable: true,
});

describe("usePushNotifications", () => {
    let queryClient: QueryClient;

    beforeEach(() => {
        queryClient = new QueryClient({
            defaultOptions: {
                queries: { retry: false },
                mutations: { retry: false },
            },
        });
        vi.clearAllMocks();
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    it("should detect if push notifications are supported", () => {
        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        expect(result.current.isSupported).toBe(true);
    });

    it("should return current notification permission", () => {
        mockNotification.permission = "default";
        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        expect(result.current.permission).toBe("default");
    });

    it("should request notification permission", async () => {
        mockNotification.requestPermission.mockResolvedValue("granted");

        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        const permission = await result.current.requestPermission();

        expect(permission).toBe("granted");
        expect(mockNotification.requestPermission).toHaveBeenCalled();
    });

    it("should register device for push notifications", async () => {
        mockNotification.permission = "granted";
        mockNotification.requestPermission.mockResolvedValue("granted");

        const mockSubscription = {
            toJSON: () => ({
                endpoint: "https://example.com/push",
                keys: {
                    p256dh: "key1",
                    auth: "key2",
                },
            }),
        };

        const mockRegistration = {
            pushManager: {
                subscribe: vi.fn().mockResolvedValue(mockSubscription),
            },
        };

        mockServiceWorker.getRegistration.mockResolvedValue(null);
        mockServiceWorker.register.mockResolvedValue(mockRegistration);

        vi.mocked(services.device.registerDevice).mockResolvedValue(undefined);

        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        result.current.registerDevice(undefined);

        await waitFor(() => {
            expect(result.current.isRegistering).toBe(false);
        });

        expect(services.device.registerDevice).toHaveBeenCalled();
    });

    it("should unregister device", async () => {
        vi.mocked(services.device.unregisterDevice).mockResolvedValue(undefined);

        const mockSubscription = {
            unsubscribe: vi.fn().mockResolvedValue(true),
        };

        const mockRegistration = {
            pushManager: {
                getSubscription: vi.fn().mockResolvedValue(mockSubscription),
            },
        };

        mockServiceWorker.getRegistration.mockResolvedValue(mockRegistration);

        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        result.current.unregisterDevice("test-token");

        await waitFor(() => {
            expect(result.current.isUnregistering).toBe(false);
        });

        expect(services.device.unregisterDevice).toHaveBeenCalledWith("test-token");
    });

    it("should update notification preferences", async () => {
        const preferences = {
            enabled: true,
            follows: true,
            likes: false,
            replies: true,
            chapters: true,
            stories: false,
        };

        vi.mocked(services.device.updatePreferences).mockResolvedValue(undefined);

        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        result.current.updatePreferences(preferences);

        await waitFor(() => {
            expect(result.current.isUpdatingPreferences).toBe(false);
        });

        expect(services.device.updatePreferences).toHaveBeenCalledWith(preferences);
    });

    it("should fetch registered devices", async () => {
        const mockDevices = [
            {
                device_id: "device1",
                device_name: "iPhone",
                platform: "ios",
                registered_at: "2024-01-01T00:00:00Z",
                last_active: "2024-01-02T00:00:00Z",
            },
        ];

        vi.mocked(services.device.getDevices).mockResolvedValue(mockDevices);

        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        await waitFor(() => {
            expect(result.current.devices).toEqual(mockDevices);
        });

        expect(services.device.getDevices).toHaveBeenCalled();
    });

    it("should handle unsupported browsers", () => {
        // Temporarily remove Notification support
        const originalNotification = global.Notification;
        // @ts-expect-error - Testing unsupported scenario
        global.Notification = undefined;

        const { result } = renderHook(() => usePushNotifications(), { wrapper });

        expect(result.current.isSupported).toBe(false);

        // Restore Notification
        global.Notification = originalNotification;
    });
});
