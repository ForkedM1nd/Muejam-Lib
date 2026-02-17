import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { api } from "@/lib/api";
import { uploadFile } from "@/lib/upload";
import { Button } from "@/components/ui/button";
import TagPill from "@/components/shared/TagPill";
import WhisperCard from "@/components/shared/WhisperCard";
import WhisperComposer from "@/components/shared/WhisperComposer";
import { PageSkeleton, ChapterListSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { BookOpen, Bookmark, ChevronRight } from "lucide-react";
import { useState } from "react";
import { toast } from "@/hooks/use-toast";

export default function StoryPage() {
  const { slug } = useParams<{ slug: string }>();
  const { isSignedIn } = useSafeAuth();
  const queryClient = useQueryClient();

  const { data: story, isLoading, isError } = useQuery({
    queryKey: ["story", slug],
    queryFn: () => api.getStory(slug!),
    enabled: !!slug,
  });

  const { data: chapters, isLoading: chaptersLoading } = useQuery({
    queryKey: ["story-chapters", story?.id],
    queryFn: () => api.getStoryChapters(story!.id),
    enabled: !!story?.id,
  });

  const { data: whispers } = useQuery({
    queryKey: ["story-whispers", story?.id],
    queryFn: () => api.getWhispers({ scope: "story", story_id: story!.id }),
    enabled: !!story?.id,
  });

  const [savingShelf, setSavingShelf] = useState(false);

  const createWhisperMutation = useMutation({
    mutationFn: async ({ content, mediaFile }: { content: string; mediaFile?: File }) => {
      let media_key: string | undefined;
      if (mediaFile) {
        media_key = await uploadFile(mediaFile, "whisper_media");
      }
      return api.createWhisper({
        content,
        scope: "STORY",
        story_id: story!.id,
        media_key,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story-whispers", story?.id] });
      toast({ title: "Whisper posted successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to post whisper",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const replyMutation = useMutation({
    mutationFn: async ({ whisperId, content }: { whisperId: string; content: string }) => {
      return api.replyWhisper(whisperId, { content });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story-whispers", story?.id] });
      toast({ title: "Reply posted successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to post reply",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const likeMutation = useMutation({
    mutationFn: async (whisperId: string, isLiked: boolean) => {
      if (isLiked) {
        await api.unlikeWhisper(whisperId);
      } else {
        await api.likeWhisper(whisperId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story-whispers", story?.id] });
    },
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !story) return <EmptyState title="Story not found" />;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-6">
        {story.cover_url && (
          <div className="sm:w-48 flex-shrink-0">
            <img
              src={story.cover_url}
              alt={story.title}
              className="w-full rounded-lg object-cover aspect-[2/3]"
              loading="lazy"
            />
          </div>
        )}
        <div className="space-y-3 flex-1">
          <h1 className="text-3xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>{story.title}</h1>
          <Link to={`/u/${story.author.handle}`} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            by {story.author.display_name}
          </Link>
          {story.blurb && <p className="text-sm text-muted-foreground leading-relaxed">{story.blurb}</p>}
          {story.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {story.tags.map((t) => <TagPill key={t.id} name={t.name} />)}
            </div>
          )}
          <div className="flex items-center gap-2 pt-2">
            {chapters && chapters.length > 0 && (
              <Link to={`/read/${chapters[0].id}`}>
                <Button size="sm"><BookOpen className="h-4 w-4 mr-1" /> Start Reading</Button>
              </Link>
            )}
            {isSignedIn ? (
              <Button
                variant="outline"
                size="sm"
                disabled={savingShelf}
                onClick={async () => {
                  toast({ title: "Save to shelf", description: "Shelf picker coming soon!" });
                }}
              >
                <Bookmark className="h-4 w-4 mr-1" /> Save
              </Button>
            ) : (
              <Button variant="outline" size="sm" disabled>
                <Bookmark className="h-4 w-4 mr-1" /> Sign in to Save
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Chapters */}
      <section>
        <h2 className="text-lg font-medium mb-3" style={{ fontFamily: "var(--font-display)" }}>Chapters</h2>
        {chaptersLoading ? (
          <ChapterListSkeleton />
        ) : chapters && chapters.length > 0 ? (
          <div className="divide-y divide-border">
            {chapters.filter(c => c.status === "published").map((ch, i) => (
              <Link
                key={ch.id}
                to={`/read/${ch.id}`}
                className="flex items-center justify-between py-3 group hover:bg-accent/30 -mx-2 px-2 rounded-md transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-6 text-right">{i + 1}</span>
                  <span className="text-sm font-medium group-hover:text-primary transition-colors">{ch.title}</span>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState title="No chapters yet" description="The author hasn't published any chapters." />
        )}
      </section>

      {/* Story Whispers */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium" style={{ fontFamily: "var(--font-display)" }}>
          Whispers about this story
        </h2>

        {isSignedIn && (
          <WhisperComposer
            placeholder="Share your thoughts about this story..."
            onSubmit={async (content, mediaFile) => {
              await createWhisperMutation.mutateAsync({ content, mediaFile });
            }}
            submitting={createWhisperMutation.isPending}
          />
        )}

        {whispers?.results && whispers.results.length > 0 ? (
          <div className="space-y-0 divide-y divide-border">
            {whispers.results.map((whisper) => (
              <WhisperCard
                key={whisper.id}
                whisper={whisper}
                onLike={() => likeMutation.mutate(whisper.id, whisper.is_liked ?? false)}
                onReply={async (content) => {
                  await replyMutation.mutateAsync({ whisperId: whisper.id, content });
                }}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No whispers yet"
            description="Be the first to share a thought about this story."
          />
        )}
      </section>
    </div>
  );
}
