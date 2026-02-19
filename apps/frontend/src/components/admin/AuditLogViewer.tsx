import { useEffect, useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
    AlertTriangle,
    FileText,
    Filter,
    RefreshCw,
    Shield,
    X,
} from "lucide-react";
import { services } from "@/lib/api";
import type { AuditLog, AuditLogParams, SuspiciousPattern } from "@/types";

export function AuditLogViewer() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [suspiciousPatterns, setSuspiciousPatterns] = useState<SuspiciousPattern[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [nextCursor, setNextCursor] = useState<string | null>(null);
    const [hasMore, setHasMore] = useState(false);

    // Filter state
    const [filters, setFilters] = useState<AuditLogParams>({
        page_size: 20,
    });
    const [showFilters, setShowFilters] = useState(false);

    // Refs for infinite scroll
    const observerTarget = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchInitialData();
    }, []);

    useEffect(() => {
        // Set up intersection observer for infinite scroll
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && hasMore && !loadingMore) {
                    loadMore();
                }
            },
            { threshold: 0.1 }
        );

        if (observerTarget.current) {
            observer.observe(observerTarget.current);
        }

        return () => observer.disconnect();
    }, [hasMore, loadingMore]);

    const fetchInitialData = async () => {
        try {
            setLoading(true);
            setError(null);
            const [logsData, patterns] = await Promise.all([
                services.admin.getAuditLogs(filters),
                services.admin.getSuspiciousPatterns(),
            ]);
            setLogs(logsData.results);
            setNextCursor(logsData.next_cursor ?? null);
            setHasMore(logsData.has_more);
            setSuspiciousPatterns(patterns);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch audit logs");
        } finally {
            setLoading(false);
        }
    };

    const loadMore = async () => {
        if (!nextCursor || loadingMore) return;

        try {
            setLoadingMore(true);
            const logsData = await services.admin.getAuditLogs({
                ...filters,
                cursor: nextCursor,
            });
            setLogs((prev) => [...prev, ...logsData.results]);
            setNextCursor(logsData.next_cursor ?? null);
            setHasMore(logsData.has_more);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load more logs");
        } finally {
            setLoadingMore(false);
        }
    };

    const applyFilters = () => {
        setLogs([]);
        setNextCursor(null);
        fetchInitialData();
    };

    const clearFilters = () => {
        setFilters({ page_size: 20 });
        setLogs([]);
        setNextCursor(null);
        fetchInitialData();
    };

    const triggerAlert = async (pattern: SuspiciousPattern) => {
        try {
            await services.admin.triggerAlert({
                alert_type: pattern.pattern_type,
                message: `Suspicious pattern detected: ${pattern.description}`,
                severity: pattern.severity,
            });
            alert("Security alert triggered successfully");
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to trigger alert");
        }
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <Card>
                    <CardHeader>
                        <Skeleton className="h-6 w-48" />
                        <Skeleton className="h-4 w-64" />
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[...Array(5)].map((_, i) => (
                                <Skeleton key={i} className="h-20 w-full" />
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
            </Alert>
        );
    }

    return (
        <div className="space-y-6">
            {/* Suspicious Patterns */}
            {suspiciousPatterns.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-destructive" />
                            Suspicious Patterns Detected
                        </CardTitle>
                        <CardDescription>
                            Security patterns that require attention
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {suspiciousPatterns.map((pattern, index) => (
                                <div
                                    key={index}
                                    className="flex items-start justify-between p-4 border rounded-lg"
                                >
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Badge
                                                variant={
                                                    pattern.severity === "critical"
                                                        ? "destructive"
                                                        : pattern.severity === "high"
                                                            ? "destructive"
                                                            : pattern.severity === "medium"
                                                                ? "default"
                                                                : "secondary"
                                                }
                                            >
                                                {pattern.severity.toUpperCase()}
                                            </Badge>
                                            <span className="font-medium">{pattern.pattern_type}</span>
                                        </div>
                                        <p className="text-sm text-muted-foreground mb-2">
                                            {pattern.description}
                                        </p>
                                        <div className="flex gap-4 text-xs text-muted-foreground">
                                            <span>Occurrences: {pattern.occurrences}</span>
                                            <span>First seen: {new Date(pattern.first_seen).toLocaleString()}</span>
                                            <span>Last seen: {new Date(pattern.last_seen).toLocaleString()}</span>
                                        </div>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => triggerAlert(pattern)}
                                    >
                                        <AlertTriangle className="h-4 w-4 mr-2" />
                                        Trigger Alert
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Audit Logs */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Audit Logs</CardTitle>
                            <CardDescription>
                                System activity and administrative actions
                            </CardDescription>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowFilters(!showFilters)}
                            >
                                <Filter className="h-4 w-4 mr-2" />
                                Filters
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={fetchInitialData}
                            >
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Refresh
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {/* Filters Panel */}
                    {showFilters && (
                        <div className="mb-6 p-4 border rounded-lg space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="action">Action Type</Label>
                                    <Input
                                        id="action"
                                        placeholder="e.g., user.login"
                                        value={filters.action ?? ""}
                                        onChange={(e) =>
                                            setFilters({ ...filters, action: e.target.value || undefined })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="user_id">User ID</Label>
                                    <Input
                                        id="user_id"
                                        placeholder="Filter by user"
                                        value={filters.user_id ?? ""}
                                        onChange={(e) =>
                                            setFilters({ ...filters, user_id: e.target.value || undefined })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="resource_type">Resource Type</Label>
                                    <Input
                                        id="resource_type"
                                        placeholder="e.g., story, user"
                                        value={filters.resource_type ?? ""}
                                        onChange={(e) =>
                                            setFilters({ ...filters, resource_type: e.target.value || undefined })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="start_date">Start Date</Label>
                                    <Input
                                        id="start_date"
                                        type="date"
                                        value={filters.start_date ?? ""}
                                        onChange={(e) =>
                                            setFilters({ ...filters, start_date: e.target.value || undefined })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="end_date">End Date</Label>
                                    <Input
                                        id="end_date"
                                        type="date"
                                        value={filters.end_date ?? ""}
                                        onChange={(e) =>
                                            setFilters({ ...filters, end_date: e.target.value || undefined })
                                        }
                                    />
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <Button onClick={applyFilters}>Apply Filters</Button>
                                <Button variant="outline" onClick={clearFilters}>
                                    <X className="h-4 w-4 mr-2" />
                                    Clear
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Logs List */}
                    <div className="space-y-3">
                        {logs.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                No audit logs found
                            </div>
                        ) : (
                            logs.map((log) => (
                                <div
                                    key={log.id}
                                    className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                                >
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <FileText className="h-4 w-4 text-muted-foreground" />
                                            <span className="font-medium">{log.action}</span>
                                            <Badge variant="outline">{log.resource_type}</Badge>
                                        </div>
                                        <span className="text-xs text-muted-foreground">
                                            {new Date(log.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                                        <div>
                                            <span className="text-muted-foreground">User: </span>
                                            <span className="font-medium">{log.user_handle}</span>
                                        </div>
                                        <div>
                                            <span className="text-muted-foreground">Resource ID: </span>
                                            <span className="font-mono text-xs">{log.resource_id}</span>
                                        </div>
                                        <div>
                                            <span className="text-muted-foreground">IP: </span>
                                            <span className="font-mono text-xs">{log.ip_address}</span>
                                        </div>
                                        <div className="col-span-2 md:col-span-1">
                                            <span className="text-muted-foreground">User Agent: </span>
                                            <span className="text-xs truncate block">{log.user_agent}</span>
                                        </div>
                                    </div>
                                    {Object.keys(log.metadata).length > 0 && (
                                        <details className="mt-2">
                                            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                                                View metadata
                                            </summary>
                                            <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                                                {JSON.stringify(log.metadata, null, 2)}
                                            </pre>
                                        </details>
                                    )}
                                </div>
                            ))
                        )}
                    </div>

                    {/* Infinite Scroll Trigger */}
                    {hasMore && (
                        <div ref={observerTarget} className="py-4 text-center">
                            {loadingMore ? (
                                <div className="flex items-center justify-center gap-2">
                                    <RefreshCw className="h-4 w-4 animate-spin" />
                                    <span className="text-sm text-muted-foreground">Loading more...</span>
                                </div>
                            ) : (
                                <Button variant="outline" onClick={loadMore}>
                                    Load More
                                </Button>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
