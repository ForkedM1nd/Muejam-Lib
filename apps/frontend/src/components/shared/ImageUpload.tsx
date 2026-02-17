import { useState } from "react";
import { uploadFile } from "@/lib/upload";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, Image as ImageIcon, X } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface ImageUploadProps {
    type: "avatar" | "cover" | "whisper_media";
    currentImageUrl?: string;
    onUploadComplete: (objectKey: string) => void;
    onRemove?: () => void;
    className?: string;
    label?: string;
    showPreview?: boolean;
}

export function ImageUpload({
    type,
    currentImageUrl,
    onUploadComplete,
    onRemove,
    className = "",
    label,
    showPreview = true,
}: ImageUploadProps) {
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setUploadProgress(0);

        try {
            // Simulate progress for better UX
            const progressInterval = setInterval(() => {
                setUploadProgress((prev) => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            const objectKey = await uploadFile(file, type);

            clearInterval(progressInterval);
            setUploadProgress(100);

            onUploadComplete(objectKey);
            toast({ title: "Image uploaded successfully!" });
        } catch (err: any) {
            toast({
                title: "Upload failed",
                description: err.message || "Please try again",
                variant: "destructive",
            });
        } finally {
            setIsUploading(false);
            setUploadProgress(0);
            // Reset file input
            e.target.value = "";
        }
    };

    const maxSizeText = {
        avatar: "2MB",
        cover: "10MB",
        whisper_media: "20MB",
    }[type];

    const recommendedSize = {
        avatar: "400x400px",
        cover: "600x900px",
        whisper_media: "1200x1200px",
    }[type];

    return (
        <div className={`space-y-3 ${className}`}>
            {label && <label className="text-sm font-medium block">{label}</label>}

            <div className="flex items-start gap-4">
                {showPreview && currentImageUrl && (
                    <div className="relative group">
                        <div className={`relative rounded-lg overflow-hidden border ${type === "avatar" ? "w-24 h-24" : "w-32 h-48"
                            }`}>
                            <img
                                src={currentImageUrl}
                                alt="Preview"
                                className="w-full h-full object-cover"
                            />
                        </div>
                        {onRemove && (
                            <button
                                onClick={onRemove}
                                className="absolute -top-2 -right-2 p-1 bg-destructive text-destructive-foreground rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                title="Remove image"
                            >
                                <X className="h-3 w-3" />
                            </button>
                        )}
                    </div>
                )}

                <div className="flex-1 space-y-2">
                    <label
                        className={`inline-flex items-center gap-2 cursor-pointer text-sm border border-border rounded-md px-4 py-2 hover:bg-accent transition-colors ${isUploading ? "opacity-50 cursor-not-allowed" : ""
                            }`}
                    >
                        {isUploading ? (
                            <>
                                <Upload className="h-4 w-4 animate-pulse" />
                                Uploading...
                            </>
                        ) : (
                            <>
                                <ImageIcon className="h-4 w-4" />
                                {currentImageUrl ? "Change Image" : "Upload Image"}
                            </>
                        )}
                        <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={handleFileSelect}
                            disabled={isUploading}
                        />
                    </label>

                    {isUploading && (
                        <div className="space-y-1">
                            <Progress value={uploadProgress} className="h-2" />
                            <p className="text-xs text-muted-foreground">
                                {uploadProgress}% uploaded
                            </p>
                        </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                        Recommended: {recommendedSize}, max {maxSizeText}
                    </p>
                </div>
            </div>
        </div>
    );
}
