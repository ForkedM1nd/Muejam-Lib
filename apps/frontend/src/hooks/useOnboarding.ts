import { useState, useEffect } from 'react';

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

export function useOnboarding() {
    const [progress, setProgress] = useState<OnboardingProgress | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchProgress = async () => {
        try {
            setLoading(true);
            const response = await fetch('/v1/onboarding/progress/', {
                credentials: 'include',
            });

            if (response.ok) {
                const data = await response.json();
                setProgress(data);
            } else {
                setError('Failed to fetch onboarding progress');
            }
        } catch (err) {
            setError('Failed to fetch onboarding progress');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const updateStep = async (step: string) => {
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
                setProgress(data);
                return true;
            }
            return false;
        } catch (err) {
            console.error('Failed to update onboarding step:', err);
            return false;
        }
    };

    const skipOnboarding = async () => {
        try {
            const response = await fetch('/v1/onboarding/skip/', {
                method: 'POST',
                credentials: 'include',
            });

            if (response.ok) {
                const data = await response.json();
                setProgress(data);
                return true;
            }
            return false;
        } catch (err) {
            console.error('Failed to skip onboarding:', err);
            return false;
        }
    };

    useEffect(() => {
        fetchProgress();
    }, []);

    return {
        progress,
        loading,
        error,
        updateStep,
        skipOnboarding,
        refetch: fetchProgress,
    };
}
