import { BookOpen } from "lucide-react";
import type { ReactNode } from "react";
import SurfacePanel from "@/components/shared/SurfacePanel";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <SurfacePanel className="px-4 py-14 text-center">
      <div className="mx-auto mb-4 text-muted-foreground">{icon ?? <BookOpen className="mx-auto h-10 w-10" />}</div>
      <h3 className="mb-1 text-lg font-medium" style={{ fontFamily: "var(--font-display)" }}>
        {title}
      </h3>
      {description && <p className="mx-auto max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </SurfacePanel>
  );
}
