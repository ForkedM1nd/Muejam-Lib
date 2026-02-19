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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Upload } from 'lucide-react';

interface ProfileSetupWizardProps {
    open: boolean;
    onClose: () => void;
    onComplete: (data: { displayName: string; bio: string; avatar?: File }) => void;
}

export function ProfileSetupWizard({ open, onClose, onComplete }: ProfileSetupWizardProps) {
    const [displayName, setDisplayName] = useState('');
    const [bio, setBio] = useState('');
    const [avatar, setAvatar] = useState<File | null>(null);
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setAvatar(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setAvatarPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async () => {
        if (!displayName.trim()) {
            return;
        }

        setIsSubmitting(true);
        try {
            // Call API to update profile
            const formData = new FormData();
            formData.append('display_name', displayName);
            if (bio.trim()) {
                formData.append('bio', bio);
            }
            if (avatar) {
                formData.append('avatar', avatar);
            }

            const response = await fetch('/v1/users/me/', {
                method: 'PATCH',
                body: formData,
                credentials: 'include',
            });

            if (response.ok) {
                onComplete({ displayName, bio, avatar: avatar || undefined });
            } else {
                console.error('Failed to update profile');
            }
        } catch (error) {
            console.error('Failed to update profile:', error);
        } finally {
            setIsSubmitting(false);
        }
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

                <div className="space-y-6 py-4">
                    {/* Avatar Upload */}
                    <div className="flex flex-col items-center gap-4">
                        <Avatar className="h-24 w-24">
                            <AvatarImage src={avatarPreview || undefined} />
                            <AvatarFallback className="text-2xl">
                                {displayName ? displayName.substring(0, 2).toUpperCase() : '?'}
                            </AvatarFallback>
                        </Avatar>
                        <Label htmlFor="avatar" className="cursor-pointer">
                            <div className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-accent transition-colors">
                                <Upload className="h-4 w-4" />
                                <span className="text-sm">Upload Profile Picture</span>
                            </div>
                            <Input
                                id="avatar"
                                type="file"
                                accept="image/*"
                                className="hidden"
                                onChange={handleAvatarChange}
                            />
                        </Label>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="displayName">
                            Display Name <span className="text-destructive">*</span>
                        </Label>
                        <Input
                            id="displayName"
                            placeholder="How should we call you?"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                            required
                        />
                        <p className="text-xs text-muted-foreground">
                            This is how other users will see you
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="bio">Bio (Optional)</Label>
                        <Textarea
                            id="bio"
                            placeholder="Tell us about yourself..."
                            value={bio}
                            onChange={(e) => setBio(e.target.value)}
                            rows={4}
                            maxLength={500}
                        />
                        <p className="text-xs text-muted-foreground text-right">
                            {bio.length}/500 characters
                        </p>
                    </div>
                </div>

                <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
                        Skip
                    </Button>
                    <Button onClick={handleSubmit} disabled={!displayName.trim() || isSubmitting}>
                        {isSubmitting ? 'Saving...' : 'Continue'}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
