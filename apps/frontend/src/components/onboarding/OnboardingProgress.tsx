import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Check } from 'lucide-react';

interface OnboardingProgressProps {
    progress: {
        profile_completed: boolean;
        interests_selected: boolean;
        tutorial_completed: boolean;
        first_story_read: boolean;
        first_whisper_posted: boolean;
        first_follow: boolean;
        authors_followed_count: number;
        onboarding_completed: boolean;
    };
}

export function OnboardingProgress({ progress }: OnboardingProgressProps) {
    const steps = [
        { key: 'profile_completed', label: 'Complete your profile', completed: progress.profile_completed },
        { key: 'interests_selected', label: 'Select your interests', completed: progress.interests_selected },
        { key: 'tutorial_completed', label: 'Complete the tutorial', completed: progress.tutorial_completed },
        { key: 'first_follow', label: `Follow 3 authors (${progress.authors_followed_count}/3)`, completed: progress.authors_followed_count >= 3 },
        { key: 'first_story_read', label: 'Read your first story', completed: progress.first_story_read },
    ];

    const completedSteps = steps.filter(step => step.completed).length;
    const progressPercentage = (completedSteps / steps.length) * 100;

    if (progress.onboarding_completed) {
        return null;
    }

    return (
        <Card className="mb-6">
            <CardHeader>
                <CardTitle>Complete Your Onboarding</CardTitle>
                <CardDescription>
                    {completedSteps} of {steps.length} steps completed
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <Progress value={progressPercentage} className="h-2" />

                <div className="space-y-2">
                    {steps.map((step) => (
                        <div key={step.key} className="flex items-center gap-2">
                            <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center ${step.completed ? 'bg-primary text-primary-foreground' : 'bg-muted'
                                }`}>
                                {step.completed && <Check className="h-3 w-3" />}
                            </div>
                            <span className={step.completed ? 'text-muted-foreground line-through' : ''}>
                                {step.label}
                            </span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
