import { Link } from "react-router-dom";
import type { Story } from "@/types";
import TagPill from "./TagPill";

export default function StoryCard({ story }: { story: Story }) {
  return (
    <Link to={`/story/${story.slug}`} className="group block">
      <div className="border border-border rounded-lg overflow-hidden bg-card hover:shadow-md transition-shadow">
        {story.cover_url && (
          <div className="aspect-[3/2] overflow-hidden bg-muted">
            <img
              src={story.cover_url}
              alt={story.title}
              className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
              loading="lazy"
            />
          </div>
        )}
        <div className="p-4 space-y-2">
          <h3 className="font-medium leading-snug group-hover:text-primary transition-colors line-clamp-2" style={{ fontFamily: "var(--font-display)" }}>
            {story.title}
          </h3>
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
