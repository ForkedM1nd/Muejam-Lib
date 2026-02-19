import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { services } from "@/lib/api";
import type { QueueParams, ModerationItem, CursorPage } from "@/types";

export function useModerationQueue(params: QueueParams = {}) {
    const queryClient = useQueryClient();

    const query = useInfiniteQuery<CursorPage<ModerationItem>>({
        queryKey: ["moderation", "queue", params],
        queryFn: ({ pageParam }) =>
            services.moderation.getQueue({
                ...params,
                cursor: pageParam as string | undefined,
            }),
        getNextPageParam: (lastPage) => lastPage.next_cursor,
        initialPageParam: undefined,
        staleTime: 30 * 1000, // 30 seconds - moderation queue should be relatively fresh
        refetchInterval: 60 * 1000, // Auto-refetch every minute for real-time updates
    });

    const invalidateQueue = () => {
        queryClient.invalidateQueries({ queryKey: ["moderation", "queue"] });
    };

    return {
        ...query,
        invalidateQueue,
    };
}
