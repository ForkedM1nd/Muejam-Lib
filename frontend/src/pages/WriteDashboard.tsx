import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PageSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Plus, PenLine, ChevronRight, FileText, CheckCircle2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { useState } from "react";
import type { Story } from "@/types";

export default function WriteDashboard() {
  const queryClient = useQueryClient();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [title, setTitle] = useState("");

  const { data: stories, isLoading } = useQuery({
    queryKey: ["my-stories"],
    queryFn: () => api.getStories({ q: "mine" }),
  });

  const createMutation = useMutation({
    mutationFn: () => api.createStory({ title }),
    onSuccess: (story) => {
      queryClient.invalidateQueries({ queryKey: ["my-stories"] });
      setTitle("");
      setShowCreateDialog(false);
      toast({ title: "Story created successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create story",
        description: error?.error?.message || "Please try again",
        variant: "destructive",
      });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (title.trim()) {
      createMutation.mutate();
    }
  };

  const drafts = stories?.results?.filter((s) => s.status === "draft") || [];
  const published = stories?.results?.filter((s) => s.status === "published") || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold mb-1" style={{ fontFamily: "var(--font-display)" }}>
            Write
          </h1>
          <p className="text-sm text-muted-foreground">
            Create and manage your stories
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-1" /> New Story
        </Button>
      </div>

      {isLoading ? (
        <PageSkeleton />
      ) : stories?.results && stories.results.length > 0 ? (
        <div className="space-y-8">
          {/* Drafts Section */}
          {drafts.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-lg font-medium">Drafts</h2>
                <span className="text-xs text-muted-foreground">({drafts.length})</span>
              </div>
              <div className="space-y-2">
                {drafts.map((story) => (
                  <Link
                    key={story.id}
                    to={`/write/story/${story.id}`}
                    className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-md bg-accent/50 group-hover:bg-accent transition-colors">
                        <PenLine className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{story.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {story.chapter_count} {story.chapter_count === 1 ? "chapter" : "chapters"}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Published Section */}
          {published.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <h2 className="text-lg font-medium">Published</h2>
                <span className="text-xs text-muted-foreground">({published.length})</span>
              </div>
              <div className="space-y-2">
                {published.map((story) => (
                  <Link
                    key={story.id}
                    to={`/write/story/${story.id}`}
                    className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-md bg-green-50 dark:bg-green-950 group-hover:bg-green-100 dark:group-hover:bg-green-900 transition-colors">
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{story.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {story.chapter_count} {story.chapter_count === 1 ? "chapter" : "chapters"}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </Link>
                ))}
              </div>
            </section>
          )}
        </div>
      ) : (
        <EmptyState
          title="No stories yet"
          description="Start writing your first serial story!"
        />
      )}

      {/* Create Story Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create a new story</DialogTitle>
            <DialogDescription>
              Give your story a title to get started. You can add more details later.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Story title"
                maxLength={100}
                autoFocus
              />
            </div>
            <DialogFooter className="mt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!title.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? "Creating..." : "Create Story"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
