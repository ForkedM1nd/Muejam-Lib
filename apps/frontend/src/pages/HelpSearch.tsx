import { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, ArrowLeft } from 'lucide-react';
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

export function HelpSearch() {
    const navigate = useNavigate();
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
            navigate(`/help/search?q=${encodeURIComponent(searchQuery)}`);
        }
    };

    return (
        <div className="mx-auto max-w-4xl space-y-5">
            <Link to="/help" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="h-4 w-4" />
                Back to Help Center
            </Link>

            <PageHeader title="Search Help Articles" eyebrow="Support" description="Find answers quickly across help documentation." />

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

            {loading ? (
                <SurfacePanel className="p-8 text-center">Searching...</SurfacePanel>
            ) : results.length > 0 ? (
                <>
                    <p className="text-sm text-muted-foreground">
                        Found {results.length} {results.length === 1 ? 'result' : 'results'} for "{initialQuery}"
                    </p>
                    <div className="space-y-3">
                        {results.map((article) => (
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
                </>
            ) : initialQuery ? (
                <SurfacePanel className="p-8 text-center">
                    <h2 className="text-xl font-semibold">No results found</h2>
                    <p className="mt-2 text-muted-foreground">
                        We couldn't find any articles matching "{initialQuery}".
                    </p>
                    <div className="mt-4">
                        <Link to="/help">
                            <Button>Browse All Categories</Button>
                        </Link>
                    </div>
                </SurfacePanel>
            ) : null}
        </div>
    );
}
