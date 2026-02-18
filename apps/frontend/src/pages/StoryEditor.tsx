import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { PageSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { ImageUpload } from "@/components/shared/ImageUpload";
import { toast } from "@/hooks/use-toast";
import { Save, Globe, Plus, Eye, PenLine, ArrowLeft, X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { useRecaptchaToken } from "@/hooks/useRecaptchaToken";

function ChapterEditor({ chapterId, onBack }: { chapterId: string; onBack: () => void }) {
  const queryClient = useQueryClient();
  const { data: chapter, isLoading } = useQuery({
    queryKey: ["chapter", chapterId],
    queryFn: () => api.getChapter(chapterId),
  });

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [initialized, setInitialized] = useState(false);
  const getRecaptchaToken = useRecaptchaToken('submit_chapter');

  if (chapter && !initialized) {
    setTitle(chapter.title);
    setContent(chapter.content ?? "");
    setInitialized(true);
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const recaptchaToken = await getRecaptchaToken();
      return api.updateChapter(chapterId, { title, content, recaptcha_token: recaptchaToken });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", chapterId] });
      queryClient.invalidateQueries({ queryKey: ["story-chapters"] });
      toast({ title: "Chapter saved successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to save chapter",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const publishMutation = useMutation({
    mutationFn: async () => {
      const recaptchaToken = await getRecaptchaToken();
      return api.publishChapter(chapterId, recaptchaToken);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", chapterId] });
      queryClient.invalidateQueries({ queryKey: ["story-chapters"] });
      toast({ title: "Chapter published successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to publish chapter",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  if (isLoading) return <PageSkeleton />;
  if (!chapter) return <EmptyState title="Chapter not found" />;

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={onBack}>
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to story
      </Button>

      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold mb-1" style={{ fontFamily: "var(--font-display)" }}>
            Edit Chapter
          </h2>
          <p className="text-sm text-muted-foreground">
            {chapter.status === "published" ? "Published" : "Draft"} · {wordCount} words
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">Chapter Title</label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Chapter title"
            className="text-lg"
            maxLength={100}
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Content</label>
          <Tabs defaultValue="write" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="write">
                <PenLine className="h-3.5 w-3.5 mr-1.5" /> Write
              </TabsTrigger>
              <TabsTrigger value="preview">
                <Eye className="h-3.5 w-3.5 mr-1.5" /> Preview
              </TabsTrigger>
            </TabsList>

            <TabsContent value="write" className="mt-4">
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write your chapter in Markdown…

**Markdown tips:**
- Use **bold** and *italic* for emphasis
- Create headings with # symbols
- Add links: [text](url)
- Insert images: ![alt](url)"
                className="min-h-[500px] font-mono text-sm resize-y"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Supports Markdown formatting
              </p>
            </TabsContent>

            <TabsContent value="preview" className="mt-4">
              <div className="prose prose-neutral dark:prose-invert max-w-none p-6 border rounded-lg min-h-[500px] bg-accent/20">
                {content.trim() ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
                    {content}
                  </ReactMarkdown>
                ) : (
                  <p className="text-muted-foreground italic">
                    Nothing to preview yet. Start writing in the Write tab.
                  </p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>

        <div className="flex gap-2 pt-4">
          <Button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || !title.trim()}
          >
            <Save className="h-4 w-4 mr-1" />
            {saveMutation.isPending ? "Saving..." : "Save Draft"}
          </Button>
          {chapter.status !== "published" && (
            <Button
              variant="outline"
              onClick={() => publishMutation.mutate()}
              disabled={publishMutation.isPending || !title.trim() || !content.trim()}
            >
              <Globe className="h-4 w-4 mr-1" />
              {publishMutation.isPending ? "Publishing..." : "Publish Chapter"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function StoryEditor() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [editingChapter, setEditingChapter] = useState<string | null>(null);
  const [newChapterTitle, setNewChapterTitle] = useState("");
  const getRecaptchaToken = useRecaptchaToken('submit_story');

  const { data: story, isLoading } = useQuery({
    queryKey: ["story-edit", id],
    queryFn: () => api.getStory(id!),
    enabled: !!id,
  });

  const { data: chapters } = useQuery({
    queryKey: ["story-chapters", id],
    queryFn: () => api.getStoryChapters(id!),
    enabled: !!id,
  });

  const [title, setTitle] = useState("");
  const [blurb, setBlurb] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [initialized, setInitialized] = useState(false);

  if (story && !initialized) {
    setTitle(story.title);
    setBlurb(story.blurb ?? "");
    setTags(story.tags.map(t => t.name));
    setInitialized(true);
  }

  const updateMutation = useMutation({
    mutationFn: async () => {
      const recaptchaToken = await getRecaptchaToken();
      return api.updateStory(id!, { title, blurb, tags, recaptcha_token: recaptchaToken } as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story-edit", id] });
      toast({ title: "Story saved successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to save story",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const publishMutation = useMutation({
    mutationFn: async () => {
      const recaptchaToken = await getRecaptchaToken();
      return api.publishStory(id!, recaptchaToken);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["story-edit", id] });
      toast({ title: "Story published successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to publish story",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const createChapterMutation = useMutation({
    mutationFn: async () => {
      const recaptchaToken = await getRecaptchaToken();
      return api.createChapter(id!, { title: newChapterTitle, recaptcha_token: recaptchaToken });
    },
    onSuccess: (chapter) => {
      queryClient.invalidateQueries({ queryKey: ["story-chapters", id] });
      setNewChapterTitle("");
      toast({ title: "Chapter created successfully!" });
      setEditingChapter(chapter.id);
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create chapter",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const handleCoverUpload = async (objectKey: string) => {
    try {
      await api.updateStory(id!, { cover_key: objectKey } as any);
      queryClient.invalidateQueries({ queryKey: ["story-edit", id] });
    } catch (err: any) {
      toast({
        title: "Failed to save cover",
        description: err.message || "Please try again",
        variant: "destructive",
      });
    }
  };

  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  };

  if (isLoading) return <PageSkeleton />;
  if (!story) return <EmptyState title="Story not found" />;

  if (editingChapter) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ChapterEditor chapterId={editingChapter} onBack={() => setEditingChapter(null)} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <Link to="/write" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Write
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold mb-1" style={{ fontFamily: "var(--font-display)" }}>
            Edit Story
          </h1>
          <p className="text-sm text-muted-foreground">
            {story.status === "published" ? "Published" : "Draft"}
          </p>
        </div>
      </div>

      <section className="space-y-6 p-6 border rounded-lg">
        <h2 className="text-lg font-medium">Story Details</h2>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Title</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter story title"
              maxLength={100}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Blurb</label>
            <Textarea
              value={blurb}
              onChange={(e) => setBlurb(e.target.value)}
              placeholder="Write a short description of your story..."
              rows={4}
              maxLength={500}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {blurb.length}/500 characters
            </p>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Tags</label>
            <div className="flex gap-2 mb-2">
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagInputKeyDown}
                placeholder="Add a tag (press Enter)"
                maxLength={30}
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddTag}
                disabled={!tagInput.trim()}
              >
                Add
              </Button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="gap-1">
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <ImageUpload
            type="cover"
            currentImageUrl={story.cover_url}
            onUploadComplete={handleCoverUpload}
            label="Cover Image"
          />
        </div>

        <div className="flex gap-2 pt-4">
          <Button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending || !title.trim()}
          >
            <Save className="h-4 w-4 mr-1" />
            {updateMutation.isPending ? "Saving..." : "Save Draft"}
          </Button>
          {story.status !== "published" && (
            <Button
              variant="outline"
              onClick={() => publishMutation.mutate()}
              disabled={publishMutation.isPending || !title.trim()}
            >
              <Globe className="h-4 w-4 mr-1" />
              {publishMutation.isPending ? "Publishing..." : "Publish Story"}
            </Button>
          )}
        </div>
      </section>

      <Separator />

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Chapters</h2>
          <span className="text-sm text-muted-foreground">
            {chapters?.length || 0} {chapters?.length === 1 ? "chapter" : "chapters"}
          </span>
        </div>

        <div className="flex gap-2">
          <Input
            value={newChapterTitle}
            onChange={(e) => setNewChapterTitle(e.target.value)}
            placeholder="New chapter title…"
            maxLength={100}
            onKeyDown={(e) => {
              if (e.key === "Enter" && newChapterTitle.trim()) {
                createChapterMutation.mutate();
              }
            }}
          />
          <Button
            variant="outline"
            disabled={!newChapterTitle.trim() || createChapterMutation.isPending}
            onClick={() => createChapterMutation.mutate()}
          >
            <Plus className="h-4 w-4 mr-1" />
            {createChapterMutation.isPending ? "Adding..." : "Add Chapter"}
          </Button>
        </div>

        {chapters && chapters.length > 0 ? (
          <div className="space-y-2">
            {chapters.map((ch, i) => (
              <button
                key={ch.id}
                onClick={() => setEditingChapter(ch.id)}
                className="w-full flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors text-left group"
              >
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-muted-foreground w-8">
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium">{ch.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {ch.status === "published" ? "Published" : "Draft"} · {ch.word_count} words
                    </p>
                  </div>
                </div>
                <PenLine className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
              </button>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No chapters yet"
            description="Add your first chapter to start writing."
          />
        )}
      </section>
    </div>
  );
}
