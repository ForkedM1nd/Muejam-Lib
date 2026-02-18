import { useState, useEffect } from 'react';
import { WelcomeModal } from './WelcomeModal';
import { ProfileSetupWizard } from './ProfileSetupWizard';
import { InterestSelection } from './InterestSelection';
import { InteractiveTutorial } from './InteractiveTutorial';

interface OnboardingFlowProps {
    onComplete: () => void;
}

type OnboardingStep = 'welcome' | 'profile' | 'interests' | 'tutorial' | 'complete';

export function OnboardingFlow({ onComplete }: OnboardingFlowProps) {
    const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');
    const [isOpen, setIsOpen] = useState(true);

    const handleSkip = async () => {
        // Call API to skip onboarding
        try {
            const response = await fetch('/v1/onboarding/skip/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
            });

            if (response.ok) {
                setIsOpen(false);
                onComplete();
            }
        } catch (error) {
            console.error('Failed to skip onboarding:', error);
        }
    };

    const handleWelcomeContinue = () => {
        setCurrentStep('profile');
    };

    const handleProfileComplete = async () => {
        // Call API to mark profile as completed
        try {
            await fetch('/v1/onboarding/step/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ step: 'profile_completed' }),
                credentials: 'include',
            });

            setCurrentStep('interests');
        } catch (error) {
            console.error('Failed to update onboarding step:', error);
        }
    };

    const handleInterestsComplete = async (interests: string[]) => {
        // Call API to save interests and mark step as completed
        try {
            // TODO: Save interests to user profile

            await fetch('/v1/onboarding/step/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ step: 'interests_selected' }),
                credentials: 'include',
            });

            setCurrentStep('tutorial');
        } catch (error) {
            console.error('Failed to update onboarding step:', error);
        }
    };

    const handleTutorialComplete = async () => {
        // Call API to mark tutorial as completed
        try {
            await fetch('/v1/onboarding/step/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ step: 'tutorial_completed' }),
                credentials: 'include',
            });

            setIsOpen(false);
            onComplete();
        } catch (error) {
            console.error('Failed to update onboarding step:', error);
        }
    };

    return (
        <>
            <WelcomeModal
                open={isOpen && currentStep === 'welcome'}
                onClose={handleSkip}
                onContinue={handleWelcomeContinue}
            />

            <ProfileSetupWizard
                open={isOpen && currentStep === 'profile'}
                onClose={handleSkip}
                onComplete={handleProfileComplete}
            />

            <InterestSelection
                open={isOpen && currentStep === 'interests'}
                onClose={handleSkip}
                onComplete={handleInterestsComplete}
            />

            <InteractiveTutorial
                open={isOpen && currentStep === 'tutorial'}
                onClose={handleSkip}
                onComplete={handleTutorialComplete}
            />
        </>
    );
}
