import { useEffect } from 'react';
import { useOnboardingStore } from '@/stores/useOnboardingStore';

export function useOnboarding() {
    const {
        progress,
        loading,
        error,
        fetchProgress,
        updateStep,
        skipOnboarding,
        markAsOnboarded,
    } = useOnboardingStore();

    useEffect(() => {
        // Fetch progress on mount if not already loaded
        if (!progress && !loading) {
            fetchProgress();
        }
    }, [progress, loading, fetchProgress]);

    return {
        progress,
        loading,
        error,
        updateStep,
        skipOnboarding,
        markAsOnboarded,
        refetch: fetchProgress,
    };
}
