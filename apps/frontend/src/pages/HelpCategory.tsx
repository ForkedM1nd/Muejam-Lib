import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import PageHeader from '@/components/shared/PageHeader';
import SurfacePanel from '@/components/shared/SurfacePanel';

interface HelpArticle {
    id: string;
    title: string;
    slug: string;
    category: string;
    excerpt: string;
    view_count: number;
}

const CATEGORY_LABELS: Record<string, string> = {
    getting_started: 'Getting Started',
    reading_stories: 'Reading Stories',
    writing_content: 'Writing Content',
    account_settings: 'Account Settings',
    privacy_safety: 'Privacy & Safety',
    troubleshooting: 'Troubleshooting',
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
            <div className="mx-auto max-w-4xl">
                <SurfacePanel className="p-8 text-center">Loading articles...</SurfacePanel>
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
                title={categoryLabel}
                eyebrow="Help Category"
                description={`${articles.length} ${articles.length === 1 ? 'article' : 'articles'} in this category.`}
            />

            {articles.length > 0 ? (
                <div className="space-y-3">
                    {articles.map((article) => (
                        <Link key={article.id} to={`/help/articles/${article.slug}`}>
                            <SurfacePanel className="p-5 transition-colors hover:bg-secondary/45">
                                <h3 className="text-lg font-semibold">{article.title}</h3>
                                {article.excerpt && (
                                    <p className="mt-1 text-sm text-muted-foreground">{article.excerpt}</p>
                                )}
                                <p className="mt-2 text-xs text-muted-foreground">{article.view_count} views</p>
                            </SurfacePanel>
                        </Link>
                    ))}
                </div>
            ) : (
                <SurfacePanel className="p-8 text-center text-muted-foreground">
                    No articles available in this category yet.
                </SurfacePanel>
            )}
        </div>
    );
}
