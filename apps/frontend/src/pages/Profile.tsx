import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { api } from "@/lib/api";
import StoryCard from "@/components/shared/StoryCard";
import { PageSkeleton, StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UserPlus, UserMinus, ShieldBan, Settings, Twitter, Instagram, Globe, Award, BookOpen, MessageSquare, Heart, Users } from "lucide-react";
import { toast } from "@/hooks/use-toast";

export default function ProfilePage() {
  const { handle } = useParams<{ handle: string }>();
  const { isSignedIn } = useSafeAuth();

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ["profile", handle],
    queryFn: () => api.getProfile(handle!),
    enabled: !!handle,
  });

  const { data: currentUser } = useQuery({
    queryKey: ["me"],
    queryFn: () => api.getMe(),
    enabled: isSignedIn,
  });

  const isOwnProfile = currentUser?.handle === handle;

  const { data: stories } = useQuery({
    queryKey: ["profile-stories", handle],
    queryFn: () => api.getStories({ q: `author:${handle}` }),
    enabled: !!handle,
  });

  // Fetch user statistics
  const { data: statistics } = useQuery({
    queryKey: ["profile-statistics", handle],
    queryFn: async () => {
      const response = await fetch(`/v1/users/${handle}/statistics/`);
      if (response.ok) return response.json();
      return null;
    },
    enabled: !!handle,
  });

  // Fetch pinned stories
  const { data: pinnedStories } = useQuery({
    queryKey: ["profile-pinned", handle],
    queryFn: async () => {
      const response = await fetch(`/v1/users/${handle}/pinned/`);
      if (response.ok) return response.json();
      return [];
    },
    enabled: !!handle,
  });

  // Fetch user badges
  const { data: badges } = useQuery({
    queryKey: ["profile-badges", handle],
    queryFn: async () => {
      const response = await fetch(`/v1/users/${handle}/badges/`);
      if (response.ok) return response.json();
      return [];
    },
    enabled: !!handle,
  });

  const followMutation = useMutation({
    mutationFn: async () => {
      if (profile?.is_following) await api.unfollowUser(handle!);
      else await api.followUser(handle!);
    },
    onSuccess: () => toast({ title: profile?.is_following ? "Unfollowed" : "Following" }),
  });

  const blockMutation = useMutation({
    mutationFn: async () => {
      if (profile?.is_blocked) await api.unblockUser(handle!);
      else await api.blockUser(handle!);
    },
    onSuccess: () => toast({ title: profile?.is_blocked ? "Unblocked" : "Blocked" }),
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !profile) return <EmptyState title="User not found" />;

  const badgeIcons: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
    VERIFIED_AUTHOR: { icon: <Award className="h-3 w-3" />, label: "Verified Author", color: "bg-blue-500" },
    TOP_CONTRIBUTOR: { icon: <Award className="h-3 w-3" />, label: "Top Contributor", color: "bg-purple-500" },
    EARLY_ADOPTER: { icon: <Award className="h-3 w-3" />, label: "Early Adopter", color: "bg-green-500" },
    PROLIFIC_WRITER: { icon: <BookOpen className="h-3 w-3" />, label: "Prolific Writer", color: "bg-orange-500" },
    POPULAR_AUTHOR: { icon: <Users className="h-3 w-3" />, label: "Popular Author", color: "bg-pink-500" },
    COMMUNITY_CHAMPION: { icon: <Heart className="h-3 w-3" />, label: "Community Champion", color: "bg-red-500" },
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Banner */}
      {profile.banner_key && (
        <div className="w-full h-48 rounded-lg overflow-hidden">
          <img
            src={`/api/media/${profile.banner_key}`}
            alt=""
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
      )}

      {/* Profile header */}
      <div className="flex items-start gap-6">
        {profile.avatar_url ? (
          <img
            src={profile.avatar_url}
            alt=""
            className="w-24 h-24 rounded-full object-cover border-4 border-background"
            style={{ borderColor: profile.theme_color || '#6366f1' }}
            loading="lazy"
          />
        ) : (
          <div
            className="w-24 h-24 rounded-full flex items-center justify-center text-3xl font-medium text-white border-4 border-background"
            style={{ backgroundColor: profile.theme_color || '#6366f1' }}
          >
            {profile.display_name.charAt(0)}
          </div>
        )}
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              {profile.display_name}
            </h1>
            {badges && badges.length > 0 && (
              <div className="flex gap-1">
                {badges.slice(0, 3).map((badge: any) => {
                  const badgeInfo = badgeIcons[badge.badge_type];
                  return badgeInfo ? (
                    <div
                      key={badge.id}
                      className={`${badgeInfo.color} text-white p-1 rounded-full`}
                      title={badgeInfo.label}
                    >
                      {badgeInfo.icon}
                    </div>
                  ) : null;
                })}
              </div>
            )}
          </div>
          <p className="text-sm text-muted-foreground">@{profile.handle}</p>
          {profile.bio && <p className="text-sm mt-2">{profile.bio}</p>}

          {/* Social links */}
          {(profile.twitter_url || profile.instagram_url || profile.website_url) && (
            <div className="flex gap-3 mt-2">
              {profile.twitter_url && (
                <a href={profile.twitter_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground">
                  <Twitter className="h-4 w-4" />
                </a>
              )}
              {profile.instagram_url && (
                <a href={profile.instagram_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground">
                  <Instagram className="h-4 w-4" />
                </a>
              )}
              {profile.website_url && (
                <a href={profile.website_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground">
                  <Globe className="h-4 w-4" />
                </a>
              )}
            </div>
          )}

          {/* Statistics */}
          {statistics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold">{statistics.total_stories}</div>
                  <div className="text-xs text-muted-foreground">Stories</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold">{statistics.total_chapters}</div>
                  <div className="text-xs text-muted-foreground">Chapters</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold">{statistics.follower_count}</div>
                  <div className="text-xs text-muted-foreground">Followers</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold">{statistics.total_likes_received}</div>
                  <div className="text-xs text-muted-foreground">Likes</div>
                </CardContent>
              </Card>
            </div>
          )}

          {isSignedIn && (
            <div className="flex gap-2 mt-4">
              {isOwnProfile ? (
                <Link to="/settings/profile">
                  <Button variant="outline" size="sm">
                    <Settings className="h-3.5 w-3.5 mr-1" /> Edit Profile
                  </Button>
                </Link>
              ) : (
                <>
                  <Button
                    variant={profile.is_following ? "outline" : "default"}
                    size="sm"
                    onClick={() => followMutation.mutate()}
                  >
                    {profile.is_following ? <><UserMinus className="h-3.5 w-3.5 mr-1" /> Unfollow</> : <><UserPlus className="h-3.5 w-3.5 mr-1" /> Follow</>}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => blockMutation.mutate()}>
                    <ShieldBan className="h-3.5 w-3.5 mr-1" /> {profile.is_blocked ? "Unblock" : "Block"}
                  </Button>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Pinned Stories */}
      {pinnedStories && pinnedStories.length > 0 && (
        <section>
          <h2 className="text-xl font-medium mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-display)" }}>
            <Award className="h-5 w-5" />
            Featured Stories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {pinnedStories.map((story: any) => <StoryCard key={story.id} story={story} />)}
          </div>
        </section>
      )}

      {/* All Stories */}
      <section>
        <h2 className="text-xl font-medium mb-4" style={{ fontFamily: "var(--font-display)" }}>Published Stories</h2>
        {stories?.results && stories.results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {stories.results.map((s) => <StoryCard key={s.id} story={s} />)}
          </div>
        ) : (
          <EmptyState title="No stories yet" description="This author hasn't published any stories." />
        )}
      </section>
    </div>
  );
}
