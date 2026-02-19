import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle, XCircle, AlertTriangle, EyeOff, AlertOctagon, Ban, Loader2, History } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { services } from "@/lib/api";
import type { ModerationItem, ModerationAction, ModerationHistory } from "@/types";
import { formatDistanceToNow } from "date-fns";

interface ModerationActionPanelProps {
    item: ModerationItem;
    onActionComplete: () => void;
}

export function ModerationActionPanel({ item, onActionComplete }: ModerationActionPanelProps) {
    const { toast } = useToast();
    const [selectedAction, setSelectedAction] = useState<ModerationAction["action"] | null>(null);
    const [reason, setReason] = useState("");
    const [notes, setNotes] = useState("");
    const [duration, setDuration] = useState<number | undefined>(undefined);
    const [showHistory, setShowHistory] = useState(false);

    // Fetch moderation history
    const { data: history, isLoading: historyLoading } = useQuery({
        queryKey: ["moderation", "history", item.id],
        queryFn: () => services.moderation.getItemHistory(item.id),
        enabled: showHistory,
    });

    // Submit moderation action
    const reviewMutation = useMutation({
        mutationFn: (action: ModerationAction) =>
            services.moderation.reviewItem(item.id, action),
        onSuccess: () => {
            toast({
                title: "Action submitted",
                description: "The moderation action has been successfully applied.",
            });
            onActionComplete();
        },
        onError: (error: any) => {
            toast({
                title: "Action failed",
                description: error?.error?.message || "Failed to submit moderation action.",
                variant: "destructive",
            });
        },
    });

    const handleSubmit = () => {
        if (!selectedAction) {
            toast({
                title: "No action selected",
                description: "Please select a moderation action.",
                variant: "destructive",
            });
            return;
        }

        if (!reason.trim()) {
            toast({
                title: "Reason required",
                description: "Please provide a reason for this action.",
                variant: "destructive",
            });
            return;
        }

        const action: ModerationAction = {
            action: selectedAction,
            reason: reason.trim(),
            notes: notes.trim() || undefined,
            duration: duration || undefined,
        };

        reviewMutation.mutate(action);
    };

    const actionButtons = [
        {
            action: "approve" as const,
            label: "Approve",
            icon: CheckCircle,
            variant: "default" as const,
            description: "Content is acceptable, dismiss report",
        },
        {
            action: "hide" as const,
            label: "Hide Content",
            icon: EyeOff,
            variant: "secondary" as const,
            description: "Hide content from public view",
        },
        {
            action: "warn" as const,
            label: "Warn User",
            icon: AlertOctagon,
            variant: "secondary" as const,
            description: "Send warning to content creator",
        },
        {
            action: "ban" as const,
            label: "Ban User",
            icon: Ban,
            variant: "destructive" as const,
            description: "Ban user from platform",
            requiresDuration: true,
        },
        {
            action: "escalate" as const,
            label: "Escalate",
            icon: AlertTriangle,
            variant: "outline" as const,
            description: "Escalate to senior moderator",
        },
    ];

    return (
        <div className="space-y-6">
            {/* Action Buttons */}
            <Card>
                <CardHeader>
                    <CardTitle>Moderation Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {actionButtons.map((btn) => {
                            const Icon = btn.icon;
                            const isSelected = selectedAction === btn.action;
                            return (
                                <Button
                                    key={btn.action}
                                    variant={isSelected ? "default" : btn.variant}
                                    className="h-auto flex-col items-start p-4 gap-2"
                                    onClick={() => setSelectedAction(btn.action)}
                                >
                                    <div className="flex items-center gap-2 w-full">
                                        <Icon className="h-5 w-5" />
                                        <span className="font-semibold">{btn.label}</span>
                                    </div>
                                    <span className="text-xs text-left opacity-80">
                                        {btn.description}
                                    </span>
                                </Button>
                            );
                        })}
                    </div>

                    {/* Action Details Form */}
                    {selectedAction && (
                        <div className="space-y-4 pt-4 border-t">
                            <div className="space-y-2">
                                <Label htmlFor="reason">Reason *</Label>
                                <Textarea
                                    id="reason"
                                    placeholder="Explain why you're taking this action..."
                                    value={reason}
                                    onChange={(e) => setReason(e.target.value)}
                                    rows={3}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="notes">Additional Notes (Optional)</Label>
                                <Textarea
                                    id="notes"
                                    placeholder="Any additional context or information..."
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    rows={2}
                                />
                            </div>

                            {/* Duration field for ban action */}
                            {selectedAction === "ban" && (
                                <div className="space-y-2">
                                    <Label htmlFor="duration">Ban Duration (days)</Label>
                                    <Input
                                        id="duration"
                                        type="number"
                                        min="1"
                                        placeholder="Enter number of days (leave empty for permanent)"
                                        value={duration || ""}
                                        onChange={(e) =>
                                            setDuration(e.target.value ? parseInt(e.target.value) : undefined)
                                        }
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Leave empty for a permanent ban
                                    </p>
                                </div>
                            )}

                            <div className="flex gap-2 pt-2">
                                <Button
                                    onClick={handleSubmit}
                                    disabled={reviewMutation.isPending}
                                    className="flex-1"
                                >
                                    {reviewMutation.isPending ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Submitting...
                                        </>
                                    ) : (
                                        "Submit Action"
                                    )}
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setSelectedAction(null);
                                        setReason("");
                                        setNotes("");
                                        setDuration(undefined);
                                    }}
                                    disabled={reviewMutation.isPending}
                                >
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Moderation History */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <History className="h-5 w-5" />
                            Moderation History
                        </CardTitle>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowHistory(!showHistory)}
                        >
                            {showHistory ? "Hide" : "Show"}
                        </Button>
                    </div>
                </CardHeader>
                {showHistory && (
                    <CardContent>
                        {historyLoading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : !history || history.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-8">
                                No moderation history for this item
                            </p>
                        ) : (
                            <div className="space-y-3">
                                {history.map((entry, index) => (
                                    <div
                                        key={index}
                                        className="flex gap-3 p-3 rounded-lg bg-muted"
                                    >
                                        <div className="flex-1 space-y-1">
                                            <div className="flex items-center gap-2">
                                                <Badge variant="outline" className="capitalize">
                                                    {entry.action}
                                                </Badge>
                                                <span className="text-xs text-muted-foreground">
                                                    by {entry.moderator_handle}
                                                </span>
                                            </div>
                                            <p className="text-sm">{entry.reason}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {formatDistanceToNow(new Date(entry.created_at), {
                                                    addSuffix: true,
                                                })}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                )}
            </Card>
        </div>
    );
}
