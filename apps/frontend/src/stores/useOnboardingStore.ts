import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface OnboardingProgress {
    user_id: string;
    profile_completed: boolean;
    interests_selected: boolean;
    tutorial_completed: boolean;
    first_story_read: boolean;
    first_whisper_posted: boolean;
    first_follow: boolean;
    authors_followed_count: number;
    onboarding_completed: boolean;
    completed_at: string | null;
    created_at: string;
    updated_at: string;
}

interface OnboardingStore {
    progress: OnboardingProgress | null;
    loading: boolean;
    error: string | null;
    showCompletionPrompt: boolean;

    // Actions
    setProgress: (progress: OnboardingProgress | null) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setShowCompletionPrompt: (show: boolean) => void;
    dismissCompletionPrompt: () => void;

    // API actions
    fetchProgress: () => Promise<void>;
    updateStep: (step: string) => Promise<boolean>;
    skipOnboarding: () => Promise<boolean>;
    markAsOnboarded: () => Promise<boolean>;
}

export const useOnboardingStore = create<OnboardingStore>()(
    persist(
        (set, get) => ({
            progress: null,
            loading: false,
            error: null,
            showCompletionPrompt: false,

            setProgress: (progress) => set({ progress }),
            setLoading: (loading) => set({ loading }),
            setError: (error) => set({ error }),
            setShowCompletionPrompt: (show) => set({ showCompletionPrompt: show }),

            dismissCompletionPrompt: () => {
                set({ showCompletionPrompt: false });
                // Store dismissal in localStorage with timestamp
                localStorage.setItem('onboarding_prompt_dismissed', Date.now().toString());
            },

            fetchProgress: async () => {
                try {
                    set({ loading: true, error: null });
                    const response = await fetch('/v1/onboarding/progress/', {
                        credentials: 'include',
                    });

                    if (response.ok) {
                        const data = await response.json();
                        set({ progress: data });

                        // Check if we should show completion prompt
                        const dismissedAt = localStorage.getItem('onboarding_prompt_dismissed');
                        const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
                        const shouldShow = !data.onboarding_completed &&
                            (!dismissedAt || parseInt(dismissedAt) < oneDayAgo);

                        set({ showCompletionPrompt: shouldShow });
                    } else {
                        set({ error: 'Failed to fetch onboarding progress' });
                    }
                } catch (err) {
                    set({ error: 'Failed to fetch onboarding progress' });
                    console.error(err);
                } finally {
                    set({ loading: false });
                }
            },

            updateStep: async (step: string) => {
                try {
                    const response = await fetch('/v1/onboarding/step/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ step }),
                        credentials: 'include',
                    });

                    if (response.ok) {
                        const data = await response.json();
                        set({ progress: data });
                        return true;
                    }
                    return false;
                } catch (err) {
                    console.error('Failed to update onboarding step:', err);
                    return false;
                }
            },

            skipOnboarding: async () => {
                try {
                    const response = await fetch('/v1/onboarding/skip/', {
                        method: 'POST',
                        credentials: 'include',
                    });

                    if (response.ok) {
                        const data = await response.json();
                        set({ progress: data, showCompletionPrompt: false });
                        return true;
                    }
                    return false;
                } catch (err) {
                    console.error('Failed to skip onboarding:', err);
                    return false;
                }
            },

            markAsOnboarded: async () => {
                try {
                    const response = await fetch('/v1/onboarding/complete/', {
                        method: 'POST',
                        credentials: 'include',
                    });

                    if (response.ok) {
                        const data = await response.json();
                        set({ progress: data, showCompletionPrompt: false });
                        return true;
                    }
                    return false;
                } catch (err) {
                    console.error('Failed to mark onboarding as complete:', err);
                    return false;
                }
            },
        }),
        {
            name: 'onboarding-storage',
            partialize: (state) => ({
                progress: state.progress,
                // Don't persist loading, error, or showCompletionPrompt
            }),
        }
    )
);
