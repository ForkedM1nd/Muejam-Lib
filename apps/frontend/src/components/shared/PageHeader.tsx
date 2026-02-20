import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  eyebrow?: string;
  action?: ReactNode;
  className?: string;
}

export default function PageHeader({ title, description, eyebrow, action, className }: PageHeaderProps) {
  return (
    <div className={cn("mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="space-y-2">
        {eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary/80">{eyebrow}</p>}
        <div>
          <h1 className="text-3xl font-semibold tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
            {title}
          </h1>
          {description && <p className="mt-2 text-sm text-muted-foreground sm:text-base">{description}</p>}
        </div>
      </div>

      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
