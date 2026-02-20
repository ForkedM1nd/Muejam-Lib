import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FooterNavLink {
  to: string;
  label: string;
  icon: LucideIcon;
}

interface UtilityLink {
  to: string;
  label: string;
}

interface FloatingFooterProps {
  navLinks: FooterNavLink[];
  utilityLinks: UtilityLink[];
  pathname: string;
}

function isPathActive(pathname: string, to: string) {
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(`${to}/`);
}

export default function FloatingFooter({ navLinks, utilityLinks, pathname }: FloatingFooterProps) {
  const mobileLinks = navLinks.slice(0, 5);

  return (
    <footer className="pointer-events-none fixed inset-x-0 bottom-3 z-50">
      <div className="pointer-events-auto mx-auto w-[min(1120px,calc(100%-1rem))] rounded-2xl border border-border/70 bg-card/92 backdrop-blur-xl shadow-[0_18px_55px_-30px_hsl(var(--foreground)/0.7)]">
        <div className="hidden items-center justify-between gap-4 px-4 py-3 md:flex">
          <nav className="flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const active = isPathActive(pathname, link.to);

              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition-all",
                    active
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {utilityLinks.map((link) => (
              <Link key={link.to} to={link.to} className="transition-colors hover:text-foreground">
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        <nav
          className="grid gap-1 p-2 md:hidden"
          style={{ gridTemplateColumns: `repeat(${Math.max(mobileLinks.length, 1)}, minmax(0, 1fr))` }}
        >
          {mobileLinks.map((link) => {
            const Icon = link.icon;
            const active = isPathActive(pathname, link.to);

            return (
              <Link
                key={link.to}
                to={link.to}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-[10px] font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="truncate">{link.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </footer>
  );
}
