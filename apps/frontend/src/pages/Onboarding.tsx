import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import { ProfileSetupWizard } from '@/components/onboarding/ProfileSetupWizard';
import { InterestSelection } from '@/components/onboarding/InterestSelection';
import { AuthorRecommendations } from '@/components/onboarding/AuthorRecommendations';
import { useOnboarding } from '@/hooks/useOnboarding';
import { toast } from '@/hooks/use-toast';
import SurfacePanel from '@/components/shared/SurfacePanel';
import PageHeader from '@/components/shared/PageHeader';

type OnboardingStep = 'profile' | 'interests' | 'authors';

const STEPS: { id: OnboardingStep; title: string; description: string }[] = [
    {
        id: 'profile',
        title: 'Set Up Your Profile',
        description: 'Tell us about yourself',
    },
    {
        id: 'interests',
        title: 'Choose Your Interests',
        description: 'Select genres you enjoy',
    },
    {
        id: 'authors',
        title: 'Follow Authors',
        description: 'Discover talented writers',
    },
];

export default function Onboarding() {
    const navigate = useNavigate();
    const { progress, updateStep, skipOnboarding, markAsOnboarded } = useOnboarding();
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
    const [completedSteps, setCompletedSteps] = useState<Set<OnboardingStep>>(new Set());

    const currentStep = STEPS[currentStepIndex];
    const progressPercentage = ((currentStepIndex + 1) / STEPS.length) * 100;

    useEffect(() => {
        // Check if onboarding is already completed
        if (progress?.onboarding_completed) {
            navigate('/discover');
        }
    }, [progress, navigate]);

    const handleNext = () => {
        if (currentStepIndex < STEPS.length - 1) {
            setCurrentStepIndex(prev => prev + 1);
        }
    };

    const handleBack = () => {
        if (currentStepIndex > 0) {
            setCurrentStepIndex(prev => prev - 1);
        }
    };

    const handleSkip = async () => {
        const success = await skipOnboarding();
        if (success) {
            toast({
                title: 'Onboarding skipped',
                description: 'You can complete it later from your profile settings.',
            });
            navigate('/discover');
        } else {
            toast({
                title: 'Error',
                description: 'Failed to skip onboarding. Please try again.',
                variant: 'destructive',
            });
        }
    };

    const handleProfileComplete = async (profileData: { displayName: string; bio: string; avatar?: File }) => {
        // Mark profile step as completed
        const success = await updateStep('profile_completed');
        if (success) {
            setCompletedSteps(prev => new Set(prev).add('profile'));
            handleNext();
        } else {
            toast({
                title: 'Error',
                description: 'Failed to save profile. Please try again.',
                variant: 'destructive',
            });
        }
    };

    const handleInterestsComplete = async (interests: string[]) => {
        setSelectedInterests(interests);
        // Mark interests step as completed
        const success = await updateStep('interests_selected');
        if (success) {
            setCompletedSteps(prev => new Set(prev).add('interests'));
            handleNext();
        } else {
            toast({
                title: 'Error',
                description: 'Failed to save interests. Please try again.',
                variant: 'destructive',
            });
        }
    };

    const handleAuthorsComplete = async (followedAuthors: string[]) => {
        // Mark onboarding as completed via backend
        const success = await markAsOnboarded();
        if (success) {
            toast({
                title: 'Welcome to MueJam!',
                description: 'Your onboarding is complete. Start exploring stories!',
            });
            navigate('/discover');
        } else {
            toast({
                title: 'Error',
                description: 'Failed to complete onboarding. Please try again.',
                variant: 'destructive',
            });
        }
    };

    return (
        <div className="min-h-screen bg-[linear-gradient(180deg,hsl(var(--background))_0%,hsl(var(--secondary)/0.65)_24%,hsl(var(--background))_76%)] p-4 sm:p-6">
            <div className="mx-auto max-w-5xl space-y-5">
                <PageHeader
                    title="Welcome to MueJam"
                    eyebrow="Onboarding"
                    description="Let's personalize your space in a few quick steps."
                    action={(
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleSkip}
                            className="text-muted-foreground hover:text-foreground"
                        >
                            <X className="h-5 w-5" />
                        </Button>
                    )}
                />

                <SurfacePanel className="p-5 sm:p-6">

                    {/* Progress Bar */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">
                                Step {currentStepIndex + 1} of {STEPS.length}
                            </span>
                            <span className="text-sm text-muted-foreground">
                                {Math.round(progressPercentage)}% complete
                            </span>
                        </div>
                        <Progress value={progressPercentage} className="h-2" />
                    </div>

                    {/* Step Indicator */}
                    <div className="flex items-center justify-between mb-8">
                        {STEPS.map((step, index) => (
                            <div
                                key={step.id}
                                className={`flex-1 ${index < STEPS.length - 1 ? 'mr-2' : ''}`}
                            >
                                <div
                                    className={`flex items-center gap-2 p-3 rounded-lg border-2 transition-colors ${index === currentStepIndex
                                        ? 'border-primary bg-secondary/75'
                                        : completedSteps.has(step.id)
                                            ? 'border-primary/35 bg-primary/10'
                                            : 'border-border bg-background'
                                        }`}
                                >
                                    <div
                                        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold ${index === currentStepIndex
                                            ? 'bg-primary text-primary-foreground'
                                            : completedSteps.has(step.id)
                                                ? 'bg-primary/80 text-primary-foreground'
                                                : 'bg-muted text-muted-foreground'
                                            }`}
                                    >
                                        {completedSteps.has(step.id) ? '✓' : index + 1}
                                    </div>
                                    <div className="hidden sm:block">
                                        <div className="text-sm font-medium">{step.title}</div>
                                        <div className="text-xs text-muted-foreground">{step.description}</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Step Content */}
                    <div className="min-h-[400px] mb-6">
                        {currentStep.id === 'profile' && (
                            <ProfileSetupWizard
                                open={true}
                                onClose={handleSkip}
                                onComplete={handleProfileComplete}
                            />
                        )}

                        {currentStep.id === 'interests' && (
                            <InterestSelection
                                open={true}
                                onClose={handleSkip}
                                onComplete={handleInterestsComplete}
                            />
                        )}

                        {currentStep.id === 'authors' && (
                            <AuthorRecommendations
                                open={true}
                                onClose={handleSkip}
                                onComplete={handleAuthorsComplete}
                                interests={selectedInterests}
                            />
                        )}
                    </div>

                    {/* Navigation Buttons */}
                    <div className="flex items-center justify-between pt-6 border-t">
                        <Button
                            variant="outline"
                            onClick={handleBack}
                            disabled={currentStepIndex === 0}
                        >
                            <ChevronLeft className="h-4 w-4 mr-1" />
                            Back
                        </Button>

                        <Button variant="ghost" onClick={handleSkip}>
                            Skip for now
                        </Button>
                    </div>
                </SurfacePanel>
            </div>
        </div>
    );
}
