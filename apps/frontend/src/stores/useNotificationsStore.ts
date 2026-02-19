import { create } from 'zustand';

export interface Notification {
    id: string;
    type: 'follow' | 'like' | 'reply' | 'chapter' | 'story' | 'system';
    title: string;
    message: string;
    read: boolean;
    created_at: string;
    link?: string;
    actor?: {
        id: string;
        handle: string;
        display_name: string;
        avatar_url?: string;
    };
}

interface NotificationsState {
    // State
    unreadCount: number;
    items: Notification[];

    // Actions
    setUnreadCount: (count: number) => void;
    addNotification: (notification: Notification) => void;
    markAsRead: (id: string) => void;
    markAllAsRead: () => void;
    removeNotification: (id: string) => void;
    setNotifications: (notifications: Notification[]) => void;
    clearNotifications: () => void;
}

export const useNotificationsStore = create<NotificationsState>((set) => ({
    unreadCount: 0,
    items: [],

    setUnreadCount: (count) => set({ unreadCount: count }),

    addNotification: (notification) =>
        set((state) => ({
            items: [notification, ...state.items],
            unreadCount: notification.read ? state.unreadCount : state.unreadCount + 1,
        })),

    markAsRead: (id) =>
        set((state) => {
            const notification = state.items.find((n) => n.id === id);
            if (!notification || notification.read) {
                return state;
            }

            return {
                items: state.items.map((n) =>
                    n.id === id ? { ...n, read: true } : n
                ),
                unreadCount: Math.max(0, state.unreadCount - 1),
            };
        }),

    markAllAsRead: () =>
        set((state) => ({
            items: state.items.map((n) => ({ ...n, read: true })),
            unreadCount: 0,
        })),

    removeNotification: (id) =>
        set((state) => {
            const notification = state.items.find((n) => n.id === id);
            const wasUnread = notification && !notification.read;

            return {
                items: state.items.filter((n) => n.id !== id),
                unreadCount: wasUnread
                    ? Math.max(0, state.unreadCount - 1)
                    : state.unreadCount,
            };
        }),

    setNotifications: (notifications) =>
        set({
            items: notifications,
            unreadCount: notifications.filter((n) => !n.read).length,
        }),

    clearNotifications: () =>
        set({
            items: [],
            unreadCount: 0,
        }),
}));
