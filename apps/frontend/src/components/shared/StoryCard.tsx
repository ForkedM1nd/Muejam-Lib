import { Link } from "react-router-dom";
import type { Story } from "@/types";
import TagPill from "./TagPill";
import NSFWWarningLabel from "./NSFWWarningLabel";
import BlurredNSFWImage from "./BlurredNSFWImage";

export default function StoryCard({ story }: { story: Story }) {
  // Check if story has NSFW flag
  const isNSFW = (story as any).is_nsfw || false;
  const isBlurred = (story as any).is_blurred || false;

  return (
    <Link to={`/story/${story.slug}`} className="group block">
      <div className="border border-border rounded-lg overflow-hidden bg-card hover:shadow-md transition-shadow">
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
                  className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
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
            <h3 className="font-medium leading-snug group-hover:text-primary transition-colors line-clamp-2 flex-1" style={{ fontFamily: "var(--font-display)" }}>
              {story.title}
            </h3>
            {isNSFW && !story.cover_url && (
              <NSFWWarningLabel variant="badge" />
            )}
          </div>
          {story.blurb && (
            <p className="text-sm text-muted-foreground line-clamp-2">{story.blurb}</p>
          )}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{story.author.display_name}</span>
            <span>·</span>
            <span>{story.chapter_count} ch.</span>
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
