import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText } from 'lucide-react';

interface RelatedArticle {
    id: string;
    title: string;
    slug: string;
    excerpt?: string;
}

interface RelatedArticlesProps {
    articleId: string;
    onFetchRelated: (articleId: string) => Promise<RelatedArticle[]>;
}

export function RelatedArticles({ articleId, onFetchRelated }: RelatedArticlesProps) {
    const [articles, setArticles] = useState<RelatedArticle[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchRelated() {
            try {
                setLoading(true);
                const related = await onFetchRelated(articleId);
                setArticles(related);
            } catch (error) {
                console.error('Failed to fetch related articles:', error);
            } finally {
                setLoading(false);
            }
        }

        fetchRelated();
    }, [articleId, onFetchRelated]);

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Related Articles</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">Loading...</p>
                </CardContent>
            </Card>
        );
    }

    if (articles.length === 0) {
        return null;
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Related Articles
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {articles.map((article) => (
                        <Link
                            key={article.id}
                            to={`/help/articles/${article.slug}`}
                            className="block p-3 rounded-lg hover:bg-muted/50 transition-colors"
                        >
                            <h4 className="font-medium mb-1">{article.title}</h4>
                            {article.excerpt && (
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                    {article.excerpt}
                                </p>
                            )}
                        </Link>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
