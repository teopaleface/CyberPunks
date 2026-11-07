"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ChevronDown, Bell, BookOpen, CircleHelp, Layers, LayoutGrid, Play, UtilityPole, Wrench } from "lucide-react";
import { cn } from "cn";
import type { Role } from "@/lib/operations/policy";

export const NAV = [
  { href: "/app", label: "Plan", short: "Plan", icon: LayoutGrid, match: (p: string) => p === "/app" || p.startsWith("/harta") },
  { href: "/coada", label: "Needs review", short: "Needs review", icon: CircleHelp, match: (p: string) => p.startsWith("/coada"), count: "review" as const },
  { href: "/posturi", label: "Substations", short: "Substations", icon: UtilityPole, match: (p: string) => p.startsWith("/posturi") },
  { href: "/lucrari", label: "Work orders", short: "Work orders", icon: Wrench, match: (p: string) => p.startsWith("/lucrari") || p.startsWith("/ordine") },
  { href: "/jurnal", label: "Activity", short: "Activity", icon: BookOpen, match: (p: string) => p.startsWith("/jurnal") },
  { href: "/alerte", label: "Alerts", short: "Alerts", icon: Bell, match: (p: string) => p.startsWith("/alerte") },
  { href: "/modele", label: "Models", short: "Models", icon: Layers, match: (p: string) => p.startsWith("/modele") },
  { href: "/rulare", label: "Run agent", short: "Agent", icon: Play, match: (p: string) => p.startsWith("/rulare") },
];

export function availableNav(consoleAllowed: boolean, role?: Role) {
  return consoleAllowed ? NAV : [{ ...NAV[0], label: role === "customer" ? "Your service" : "Your work", short: role === "customer" ? "Your service" : "Your work", match: (p: string) => p === "/app" }];
}

function useNav() {
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const href = (h: string) => (scenario ? `${h}?scenariu=${encodeURIComponent(scenario)}` : h);
  return { pathname, href };
}

const OPERATIONS = [0, 1, 2, 3, 5];
const AGENT_TOOLS = [4, 6, 7];

export function SideNav({ counts, consoleAllowed = false, role }: { counts?: { review: number; alerts: number }; consoleAllowed?: boolean; role?: Role }) {
  const { pathname, href } = useNav();
  const links = availableNav(consoleAllowed, role);
  const renderLink = (index: number) => {
    const n = links[index];
    const active = n.match(pathname);
    const count = consoleAllowed && n.count ? counts?.[n.count] ?? 0 : 0;
    const Icon = n.icon;
    return (
      <Link key={n.href} href={href(n.href)} aria-current={active ? "page" : undefined}
        className={cn(
          "flex min-h-11 items-center gap-3 rounded-xl border px-3 py-2.5 text-[15px] transition-colors duration-150",
          active ? "border-action/25 bg-action/10 font-semibold text-action" : "border-transparent text-ink-soft hover:bg-surface-2 hover:text-ink",
        )}>
        <Icon aria-hidden="true" size={20} strokeWidth={1.6} className="shrink-0" />
        <span className="min-w-0 flex-1 whitespace-nowrap">{n.label}</span>
        {count ? (
          <span className={cn("shrink-0 rounded-md px-2 py-0.5 text-[12px] font-semibold tabular-nums", n.count === "review" ? "bg-action text-primary-foreground" : "bg-surface-2 text-ink-soft")}>
            {count}<span className="sr-only">{n.count === "review" ? " cases need review" : " alerts"}</span>
          </span>
        ) : null}
      </Link>
    );
  };
  return (
    <nav aria-label="Workspace navigation" className="space-y-6">
      <div className="space-y-1">{(consoleAllowed ? OPERATIONS : [0]).map(renderLink)}</div>
      {consoleAllowed ? <details open={AGENT_TOOLS.some((i) => NAV[i].match(pathname))} className="group/nav border-t border-rule pt-4">
        <summary className="mb-2 flex min-h-10 cursor-pointer list-none items-center justify-between rounded-lg px-3 text-[14px] text-ink-soft hover:text-ink [&::-webkit-details-marker]:hidden">
          Agent tools <ChevronDown aria-hidden="true" size={15} className="transition-transform group-open/nav:rotate-180" />
        </summary>
        <div className="space-y-1">{AGENT_TOOLS.map(renderLink)}</div>
      </details> : null}
    </nav>
  );
}

/** Pe telefon, patru destinații frecvente. Meniul din antet include toate ecranele. */
export function MobileBottomNav({ consoleAllowed = false, role }: { consoleAllowed?: boolean; role?: Role }) {
  const { pathname, href } = useNav();
  const links = consoleAllowed ? [NAV[0], NAV[1], NAV[2], NAV[5]] : availableNav(false, role);
  return (
    <nav aria-label="Main navigation" className={cn("fixed inset-x-0 bottom-0 z-40 grid border-t border-rule bg-canvas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden", consoleAllowed ? "grid-cols-4" : "grid-cols-1")}>
      {links.map((n) => {
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
