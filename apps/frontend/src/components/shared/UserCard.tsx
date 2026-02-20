import { Link } from "react-router-dom";
import type { UserProfile } from "@/types";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface UserCardProps {
    user: UserProfile;
    showFollowButton?: boolean;
    onFollowToggle?: (userId: string) => void;
}

export default function UserCard({ user, showFollowButton = false, onFollowToggle }: UserCardProps) {
    const handleFollowClick = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        onFollowToggle?.(user.id);
    };

    return (
        <Link to={`/u/${user.handle}`} className="group block">
            <div className="border border-border rounded-lg overflow-hidden bg-card hover:shadow-md transition-shadow p-4">
                <div className="flex items-start gap-4">
                    <Avatar className="h-16 w-16 flex-shrink-0">
                        <AvatarImage src={user.avatar_url} alt={user.display_name} />
                        <AvatarFallback>
                            {user.display_name.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>

                    <div className="flex-1 min-w-0 space-y-2">
                        <div>
                            <h3 className="font-medium leading-snug group-hover:text-primary transition-colors truncate" style={{ fontFamily: "var(--font-display)" }}>
                                {user.display_name}
                            </h3>
                            <p className="text-sm text-muted-foreground">@{user.handle}</p>
                        </div>

                        {user.bio && (
                            <p className="text-sm text-muted-foreground line-clamp-2">{user.bio}</p>
                        )}

                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{user.follower_count} followers</span>
                            <span>·</span>
                            <span>{user.following_count} following</span>
                        </div>
                    </div>

                    {showFollowButton && onFollowToggle && (
                        <Button
                            variant={user.is_following ? "outline" : "default"}
                            size="sm"
                            onClick={handleFollowClick}
                            className="flex-shrink-0"
                        >
                            {user.is_following ? "Following" : "Follow"}
                        </Button>
                    )}
                </div>
            </div>
        </Link>
    );
}
