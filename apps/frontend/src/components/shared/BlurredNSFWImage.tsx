import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import NSFWWarningLabel from "./NSFWWarningLabel";

interface BlurredNSFWImageProps {
    src: string;
    alt: string;
    className?: string;
    aspectRatio?: string;
}

/**
 * Blurred image component for NSFW content.
 * Shows a blurred preview with a click-to-reveal button.
 */
export default function BlurredNSFWImage({
    src,
    alt,
    className = "",
    aspectRatio = "3/2"
}: BlurredNSFWImageProps) {
    const [isRevealed, setIsRevealed] = useState(false);

    return (
        <div
            className={`relative overflow-hidden bg-muted ${className}`}
            style={{ aspectRatio }}
        >
            <img
                src={src}
                alt={alt}
                className={`w-full h-full object-cover transition-all duration-300 ${isRevealed ? "" : "blur-2xl scale-110"
                    }`}
                loading="lazy"
            />

            {!isRevealed && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/40 backdrop-blur-sm">
                    <NSFWWarningLabel variant="badge" className="mb-3" />
                    <button
                        onClick={(e) => {
                            e.preventDefault();
                            setIsRevealed(true);
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-background/90 hover:bg-background rounded-lg text-sm font-medium transition-colors"
                    >
                        <Eye className="h-4 w-4" />
                        Click to reveal
                    </button>
                </div>
            )}

            {isRevealed && (
                <button
                    onClick={(e) => {
                        e.preventDefault();
                        setIsRevealed(false);
                    }}
                    className="absolute top-2 right-2 p-2 bg-background/90 hover:bg-background rounded-lg transition-colors"
                    title="Hide content"
                >
                    <EyeOff className="h-4 w-4" />
                </button>
            )}
        </div>
    );
}
