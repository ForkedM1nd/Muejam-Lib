import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from "@tanstack/react-query";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { api } from "@/lib/api";
import WhisperCard from "@/components/shared/WhisperCard";
import WhisperComposer from "@/components/shared/WhisperComposer";
import { WhisperSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { uploadFile } from "@/lib/upload";
import { Loader2 } from "lucide-react";
import type { Whisper } from "@/types";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";

export default function WhispersPage() {
  const { isSignedIn } = useSafeAuth();
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery({
    queryKey: ["whispers", "global"],
    queryFn: ({ pageParam }) => api.getWhispers({ scope: "global", cursor: pageParam }),
    getNextPageParam: (lastPage) => lastPage.has_more ? lastPage.next_cursor : undefined,
    initialPageParam: undefined as string | undefined,
  });

  const whispers = data?.pages.flatMap((page) => page.results) ?? [];

  // Filter out whispers from blocked users
  const filteredWhispers = whispers.filter((whisper) => !whisper.author.is_blocked);

  const createMutation = useMutation({
    mutationFn: async ({ content, mediaFile, recaptchaToken }: { content: string; mediaFile?: File; recaptchaToken?: string | null }) => {
      let media_key: string | undefined;
      if (mediaFile) {
        media_key = await uploadFile(mediaFile, "whisper_media");
      }
      return api.createWhisper({ content, scope: "GLOBAL", media_key, recaptcha_token: recaptchaToken });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["whispers"] });
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
      queryClient.invalidateQueries({ queryKey: ["whispers"] });
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
    mutationFn: async (whisper: Whisper) => {
      if (whisper.is_liked) {
        await api.unlikeWhisper(whisper.id);
      } else {
        await api.likeWhisper(whisper.id);
      }
    },
    onMutate: async (whisper) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ["whispers"] });
      const previousData = queryClient.getQueryData(["whispers", "global"]);

      queryClient.setQueryData(["whispers", "global"], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          pages: old.pages.map((page: any) => ({
            ...page,
            results: page.results.map((w: Whisper) =>
              w.id === whisper.id
                ? {
                  ...w,
                  is_liked: !w.is_liked,
                  like_count: w.is_liked ? w.like_count - 1 : w.like_count + 1,
                }
                : w
            ),
          })),
        };
      });

      return { previousData };
    },
    onError: (err, whisper, context) => {
      queryClient.setQueryData(["whispers", "global"], context?.previousData);
      toast({
        title: "Failed to update like",
        variant: "destructive",
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["whispers"] });
    },
  });

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader title="Whispers" eyebrow="Threads" description="Share quick thoughts with the community." />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_250px]">
        <div className="space-y-4">
          {isSignedIn ? (
            <SurfacePanel className="p-4">
              <WhisperComposer
                onSubmit={async (content, mediaFile, _scope, _storyId, _highlightId, recaptchaToken) => {
                  await createMutation.mutateAsync({ content, mediaFile, recaptchaToken });
                }}
                submitting={createMutation.isPending}
              />
            </SurfacePanel>
          ) : (
            <SurfacePanel className="p-4">
              <p className="text-sm text-muted-foreground">Sign in to post whispers and join the conversation.</p>
              <div className="mt-3">
                <Link to="/sign-in">
                  <Button size="sm">Sign In</Button>
                </Link>
              </div>
            </SurfacePanel>
          )}

          {isLoading ? (
            <SurfacePanel className="space-y-4 p-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <WhisperSkeleton key={i} />
              ))}
            </SurfacePanel>
          ) : isError ? (
            <EmptyState
              title="Failed to load whispers"
              description="Something went wrong. Please try again."
              action={<Button variant="outline" onClick={() => refetch()}>Retry</Button>}
            />
          ) : filteredWhispers.length === 0 ? (
            <EmptyState
              title="No whispers yet"
              description="Be the first to share your thoughts!"
            />
          ) : (
            <SurfacePanel className="overflow-hidden">
              <div className="divide-y divide-border/70">
                {filteredWhispers.map((whisper) => (
                  <WhisperCard
                    key={whisper.id}
                    whisper={whisper}
                    onLike={() => likeMutation.mutate(whisper)}
                    onReply={async (content) => {
                      await replyMutation.mutateAsync({ whisperId: whisper.id, content });
                    }}
                  />
                ))}
              </div>
            </SurfacePanel>
          )}

          {hasNextPage && (
            <div className="flex justify-center py-2">
              <Button
                variant="outline"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  "Load more"
                )}
              </Button>
            </div>
          )}
        </div>

        <SurfacePanel className="hidden h-fit p-4 lg:block">
          <h3 className="text-sm font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            Whisper Tips
          </h3>
          <ul className="mt-2 space-y-2 text-xs text-muted-foreground">
            <li>Keep posts short and specific.</li>
            <li>Tag spoilers clearly when needed.</li>
            <li>Respond to chapters to boost discovery.</li>
          </ul>
        </SurfacePanel>
      </div>
    </div>
  );
}
