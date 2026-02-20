import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { api } from "@/lib/api";
import StoryCard from "@/components/shared/StoryCard";
import { PageSkeleton, StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { UserPlus, UserMinus, ShieldBan, Settings, Twitter, Instagram, Globe, Award, BookOpen, Heart, Users } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { BlockConfirmDialog } from "@/components/shared/BlockConfirmDialog";
import { useState, type ReactNode } from "react";
import type { Story } from "@/types";
import SurfacePanel from "@/components/shared/SurfacePanel";
import PageHeader from "@/components/shared/PageHeader";

interface ProfileBadge {
  id: string;
  badge_type: string;
}

export default function ProfilePage() {
  const { handle } = useParams<{ handle: string }>();
  const { isSignedIn } = useSafeAuth();
  const queryClient = useQueryClient();
  const [blockDialogOpen, setBlockDialogOpen] = useState(false);

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

  // Fetch mutual followers (social proof)
  const { data: mutualFollowers } = useQuery({
    queryKey: ["profile-mutual-followers", handle],
    queryFn: async () => {
      if (!isSignedIn || isOwnProfile) return null;
      // Get followers of the profile user
      const followers = await api.getFollowers(profile?.id || '', undefined);
      // Get current user's following
      const following = await api.getFollowing(currentUser?.id || '', undefined);

      // Find mutual followers (people who follow this profile and are followed by current user)
      const followingIds = new Set(following.results.map(u => u.id));
      const mutual = followers.results.filter(u => followingIds.has(u.id)).slice(0, 3);

      return mutual;
    },
    enabled: !!handle && !!profile?.id && !!currentUser?.id && !isOwnProfile && isSignedIn,
  });

  // Fetch pinned stories
  const { data: pinnedStories } = useQuery<Story[]>({
    queryKey: ["profile-pinned", handle],
    queryFn: async () => {
      const response = await fetch(`/v1/users/${handle}/pinned/`);
      if (response.ok) {
        const payload = await response.json();
        return Array.isArray(payload) ? (payload as Story[]) : [];
      }
      return [];
    },
    enabled: !!handle,
  });

  // Fetch user badges
  const { data: badges } = useQuery<ProfileBadge[]>({
    queryKey: ["profile-badges", handle],
    queryFn: async () => {
      const response = await fetch(`/v1/users/${handle}/badges/`);
      if (response.ok) {
        const payload = await response.json();
        return Array.isArray(payload) ? (payload as ProfileBadge[]) : [];
      }
      return [];
    },
    enabled: !!handle,
  });

  const followMutation = useMutation({
    mutationFn: async () => {
      if (!profile?.id) throw new Error("Profile ID not found");
      if (profile?.is_following) {
        await api.unfollowUser(profile.id);
      } else {
        await api.followUser(profile.id);
      }
    },
    onMutate: async () => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ["profile", handle] });
      const previousProfile = queryClient.getQueryData(["profile", handle]);

      queryClient.setQueryData(["profile", handle], (old: typeof profile | undefined) => {
        if (!old) return old;
        return {
          ...old,
          is_following: !old.is_following,
          follower_count: old.is_following ? old.follower_count - 1 : old.follower_count + 1,
        };
      });

      return { previousProfile };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousProfile) {
        queryClient.setQueryData(["profile", handle], context.previousProfile);
      }
      toast({
        title: "Error",
        description: "Failed to update follow status",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      toast({ title: profile?.is_following ? "Unfollowed" : "Following" });
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["profile", handle] });
      queryClient.invalidateQueries({ queryKey: ["profile-mutual-followers", handle] });
    },
  });

  const blockMutation = useMutation({
    mutationFn: async () => {
      if (!profile?.id) throw new Error("Profile ID not found");
      if (profile?.is_blocked) {
        await api.unblockUser(profile.id);
      } else {
        await api.blockUser(profile.id);
      }
    },
    onMutate: async () => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ["profile", handle] });
      const previousProfile = queryClient.getQueryData(["profile", handle]);

      queryClient.setQueryData(["profile", handle], (old: typeof profile | undefined) => {
        if (!old) return old;
        return {
          ...old,
          is_blocked: !old.is_blocked,
        };
      });

      return { previousProfile };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousProfile) {
        queryClient.setQueryData(["profile", handle], context.previousProfile);
      }
      toast({
        title: "Error",
        description: "Failed to update block status",
        variant: "destructive"
      });
    },
    onSuccess: () => {
      toast({ title: profile?.is_blocked ? "Unblocked" : "Blocked" });
      // Invalidate related queries to remove blocked user content
      queryClient.invalidateQueries({ queryKey: ["profile", handle] });
      queryClient.invalidateQueries({ queryKey: ["activity-feed"] });
      queryClient.invalidateQueries({ queryKey: ["whispers"] });
      queryClient.invalidateQueries({ queryKey: ["discover"] });
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["followers"] });
      queryClient.invalidateQueries({ queryKey: ["following"] });
    },
  });

  const handleBlockClick = () => {
    if (profile?.is_blocked) {
      // Unblock immediately without confirmation
      blockMutation.mutate();
    } else {
      // Show confirmation dialog for blocking
      setBlockDialogOpen(true);
    }
  };

  const handleBlockConfirm = () => {
    setBlockDialogOpen(false);
    blockMutation.mutate();
  };

  if (isLoading) return <PageSkeleton />;
  if (isError || !profile) return <EmptyState title="User not found" />;

  const badgeIcons: Record<string, { icon: ReactNode; label: string; color: string }> = {
    VERIFIED_AUTHOR: { icon: <Award className="h-3 w-3" />, label: "Verified Author", color: "bg-primary/15 text-primary border border-primary/25" },
    TOP_CONTRIBUTOR: { icon: <Award className="h-3 w-3" />, label: "Top Contributor", color: "bg-secondary text-foreground border border-border" },
    EARLY_ADOPTER: { icon: <Award className="h-3 w-3" />, label: "Early Adopter", color: "bg-accent text-foreground border border-border" },
    PROLIFIC_WRITER: { icon: <BookOpen className="h-3 w-3" />, label: "Prolific Writer", color: "bg-primary/10 text-primary border border-primary/20" },
    POPULAR_AUTHOR: { icon: <Users className="h-3 w-3" />, label: "Popular Author", color: "bg-secondary text-foreground border border-border" },
    COMMUNITY_CHAMPION: { icon: <Heart className="h-3 w-3" />, label: "Community Champion", color: "bg-accent text-foreground border border-border" },
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title={profile.display_name}
        eyebrow="Profile"
        description={`@${profile.handle}`}
        action={isSignedIn ? (
          isOwnProfile ? (
            <Link to="/settings/profile">
              <Button variant="outline" size="sm">
                <Settings className="mr-1 h-3.5 w-3.5" /> Edit Profile
              </Button>
            </Link>
          ) : (
            <div className="flex gap-2">
              <Button
                variant={profile.is_following ? "outline" : "default"}
                size="sm"
                onClick={() => followMutation.mutate()}
              >
                {profile.is_following ? <><UserMinus className="mr-1 h-3.5 w-3.5" /> Unfollow</> : <><UserPlus className="mr-1 h-3.5 w-3.5" /> Follow</>}
              </Button>
              <Button variant="ghost" size="sm" onClick={handleBlockClick}>
                <ShieldBan className="mr-1 h-3.5 w-3.5" /> {profile.is_blocked ? "Unblock" : "Block"}
              </Button>
            </div>
          )
        ) : undefined}
      />

      <SurfacePanel className="overflow-hidden">
        {profile.banner_key ? (
          <div className="h-44 w-full overflow-hidden border-b border-border">
            <img
              src={`/api/media/${profile.banner_key}`}
              alt=""
              className="h-full w-full object-cover"
              loading="lazy"
            />
          </div>
        ) : (
          <div className="h-16 w-full border-b border-border bg-secondary/40" />
        )}

        <div className="p-5 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt=""
                className="-mt-12 h-24 w-24 rounded-full border-4 border-background object-cover"
                style={{ borderColor: profile.theme_color || "#3a9679" }}
                loading="lazy"
              />
            ) : (
              <div
                className="-mt-12 flex h-24 w-24 items-center justify-center rounded-full border-4 border-background text-3xl font-medium text-white"
                style={{ backgroundColor: profile.theme_color || "#3a9679" }}
              >
                {profile.display_name.charAt(0)}
              </div>
            )}

            <div className="flex-1 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm text-muted-foreground">@{profile.handle}</p>
                {badges && badges.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {badges.slice(0, 4).map((badge) => {
                      const badgeInfo = badgeIcons[badge.badge_type];
                      return badgeInfo ? (
                        <span
                          key={badge.id}
                          className={`${badgeInfo.color} inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]`}
                          title={badgeInfo.label}
                        >
                          {badgeInfo.icon}
                          {badgeInfo.label}
                        </span>
                      ) : null;
                    })}
                  </div>
                )}
              </div>

              {profile.bio && <p className="text-sm leading-relaxed text-muted-foreground">{profile.bio}</p>}

              {(profile.twitter_url || profile.instagram_url || profile.website_url) && (
                <div className="flex gap-3">
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

              {mutualFollowers && mutualFollowers.length > 0 && (
                <div className="flex items-start gap-2 rounded-lg bg-secondary/45 px-3 py-2 text-sm text-muted-foreground">
                  <Users className="mt-0.5 h-4 w-4" />
                  <span>
                    Followed by{" "}
                    {mutualFollowers.map((user, idx) => (
                      <span key={user.id}>
                        <Link to={`/u/${user.handle}`} className="font-medium text-foreground hover:underline">
                          {user.display_name}
                        </Link>
                        {idx < mutualFollowers.length - 1 && (idx === mutualFollowers.length - 2 ? " and " : ", ")}
                      </span>
                    ))}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </SurfacePanel>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Link to={`/users/${handle}/followers`}>
          <SurfacePanel className="p-4 text-center transition-colors hover:bg-secondary/55">
            <div className="text-2xl font-bold">{profile.follower_count}</div>
            <div className="text-xs text-muted-foreground">Followers</div>
          </SurfacePanel>
        </Link>
        <Link to={`/users/${handle}/following`}>
          <SurfacePanel className="p-4 text-center transition-colors hover:bg-secondary/55">
            <div className="text-2xl font-bold">{profile.following_count}</div>
            <div className="text-xs text-muted-foreground">Following</div>
          </SurfacePanel>
        </Link>
        <SurfacePanel className="p-4 text-center">
          <div className="text-2xl font-bold">{statistics?.total_stories || stories?.results?.length || 0}</div>
          <div className="text-xs text-muted-foreground">Stories</div>
        </SurfacePanel>
        <SurfacePanel className="p-4 text-center">
          <div className="text-2xl font-bold">{statistics?.total_whispers || 0}</div>
          <div className="text-xs text-muted-foreground">Whispers</div>
        </SurfacePanel>
      </div>

      {pinnedStories && pinnedStories.length > 0 && (
        <SurfacePanel className="p-5 sm:p-6">
          <h2 className="mb-4 flex items-center gap-2 text-xl font-medium" style={{ fontFamily: "var(--font-display)" }}>
            <Award className="h-5 w-5 text-primary" />
            Featured Stories
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {pinnedStories.map((story) => <StoryCard key={story.id} story={story} />)}
          </div>
        </SurfacePanel>
      )}

      <SurfacePanel className="p-5 sm:p-6">
        <h2 className="mb-4 text-xl font-medium" style={{ fontFamily: "var(--font-display)" }}>
          Published Stories
        </h2>
        {stories?.results && stories.results.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {stories.results.map((s) => <StoryCard key={s.id} story={s} />)}
          </div>
        ) : (
          <EmptyState title="No stories yet" description="This author hasn't published any stories." />
        )}
      </SurfacePanel>

      {/* Block Confirmation Dialog */}
      <BlockConfirmDialog
        open={blockDialogOpen}
        onOpenChange={setBlockDialogOpen}
        onConfirm={handleBlockConfirm}
        userName={profile.display_name}
        isBlocking={!profile.is_blocked}
      />
    </div>
  );
}
