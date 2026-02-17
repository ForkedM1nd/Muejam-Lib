import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { api } from "@/lib/api";
import StoryCard from "@/components/shared/StoryCard";
import { PageSkeleton, StoryCardSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { UserPlus, UserMinus, ShieldBan, Settings } from "lucide-react";
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

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      {/* Profile header */}
      <div className="flex items-start gap-4">
        {profile.avatar_url ? (
          <img
            src={profile.avatar_url}
            alt=""
            className="w-20 h-20 rounded-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-20 h-20 rounded-full bg-secondary flex items-center justify-center text-2xl font-medium text-secondary-foreground">
            {profile.display_name.charAt(0)}
          </div>
        )}
        <div className="flex-1 space-y-1">
          <h1 className="text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>{profile.display_name}</h1>
          <p className="text-sm text-muted-foreground">@{profile.handle}</p>
          {profile.bio && <p className="text-sm mt-2">{profile.bio}</p>}
          <div className="flex gap-4 text-sm text-muted-foreground mt-2">
            <span><strong className="text-foreground">{profile.follower_count}</strong> followers</span>
            <span><strong className="text-foreground">{profile.following_count}</strong> following</span>
          </div>
          {isSignedIn && (
            <div className="flex gap-2 mt-3">
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

      {/* Stories */}
      <section>
        <h2 className="text-lg font-medium mb-4" style={{ fontFamily: "var(--font-display)" }}>Published Stories</h2>
        {stories?.results && stories.results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {stories.results.map((s) => <StoryCard key={s.id} story={s} />)}
          </div>
        ) : (
          <EmptyState title="No stories yet" description="This author hasn't published any stories." />
        )}
      </section>
    </div>
  );
}
