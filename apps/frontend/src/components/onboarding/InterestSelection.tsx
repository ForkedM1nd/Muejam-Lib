import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check } from 'lucide-react';
import { RecommendedStories } from './RecommendedStories';

interface InterestSelectionProps {
    open: boolean;
    onClose: () => void;
    onComplete: (interests: string[]) => void;
}

const AVAILABLE_INTERESTS = [
    'Fantasy',
    'Science Fiction',
    'Romance',
    'Mystery',
    'Thriller',
    'Horror',
    'Adventure',
    'Drama',
    'Comedy',
    'Historical',
    'Young Adult',
    'Poetry',
];

export function InterestSelection({ open, onClose, onComplete }: InterestSelectionProps) {
    const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
    const [showRecommendations, setShowRecommendations] = useState(false);

    const toggleInterest = (interest: string) => {
        setSelectedInterests(prev =>
            prev.includes(interest)
                ? prev.filter(i => i !== interest)
                : [...prev, interest]
        );
    };

    const handleContinue = () => {
        if (selectedInterests.length > 0) {
            setShowRecommendations(true);
        } else {
            onComplete(selectedInterests);
        }
    };

    const handleFinish = () => {
        onComplete(selectedInterests);
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>
                        {showRecommendations ? 'Stories You Might Like' : 'What are you interested in?'}
                    </DialogTitle>
                    <DialogDescription>
                        {showRecommendations
                            ? 'Check out these popular stories based on your interests'
                            : 'Select genres you enjoy so we can recommend stories you\'ll love.'}
                    </DialogDescription>
                </DialogHeader>

                {!showRecommendations ? (
                    <div className="py-4">
                        <div className="flex flex-wrap gap-2">
                            {AVAILABLE_INTERESTS.map((interest) => {
                                const isSelected = selectedInterests.includes(interest);
                                return (
                                    <Badge
                                        key={interest}
                                        variant={isSelected ? 'default' : 'outline'}
                                        className="cursor-pointer px-3 py-2 text-sm"
                                        onClick={() => toggleInterest(interest)}
                                    >
                                        {isSelected && <Check className="h-3 w-3 mr-1" />}
                                        {interest}
                                    </Badge>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div className="py-4">
                        <RecommendedStories interests={selectedInterests} />
                    </div>
                )}

                <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={onClose}>
                        Skip
                    </Button>
                    <Button
                        onClick={showRecommendations ? handleFinish : handleContinue}
                        disabled={!showRecommendations && selectedInterests.length === 0}
                    >
                        {showRecommendations ? 'Continue' : 'See Recommendations'}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
