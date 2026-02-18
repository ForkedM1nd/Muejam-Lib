import { AlertTriangle } from "lucide-react";

interface NSFWWarningLabelProps {
    variant?: "badge" | "banner";
    className?: string;
}

/**
 * NSFW warning label component for displaying content warnings.
 * 
 * Variants:
 * - badge: Small badge for cards and thumbnails
 * - banner: Full-width banner for content pages
 */
export default function NSFWWarningLabel({
    variant = "badge",
    className = ""
}: NSFWWarningLabelProps) {
    if (variant === "banner") {
        return (
            <div className={`bg-destructive/10 border border-destructive/20 rounded-lg p-4 flex items-center gap-3 ${className}`}>
                <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" />
                <div className="flex-1">
                    <p className="text-sm font-medium text-destructive">
                        NSFW Content Warning
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                        This content has been flagged as Not Safe For Work and may contain mature themes.
                    </p>
                </div>
            </div>
        );
    }

    // Badge variant (default)
    return (
        <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-destructive/10 border border-destructive/20 ${className}`}>
            <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
            <span className="text-xs font-medium text-destructive">NSFW</span>
        </div>
    );
}
