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

interface InterestSelectionProps {
    open: boolean;
    onClose: () => void;
    onComplete: (interests: string[]) => void;
}

const AVAILABLE_GENRES = [
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
    'Non-Fiction',
    'Biography',
    'Self-Help',
    'Action',
];

const AVAILABLE_TAGS = [
    'Magic',
    'Dragons',
    'Space',
    'Time Travel',
    'Vampires',
    'Werewolves',
    'Dystopian',
    'Post-Apocalyptic',
    'Steampunk',
    'Cyberpunk',
    'Urban Fantasy',
    'Epic Fantasy',
    'Paranormal',
    'Supernatural',
    'Coming of Age',
    'LGBTQ+',
];

export function InterestSelection({ open, onClose, onComplete }: InterestSelectionProps) {
    const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const toggleGenre = (genre: string) => {
        setSelectedGenres(prev =>
            prev.includes(genre)
                ? prev.filter(g => g !== genre)
                : [...prev, genre]
        );
    };

    const toggleTag = (tag: string) => {
        setSelectedTags(prev =>
            prev.includes(tag)
                ? prev.filter(t => t !== tag)
                : [...prev, tag]
        );
    };

    const handleContinue = async () => {
        if (selectedGenres.length === 0) {
            return;
        }

        setIsSubmitting(true);
        try {
            onComplete([...selectedGenres, ...selectedTags]);
        } finally {
            setIsSubmitting(false);
        }
    };

    const totalSelected = selectedGenres.length + selectedTags.length;

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>What are you interested in?</DialogTitle>
                    <DialogDescription>
                        Select at least one genre and optionally some tags to help us recommend stories you'll love.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-4 space-y-6">
                    {/* Genres Section */}
                    <div className="space-y-3">
                        <div>
                            <h3 className="text-sm font-semibold mb-2">Genres</h3>
                            <p className="text-xs text-muted-foreground mb-3">
                                Select at least one genre
                            </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {AVAILABLE_GENRES.map((genre) => {
                                const isSelected = selectedGenres.includes(genre);
                                return (
                                    <Badge
                                        key={genre}
                                        variant={isSelected ? 'default' : 'outline'}
                                        className="cursor-pointer px-3 py-2 text-sm hover:scale-105 transition-transform"
                                        onClick={() => toggleGenre(genre)}
                                    >
                                        {isSelected && <Check className="h-3 w-3 mr-1" />}
                                        {genre}
                                    </Badge>
                                );
                            })}
                        </div>
                    </div>

                    {/* Tags Section */}
                    <div className="space-y-3">
                        <div>
                            <h3 className="text-sm font-semibold mb-2">Tags (Optional)</h3>
                            <p className="text-xs text-muted-foreground mb-3">
                                Add specific themes or elements you enjoy
                            </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {AVAILABLE_TAGS.map((tag) => {
                                const isSelected = selectedTags.includes(tag);
                                return (
                                    <Badge
                                        key={tag}
                                        variant={isSelected ? 'secondary' : 'outline'}
                                        className="cursor-pointer px-3 py-2 text-sm hover:scale-105 transition-transform"
                                        onClick={() => toggleTag(tag)}
                                    >
                                        {isSelected && <Check className="h-3 w-3 mr-1" />}
                                        {tag}
                                    </Badge>
                                );
                            })}
                        </div>
                    </div>

                    {/* Selection Summary */}
                    {totalSelected > 0 && (
                        <div className="p-3 bg-muted rounded-lg">
                            <p className="text-sm">
                                <span className="font-semibold">{totalSelected}</span> interest{totalSelected !== 1 ? 's' : ''} selected
                                {selectedGenres.length > 0 && (
                                    <span className="text-muted-foreground">
                                        {' '}({selectedGenres.length} genre{selectedGenres.length !== 1 ? 's' : ''}
                                        {selectedTags.length > 0 && `, ${selectedTags.length} tag${selectedTags.length !== 1 ? 's' : ''}`})
                                    </span>
                                )}
                            </p>
                        </div>
                    )}
                </div>

                <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
                        Skip
                    </Button>
                    <Button
                        onClick={handleContinue}
                        disabled={selectedGenres.length === 0 || isSubmitting}
                    >
                        {isSubmitting ? 'Saving...' : 'Continue'}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
