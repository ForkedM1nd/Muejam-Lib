import { useState } from "react";
import { Heart, MessageCircle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import WhisperComposer from "./WhisperComposer";
import NSFWWarningLabel from "./NSFWWarningLabel";
import BlurredNSFWImage from "./BlurredNSFWImage";
import type { Whisper } from "@/types";

interface WhisperCardProps {
  whisper: Whisper;
  onLike?: () => void;
  onReply?: (content: string) => Promise<void>;
  showReplyButton?: boolean;
  compact?: boolean;
}

export default function WhisperCard({
  whisper,
  onLike,
  onReply,
  showReplyButton = true,
  compact = false,
}: WhisperCardProps) {
  const [showReplyComposer, setShowReplyComposer] = useState(false);
  const [isSubmittingReply, setIsSubmittingReply] = useState(false);

  // Check if whisper has NSFW flag
  const isNSFW = (whisper as any).is_nsfw || false;
  const isBlurred = (whisper as any).is_blurred || false;

  const handleReply = async (content: string) => {
    if (!onReply) return;
    setIsSubmittingReply(true);
    try {
      await onReply(content);
      setShowReplyComposer(false);
    } finally {
      setIsSubmittingReply(false);
    }
  };

  return (
    <div className={cn("py-4 space-y-3", !compact && "border-b border-border")}>
      {/* Header */}
      <div className="flex items-center gap-2">
        {whisper.author.avatar_url ? (
          <img
            src={whisper.author.avatar_url}
            alt={whisper.author.display_name}
            className="w-8 h-8 rounded-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-xs font-medium text-secondary-foreground">
            {whisper.author.display_name.charAt(0).toUpperCase()}
          </div>
        )}
        <div className="flex items-center gap-1.5 text-sm flex-wrap flex-1">
          <span className="font-medium">{whisper.author.display_name}</span>
          <span className="text-muted-foreground">@{whisper.author.handle}</span>
          <span className="text-muted-foreground">·</span>
          <span className="text-muted-foreground text-xs">
            {formatDistanceToNow(new Date(whisper.created_at), { addSuffix: true })}
          </span>
        </div>
        {isNSFW && (
          <NSFWWarningLabel variant="badge" />
        )}
      </div>

      {/* Quote */}
      {whisper.quote_text && (
        <blockquote className="border-l-2 border-primary/30 pl-3 text-sm text-muted-foreground italic">
          "{whisper.quote_text}"
        </blockquote>
      )}

      {/* Body */}
      <p className="text-sm leading-relaxed whitespace-pre-wrap">{whisper.body}</p>

      {/* Media */}
      {whisper.media_url && (
        <>
          {isNSFW && isBlurred ? (
            <BlurredNSFWImage
              src={whisper.media_url}
              alt=""
              aspectRatio="auto"
              className="rounded-lg border border-border max-h-80"
            />
          ) : (
            <div className="rounded-lg overflow-hidden border border-border">
              <img
                src={whisper.media_url}
                alt=""
                className="max-h-80 w-auto"
                loading="lazy"
              />
            </div>
          )}
        </>
      )}

      {/* Actions */}
      <div className="flex items-center gap-4 pt-1">
        {onLike && (
          <button
            onClick={onLike}
            className={cn(
              "flex items-center gap-1.5 text-xs transition-colors group",
              whisper.is_liked
                ? "text-red-500"
                : "text-muted-foreground hover:text-red-500"
            )}
            aria-label={whisper.is_liked ? "Unlike" : "Like"}
          >
            <Heart
              className={cn(
                "h-4 w-4 transition-all",
                whisper.is_liked && "fill-red-500",
                !whisper.is_liked && "group-hover:scale-110"
              )}
            />
            {whisper.like_count > 0 && (
              <span className="font-medium">{whisper.like_count}</span>
            )}
          </button>
        )}

        {showReplyButton && (
          <button
            onClick={() => setShowReplyComposer(!showReplyComposer)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary transition-colors group"
            aria-label="Reply"
          >
            <MessageCircle className="h-4 w-4 group-hover:scale-110 transition-all" />
            {whisper.reply_count > 0 && (
              <span className="font-medium">{whisper.reply_count}</span>
            )}
          </button>
        )}
      </div>

      {/* Reply Composer */}
      {showReplyComposer && onReply && (
        <div className="pl-10 pt-2">
          <WhisperComposer
            placeholder="Write your reply..."
            onSubmit={handleReply}
            submitting={isSubmittingReply}
          />
        </div>
      )}
    </div>
  );
}
