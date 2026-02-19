import { useState } from "react";
import { toast } from "@/hooks/use-toast";

export interface ShareOptions {
    url: string;
    title: string;
    text?: string;
}

export function useShare() {
    const [isSharing, setIsSharing] = useState(false);

    const copyToClipboard = async (url: string) => {
        try {
            await navigator.clipboard.writeText(url);
            toast({
                title: "Link copied!",
                description: "The link has been copied to your clipboard.",
            });
            return true;
        } catch (error) {
            toast({
                title: "Failed to copy",
                description: "Could not copy the link to clipboard.",
                variant: "destructive",
            });
            return false;
        }
    };

    const shareToTwitter = ({ url, title, text }: ShareOptions) => {
        const tweetText = text || title;
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(url)}`;
        window.open(twitterUrl, "_blank", "noopener,noreferrer");
    };

    const shareToFacebook = ({ url }: ShareOptions) => {
        const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
        window.open(facebookUrl, "_blank", "noopener,noreferrer");
    };

    const shareToReddit = ({ url, title }: ShareOptions) => {
        const redditUrl = `https://www.reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`;
        window.open(redditUrl, "_blank", "noopener,noreferrer");
    };

    const shareNative = async ({ url, title, text }: ShareOptions) => {
        if (!navigator.share) {
            return false;
        }

        try {
            setIsSharing(true);
            await navigator.share({
                title,
                text,
                url,
            });
            return true;
        } catch (error) {
            // User cancelled or error occurred
            if ((error as Error).name !== "AbortError") {
                toast({
                    title: "Failed to share",
                    description: "Could not share the content.",
                    variant: "destructive",
                });
            }
            return false;
        } finally {
            setIsSharing(false);
        }
    };

    const canUseNativeShare = typeof navigator !== "undefined" && !!navigator.share;

    return {
        copyToClipboard,
        shareToTwitter,
        shareToFacebook,
        shareToReddit,
        shareNative,
        canUseNativeShare,
        isSharing,
    };
}
