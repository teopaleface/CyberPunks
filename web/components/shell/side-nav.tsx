"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Bell, BookOpen, CircleHelp, Layers, LayoutGrid, Monitor, UtilityPole, Wrench } from "lucide-react";
import { cn } from "cn";

export const NAV = [
  { href: "/app", label: "Planul de mâine", short: "Planul", icon: LayoutGrid, match: (p: string) => p === "/app" || p.startsWith("/harta") },
  { href: "/coada", label: "De verificat", short: "De verificat", icon: CircleHelp, match: (p: string) => p.startsWith("/coada"), count: "review" as const },
  { href: "/posturi", label: "Posturile", short: "Posturile", icon: UtilityPole, match: (p: string) => p.startsWith("/posturi") },
  { href: "/lucrari", label: "Lucrări", short: "Lucrări", icon: Wrench, match: (p: string) => p.startsWith("/lucrari") || p.startsWith("/ordine") },
  { href: "/jurnal", label: "Jurnal", short: "Jurnal", icon: BookOpen, match: (p: string) => p.startsWith("/jurnal") },
  { href: "/alerte", label: "Alerte și mesaje", short: "Alerte", icon: Bell, match: (p: string) => p.startsWith("/alerte") },
  { href: "/modele", label: "Modele", short: "Modele", icon: Layers, match: (p: string) => p.startsWith("/modele") },
  { href: "/demo", label: "Prezentare", short: "Prezentare", icon: Monitor, match: (p: string) => p.startsWith("/demo") },
];

function useNav() {
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const href = (h: string) => (scenario ? `${h}?scenariu=${encodeURIComponent(scenario)}` : h);
  return { pathname, href };
}

const GROUPS = [
  { label: "Dispecerat", entries: [0, 1] },
  { label: "Rețeaua", entries: [2, 3, 5] },
  { label: "Cum decide agentul", entries: [4, 6, 7] },
];

/** Meniul urmărește sarcinile dispecerului, cu pagina curentă marcată și prin formă. */
export function SideNav({ counts }: { counts: { review: number; alerts: number } }) {
  const { pathname, href } = useNav();
  return (
    <nav aria-label="Ecranele consolei" className="space-y-7">
      {GROUPS.map((group) => (
        <div key={group.label}>
          <p className="mb-2 px-3 text-[13px] font-medium text-muted-foreground">{group.label}</p>
          <div className="space-y-1">
            {group.entries.map((index) => {
              const n = NAV[index];
              const active = n.match(pathname);
              const count = n.count ? counts[n.count] : 0;
              const Icon = n.icon;
              return (
                <Link
                  key={n.href}
                  href={href(n.href)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex min-h-11 items-center gap-3 rounded-xl border px-3 py-2.5 text-[15px] transition-colors duration-150",
                    active ? "border-action/25 bg-action/10 font-semibold text-action" : "border-transparent text-ink-soft hover:bg-surface-2 hover:text-ink",
                  )}
                >
                  <Icon aria-hidden="true" size={21} strokeWidth={1.6} className="shrink-0" />
                  <span className="min-w-0 flex-1 whitespace-nowrap">{n.label}</span>
                  {count ? (
                    <span className={cn("shrink-0 rounded-md px-2 py-0.5 text-[12px] font-semibold tabular-nums", n.count === "review" ? "bg-action text-primary-foreground" : "bg-surface-2 text-ink-soft")}>
                      {count}
                      <span className="sr-only">{n.count === "review" ? " cazuri așteaptă decizia ta" : " alerte"}</span>
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

/** Pe telefon, patru destinații frecvente. Meniul din antet include toate ecranele. */
export function MobileBottomNav() {
  const { pathname, href } = useNav();
  return (
    <nav aria-label="Ecranele principale" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-rule bg-canvas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
      {[NAV[0], NAV[1], NAV[2], NAV[5]].map((n) => {
        const active = n.match(pathname);
        const Icon = n.icon;
        return (
          <Link
            key={n.href}
            href={href(n.href)}
            aria-current={active ? "page" : undefined}
            className={cn("flex min-h-16 flex-col items-center justify-center gap-1 px-1 py-2.5 text-center text-[12px] leading-tight", active ? "bg-action/8 font-semibold text-action" : "text-ink-soft")}
          >
            <Icon aria-hidden="true" size={22} strokeWidth={1.6} />
            {n.short}
          </Link>
        );
      })}
    </nav>
  );
}
