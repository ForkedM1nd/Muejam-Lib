import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft } from 'lucide-react';

interface HelpArticle {
    id: string;
    title: string;
    slug: string;
    category: string;
    excerpt: string;
    view_count: number;
}

const CATEGORY_LABELS: Record<string, string> = {
    'getting_started': 'Getting Started',
    'reading_stories': 'Reading Stories',
    'writing_content': 'Writing Content',
    'account_settings': 'Account Settings',
    'privacy_safety': 'Privacy & Safety',
    'troubleshooting': 'Troubleshooting',
};

export function HelpCategory() {
    const { category } = useParams<{ category: string }>();
    const [articles, setArticles] = useState<HelpArticle[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (category) {
            fetchArticles();
        }
    }, [category]);

    const fetchArticles = async () => {
        try {
            setLoading(true);
            const categoryUpper = category?.toUpperCase();
            const response = await fetch(`/v1/help/articles/?category=${categoryUpper}`);

            if (response.ok) {
                const data = await response.json();
                setArticles(data);
            }
        } catch (error) {
            console.error('Failed to fetch articles:', error);
        } finally {
            setLoading(false);
        }
    };

    const categoryLabel = category ? CATEGORY_LABELS[category] || category : '';

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center">Loading...</div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            <h1 className="text-3xl font-bold mb-2">{categoryLabel}</h1>
            <p className="text-muted-foreground mb-8">
                {articles.length} {articles.length === 1 ? 'article' : 'articles'} in this category
            </p>

            {articles.length > 0 ? (
                <div className="space-y-4">
                    {articles.map((article) => (
                        <Link key={article.id} to={`/help/articles/${article.slug}`}>
                            <Card className="hover:shadow-md transition-shadow">
                                <CardContent className="p-6">
                                    <h3 className="text-xl font-semibold mb-2">{article.title}</h3>
                                    {article.excerpt && (
                                        <p className="text-muted-foreground mb-2">{article.excerpt}</p>
                                    )}
                                    <p className="text-xs text-muted-foreground">
                                        {article.view_count} views
                                    </p>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>
            ) : (
                <Card>
                    <CardContent className="p-8 text-center">
                        <p className="text-muted-foreground">
                            No articles available in this category yet.
                        </p>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
