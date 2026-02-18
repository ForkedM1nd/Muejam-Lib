import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, ArrowLeft } from 'lucide-react';

interface HelpArticle {
    id: string;
    title: string;
    slug: string;
    category: string;
    excerpt: string;
    view_count: number;
}

export function HelpSearch() {
    const [searchParams] = useSearchParams();
    const initialQuery = searchParams.get('q') || '';
    const [searchQuery, setSearchQuery] = useState(initialQuery);
    const [results, setResults] = useState<HelpArticle[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (initialQuery) {
            performSearch(initialQuery);
        }
    }, [initialQuery]);

    const performSearch = async (query: string) => {
        if (!query.trim()) return;

        try {
            setLoading(true);
            const response = await fetch(`/v1/help/search/?q=${encodeURIComponent(query)}`);

            if (response.ok) {
                const data = await response.json();
                setResults(data);
            }
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            performSearch(searchQuery);
            window.history.pushState({}, '', `/help/search?q=${encodeURIComponent(searchQuery)}`);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            <h1 className="text-3xl font-bold mb-6">Search Help Articles</h1>

            <form onSubmit={handleSearch} className="mb-8">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                        type="text"
                        placeholder="Search for help..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 pr-4 py-6"
                    />
                </div>
            </form>

            {loading ? (
                <div className="text-center py-8">Searching...</div>
            ) : results.length > 0 ? (
                <div>
                    <p className="text-muted-foreground mb-4">
                        Found {results.length} {results.length === 1 ? 'result' : 'results'} for "{initialQuery}"
                    </p>
                    <div className="space-y-4">
                        {results.map((article) => (
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
                </div>
            ) : initialQuery ? (
                <Card>
                    <CardContent className="p-8 text-center">
                        <h2 className="text-xl font-semibold mb-2">No results found</h2>
                        <p className="text-muted-foreground mb-4">
                            We couldn't find any articles matching "{initialQuery}"
                        </p>
                        <Link to="/help">
                            <Button>Browse All Categories</Button>
                        </Link>
                    </CardContent>
                </Card>
            ) : null}
        </div>
    );
}
