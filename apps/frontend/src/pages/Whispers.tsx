import { useState } from "react";
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
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold mb-1" style={{ fontFamily: "var(--font-display)" }}>
          Whispers
        </h1>
        <p className="text-sm text-muted-foreground">
          Share your thoughts with the community
        </p>
      </div>

      {isSignedIn && (
        <WhisperComposer
          onSubmit={async (content, mediaFile, _scope, _storyId, _highlightId, recaptchaToken) => {
            await createMutation.mutateAsync({ content, mediaFile, recaptchaToken });
          }}
          submitting={createMutation.isPending}
        />
      )}

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <WhisperSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <EmptyState
          title="Failed to load whispers"
          description="Something went wrong. Please try again."
          action={<Button variant="outline" onClick={() => refetch()}>Retry</Button>}
        />
      ) : whispers.length === 0 ? (
        <EmptyState
          title="No whispers yet"
          description="Be the first to share your thoughts!"
        />
      ) : (
        <div className="space-y-0 divide-y divide-border">
          {whispers.map((whisper) => (
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
      )}

      {hasNextPage && (
        <div className="flex justify-center py-6">
          <Button
            variant="outline"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
          >
            {isFetchingNextPage ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              "Load more"
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
