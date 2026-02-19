import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ReaderSettings {
    fontSize: number; // 12-24
    fontFamily: 'serif' | 'sans-serif' | 'mono';
    lineHeight: number; // 1.2-2.0
    theme: 'light' | 'dark' | 'sepia';
    width: 'narrow' | 'medium' | 'wide';
}

interface UIState {
    // Sidebar state
    sidebarOpen: boolean;

    // Theme
    theme: 'light' | 'dark' | 'system';

    // Reader settings
    readerSettings: ReaderSettings;

    // Actions
    setSidebarOpen: (open: boolean) => void;
    toggleSidebar: () => void;
    setTheme: (theme: 'light' | 'dark' | 'system') => void;
    updateReaderSettings: (settings: Partial<ReaderSettings>) => void;
    resetReaderSettings: () => void;
}

const defaultReaderSettings: ReaderSettings = {
    fontSize: 16,
    fontFamily: 'serif',
    lineHeight: 1.6,
    theme: 'light',
    width: 'medium',
};

export const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            sidebarOpen: true,
            theme: 'system',
            readerSettings: defaultReaderSettings,

            setSidebarOpen: (open) => set({ sidebarOpen: open }),

            toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

            setTheme: (theme) => set({ theme }),

            updateReaderSettings: (settings) =>
                set((state) => ({
                    readerSettings: { ...state.readerSettings, ...settings },
                })),

            resetReaderSettings: () => set({ readerSettings: defaultReaderSettings }),
        }),
        {
            name: 'ui-storage',
            partialize: (state) => ({
                theme: state.theme,
                readerSettings: state.readerSettings,
                // Don't persist sidebarOpen - let it reset on page load
            }),
        }
    )
);
