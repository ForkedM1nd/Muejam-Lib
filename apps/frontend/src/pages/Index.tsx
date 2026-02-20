import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import SurfacePanel from "@/components/shared/SurfacePanel";
import { BookOpen, Flame, MessageCircle, PenLine, Sparkles, Users } from "lucide-react";

const FEATURE_ITEMS = [
  {
    icon: BookOpen,
    title: "Serialized reading",
    description: "Follow chapter drops in real time and never lose your place.",
  },
  {
    icon: MessageCircle,
    title: "Thread-style whispers",
    description: "Post quick thoughts, reactions, and quote takes as you read.",
  },
  {
    icon: PenLine,
    title: "Creator-first writing",
    description: "Draft, publish, and iterate chapters with a focused editor.",
  },
  {
    icon: Sparkles,
    title: "Highlights and saves",
    description: "Capture favorite lines and organize stories into shelves.",
  },
];

export default function Index() {
  return (
    <div className="space-y-10">
      <section className="overflow-hidden rounded-3xl border border-border/70 bg-card/90 p-8 shadow-[0_24px_60px_-40px_hsl(var(--foreground)/0.7)] backdrop-blur-sm sm:p-12">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary/80">Wattpad x Threads energy</p>
        <h1 className="mt-4 text-4xl font-semibold leading-tight sm:text-5xl" style={{ fontFamily: "var(--font-display)" }}>
          Clean chapter reading.
          <br />
          Fast social conversation.
        </h1>
        <p className="mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
          MueJam blends the focus of story platforms with the speed of social threads. Read deeply, react quickly, and
          publish consistently.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link to="/discover">
            <Button size="lg">Start Reading</Button>
          </Link>
          <Link to="/write">
            <Button size="lg" variant="outline">
              Start Writing
            </Button>
          </Link>
          <Link to="/community">
            <Button size="lg" variant="ghost">
              Join Community
            </Button>
          </Link>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Discover</p>
            <p className="mt-1 text-xl font-semibold">Trending stories daily</p>
          </div>
          <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Whispers</p>
            <p className="mt-1 text-xl font-semibold">Real-time reactions</p>
          </div>
          <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Creators</p>
            <p className="mt-1 text-xl font-semibold">Chapter-first publishing</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURE_ITEMS.map(({ icon: Icon, title, description }) => (
          <SurfacePanel key={title} className="p-5">
            <Icon className="h-5 w-5 text-primary" />
            <h3 className="mt-4 text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              {title}
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </SurfacePanel>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <SurfacePanel className="p-6">
          <div className="flex items-center gap-2 text-primary">
            <Flame className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Reader experience</span>
          </div>
          <h3 className="mt-3 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            Build your reading flow
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Follow ongoing series, keep highlights, and jump from story to whisper conversations in one clean flow.
          </p>
          <Link to="/library" className="mt-4 inline-flex text-sm font-medium text-primary hover:underline">
            Open your library
          </Link>
        </SurfacePanel>

        <SurfacePanel className="p-6">
          <div className="flex items-center gap-2 text-primary">
            <Users className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Creator momentum</span>
          </div>
          <h3 className="mt-3 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            Grow chapter by chapter
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Publish serially, interact with readers through whispers, and track response loops between updates.
          </p>
          <Link to="/write" className="mt-4 inline-flex text-sm font-medium text-primary hover:underline">
            Open writer tools
          </Link>
        </SurfacePanel>
      </section>
    </div>
  );
}
