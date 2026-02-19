import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Flag } from "lucide-react";
import { ReportModal } from "./ReportModal";
import type { ReportableContentType } from "@/types";

interface ReportButtonProps {
    contentType: ReportableContentType;
    contentId: string;
    contentTitle?: string;
    variant?: "default" | "ghost" | "outline";
    size?: "default" | "sm" | "lg" | "icon";
    className?: string;
}

/**
 * ReportButton Component
 * 
 * A button that opens a modal for reporting content that violates community guidelines.
 * Includes built-in rate limiting to prevent abuse.
 * 
 * @example
 * // Report a story
 * <ReportButton
 *   contentType="story"
 *   contentId={story.id}
 *   contentTitle={story.title}
 * />
 * 
 * @example
 * // Report a whisper
 * <ReportButton
 *   contentType="whisper"
 *   contentId={whisper.id}
 *   variant="outline"
 *   size="sm"
 * />
 * 
 * @example
 * // Report a user
 * <ReportButton
 *   contentType="user"
 *   contentId={user.id}
 *   contentTitle={user.display_name}
 * />
 */
export function ReportButton({
    contentType,
    contentId,
    contentTitle,
    variant = "ghost",
    size = "sm",
    className,
}: ReportButtonProps) {
    const [showReportModal, setShowReportModal] = useState(false);

    return (
        <>
            <Button
                variant={variant}
                size={size}
                onClick={() => setShowReportModal(true)}
                className={className}
                aria-label="Report content"
            >
                <Flag className="h-4 w-4 mr-1" />
                Report
            </Button>

            <ReportModal
                open={showReportModal}
                onOpenChange={setShowReportModal}
                contentType={contentType}
                contentId={contentId}
                contentTitle={contentTitle}
            />
        </>
    );
}
