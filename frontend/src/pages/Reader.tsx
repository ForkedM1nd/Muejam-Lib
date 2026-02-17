import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
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
  const readerSettings = useReaderSettings();
  const { settings, lineWidthPx } = readerSettings;
  const contentRef = useRef<HTMLDivElement>(null);

  const [selection, setSelection] = useState<{ text: string; top: number; left: number } | null>(null);
  const [whisperModalOpen, setWhisperModalOpen] = useState(false);
  const [quoteForWhisper, setQuoteForWhisper] = useState("");

  const { data: chapter, isLoading, isError } = useQuery({
    queryKey: ["chapter", chapterId],
    queryFn: () => api.getChapter(chapterId!),
    enabled: !!chapterId,
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
        api.updateProgress(chapterId, progress).catch(() => {});
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
      return api.createHighlight({
        chapter_id: chapterId!,
        quote_text: quoteText.slice(0, 300),
        start_offset: start >= 0 ? start : 0,
        end_offset: start >= 0 ? start + quoteText.length : 0,
      });
    },
    onSuccess: () => {
      toast({ title: "Highlighted!" });
      setSelection(null);
      window.getSelection()?.removeAllRanges();
    },
    onError: () => toast({ title: "Failed to highlight", variant: "destructive" }),
  });

  const handleHighlight = () => {
    if (!selection || !isSignedIn) return;
    highlightMutation.mutate(selection.text);
  };

  const handleWhisperFromHighlight = async () => {
    if (!selection || !isSignedIn) return;
    const hl = await highlightMutation.mutateAsync(selection.text);
    setQuoteForWhisper(selection.text);
    setWhisperModalOpen(true);
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  };

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
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
            {chapter.content ?? ""}
          </ReactMarkdown>
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
      </div>

      {/* Whisper from highlight modal */}
      {whisperModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setWhisperModalOpen(false)}>
          <div className="bg-popover border border-border rounded-lg shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-medium mb-4" style={{ fontFamily: "var(--font-display)" }}>Whisper about this passage</h3>
            <WhisperComposer
              quoteText={quoteForWhisper}
              placeholder="Share your thoughts on this passage…"
              onSubmit={async (body) => {
                await api.createWhisper({ body, scope: "HIGHLIGHT" });
                setWhisperModalOpen(false);
                toast({ title: "Whisper posted!" });
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
