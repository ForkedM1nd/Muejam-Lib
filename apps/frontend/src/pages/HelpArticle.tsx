import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ThumbsUp, ThumbsDown, ArrowLeft, Eye } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Article {
    id: string;
    title: string;
    slug: string;
    category: string;
    content: string;
    view_count: number;
    helpful_yes: number;
    helpful_no: number;
    created_at: string;
    updated_at: string;
}

export function HelpArticle() {
    const { slug } = useParams<{ slug: string }>();
    const [article, setArticle] = useState<Article | null>(null);
    const [loading, setLoading] = useState(true);
    const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
    const [showCommentBox, setShowCommentBox] = useState(false);
    const [comment, setComment] = useState('');

    useEffect(() => {
        if (slug) {
            fetchArticle();
        }
    }, [slug]);

    const fetchArticle = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/v1/help/articles/${slug}/`);

            if (response.ok) {
                const data = await response.json();
                setArticle(data);
            }
        } catch (error) {
            console.error('Failed to fetch article:', error);
        } finally {
            setLoading(false);
        }
    };

    const submitFeedback = async (helpful: boolean) => {
        if (!article || feedbackSubmitted) return;

        try {
            const response = await fetch(`/v1/help/articles/${article.id}/feedback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    helpful,
                    comment: comment || undefined
                }),
            });

            if (response.ok) {
                setFeedbackSubmitted(true);
                if (!helpful) {
                    setShowCommentBox(false);
                }
            }
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        }
    };

    const handleNotHelpful = () => {
        setShowCommentBox(true);
    };

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center">Loading...</div>
            </div>
        );
    }

    if (!article) {
        return (
            <div className="container mx-auto px-4 py-8">
                <Card>
                    <CardContent className="p-8 text-center">
                        <h2 className="text-2xl font-semibold mb-4">Article Not Found</h2>
                        <p className="text-muted-foreground mb-6">
                            The help article you're looking for doesn't exist.
                        </p>
                        <Link to="/help">
                            <Button>Back to Help Center</Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            {/* Back button */}
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            {/* Article */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                        <Eye className="h-4 w-4" />
                        {article.view_count} views
                    </div>
                    <CardTitle className="text-3xl">{article.title}</CardTitle>
                </CardHeader>
                <CardContent className="prose prose-slate max-w-none">
                    <ReactMarkdown>{article.content}</ReactMarkdown>
                </CardContent>
            </Card>

            {/* Feedback */}
            <Card className="mt-6">
                <CardContent className="p-6">
                    {!feedbackSubmitted ? (
                        <div>
                            <h3 className="font-semibold mb-4">Was this article helpful?</h3>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    onClick={() => submitFeedback(true)}
                                    className="flex items-center gap-2"
                                >
                                    <ThumbsUp className="h-4 w-4" />
                                    Yes
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={handleNotHelpful}
                                    className="flex items-center gap-2"
                                >
                                    <ThumbsDown className="h-4 w-4" />
                                    No
                                </Button>
                            </div>

                            {showCommentBox && (
                                <div className="mt-4 space-y-3">
                                    <p className="text-sm text-muted-foreground">
                                        Help us improve this article. What was missing or unclear?
                                    </p>
                                    <Textarea
                                        placeholder="Your feedback..."
                                        value={comment}
                                        onChange={(e) => setComment(e.target.value)}
                                        rows={4}
                                    />
                                    <Button onClick={() => submitFeedback(false)}>
                                        Submit Feedback
                                    </Button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-center py-4">
                            <p className="text-green-600 font-medium">
                                Thank you for your feedback!
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Stats */}
            <div className="mt-4 text-center text-sm text-muted-foreground">
                {article.helpful_yes + article.helpful_no > 0 && (
                    <p>
                        {article.helpful_yes} of {article.helpful_yes + article.helpful_no} people found this helpful
                    </p>
                )}
            </div>
        </div>
    );
}
