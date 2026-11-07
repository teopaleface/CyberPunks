"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Bell, BookOpen, CircleHelp, Layers, LayoutGrid, Monitor, UtilityPole, Wrench } from "lucide-react";
import { cn } from "cn";

export const NAV = [
  { href: "/", label: "Planul de mâine", short: "Planul", icon: LayoutGrid, match: (p: string) => p === "/" || p.startsWith("/harta") },
  { href: "/coada", label: "Nu sunt sigur", short: "Nu sunt sigur", icon: CircleHelp, match: (p: string) => p.startsWith("/coada"), count: "review" as const },
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

/** Meniul din stânga (design app-01): iconiță și nume, rândul activ pe fundal mai deschis. */
export function SideNav({ counts }: { counts: { review: number; alerts: number } }) {
  const { pathname, href } = useNav();
  return (
    <nav aria-label="Ecranele consolei" className="flex flex-col gap-1.5">
      {NAV.map((n) => {
        const active = n.match(pathname);
        const count = n.count ? counts[n.count] : 0;
        const Icon = n.icon;
        return (
          <Link
            key={n.href}
            href={href(n.href)}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex h-11 items-center gap-3 rounded-[10px] px-3 text-[15px] transition-colors duration-150",
              active ? "bg-[#1b2434] font-[600] text-ink" : "text-ink-soft hover:bg-[#0f1a2b] hover:text-ink",
            )}
          >
            <Icon aria-hidden="true" size={21} strokeWidth={1.6} className="shrink-0" />
            <span className="min-w-0 flex-1 truncate">{n.label}</span>
            {count ? (
              <span className={cn("rounded-full px-2 py-0.5 text-[12px] font-[650] tabular-nums", n.count === "review" ? "bg-att text-white" : "bg-[#1c2a3e] text-ink-soft")}>
                {count}
                <span className="sr-only">{n.count === "review" ? " cazuri așteaptă decizia ta" : " alerte"}</span>
              </span>
            ) : null}
          </Link>
        );
      })}
    </nav>
  );
}

/** Pe telefon: trei file sus, restul ecranelor pe bara de jos (design app-14). */
export function MobileTabs() {
  const { pathname, href } = useNav();
  return (
    <nav aria-label="Ecranele principale" className="flex gap-2 overflow-x-auto px-4 pb-3 md:hidden">
      {NAV.slice(0, 3).map((n) => {
        const active = n.match(pathname);
        return (
          <Link
            key={n.href}
            href={href(n.href)}
            aria-current={active ? "page" : undefined}
            className={cn("rounded-[10px] px-3.5 py-2 text-[15px] whitespace-nowrap", active ? "border border-[#2a3a52] bg-[#1b2434] font-[600]" : "text-ink-soft")}
          >
            {n.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function MobileBottomNav() {
  const { pathname, href } = useNav();
  return (
    <nav aria-label="Celelalte ecrane" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-6 border-t border-[#152133] bg-canvas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
      {NAV.slice(2).map((n) => {
        const active = n.match(pathname);
        const Icon = n.icon;
        return (
          <Link
            key={n.href}
            href={href(n.href)}
            aria-current={active ? "page" : undefined}
            className={cn("flex flex-col items-center gap-1 px-1 py-2.5 text-center text-[11.5px] leading-tight", active ? "text-ink" : "text-ink-soft")}
          >
            <Icon aria-hidden="true" size={22} strokeWidth={1.6} />
            {n.short}
          </Link>
        );
      })}
    </nav>
  );
}
