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
        "rounded-2xl border border-border bg-card shadow-[0_10px_28px_-24px_hsl(var(--foreground)/0.45)]",
        className
      )}
    >
      {children}
    </div>
  );
}
