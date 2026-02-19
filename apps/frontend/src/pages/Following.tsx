import { useParams, Link } from "react-router-dom";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Users } from "lucide-react";
import { useInView } from "react-intersection-observer";
import { useEffect } from "react";

export default function FollowingPage() {
    const { handle } = useParams<{ handle: string }>();
    const { ref, inView } = useInView();

    const { data: profile, isLoading: profileLoading } = useQuery({
        queryKey: ["profile", handle],
        queryFn: () => api.getProfile(handle!),
        enabled: !!handle,
    });

    const {
        data,
        isLoading,
        isError,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
    } = useInfiniteQuery({
        queryKey: ["following", profile?.id],
        queryFn: ({ pageParam }) => api.getFollowing(profile!.id, pageParam),
        getNextPageParam: (lastPage) => lastPage.next_cursor,
        initialPageParam: undefined,
        enabled: !!profile?.id,
    });

    useEffect(() => {
        if (inView && hasNextPage && !isFetchingNextPage) {
            fetchNextPage();
        }
    }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

    if (profileLoading || isLoading) return <PageSkeleton />;
    if (isError || !profile) return <EmptyState title="User not found" />;

    const following = data?.pages.flatMap((page) => page.results) || [];

    // Filter out blocked users
    const filteredFollowing = following.filter((user) => !user.is_blocked);

    return (
        <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link to={`/u/${handle}`}>
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                        Following
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        People {profile.display_name} follows
                    </p>
                </div>
            </div>

            {/* Following List */}
            {filteredFollowing.length > 0 ? (
                <div className="space-y-3">
                    {filteredFollowing.map((user) => (
                        <Card key={user.id}>
                            <CardContent className="p-4">
                                <Link to={`/u/${user.handle}`} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                                    {user.avatar_url ? (
                                        <img
                                            src={user.avatar_url}
                                            alt=""
                                            className="w-12 h-12 rounded-full object-cover"
                                            loading="lazy"
                                        />
                                    ) : (
                                        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-medium">
                                            {user.display_name.charAt(0)}
                                        </div>
                                    )}
                                    <div className="flex-1">
                                        <div className="font-medium">{user.display_name}</div>
                                        <div className="text-sm text-muted-foreground">@{user.handle}</div>
                                        {user.bio && (
                                            <div className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                {user.bio}
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-sm text-muted-foreground">
                                        <div className="flex items-center gap-1">
                                            <Users className="h-4 w-4" />
                                            {user.follower_count}
                                        </div>
                                    </div>
                                </Link>
                            </CardContent>
                        </Card>
                    ))}
                    {hasNextPage && (
                        <div ref={ref} className="py-4 text-center">
                            {isFetchingNextPage ? "Loading more..." : ""}
                        </div>
                    )}
                </div>
            ) : (
                <EmptyState
                    icon={<Users className="h-12 w-12" />}
                    title="Not following anyone"
                    description={`${profile.display_name} isn't following anyone yet.`}
                />
            )}
        </div>
    );
}
