import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { AlertCircle, Eye, User, FileText, MessageSquare } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ModerationItem } from "@/types";

interface ModerationQueueItemProps {
    item: ModerationItem;
    onReview: (itemId: string) => void;
}

const contentTypeIcons = {
    story: FileText,
    chapter: FileText,
    whisper: MessageSquare,
    user: User,
};

const severityColors = {
    low: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    high: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

const statusColors = {
    pending: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
    reviewing: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    resolved: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    escalated: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
};

export function ModerationQueueItem({ item, onReview }: ModerationQueueItemProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const ContentIcon = contentTypeIcons[item.content_type];

    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                        <div className="mt-1">
                            <ContentIcon className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-2">
                                <Badge variant="outline" className="capitalize">
                                    {item.content_type}
                                </Badge>
                                <Badge className={severityColors[item.severity]}>
                                    <AlertCircle className="h-3 w-3 mr-1" />
                                    {item.severity}
                                </Badge>
                                <Badge className={statusColors[item.status]}>
                                    {item.status}
                                </Badge>
                            </div>
                            <p className="text-sm font-medium mb-1">
                                Reason: {item.report_reason}
                            </p>
                            <p className="text-xs text-muted-foreground">
                                Reported {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onReview(item.id)}
                    >
                        <Eye className="h-4 w-4 mr-2" />
                        Review
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {/* Content Preview */}
                    <div>
                        <p className="text-sm font-medium mb-1">Content Preview:</p>
                        <div className="bg-muted p-3 rounded-md">
                            <p className="text-sm line-clamp-3">
                                {item.content_preview}
                            </p>
                        </div>
                    </div>

                    {/* Report Details - Expandable */}
                    {item.report_details && (
                        <div>
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="text-sm font-medium text-primary hover:underline"
                            >
                                {isExpanded ? "Hide" : "Show"} Report Details
                            </button>
                            {isExpanded && (
                                <div className="mt-2 bg-muted p-3 rounded-md">
                                    <p className="text-sm whitespace-pre-wrap">
                                        {item.report_details}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
                        <span>Content ID: {item.content_id}</span>
                        <span>Reporter ID: {item.reporter_id}</span>
                        {item.assigned_to && (
                            <span>Assigned to: {item.assigned_to}</span>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
