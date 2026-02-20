import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SurfacePanelProps {
  children: ReactNode;
  className?: string;
}

export default function SurfacePanel({ children, className }: SurfacePanelProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border/70 bg-card/90 shadow-[0_16px_40px_-32px_hsl(var(--foreground)/0.7)] backdrop-blur-sm",
        className
      )}
    >
      {children}
    </div>
  );
}
