"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "cn";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface Tab {
  href: string;
  label: string;
  count?: number;
  attention?: boolean;
  match: (path: string) => boolean;
}

const TAB_CLASS = cn(
  "relative flex items-center gap-2 px-4 text-[16px] whitespace-nowrap transition-colors duration-150 max-[1600px]:px-3",
  "after:absolute after:inset-x-3 after:bottom-0 after:h-[3px] after:rounded-t-[2px] after:bg-ink after:opacity-0 after:transition-opacity after:duration-150",
);

function Count({ n, attention }: { n: number; attention?: boolean }) {
  return (
    <span
      className={cn(
        "inline-grid h-[22px] min-w-[22px] place-items-center rounded-full px-1.5 text-[13px] font-[650] tabular-nums",
        attention ? "bg-att text-on-att" : "bg-muted text-ink",
      )}
    >
      {n}
      <span className="sr-only">{attention ? " cazuri așteaptă decizia ta" : " în listă"}</span>
    </span>
  );
}

/**
 * Navigarea: trei intrări clare (planul, ce e de decis, posturile) și „Mai mult” pentru restul.
 * Când ești pe o pagină din „Mai mult”, butonul îi poartă numele, ca să fie clar unde ești.
 */
export function NavTabs({ review, alerts }: { review: number; alerts: number }) {
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const withScenario = (href: string) => (scenario ? `${href}?scenariu=${encodeURIComponent(scenario)}` : href);
  const main: Tab[] = [
    { href: "/", label: "Planul de mâine", match: (p) => p === "/" || p.startsWith("/lucrari") },
    { href: "/coada", label: "De decis", count: review, attention: review > 0, match: (p) => p.startsWith("/coada") },
    { href: "/posturi", label: "Posturi", match: (p) => p.startsWith("/posturi") },
  ];
  const more: Tab[] = [
    { href: "/alerte", label: "Alerte și mesaje", count: alerts, match: (p) => p.startsWith("/alerte") },
    { href: "/jurnal", label: "Jurnalul deciziilor", match: (p) => p.startsWith("/jurnal") },
    { href: "/modele", label: "Modelele", match: (p) => p.startsWith("/modele") },
  ];
  const activeMore = more.find((t) => t.match(pathname));
  return (
    <nav aria-label="Ecranele consolei" className="flex h-full items-stretch">
      {main.map((t) => {
        const active = t.match(pathname);
        return (
          <Link
            key={t.href}
            href={withScenario(t.href)}
            aria-current={active ? "page" : undefined}
            className={cn(TAB_CLASS, active ? "font-[620] text-ink after:opacity-100" : "font-[450] text-muted-foreground hover:text-ink")}
          >
            {t.label}
            {t.count ? <Count n={t.count} attention={t.attention} /> : null}
          </Link>
        );
      })}
      <DropdownMenu>
        <DropdownMenuTrigger
          className={cn(
            TAB_CLASS,
            "outline-none focus-visible:outline-2 focus-visible:outline-offset-[-4px] focus-visible:outline-ink",
            activeMore ? "font-[620] text-ink after:opacity-100" : "font-[450] text-muted-foreground hover:text-ink",
          )}
          aria-current={activeMore ? "page" : undefined}
        >
          {activeMore ? activeMore.label : "Mai mult"}
          <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
            <path d="M3 4.5 6 7.5 9 4.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="min-w-[240px] p-1.5">
          {more.map((t) => (
            <DropdownMenuItem key={t.href} asChild className="cursor-pointer px-3 py-2.5 text-[15.5px]">
              <Link href={withScenario(t.href)} aria-current={t.match(pathname) ? "page" : undefined} className="flex items-center justify-between gap-4">
                <span className={t.match(pathname) ? "font-[620]" : undefined}>{t.label}</span>
                {t.count ? <Count n={t.count} /> : null}
              </Link>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </nav>
  );
}
