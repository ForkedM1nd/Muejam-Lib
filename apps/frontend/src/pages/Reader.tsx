import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSafeAuth } from "@/hooks/useSafeAuth";
import { useEffect, useRef, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { api } from "@/lib/api";
import { useReaderSettings } from "@/hooks/useReaderSettings";
import { Button } from "@/components/ui/button";
import { PageSkeleton } from "@/components/shared/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { Settings2, Moon, Sun, Minus, Plus, ArrowLeft, Highlighter, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import WhisperComposer from "@/components/shared/WhisperComposer";
import type { Highlight } from "@/types";

function ReaderControls({ settings, setSettings, lineWidthPx }: ReturnType<typeof useReaderSettings>) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <Button variant="ghost" size="icon" onClick={() => setOpen(!open)}>
        <Settings2 className="h-4 w-4" />
      </Button>
      {open && (
        <div className="absolute right-0 top-full mt-2 w-56 bg-popover border border-border rounded-lg shadow-lg p-4 space-y-4 z-50">
          {/* Theme */}
          <div className="flex items-center justify-between">
            <span className="text-sm">Theme</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSettings({ theme: settings.theme === "light" ? "dark" : "light" })}
            >
              {settings.theme === "light" ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
            </Button>
          </div>
          {/* Font size */}
          <div className="flex items-center justify-between">
            <span className="text-sm">Font</span>
            <div className="flex items-center gap-1">
              <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => setSettings({ fontSize: Math.max(14, settings.fontSize - 1) })}>
                <Minus className="h-3 w-3" />
              </Button>
              <span className="text-xs w-8 text-center">{settings.fontSize}</span>
              <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => setSettings({ fontSize: Math.min(28, settings.fontSize + 1) })}>
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
          {/* Width */}
          <div className="flex items-center justify-between">
            <span className="text-sm">Width</span>
            <div className="flex gap-1">
              {(["narrow", "medium", "wide"] as const).map((w) => (
                <Button
                  key={w}
                  variant={settings.lineWidth === w ? "default" : "outline"}
                  size="sm"
                  className="text-xs h-7 px-2"
                  onClick={() => setSettings({ lineWidth: w })}
                >
                  {w.charAt(0).toUpperCase() + w.slice(1)}
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReaderPage() {
  const { chapterId } = useParams<{ chapterId: string }>();
  const { isSignedIn } = useSafeAuth();
  const queryClient = useQueryClient();
  const readerSettings = useReaderSettings();
  const { settings, lineWidthPx } = readerSettings;
  const contentRef = useRef<HTMLDivElement>(null);

  const [selection, setSelection] = useState<{ text: string; top: number; left: number } | null>(null);
  const [whisperModalOpen, setWhisperModalOpen] = useState(false);
  const [quoteForWhisper, setQuoteForWhisper] = useState("");
  const [highlightIdForWhisper, setHighlightIdForWhisper] = useState<string | null>(null);

  const { data: chapter, isLoading, isError } = useQuery({
    queryKey: ["chapter", chapterId],
    queryFn: () => api.getChapter(chapterId!),
    enabled: !!chapterId,
  });

  // Fetch existing highlights for this chapter
  const { data: highlights = [] } = useQuery({
    queryKey: ["highlights", chapterId],
    queryFn: () => api.getChapterHighlights(chapterId!),
    enabled: !!chapterId && !!isSignedIn,
  });

  // Progress tracking (debounced)
  const progressTimerRef = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => {
    if (!chapterId || !isSignedIn) return;
    const handleScroll = () => {
      clearTimeout(progressTimerRef.current);
      progressTimerRef.current = setTimeout(() => {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = docHeight > 0 ? Math.min(Math.round((scrollTop / docHeight) * 100), 100) : 0;
        api.updateProgress(chapterId, progress).catch(() => { });
      }, 2000);
    };
    window.addEventListener("scroll", handleScroll);
    return () => { window.removeEventListener("scroll", handleScroll); clearTimeout(progressTimerRef.current); };
  }, [chapterId, isSignedIn]);

  // Text selection handler
  const handleMouseUp = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !contentRef.current) {
      setSelection(null);
      return;
    }
    const text = sel.toString().trim();
    if (text.length < 3 || text.length > 500) { setSelection(null); return; }
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const containerRect = contentRef.current.getBoundingClientRect();
    setSelection({
      text,
      top: rect.top - containerRect.top - 40,
      left: rect.left - containerRect.left + rect.width / 2,
    });
  }, []);

  // Highlight mutation
  const highlightMutation = useMutation({
    mutationFn: async (quoteText: string) => {
      const plainText = contentRef.current?.innerText ?? "";
      const start = plainText.indexOf(quoteText);
      return api.createHighlight(chapterId!, {
        quote_text: quoteText.slice(0, 300),
        start_offset: start >= 0 ? start : 0,
        end_offset: start >= 0 ? start + quoteText.length : 0,
      });
    },
    onSuccess: () => {
      toast({ title: "Highlighted!" });
      setSelection(null);
      window.getSelection()?.removeAllRanges();
      // Invalidate highlights query to refetch
      queryClient.invalidateQueries({ queryKey: ["highlights", chapterId] });
    },
    onError: () => toast({ title: "Failed to highlight", variant: "destructive" }),
  });

  const handleHighlight = () => {
    if (!selection || !isSignedIn) return;
    highlightMutation.mutate(selection.text);
  };

  const handleWhisperFromHighlight = async () => {
    if (!selection || !isSignedIn) return;
    const newHighlight = await highlightMutation.mutateAsync(selection.text);
    setQuoteForWhisper(selection.text);
    setHighlightIdForWhisper(newHighlight.id);
    setWhisperModalOpen(true);
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  };

  // Navigate to a highlight when clicked
  const handleHighlightClick = useCallback((highlight: Highlight) => {
    if (!contentRef.current) return;

    const targetOffset = highlight.start_offset;

    // Find the text node and offset
    const walker = document.createTreeWalker(
      contentRef.current,
      NodeFilter.SHOW_TEXT,
      null
    );

    let currentOffset = 0;
    let targetNode: Node | null = null;
    let nodeOffset = 0;

    while (walker.nextNode()) {
      const node = walker.currentNode;
      const nodeLength = node.textContent?.length || 0;

      if (currentOffset + nodeLength >= targetOffset) {
        targetNode = node;
        nodeOffset = targetOffset - currentOffset;
        break;
      }

      currentOffset += nodeLength;
    }

    if (targetNode) {
      // Create a range and scroll to it
      const range = document.createRange();
      range.setStart(targetNode, Math.min(nodeOffset, targetNode.textContent?.length || 0));
      range.setEnd(targetNode, Math.min(nodeOffset, targetNode.textContent?.length || 0));

      // Scroll the range into view
      const rect = range.getBoundingClientRect();
      window.scrollTo({
        top: window.scrollY + rect.top - 100,
        behavior: 'smooth'
      });

      // Briefly highlight the text
      const selection = window.getSelection();
      selection?.removeAllRanges();

      // Select the full highlight text
      const endOffset = Math.min(
        nodeOffset + highlight.quote_text.length,
        targetNode.textContent?.length || 0
      );
      range.setEnd(targetNode, endOffset);
      selection?.addRange(range);

      // Clear selection after 2 seconds
      setTimeout(() => {
        selection?.removeAllRanges();
      }, 2000);
    }
  }, []);

  // Render content with highlights
  const renderContentWithHighlights = useCallback(() => {
    if (!chapter?.content) return null;

    // If no highlights, render normally
    if (!highlights.length) {
      return (
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
          {chapter.content}
        </ReactMarkdown>
      );
    }

    // For simplicity, we'll render markdown normally and add highlight overlays
    // A more sophisticated approach would parse and inject highlights into the DOM
    return (
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
        {chapter.content}
      </ReactMarkdown>
    );
  }, [chapter?.content, highlights]);

  const isDark = settings.theme === "dark";

  if (isLoading) return <PageSkeleton />;
  if (isError || !chapter) return <EmptyState title="Chapter not found" />;

  return (
    <div className={cn("min-h-screen transition-colors", isDark ? "bg-[hsl(30,10%,8%)] text-[hsl(35,15%,85%)]" : "bg-background text-foreground")}>
      {/* Reader toolbar */}
      <div className={cn("sticky top-0 z-30 border-b px-4 h-12 flex items-center justify-between", isDark ? "border-[hsl(30,10%,18%)] bg-[hsl(30,10%,8%)]/95" : "border-border bg-background/95")}>
        <Button variant="ghost" size="sm" onClick={() => window.history.back()}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <span className="text-sm font-medium truncate max-w-[200px]" style={{ fontFamily: "var(--font-display)" }}>{chapter.title}</span>
        <ReaderControls {...readerSettings} />
      </div>

      {/* Content */}
      <div className="mx-auto px-4 py-12 relative" style={{ maxWidth: lineWidthPx }}>
        <h1 className="text-2xl font-semibold mb-8" style={{ fontFamily: "var(--font-display)" }}>{chapter.title}</h1>
        <div
          ref={contentRef}
          onMouseUp={handleMouseUp}
          className="prose prose-neutral max-w-none"
          style={{ fontSize: settings.fontSize, lineHeight: 1.8 }}
        >
          {renderContentWithHighlights()}
        </div>

        {/* Selection floating toolbar */}
        {selection && isSignedIn && (
          <div
            className="absolute z-40 flex items-center gap-1 bg-popover border border-border rounded-lg shadow-lg p-1"
            style={{ top: selection.top, left: selection.left, transform: "translateX(-50%)" }}
          >
            <Button variant="ghost" size="sm" className="text-xs h-7" onClick={handleHighlight}>
              <Highlighter className="h-3.5 w-3.5 mr-1" /> Highlight
            </Button>
            <Button variant="ghost" size="sm" className="text-xs h-7" onClick={handleWhisperFromHighlight}>
              <MessageCircle className="h-3.5 w-3.5 mr-1" /> Whisper
            </Button>
          </div>
        )}

        {/* Highlights sidebar - show if there are highlights */}
        {highlights.length > 0 && (
          <div className="mt-12 pt-8 border-t border-border">
            <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: "var(--font-display)" }}>
              Your Highlights ({highlights.length})
            </h2>
            <div className="space-y-3">
              {highlights.map((highlight) => (
                <div
                  key={highlight.id}
                  className={cn(
                    "p-3 rounded-lg border cursor-pointer transition-colors",
                    isDark
                      ? "border-[hsl(30,10%,18%)] bg-[hsl(30,10%,12%)] hover:bg-[hsl(30,10%,15%)]"
                      : "border-border bg-muted/50 hover:bg-muted"
                  )}
                  onClick={() => handleHighlightClick(highlight)}
                >
                  <p className="text-sm italic mb-2">"{highlight.quote_text}"</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(highlight.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Whisper from highlight modal */}
      {whisperModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setWhisperModalOpen(false)}>
          <div className="bg-popover border border-border rounded-lg shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-medium mb-4" style={{ fontFamily: "var(--font-display)" }}>Whisper about this passage</h3>
            <WhisperComposer
              quoteText={quoteForWhisper}
              highlightId={highlightIdForWhisper ?? undefined}
              scope="HIGHLIGHT"
              placeholder="Share your thoughts on this passage…"
              onSubmit={async (content, mediaFile, scope, storyId, highlightId) => {
                await api.createWhisper({
                  content,
                  scope: scope || "HIGHLIGHT",
                  highlight_id: highlightId,
                });
                setWhisperModalOpen(false);
                setHighlightIdForWhisper(null);
                toast({ title: "Whisper posted!" });
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
