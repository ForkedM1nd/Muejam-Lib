import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, BookOpen, TrendingUp, Mail } from 'lucide-react';

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

            // Fetch categories
            const categoriesRes = await fetch('/v1/help/categories/');
            if (categoriesRes.ok) {
                const categoriesData = await categoriesRes.json();
                setCategories(categoriesData.map((cat: any) => ({
                    ...cat,
                    icon: CATEGORY_ICONS[cat.value]
                })));
            }

            // Fetch most viewed articles
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
            window.location.href = `/help/search?q=${encodeURIComponent(searchQuery)}`;
        }
    };

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center">Loading...</div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold mb-4">How can we help you?</h1>
                <p className="text-muted-foreground mb-6">
                    Search our help center or browse by category
                </p>

                {/* Search */}
                <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                        <Input
                            type="text"
                            placeholder="Search for help..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10 pr-4 py-6 text-lg"
                        />
                    </div>
                </form>
            </div>

            {/* Categories */}
            <div className="mb-12">
                <h2 className="text-2xl font-semibold mb-6">Browse by Category</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categories.map((category) => (
                        <Link key={category.value} to={`/help/category/${category.value.toLowerCase()}`}>
                            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                                <CardHeader>
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-primary/10 rounded-lg">
                                            {category.icon}
                                        </div>
                                        <CardTitle className="text-lg">{category.label}</CardTitle>
                                    </div>
                                </CardHeader>
                            </Card>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Most Viewed Articles */}
            {mostViewed.length > 0 && (
                <div className="mb-12">
                    <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                        <TrendingUp className="h-6 w-6" />
                        Most Viewed Articles
                    </h2>
                    <Card>
                        <CardContent className="p-0">
                            <div className="divide-y">
                                {mostViewed.map((article) => (
                                    <Link
                                        key={article.id}
                                        to={`/help/articles/${article.slug}`}
                                        className="block p-4 hover:bg-muted/50 transition-colors"
                                    >
                                        <h3 className="font-medium mb-1">{article.title}</h3>
                                        {article.excerpt && (
                                            <p className="text-sm text-muted-foreground line-clamp-2">
                                                {article.excerpt}
                                            </p>
                                        )}
                                        <p className="text-xs text-muted-foreground mt-2">
                                            {article.view_count} views
                                        </p>
                                    </Link>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Contact Support */}
            <Card className="bg-primary/5">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Mail className="h-5 w-5" />
                        Still need help?
                    </CardTitle>
                    <CardDescription>
                        Can't find what you're looking for? Contact our support team.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Link to="/help/contact">
                        <Button>Contact Support</Button>
                    </Link>
                </CardContent>
            </Card>
        </div>
    );
}
