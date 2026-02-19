import { useMutation, useQueryClient } from '@tanstack/react-query';
import { cacheInvalidation, createOptimisticUpdate } from '@/lib/mutations';
import { queryKeys } from '@/lib/queryKeys';

/**
 * Example mutation hooks demonstrating cache invalidation and optimistic updates
 * 
 * These hooks show the patterns for implementing mutations with:
 * - Automatic cache invalidation
 * - Optimistic updates
 * - Rollback on error
 * 
 * NOTE: These are example implementations showing the pattern.
 * Actual API methods would need to be added to the api.ts file for each endpoint.
 */

/**
 * Hook for following/unfollowing a user with optimistic updates
 * 
 * Example usage:
 * const followMutation = useFollowUser(userId);
 * followMutation.mutate('follow');
 */
export function useFollowUser(userId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (action: 'follow' | 'unfollow') => {
            // TODO: Add followUser/unfollowUser methods to api.ts
            const endpoint = action === 'follow'
                ? `/v1/users/${userId}/follow/`
                : `/v1/users/${userId}/unfollow/`;

            const response = await fetch(endpoint, {
                method: 'POST',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to follow/unfollow user');
            }

            return response.json();
        },
        ...createOptimisticUpdate<
            { is_following: boolean; followers_count: number },
            'follow' | 'unfollow'
        >(
            queryClient,
            queryKeys.users.profile(userId),
            (old, action) => {
                if (!old) return old as any;
                const isFollowing = action === 'follow';
                return {
                    ...old,
                    is_following: isFollowing,
                    followers_count: old.followers_count + (isFollowing ? 1 : -1),
                };
            }
        ),
        onSuccess: () => {
            cacheInvalidation.user(queryClient, userId);
        },
    });
}

/**
 * Hook for creating a story with cache invalidation
 */
export function useCreateStory() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: { title: string; description: string; genre: string }) => {
            // TODO: Add createStory method to api.ts
            const response = await fetch('/v1/stories/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to create story');
            }

            return response.json();
        },
        onSuccess: (data) => {
            cacheInvalidation.story(queryClient);
            cacheInvalidation.discovery(queryClient);
            return data;
        },
    });
}

/**
 * Hook for updating a story with optimistic updates
 */
export function useUpdateStory(storyId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: Partial<{ title: string; description: string }>) => {
            // TODO: Add updateStory method to api.ts
            const response = await fetch(`/v1/stories/${storyId}/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to update story');
            }

            return response.json();
        },
        ...createOptimisticUpdate<
            { id: string; title: string; description: string },
            Partial<{ title: string; description: string }>
        >(
            queryClient,
            queryKeys.stories.detail(storyId),
            (old, variables) => {
                if (!old) return old as any;
                return { ...old, ...variables };
            }
        ),
        onSuccess: () => {
            cacheInvalidation.story(queryClient, storyId);
        },
    });
}

/**
 * Hook for deleting a story with cache invalidation
 */
export function useDeleteStory() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (storyId: string) => {
            // TODO: Add deleteStory method to api.ts
            const response = await fetch(`/v1/stories/${storyId}/`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to delete story');
            }

            return response.json();
        },
        onSuccess: (_data, storyId) => {
            queryClient.removeQueries({ queryKey: queryKeys.stories.detail(storyId) });
            cacheInvalidation.story(queryClient);
            cacheInvalidation.discovery(queryClient);
        },
    });
}

/**
 * Hook for creating a highlight with cache invalidation
 */
export function useCreateHighlight(chapterId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: { text: string; start_offset: number; end_offset: number }) => {
            // TODO: Add createHighlight method to api.ts
            const response = await fetch(`/v1/chapters/${chapterId}/highlights/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to create highlight');
            }

            return response.json();
        },
        onSuccess: () => {
            cacheInvalidation.highlights(queryClient, chapterId);
        },
    });
}

/**
 * Hook for deleting a highlight with cache invalidation
 */
export function useDeleteHighlight(chapterId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (highlightId: string) => {
            // TODO: Add deleteHighlight method to api.ts
            const response = await fetch(`/v1/highlights/${highlightId}/`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to delete highlight');
            }

            return response.json();
        },
        onSuccess: () => {
            cacheInvalidation.highlights(queryClient, chapterId);
        },
    });
}

/**
 * Hook for marking notifications as read with optimistic updates
 */
export function useMarkNotificationRead() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (notificationId: string) => {
            // TODO: Add markNotificationRead method to api.ts
            const response = await fetch(`/v1/notifications/${notificationId}/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ read: true }),
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to mark notification as read');
            }

            return response.json();
        },
        ...createOptimisticUpdate<
            Array<{ id: string; read: boolean }>,
            string
        >(
            queryClient,
            queryKeys.notifications.list(),
            (old, notificationId) => {
                if (!old) return old as any;
                return old.map((notification) =>
                    notification.id === notificationId
                        ? { ...notification, read: true }
                        : notification
                );
            }
        ),
        onSuccess: () => {
            cacheInvalidation.notifications(queryClient);
        },
    });
}

/**
 * Hook for marking all notifications as read
 */
export function useMarkAllNotificationsRead() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            // TODO: Add markAllNotificationsRead method to api.ts
            const response = await fetch('/v1/notifications/mark-all-read/', {
                method: 'POST',
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to mark all notifications as read');
            }

            return response.json();
        },
        onMutate: async () => {
            await queryClient.cancelQueries({ queryKey: queryKeys.notifications.list() });
            const previous = queryClient.getQueryData(queryKeys.notifications.list());

            queryClient.setQueryData<Array<{ id: string; read: boolean }>>(
                queryKeys.notifications.list(),
                (old) => {
                    if (!old) return old;
                    return old.map((notification) => ({ ...notification, read: true }));
                }
            );

            return { previous };
        },
        onError: (_error, _variables, context) => {
            if (context?.previous) {
                queryClient.setQueryData(queryKeys.notifications.list(), context.previous);
            }
        },
        onSuccess: () => {
            cacheInvalidation.notifications(queryClient);
        },
    });
}

/**
 * Hook for creating a whisper with cache invalidation
 */
export function useCreateWhisper() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: { content: string; story_id?: string; highlight_id?: string }) => {
            // TODO: Add createWhisper method to api.ts
            const response = await fetch('/v1/whispers/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to create whisper');
            }

            return response.json();
        },
        onSuccess: () => {
            cacheInvalidation.whispers(queryClient);
        },
    });
}

/**
 * Hook for updating privacy settings with optimistic updates
 */
export function useUpdatePrivacySettings() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (settings: Record<string, unknown>) => {
            // TODO: Add updatePrivacySettings method to api.ts
            const response = await fetch('/v1/gdpr/privacy/settings/update/', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
                credentials: 'include',
            });

            if (!response.ok) {
                throw new Error('Failed to update privacy settings');
            }

            return response.json();
        },
        ...createOptimisticUpdate<
            Record<string, unknown>,
            Record<string, unknown>
        >(
            queryClient,
            queryKeys.gdpr.privacySettings(),
            (old, variables) => {
                if (!old) return old as any;
                return { ...old, ...variables };
            }
        ),
    });
}
