import { Link } from "react-router-dom";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";
import { BookOpen, MessageCircle, PenTool, ShieldCheck } from "lucide-react";

const VALUES = [
  {
    icon: BookOpen,
    title: "Story-first design",
    description: "A reading experience that stays clean, clear, and chapter-focused.",
  },
  {
    icon: MessageCircle,
    title: "Conversation layer",
    description: "Thread-style whispers that keep community discussion fast and contextual.",
  },
  {
    icon: PenTool,
    title: "Creator momentum",
    description: "Publishing tools built for consistent chapter drops and audience growth.",
  },
  {
    icon: ShieldCheck,
    title: "Safer platform",
    description: "Moderation, reporting, and policy tooling to support healthy communities.",
  },
];

export default function AboutPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="About MueJam"
        eyebrow="Platform"
        description="We are building a modern home for serialized fiction and social reading."
      />

      <SurfacePanel className="p-6 sm:p-8">
        <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
          MueJam combines the depth of chapter-based storytelling with the speed of social conversation. Readers can
          discover new stories, follow creators, and react in whispers. Writers can publish chapter by chapter while
          building direct reader loops.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/discover" className="text-sm font-medium text-primary hover:underline">
            Explore stories
          </Link>
          <Link to="/write" className="text-sm font-medium text-primary hover:underline">
            Start writing
          </Link>
          <Link to="/community" className="text-sm font-medium text-primary hover:underline">
            Community hub
          </Link>
        </div>
      </SurfacePanel>

      <div className="grid gap-4 sm:grid-cols-2">
        {VALUES.map(({ icon: Icon, title, description }) => (
          <SurfacePanel key={title} className="p-5">
            <Icon className="h-5 w-5 text-primary" />
            <h3 className="mt-3 text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              {title}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </SurfacePanel>
        ))}
      </div>
    </div>
  );
}
