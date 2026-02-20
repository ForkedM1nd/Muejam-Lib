import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import StoryCard from "@/components/shared/StoryCard";
import EmptyState from "@/components/shared/EmptyState";
import { PageSkeleton, StoryCardSkeleton } from "@/components/shared/Skeletons";
import { ShelfManager, StoryRemovalButton } from "@/components/shared/ShelfManager";
import { Plus, BookMarked, ChevronRight, ArrowLeft } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import type { Shelf } from "@/types";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

function CreateShelfForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => api.createShelf({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shelves"] });
      setName("");
      onCreated();
      toast({ title: "Shelf created successfully!" });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create shelf",
        description: error?.error?.message || "Please try again",
        variant: "destructive"
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      mutation.mutate();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Shelf name…"
        className="max-w-xs"
        maxLength={50}
        autoFocus
      />
      <Button type="submit" disabled={!name.trim() || mutation.isPending}>
        {mutation.isPending ? "Creating..." : "Create"}
      </Button>
    </form>
  );
}

function ShelfDetail({ shelf, onBack }: { shelf: Shelf; onBack: () => void }) {
  const { data: items, isLoading } = useQuery({
    queryKey: ["shelf-items", shelf.id],
    queryFn: () => api.getShelfItems(shelf.id),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Library
        </Button>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-semibold mb-1" style={{ fontFamily: "var(--font-display)" }}>
            {shelf.name}
          </h2>
          <p className="text-sm text-muted-foreground">
            {shelf.story_count} {shelf.story_count === 1 ? "story" : "stories"}
          </p>
        </div>
        <ShelfManager shelf={shelf} onShelfDeleted={onBack} />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <StoryCardSkeleton key={i} />)}
        </div>
      ) : items && items.length > 0 ? (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.story.id} className="border rounded-lg p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <StoryCard story={item.story} />
                </div>
                <StoryRemovalButton
                  shelfId={shelf.id}
                  storyId={item.story.id}
                  storyTitle={item.story.title}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="Empty shelf"
          description="Save stories to this shelf from any story page."
        />
      )}
    </div>
  );
}

export default function LibraryPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [selectedShelf, setSelectedShelf] = useState<Shelf | null>(null);

  const { data: shelves, isLoading } = useQuery({
    queryKey: ["shelves"],
    queryFn: () => api.getShelves(),
  });

  if (selectedShelf) {
    return (
      <div className="mx-auto max-w-5xl">
        <ShelfDetail shelf={selectedShelf} onBack={() => setSelectedShelf(null)} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Library"
        eyebrow="Your shelves"
        description="Organize your favorite stories into custom shelves."
        action={(
          <Button variant="outline" size="sm" onClick={() => setShowCreate(!showCreate)}>
            <Plus className="h-4 w-4 mr-1" /> New Shelf
          </Button>
        )}
      />

      {showCreate && (
        <SurfacePanel className="p-4">
          <h3 className="text-sm font-medium mb-3">Create a new shelf</h3>
          <CreateShelfForm onCreated={() => setShowCreate(false)} />
        </SurfacePanel>
      )}

      {isLoading ? (
        <PageSkeleton />
      ) : shelves && shelves.length > 0 ? (
        <SurfacePanel className="p-2">
          <div className="space-y-2">
            {shelves.map((shelf) => (
              <button
                key={shelf.id}
                onClick={() => setSelectedShelf(shelf)}
                className="group flex w-full items-center justify-between rounded-xl border border-transparent p-4 text-left transition-colors hover:border-border hover:bg-accent/30"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-accent/50 p-2 transition-colors group-hover:bg-accent">
                    <BookMarked className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{shelf.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {shelf.story_count} {shelf.story_count === 1 ? "story" : "stories"}
                    </p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
              </button>
            ))}
          </div>
        </SurfacePanel>
      ) : (
        <EmptyState
          title="No shelves yet"
          description="Create a shelf to organize your favorite stories."
        />
      )}
    </div>
  );
}
