import { Link } from "react-router-dom";
import PageHeader from "@/components/shared/PageHeader";
import SurfacePanel from "@/components/shared/SurfacePanel";
import { LifeBuoy, ShieldAlert, Gavel, Radio, ArrowRight } from "lucide-react";

const COMMUNITY_LINKS = [
  {
    to: "/help",
    icon: LifeBuoy,
    title: "Help Center",
    description: "Guides, FAQs, and support articles.",
  },
  {
    to: "/legal/guidelines",
    icon: ShieldAlert,
    title: "Community Guidelines",
    description: "Shared expectations for respectful conversation.",
  },
  {
    to: "/legal/copyright",
    icon: Gavel,
    title: "Copyright Policy",
    description: "Reporting and rights-protection workflows.",
  },
  {
    to: "/status",
    icon: Radio,
    title: "Platform Status",
    description: "Live service health and incident updates.",
  },
];

export default function CommunityPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Community Hub"
        eyebrow="Support and safety"
        description="Everything you need to stay informed, safe, and connected on MueJam."
      />

      <div className="grid gap-4 sm:grid-cols-2">
        {COMMUNITY_LINKS.map(({ to, icon: Icon, title, description }) => (
          <Link key={to} to={to}>
            <SurfacePanel className="h-full p-5 transition hover:-translate-y-0.5 hover:bg-accent/35">
              <div className="flex items-center gap-3">
                <Icon className="h-5 w-5 text-primary" />
                <h3 className="text-base font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                  {title}
                </h3>
                <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
              </div>
              <p className="mt-3 text-sm text-muted-foreground">{description}</p>
            </SurfacePanel>
          </Link>
        ))}
      </div>
    </div>
  );
}
