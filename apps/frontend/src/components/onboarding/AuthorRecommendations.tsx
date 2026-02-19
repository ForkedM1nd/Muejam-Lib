import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { UserPlus, Check } from 'lucide-react';

interface Author {
    id: string;
    handle: string;
    display_name: string;
    avatar_url?: string;
    bio?: string;
    follower_count: number;
    story_count: number;
}

interface AuthorRecommendationsProps {
    open: boolean;
    onClose: () => void;
    onComplete: (followedAuthors: string[]) => void;
    interests: string[];
}

export function AuthorRecommendations({ open, onClose, onComplete, interests }: AuthorRecommendationsProps) {
    const [authors, setAuthors] = useState<Author[]>([]);
    const [followedAuthors, setFollowedAuthors] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (open) {
            fetchRecommendedAuthors();
        }
    }, [open, interests]);

    const fetchRecommendedAuthors = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual API endpoint that takes interests into account
            const response = await fetch('/v1/users/recommended/', {
                credentials: 'include',
            });

            if (response.ok) {
                const data = await response.json();
                setAuthors(data.results || data);
            }
        } catch (error) {
            console.error('Failed to fetch recommended authors:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleFollow = async (authorId: string) => {
        const isFollowing = followedAuthors.has(authorId);

        try {
            const response = await fetch(`/v1/users/${authorId}/follow/`, {
                method: isFollowing ? 'DELETE' : 'POST',
                credentials: 'include',
            });

            if (response.ok) {
                setFollowedAuthors(prev => {
                    const newSet = new Set(prev);
                    if (isFollowing) {
                        newSet.delete(authorId);
                    } else {
                        newSet.add(authorId);
                    }
                    return newSet;
                });
            }
        } catch (error) {
            console.error('Failed to toggle follow:', error);
        }
    };

    const handleComplete = () => {
        onComplete(Array.from(followedAuthors));
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Follow Authors You'll Love</DialogTitle>
                    <DialogDescription>
                        Discover talented writers based on your interests. Follow at least 3 to get started.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-4">
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                    ) : authors.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            No recommended authors found. Try selecting more interests!
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {authors.map((author) => {
                                const isFollowing = followedAuthors.has(author.id);
                                return (
                                    <Card key={author.id} className="hover:shadow-md transition-shadow">
                                        <CardHeader className="pb-3">
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-center gap-3">
                                                    <Avatar className="h-12 w-12">
                                                        <AvatarImage src={author.avatar_url} alt={author.display_name} />
                                                        <AvatarFallback>
                                                            {author.display_name.substring(0, 2).toUpperCase()}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <div>
                                                        <CardTitle className="text-base">{author.display_name}</CardTitle>
                                                        <CardDescription>@{author.handle}</CardDescription>
                                                    </div>
                                                </div>
                                                <Button
                                                    size="sm"
                                                    variant={isFollowing ? 'secondary' : 'default'}
                                                    onClick={() => toggleFollow(author.id)}
                                                >
                                                    {isFollowing ? (
                                                        <>
                                                            <Check className="h-4 w-4 mr-1" />
                                                            Following
                                                        </>
                                                    ) : (
                                                        <>
                                                            <UserPlus className="h-4 w-4 mr-1" />
                                                            Follow
                                                        </>
                                                    )}
                                                </Button>
                                            </div>
                                        </CardHeader>
                                        {author.bio && (
                                            <CardContent className="pt-0">
                                                <p className="text-sm text-muted-foreground line-clamp-2">{author.bio}</p>
                                                <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                                                    <span>{author.follower_count} followers</span>
                                                    <span>{author.story_count} stories</span>
                                                </div>
                                            </CardContent>
                                        )}
                                    </Card>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="flex gap-2 justify-between items-center">
                    <div className="text-sm text-muted-foreground">
                        {followedAuthors.size} author{followedAuthors.size !== 1 ? 's' : ''} followed
                        {followedAuthors.size < 3 && ` (${3 - followedAuthors.size} more to continue)`}
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={onClose}>
                            Skip
                        </Button>
                        <Button
                            onClick={handleComplete}
                            disabled={followedAuthors.size < 3}
                        >
                            Continue
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
