import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { services } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useReportRateLimit } from "@/hooks/useReportRateLimit";
import { AlertTriangle, Flag, Info } from "lucide-react";
import type { ReportReason, ReportableContentType } from "@/types";

interface ReportModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    contentType: ReportableContentType;
    contentId: string;
    contentTitle?: string;
}

const REPORT_REASONS: { value: ReportReason; label: string; description: string }[] = [
    { value: "spam", label: "Spam", description: "Unwanted or repetitive content" },
    { value: "harassment", label: "Harassment", description: "Bullying or targeted attacks" },
    { value: "hate_speech", label: "Hate Speech", description: "Content promoting hatred or discrimination" },
    { value: "violence", label: "Violence", description: "Graphic or threatening violent content" },
    { value: "sexual_content", label: "Sexual Content", description: "Inappropriate sexual material" },
    { value: "copyright", label: "Copyright Violation", description: "Unauthorized use of copyrighted material" },
    { value: "misinformation", label: "Misinformation", description: "False or misleading information" },
    { value: "other", label: "Other", description: "Other policy violations" },
];

export function ReportModal({
    open,
    onOpenChange,
    contentType,
    contentId,
    contentTitle,
}: ReportModalProps) {
    const [reason, setReason] = useState<ReportReason | "">("");
    const [additionalContext, setAdditionalContext] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { toast } = useToast();
    const {
        isRateLimited,
        rateLimitMessage,
        recordSubmission,
        hasReportedRecently,
        getRemainingReportsThisHour,
    } = useReportRateLimit();

    // Check if this specific content was already reported recently
    const alreadyReported = hasReportedRecently(contentId);

    const handleSubmit = async () => {
        if (!reason) {
            setError("Please select a reason for reporting.");
            return;
        }

        if (isRateLimited) {
            setError(rateLimitMessage || "You've reached the report limit. Please try again later.");
            return;
        }

        if (alreadyReported) {
            setError("You've already reported this content recently. Please wait before reporting again.");
            return;
        }

        try {
            setLoading(true);
            setError(null);
            await services.reports.submitReport({
                content_type: contentType,
                content_id: contentId,
                reason,
                additional_context: additionalContext || undefined,
            });

            // Record the submission for rate limiting
            recordSubmission(contentId);

            toast({
                title: "Report Submitted",
                description: "Thank you for helping keep our community safe. We'll review your report shortly.",
            });

            onOpenChange(false);
            // Reset form
            setTimeout(() => {
                setReason("");
                setAdditionalContext("");
                setError(null);
            }, 300);
        } catch (err: any) {
            const errorMessage = err?.error?.message || "Failed to submit report. Please try again.";
            setError(errorMessage);
            toast({
                title: "Error",
                description: errorMessage,
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCancel = () => {
        onOpenChange(false);
        setTimeout(() => {
            setReason("");
            setAdditionalContext("");
            setError(null);
        }, 300);
    };

    const getContentTypeLabel = () => {
        switch (contentType) {
            case "story":
                return "story";
            case "whisper":
                return "whisper";
            case "user":
                return "user";
            case "comment":
                return "comment";
            default:
                return "content";
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Flag className="h-5 w-5 text-destructive" />
                        Report {getContentTypeLabel()}
                    </DialogTitle>
                    <DialogDescription>
                        {contentTitle
                            ? `Report "${contentTitle}" for violating community guidelines`
                            : `Report this ${getContentTypeLabel()} for violating community guidelines`}
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    {/* Rate limit warning */}
                    {isRateLimited && (
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>{rateLimitMessage}</AlertDescription>
                        </Alert>
                    )}

                    {/* Already reported warning */}
                    {alreadyReported && !isRateLimited && (
                        <Alert>
                            <Info className="h-4 w-4" />
                            <AlertDescription>
                                You've already reported this content recently. Submitting multiple reports for the
                                same content won't expedite the review process.
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Rate limit info */}
                    {!isRateLimited && !alreadyReported && (
                        <Alert>
                            <Info className="h-4 w-4" />
                            <AlertDescription>
                                You have {getRemainingReportsThisHour()} report{getRemainingReportsThisHour() !== 1 ? "s" : ""} remaining this hour.
                            </AlertDescription>
                        </Alert>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="reason">Reason for reporting *</Label>
                        <Select
                            value={reason}
                            onValueChange={(value) => setReason(value as ReportReason)}
                            disabled={isRateLimited || alreadyReported}
                        >
                            <SelectTrigger id="reason">
                                <SelectValue placeholder="Select a reason" />
                            </SelectTrigger>
                            <SelectContent>
                                {REPORT_REASONS.map((r) => (
                                    <SelectItem key={r.value} value={r.value}>
                                        <div className="flex flex-col">
                                            <span className="font-medium">{r.label}</span>
                                            <span className="text-xs text-muted-foreground">{r.description}</span>
                                        </div>
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="context">Additional context (optional)</Label>
                        <Textarea
                            id="context"
                            placeholder="Provide any additional details that might help us review this report..."
                            value={additionalContext}
                            onChange={(e) => setAdditionalContext(e.target.value)}
                            rows={4}
                            maxLength={1000}
                            disabled={isRateLimited || alreadyReported}
                        />
                        <p className="text-xs text-muted-foreground">
                            {additionalContext.length}/1000 characters
                        </p>
                    </div>

                    <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                            False reports may result in action against your account. Please only report content
                            that genuinely violates our community guidelines.
                        </AlertDescription>
                    </Alert>

                    {error && (
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}
                </div>

                <DialogFooter className="flex gap-2">
                    <Button variant="outline" onClick={handleCancel} disabled={loading}>
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleSubmit}
                        disabled={loading || !reason || isRateLimited || alreadyReported}
                    >
                        {loading ? "Submitting..." : "Submit Report"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
