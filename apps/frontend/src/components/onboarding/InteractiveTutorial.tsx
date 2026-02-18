import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { BookOpen, MessageCircle, Users, Heart } from 'lucide-react';

interface InteractiveTutorialProps {
    open: boolean;
    onClose: () => void;
    onComplete: () => void;
}

const TUTORIAL_STEPS = [
    {
        icon: BookOpen,
        title: 'Discover Stories',
        description: 'Browse our library to find stories that match your interests. Click on any story to start reading.',
    },
    {
        icon: MessageCircle,
        title: 'Post Whispers',
        description: 'Share your thoughts about stories with quick posts called "Whispers". You can whisper about specific highlights or just share general thoughts.',
    },
    {
        icon: Users,
        title: 'Follow Authors',
        description: 'Follow your favorite authors to get notified when they publish new chapters or stories.',
    },
    {
        icon: Heart,
        title: 'Engage with Content',
        description: 'Like whispers, bookmark chapters, and highlight your favorite passages to save them for later.',
    },
];

export function InteractiveTutorial({ open, onClose, onComplete }: InteractiveTutorialProps) {
    const [currentStep, setCurrentStep] = useState(0);

    const handleNext = () => {
        if (currentStep < TUTORIAL_STEPS.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            onComplete();
        }
    };

    const handlePrevious = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const step = TUTORIAL_STEPS[currentStep];
    const Icon = step.icon;

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Quick Tutorial</DialogTitle>
                    <DialogDescription>
                        Step {currentStep + 1} of {TUTORIAL_STEPS.length}
                    </DialogDescription>
                </DialogHeader>

                <div className="py-6">
                    <div className="flex flex-col items-center text-center space-y-4">
                        <div className="p-4 bg-primary/10 rounded-full">
                            <Icon className="h-12 w-12 text-primary" />
                        </div>
                        <h3 className="text-xl font-semibold">{step.title}</h3>
                        <p className="text-muted-foreground">{step.description}</p>
                    </div>
                </div>

                <div className="flex gap-2 justify-between">
                    <Button
                        variant="outline"
                        onClick={handlePrevious}
                        disabled={currentStep === 0}
                    >
                        Previous
                    </Button>
                    <div className="flex gap-1">
                        {TUTORIAL_STEPS.map((_, index) => (
                            <div
                                key={index}
                                className={`h-2 w-2 rounded-full ${index === currentStep ? 'bg-primary' : 'bg-muted'
                                    }`}
                            />
                        ))}
                    </div>
                    <Button onClick={handleNext}>
                        {currentStep === TUTORIAL_STEPS.length - 1 ? 'Finish' : 'Next'}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
