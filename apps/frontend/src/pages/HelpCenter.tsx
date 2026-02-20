import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, BookOpen, TrendingUp, Mail, ArrowRight } from 'lucide-react';
import PageHeader from '@/components/shared/PageHeader';
import SurfacePanel from '@/components/shared/SurfacePanel';

interface HelpCategory {
    value: string;
    label: string;
    icon: React.ReactNode;
}

interface HelpArticle {
    id: string;
    title: string;
    slug: string;
    category: string;
    excerpt: string;
    view_count: number;
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    GETTING_STARTED: <BookOpen className="h-5 w-5" />,
    READING_STORIES: <BookOpen className="h-5 w-5" />,
    WRITING_CONTENT: <BookOpen className="h-5 w-5" />,
    ACCOUNT_SETTINGS: <BookOpen className="h-5 w-5" />,
    PRIVACY_SAFETY: <BookOpen className="h-5 w-5" />,
    TROUBLESHOOTING: <BookOpen className="h-5 w-5" />,
};

export function HelpCenter() {
    const navigate = useNavigate();
    const [categories, setCategories] = useState<HelpCategory[]>([]);
    const [mostViewed, setMostViewed] = useState<HelpArticle[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchHelpData();
    }, []);

    const fetchHelpData = async () => {
        try {
            setLoading(true);

            const categoriesRes = await fetch('/v1/help/categories/');
            if (categoriesRes.ok) {
                const categoriesData = await categoriesRes.json();
                setCategories(categoriesData.map((cat: any) => ({
                    ...cat,
                    icon: CATEGORY_ICONS[cat.value]
                })));
            }

            const articlesRes = await fetch('/v1/help/articles/');
            if (articlesRes.ok) {
                const articlesData = await articlesRes.json();
                setMostViewed(articlesData.slice(0, 5));
            }
        } catch (error) {
            console.error('Failed to fetch help data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            navigate(`/help/search?q=${encodeURIComponent(searchQuery)}`);
        }
    };

    if (loading) {
        return (
            <div className="mx-auto max-w-5xl">
                <SurfacePanel className="p-8 text-center">Loading help center...</SurfacePanel>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-5xl space-y-5">
            <PageHeader
                title="Help Center"
                eyebrow="Support"
                description="Search our help center or browse by category."
            />

            <SurfacePanel className="p-5 sm:p-6">
                <form onSubmit={handleSearch}>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                        <Input
                            type="text"
                            placeholder="Search for help..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="h-11 border-border pl-10"
                        />
                    </div>
                </form>
            </SurfacePanel>

            <div>
                <h2 className="mb-3 text-xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
                    Browse by Category
                </h2>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {categories.map((category) => (
                        <Link key={category.value} to={`/help/category/${category.value.toLowerCase()}`}>
                            <SurfacePanel className="h-full p-5 transition-colors hover:bg-secondary/55">
                                <div className="flex items-center gap-3">
                                    <div className="rounded-lg bg-secondary p-2 text-primary">
                                        {category.icon}
                                    </div>
                                    <h3 className="font-semibold">{category.label}</h3>
                                    <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
                                </div>
                            </SurfacePanel>
                        </Link>
                    ))}
                </div>
            </div>

            {mostViewed.length > 0 && (
                <SurfacePanel className="p-5 sm:p-6">
                    <h2 className="mb-4 flex items-center gap-2 text-xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
                        <TrendingUp className="h-5 w-5 text-primary" />
                        Most Viewed Articles
                    </h2>
                    <div className="divide-y divide-border rounded-xl border border-border">
                        {mostViewed.map((article) => (
                            <Link
                                key={article.id}
                                to={`/help/articles/${article.slug}`}
                                className="block px-4 py-4 transition-colors hover:bg-secondary/45"
                            >
                                <h3 className="font-medium">{article.title}</h3>
                                {article.excerpt && (
                                    <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                                        {article.excerpt}
                                    </p>
                                )}
                                <p className="mt-2 text-xs text-muted-foreground">{article.view_count} views</p>
                            </Link>
                        ))}
                    </div>
                </SurfacePanel>
            )}

            <SurfacePanel className="p-5 sm:p-6">
                <h3 className="flex items-center gap-2 text-lg font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
                    <Mail className="h-5 w-5 text-primary" />
                    Still need help?
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                    Can't find what you're looking for? Contact our support team.
                </p>
                <div className="mt-4">
                    <Link to="/help/contact">
                        <Button>Contact Support</Button>
                    </Link>
                </div>
            </SurfacePanel>
        </div>
    );
}
