"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useSyncExternalStore } from "react";
import { ChevronDown, Bell, BookOpen, CircleHelp, Layers, LayoutGrid, Play, UtilityPole, Wrench, MessagesSquare, Route, PlugZap, type LucideIcon } from "lucide-react";
import { cn } from "cn";
import type { Role } from "@/lib/operations/policy";

interface NavItem {
  href: string;
  label: string;
  short: string;
  icon: LucideIcon;
  match: (path: string) => boolean;
  count?: "review" | "alerts";
}
export const NAV: NavItem[] = [
  { href: "/app", label: "Dashboard", short: "Dashboard", icon: LayoutGrid, match: (p: string) => p === "/app" || p.startsWith("/harta") },
  { href: "/coada", label: "Needs review", short: "Needs review", icon: CircleHelp, match: (p: string) => p.startsWith("/coada"), count: "review" as const },
  { href: "/posturi", label: "Substations", short: "Substations", icon: UtilityPole, match: (p: string) => p.startsWith("/posturi") },
  { href: "/lucrari", label: "Work orders", short: "Work orders", icon: Wrench, match: (p: string) => p.startsWith("/lucrari") || p.startsWith("/ordine") },
  { href: "/jurnal", label: "Activity", short: "Activity", icon: BookOpen, match: (p: string) => p.startsWith("/jurnal") },
  { href: "/alerte", label: "Alerts", short: "Alerts", icon: Bell, match: (p: string) => p.startsWith("/alerte") },
  { href: "/modele", label: "Models", short: "Models", icon: Layers, match: (p: string) => p.startsWith("/modele") },
  { href: "/rulare", label: "Run agent", short: "Agent", icon: Play, match: (p: string) => p.startsWith("/rulare") },
  { href: "/app#assistant", label: "Daybreak assistant", short: "Assistant", icon: MessagesSquare, match: (p: string) => p === "/app#assistant" },
];

export function availableNav(consoleAllowed: boolean, role?: Role): NavItem[] {
  if (consoleAllowed) return NAV;
  const anchor = (hash: string, label: string, icon: typeof LayoutGrid, short = label) => ({ href: `/app#${hash}`, label, short, icon, match: (p: string) => p === `/app#${hash}` });
  return [
    { ...NAV[0], match: (p: string) => p === "/app" },
    ...(role === "technician" ? [anchor("route", "My route", Route), anchor("work", "Assigned work", Wrench, "Work"), anchor("cases", "Shared cases", CircleHelp, "Cases")] : [anchor("cases", "My requests", CircleHelp, "Requests"), anchor("connection", "My connection", PlugZap, "Connection")]),
    anchor("assistant", "Daybreak assistant", MessagesSquare, "Assistant"),
  ];
}

export function navigationHref(path: string, scenario: string | null) {
  if (!scenario) return path;
  const [base, hash] = path.split("#", 2);
  const query = new URLSearchParams(base.split("?", 2)[1]);
  query.set("scenariu", scenario);
  return `${base.split("?", 1)[0]}?${query.toString()}${hash ? `#${hash}` : ""}`;
}
const subscribeHash = (listener: () => void) => {
  window.addEventListener("hashchange", listener);
  window.addEventListener("popstate", listener);
  return () => { window.removeEventListener("hashchange", listener); window.removeEventListener("popstate", listener); };
};
function useNav() {
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const hash = useSyncExternalStore(subscribeHash, () => window.location.hash, () => "");
  const href = (h: string) => navigationHref(h, scenario);
  return { pathname: pathname + hash, href };
}

const OPERATIONS = [0, 1, 2, 3, 5, 8];
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
      <div className="space-y-1">{(consoleAllowed ? OPERATIONS : links.map((_, index) => index)).map(renderLink)}</div>
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
  const available = availableNav(consoleAllowed, role);
  const links = consoleAllowed ? [NAV[0], NAV[1], NAV[3], NAV[8]] : available.filter((n) => role !== "technician" || n.href !== "/app#cases");
  return (
    <nav aria-label="Main navigation" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-rule bg-canvas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
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
