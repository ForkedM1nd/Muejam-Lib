import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { X, Sparkles } from 'lucide-react';
import { useOnboardingStore } from '@/stores/useOnboardingStore';

export function OnboardingCompletionPrompt() {
    const navigate = useNavigate();
    const { showCompletionPrompt, dismissCompletionPrompt, progress } = useOnboardingStore();

    useEffect(() => {
        // Fetch progress on mount to check if onboarding is incomplete
        useOnboardingStore.getState().fetchProgress();
    }, []);

    if (!showCompletionPrompt || progress?.onboarding_completed) {
        return null;
    }

    const handleComplete = () => {
        dismissCompletionPrompt();
        navigate('/onboarding');
    };

    const handleDismiss = () => {
        dismissCompletionPrompt();
    };

    return (
        <Alert className="fixed bottom-4 right-4 max-w-md shadow-lg border-primary z-50">
            <Sparkles className="h-4 w-4" />
            <AlertTitle className="flex items-center justify-between">
                Complete Your Profile
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 -mr-2"
                    onClick={handleDismiss}
                >
                    <X className="h-4 w-4" />
                </Button>
            </AlertTitle>
            <AlertDescription className="mt-2">
                <p className="text-sm mb-3">
                    Finish setting up your profile to get personalized recommendations and connect with authors you'll love.
                </p>
                <div className="flex gap-2">
                    <Button size="sm" onClick={handleComplete}>
                        Complete Now
                    </Button>
                    <Button size="sm" variant="outline" onClick={handleDismiss}>
                        Remind Me Later
                    </Button>
                </div>
            </AlertDescription>
        </Alert>
    );
}
