"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Bell, BookOpen, CalendarDays, CircleHelp, ClipboardList, Layers, Map, MessagesSquare, Play, PlugZap, Presentation, Route, UtilityPole, Wrench, type LucideIcon } from "lucide-react";
import { cn } from "cn";
import type { Role } from "@/lib/operations/policy";

interface NavItem {
  href: string;
  label: string;
  short: string;
  icon: LucideIcon;
  match: (path: string) => boolean;
  count?: "review" | "alerts";
  secondary?: boolean;
}

const at = (href: string) => (path: string) => {
  const pathname = path.split(/[?#]/, 1)[0];
  return pathname === href || pathname.startsWith(`${href}/`);
};
const assistant: NavItem = { href: "/app", label: "Assistant", short: "Assistant", icon: MessagesSquare, match: at("/app") };
const activity: NavItem = { href: "/activitate", label: "Activity", short: "Activity", icon: BookOpen, match: at("/activitate") };
const cases = (label: string): NavItem => ({ href: "/cazuri", label, short: "Cases", icon: CircleHelp, match: at("/cazuri") });

export const NAV: NavItem[] = [
  assistant,
  { href: "/planificare", label: "Daily plan", short: "Plan", icon: CalendarDays, match: at("/planificare") },
  { href: "/coada", label: "Needs review", short: "Review", icon: CircleHelp, match: at("/coada"), count: "review" },
  { href: "/harta", label: "Map & crews", short: "Map", icon: Map, match: at("/harta") },
  { href: "/lucrari", label: "Work orders", short: "Work orders", icon: Wrench, match: (p) => at("/lucrari")(p) || at("/ordine")(p) },
  cases("Service cases"),
  { href: "/posturi", label: "Substations", short: "Substations", icon: UtilityPole, match: at("/posturi") },
  { href: "/jurnal", label: "Decision history", short: "History", icon: BookOpen, match: at("/jurnal"), secondary: true },
  { href: "/alerte", label: "Alerts", short: "Alerts", icon: Bell, match: at("/alerte"), count: "alerts", secondary: true },
  { href: "/modele", label: "Models", short: "Models", icon: Layers, match: at("/modele"), secondary: true },
  { href: "/rulare", label: "Run history", short: "Runs", icon: Play, match: at("/rulare"), secondary: true },
  { href: "/demo", label: "Presentation", short: "Presentation", icon: Presentation, match: at("/demo"), secondary: true },
];

export function availableNav(consoleAllowed: boolean, role?: Role): NavItem[] {
  if (consoleAllowed && role === "dispatcher") return NAV;
  if (role === "technician") return [
    assistant,
    { href: "/traseu", label: "My route", short: "Route", icon: Route, match: at("/traseu") },
    { href: "/sarcini", label: "Assigned work", short: "Work", icon: ClipboardList, match: at("/sarcini") },
    cases("Shared cases"),
    activity,
  ];
  if (role === "dispatcher") return [assistant, cases("Shared cases"), activity];
  return [
    assistant,
    cases("My cases"),
    { href: "/conexiuni", label: "My connections", short: "Connections", icon: PlugZap, match: at("/conexiuni") },
    activity,
  ];
}

export function mobileNav(consoleAllowed: boolean, role?: Role): NavItem[] {
  const links = availableNav(consoleAllowed, role);
  if (consoleAllowed && role === "dispatcher") return links.filter((n) => ["/app", "/planificare", "/coada", "/harta"].includes(n.href));
  if (role === "technician") return links.filter((n) => n.href !== "/cazuri");
  return links;
}

export function navigationHref(path: string, scenario: string | null) {
  if (!scenario) return path;
  const [base, hash] = path.split("#", 2);
  const query = new URLSearchParams(base.split("?", 2)[1]);
  query.set("scenariu", scenario);
  return `${base.split("?", 1)[0]}?${query.toString()}${hash ? `#${hash}` : ""}`;
}
function useNav() {
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  return { pathname, href: (path: string) => navigationHref(path, scenario) };
}

export function SideNav({ counts, consoleAllowed = false, role }: { counts?: { review: number; alerts: number }; consoleAllowed?: boolean; role?: Role }) {
  const { pathname, href } = useNav();
  const links = availableNav(consoleAllowed, role);
  const renderLink = (n: NavItem) => {
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
  const secondary = links.filter((n) => n.secondary);
  return (
    <nav aria-label="Workspace navigation" className="space-y-4">
      <div className="space-y-1">{links.filter((n) => !n.secondary).map(renderLink)}</div>
      {secondary.length ? <div className="space-y-1 border-t border-rule pt-4">{secondary.map(renderLink)}</div> : null}
    </nav>
  );
}

/** Four frequent destinations. The header menu includes every available page. */
export function MobileBottomNav({ consoleAllowed = false, role }: { consoleAllowed?: boolean; role?: Role }) {
  const { pathname, href } = useNav();
  const links = mobileNav(consoleAllowed, role);
  return (
    <nav aria-label="Main navigation" className={cn("fixed inset-x-0 bottom-0 z-40 grid border-t border-rule bg-canvas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden", links.length === 3 ? "grid-cols-3" : "grid-cols-4")}>
      {links.map((n) => {
        const active = n.match(pathname);
        const Icon = n.icon;
        return (
          <Link key={n.href} href={href(n.href)} aria-current={active ? "page" : undefined}
            className={cn("flex h-16 flex-col items-center justify-center gap-1 px-1 py-2.5 text-center text-[12px] leading-tight", active ? "bg-action/8 font-semibold text-action" : "text-ink-soft")}>
            <Icon aria-hidden="true" size={22} strokeWidth={1.6} />
            {n.short}
          </Link>
        );
      })}
    </nav>
  );
}
