import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ImagePlus, X, Globe, BookOpen, Quote } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRecaptchaToken } from "@/hooks/useRecaptchaToken";

interface WhisperComposerProps {
  placeholder?: string;
  initialContent?: string;
  quoteText?: string;
  scope?: "GLOBAL" | "STORY" | "HIGHLIGHT";
  storyId?: string;
  highlightId?: string;
  showScopeSelector?: boolean;
  onSubmit: (content: string, mediaFile?: File, scope?: string, storyId?: string, highlightId?: string, recaptchaToken?: string | null) => Promise<void>;
  submitting?: boolean;
}

const MAX_LENGTH = 280;

export default function WhisperComposer({
  placeholder = "What's on your mind?",
  initialContent = "",
  quoteText,
  scope = "GLOBAL",
  storyId,
  highlightId,
  showScopeSelector = false,
  onSubmit,
  submitting,
}: WhisperComposerProps) {
  const [content, setContent] = useState(initialContent);
  const [selectedScope, setSelectedScope] = useState(scope);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const getRecaptchaToken = useRecaptchaToken('post_whisper');

  const handleMedia = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (20MB max for whisper_media)
    if (file.size > 20 * 1024 * 1024) {
      alert("File too large. Maximum size is 20MB.");
      return;
    }

    setMediaFile(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async () => {
    if (!content.trim()) return;

    // Get reCAPTCHA token
    const recaptchaToken = await getRecaptchaToken();

    await onSubmit(
      content.trim(),
      mediaFile ?? undefined,
      selectedScope,
      storyId,
      highlightId,
      recaptchaToken
    );
    setContent("");
    setMediaFile(null);
    setPreview(null);
  };

  const remainingChars = MAX_LENGTH - content.length;
  const isOverLimit = remainingChars < 0;

  return (
    <div className="space-y-3 p-4 border border-border rounded-lg bg-card">
      {quoteText && (
        <blockquote className="border-l-2 border-primary/30 pl-3 text-sm text-muted-foreground italic">
          <Quote className="h-3 w-3 inline mr-1" />
          "{quoteText}"
        </blockquote>
      )}

      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder}
        rows={3}
        maxLength={MAX_LENGTH + 50} // Allow typing a bit over to show error
        className={cn(
          "resize-none border-0 bg-transparent focus-visible:ring-0 p-0 text-sm",
          isOverLimit && "text-destructive"
        )}
      />

      {preview && (
        <div className="relative inline-block">
          <img
            src={preview}
            alt="upload preview"
            className="max-h-40 rounded-md border"
            loading="lazy"
          />
          <button
            onClick={() => {
              setMediaFile(null);
              setPreview(null);
              if (preview) URL.revokeObjectURL(preview);
            }}
            className="absolute -top-2 -right-2 bg-background border border-border rounded-full p-1 hover:bg-accent transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <label className="cursor-pointer text-muted-foreground hover:text-foreground transition-colors">
            <ImagePlus className="h-4 w-4" />
            <input
              type="file"
              accept="image/*,video/mp4"
              className="hidden"
              onChange={handleMedia}
              disabled={submitting}
            />
          </label>

          {showScopeSelector && (
            <Select value={selectedScope} onValueChange={(v) => setSelectedScope(v as any)}>
              <SelectTrigger className="w-[140px] h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="GLOBAL">
                  <div className="flex items-center gap-2">
                    <Globe className="h-3 w-3" />
                    <span>Global</span>
                  </div>
                </SelectItem>
                <SelectItem value="STORY">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-3 w-3" />
                    <span>Story</span>
                  </div>
                </SelectItem>
                <SelectItem value="HIGHLIGHT">
                  <div className="flex items-center gap-2">
                    <Quote className="h-3 w-3" />
                    <span>Highlight</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span
            className={cn(
              "text-xs tabular-nums",
              remainingChars < 20 ? "text-warning" : "text-muted-foreground",
              isOverLimit && "text-destructive font-medium"
            )}
          >
            {remainingChars}
          </span>
          <Button
            size="sm"
            disabled={!content.trim() || isOverLimit || submitting}
            onClick={handleSubmit}
          >
            {submitting ? "Posting…" : "Post"}
          </Button>
        </div>
      </div>
    </div>
  );
}
