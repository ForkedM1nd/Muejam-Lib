import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import EmptyState from "@/components/shared/EmptyState";
import { PageSkeleton } from "@/components/shared/Skeletons";
import { Bell, Check, CheckCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import type { Notification, CursorPage } from "@/types";

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [allNotifs, setAllNotifs] = useState<Notification[]>([]);
  const [cursor, setCursor] = useState<string | undefined>();

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", cursor],
    queryFn: async () => {
      const page = await api.getNotifications(cursor);
      if (cursor) setAllNotifs((prev) => [...prev, ...page.results]);
      else setAllNotifs(page.results);
      return page;
    },
  });

  const notifs = cursor ? allNotifs : (data?.results ?? []);

  // Filter out notifications from blocked users
  const filteredNotifs = notifs.filter((n) => !n.actor?.is_blocked);

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const hasUnread = filteredNotifs.some((n) => !n.is_read);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>Notifications</h1>
        {hasUnread && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
          >
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark All as Read
          </Button>
        )}
      </div>

      {isLoading && filteredNotifs.length === 0 ? (
        <PageSkeleton />
      ) : filteredNotifs.length === 0 ? (
        <EmptyState icon={<Bell className="h-10 w-10" />} title="All caught up" description="You have no notifications." />
      ) : (
        <div className="space-y-1">
          {filteredNotifs.map((n) => {
            const NotificationWrapper = n.target_url ? Link : "div";
            const wrapperProps = n.target_url
              ? { to: n.target_url, className: "block" }
              : {};

            return (
              <NotificationWrapper key={n.id} {...wrapperProps}>
                <div
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg transition-colors",
                    !n.is_read && "bg-accent/30",
                    n.target_url && "hover:bg-accent/50 cursor-pointer"
                  )}
                >
                  {n.actor?.avatar_url ? (
                    <img
                      src={n.actor.avatar_url}
                      alt=""
                      className="w-8 h-8 rounded-full object-cover mt-0.5"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-xs font-medium mt-0.5">
                      {n.actor?.display_name?.charAt(0) ?? "?"}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm">{n.message}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                    </p>
                  </div>
                  {!n.is_read && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 flex-shrink-0"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        markReadMutation.mutate(n.id);
                      }}
                    >
                      <Check className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              </NotificationWrapper>
            );
          })}
          {data?.has_more && (
            <div className="text-center py-4">
              <Button variant="outline" onClick={() => setCursor(data.next_cursor ?? undefined)}>Load more</Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
