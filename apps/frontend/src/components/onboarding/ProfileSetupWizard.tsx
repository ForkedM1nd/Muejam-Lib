import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface ProfileSetupWizardProps {
    open: boolean;
    onClose: () => void;
    onComplete: () => void;
}

export function ProfileSetupWizard({ open, onClose, onComplete }: ProfileSetupWizardProps) {
    const [displayName, setDisplayName] = useState('');
    const [bio, setBio] = useState('');

    const handleSubmit = async () => {
        // TODO: Call API to update profile
        onComplete();
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Set Up Your Profile</DialogTitle>
                    <DialogDescription>
                        Tell us a bit about yourself to personalize your experience.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="displayName">Display Name</Label>
                        <Input
                            id="displayName"
                            placeholder="How should we call you?"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="bio">Bio (Optional)</Label>
                        <Textarea
                            id="bio"
                            placeholder="Tell us about yourself..."
                            value={bio}
                            onChange={(e) => setBio(e.target.value)}
                            rows={4}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="avatar">Profile Picture (Optional)</Label>
                        <Input
                            id="avatar"
                            type="file"
                            accept="image/*"
                        />
                    </div>
                </div>

                <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={onClose}>
                        Skip
                    </Button>
                    <Button onClick={handleSubmit}>
                        Continue
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
