import { cn } from "@/lib/utils";

export default function TagPill({ name, className, onClick }: { name: string; className?: string; onClick?: () => void }) {
  return (
    <span
      onClick={onClick}
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary text-secondary-foreground",
        onClick && "cursor-pointer hover:bg-secondary/80 transition-colors",
        className
      )}
    >
      {name}
    </span>
  );
}
