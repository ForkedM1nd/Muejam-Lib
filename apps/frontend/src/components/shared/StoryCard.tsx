import { Link } from "react-router-dom";
import type { Story } from "@/types";
import TagPill from "./TagPill";
import NSFWWarningLabel from "./NSFWWarningLabel";
import BlurredNSFWImage from "./BlurredNSFWImage";
import ShareButton from "./ShareButton";
import { getStoryShareOptions } from "@/lib/shareUtils";

export default function StoryCard({ story }: { story: Story }) {
  const moderatedStory = story as Story & { is_nsfw?: boolean; is_blurred?: boolean };
  const isNSFW = Boolean(moderatedStory.is_nsfw);
  const isBlurred = Boolean(moderatedStory.is_blurred);

  const handleShareClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <Link to={`/story/${story.slug}`} className="group block">
      <div className="relative overflow-hidden rounded-2xl border border-border/70 bg-card/90 shadow-[0_14px_34px_-28px_hsl(var(--foreground)/0.7)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_20px_44px_-26px_hsl(var(--foreground)/0.7)]">
        {story.cover_url && (
          <>
            {isNSFW && isBlurred ? (
              <BlurredNSFWImage
                src={story.cover_url}
                alt={story.title}
                aspectRatio="3/2"
              />
            ) : (
              <div className="aspect-[3/2] overflow-hidden bg-muted relative">
                <img
                  src={story.cover_url}
                  alt={story.title}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
                  loading="lazy"
                />
                {isNSFW && (
                  <div className="absolute top-2 right-2">
                    <NSFWWarningLabel variant="badge" />
                  </div>
                )}
              </div>
            )}
          </>
        )}
        <div className="p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="flex-1 line-clamp-2 font-medium leading-snug transition-colors group-hover:text-primary" style={{ fontFamily: "var(--font-display)" }}>
              {story.title}
            </h3>
            {isNSFW && !story.cover_url && (
              <NSFWWarningLabel variant="badge" />
            )}
          </div>
          {story.blurb && (
            <p className="text-sm text-muted-foreground line-clamp-2">{story.blurb}</p>
          )}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{story.author.display_name}</span>
              <span>·</span>
              <span>{story.chapter_count} ch.</span>
            </div>
            <div onClick={handleShareClick}>
              <ShareButton
                shareOptions={getStoryShareOptions(story)}
                variant="ghost"
                size="sm"
                iconOnly
              />
            </div>
          </div>
          {story.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {story.tags.slice(0, 3).map((t) => (
                <TagPill key={t.id} name={t.name} />
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
