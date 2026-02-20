import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BookOpen, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '@/lib/api';
import type { Story } from '@/types';

interface RecommendedStoriesProps {
    interests?: string[];
}

export function RecommendedStories({ interests = [] }: RecommendedStoriesProps) {
    const [stories, setStories] = useState<Story[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRecommendedStories();
    }, [interests]);

    const fetchRecommendedStories = async () => {
        try {
            setLoading(true);
            const feed = await api.getDiscoverFeed({
                tab: interests.length > 0 ? 'for-you' : 'trending',
                page_size: 3,
            });
            setStories(feed.results.slice(0, 3));
        } catch (error) {
            console.error('Failed to fetch recommended stories:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Recommended for You
                    </CardTitle>
                    <CardDescription>Loading recommendations...</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    if (stories.length === 0) {
        return null;
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Recommended for You
                </CardTitle>
                <CardDescription>
                    {interests.length > 0
                        ? 'Based on your interests'
                        : 'Popular stories to get you started'}
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {stories.map((story) => (
                    <div key={story.id} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between">
                            <div className="space-y-1 flex-1">
                                <Link
                                    to={`/story/${story.slug}`}
                                    className="font-semibold hover:underline"
                                >
                                    {story.title}
                                </Link>
                                <p className="text-sm text-muted-foreground">
                                    by {story.author.display_name}
                                </p>
                            </div>
                            <BookOpen className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                        </div>
                        <p className="text-sm line-clamp-2">{story.blurb || 'No description yet.'}</p>
                        {story.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                                {story.tags.slice(0, 3).map((tag) => (
                                    <span
                                        key={tag.id}
                                        className="text-xs bg-muted px-2 py-1 rounded"
                                    >
                                        {tag.name}
                                    </span>
                                ))}
                            </div>
                        )}
                        <Link to={`/story/${story.slug}`}>
                            <Button size="sm" variant="outline" className="w-full">
                                Start Reading
                            </Button>
                        </Link>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}
