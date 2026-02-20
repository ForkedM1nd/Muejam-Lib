import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ThumbsUp, ThumbsDown, ArrowLeft, Eye } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import PageHeader from '@/components/shared/PageHeader';
import SurfacePanel from '@/components/shared/SurfacePanel';

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
                    comment: comment || undefined,
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

    if (loading) {
        return (
            <div className="mx-auto max-w-4xl">
                <SurfacePanel className="p-8 text-center">Loading article...</SurfacePanel>
            </div>
        );
    }

    if (!article) {
        return (
            <div className="mx-auto max-w-4xl">
                <SurfacePanel className="p-8 text-center">
                    <h2 className="text-2xl font-semibold">Article Not Found</h2>
                    <p className="mt-2 text-muted-foreground">
                        The help article you're looking for doesn't exist.
                    </p>
                    <div className="mt-5">
                        <Link to="/help">
                            <Button>Back to Help Center</Button>
                        </Link>
                    </div>
                </SurfacePanel>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-4xl space-y-5">
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            <PageHeader
                title={article.title}
                eyebrow="Help Article"
                description={`Updated ${new Date(article.updated_at).toLocaleDateString()}`}
                action={(
                    <div className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <Eye className="h-4 w-4" />
                        {article.view_count} views
                    </div>
                )}
            />

            <SurfacePanel className="p-5 sm:p-6">
                <div className="prose prose-slate max-w-none dark:prose-invert">
                    <ReactMarkdown>{article.content}</ReactMarkdown>
                </div>
            </SurfacePanel>

            <SurfacePanel className="p-5 sm:p-6">
                {!feedbackSubmitted ? (
                    <div>
                        <h3 className="font-semibold">Was this article helpful?</h3>
                        <div className="mt-3 flex gap-2">
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
                                onClick={() => setShowCommentBox(true)}
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
                                <Button onClick={() => submitFeedback(false)}>Submit Feedback</Button>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-sm font-medium text-primary">Thank you for your feedback!</p>
                )}
            </SurfacePanel>

            {article.helpful_yes + article.helpful_no > 0 && (
                <p className="text-center text-sm text-muted-foreground">
                    {article.helpful_yes} of {article.helpful_yes + article.helpful_no} people found this helpful.
                </p>
            )}
        </div>
    );
}
