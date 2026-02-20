import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import SurfacePanel from "@/components/shared/SurfacePanel";
import { BookOpen, MessageCircle, PenLine, Sparkles } from "lucide-react";

const FEATURES = [
  {
    icon: BookOpen,
    title: "Chapter-based stories",
    description: "Follow serialized stories and keep momentum between chapter drops.",
  },
  {
    icon: MessageCircle,
    title: "Whisper conversations",
    description: "Thread-style reactions and short posts around stories and highlights.",
  },
  {
    icon: PenLine,
    title: "Clean writing flow",
    description: "Draft and publish with a focused editor built for consistency.",
  },
  {
    icon: Sparkles,
    title: "Highlights and shelves",
    description: "Save moments and organize your reading list with minimal friction.",
  },
];

export default function Index() {
  return (
    <div className="space-y-8">
      <SurfacePanel className="overflow-hidden p-6 sm:p-8 lg:p-10">
        <div className="grid gap-8 lg:grid-cols-[1.35fr_1fr] lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">MueJam Library</p>
            <h1 className="mt-3 text-4xl font-semibold leading-tight sm:text-5xl" style={{ fontFamily: "var(--font-display)" }}>
              Read deeply.
              <br />
              Share quickly.
            </h1>
            <p className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
              A modern space for serialized fiction with social threads. Discover stories, follow creators, and react in
              real time.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/discover">
                <Button size="lg">Explore Stories</Button>
              </Link>
              <Link to="/write">
                <Button size="lg" variant="outline">
                  Start Writing
                </Button>
              </Link>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-xl border border-border bg-secondary/55 p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Discover</p>
              <p className="mt-1 text-lg font-semibold">Curated daily feeds</p>
            </div>
            <div className="rounded-xl border border-border bg-secondary/55 p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Whispers</p>
              <p className="mt-1 text-lg font-semibold">Fast conversation layer</p>
            </div>
            <div className="rounded-xl border border-border bg-secondary/55 p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Writers</p>
              <p className="mt-1 text-lg font-semibold">Chapter-first workflow</p>
            </div>
          </div>
        </div>
      </SurfacePanel>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <SurfacePanel key={title} className="p-5">
            <Icon className="h-5 w-5 text-primary" />
            <h3 className="mt-3 text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              {title}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </SurfacePanel>
        ))}
      </section>
    </div>
  );
}
