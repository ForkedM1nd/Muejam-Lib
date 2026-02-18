import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { BookOpen, MessageCircle, Users } from 'lucide-react';

interface WelcomeModalProps {
    open: boolean;
    onClose: () => void;
    onContinue: () => void;
}

export function WelcomeModal({ open, onClose, onContinue }: WelcomeModalProps) {
    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="text-2xl">Welcome to MueJam Library!</DialogTitle>
                    <DialogDescription className="text-base pt-4">
                        Discover amazing stories, connect with authors, and share your thoughts.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <BookOpen className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h4 className="font-medium">Read Serial Stories</h4>
                            <p className="text-sm text-muted-foreground">
                                Explore a vast library of ongoing stories updated regularly by talented authors.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <MessageCircle className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h4 className="font-medium">Share Whispers</h4>
                            <p className="text-sm text-muted-foreground">
                                Post quick thoughts and reactions to stories you love.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <Users className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h4 className="font-medium">Follow Authors</h4>
                            <p className="text-sm text-muted-foreground">
                                Stay updated with your favorite authors and never miss a new chapter.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={onClose}>
                        Skip
                    </Button>
                    <Button onClick={onContinue}>
                        Get Started
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
