"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "cn";

interface Tab {
  href: string;
  label: string;
  count?: number;
  attention?: boolean;
  match: (path: string) => boolean;
}

/** Ecranele consolei. Contorul de la „Nu sunt sigur” e portocaliu: acolo așteaptă un om. */
export function NavTabs({ review, alerts }: { review: number; alerts: number }) {
  const pathname = usePathname();
  const tabs: Tab[] = [
    { href: "/", label: "Planul de mâine", match: (p) => p === "/" || p.startsWith("/lucrari") },
    { href: "/coada", label: "Nu sunt sigur", count: review, attention: review > 0, match: (p) => p.startsWith("/coada") },
    { href: "/alerte", label: "Alerte și mesaje", count: alerts, match: (p) => p.startsWith("/alerte") },
    { href: "/jurnal", label: "Jurnal", match: (p) => p.startsWith("/jurnal") },
    { href: "/modele", label: "Modele", match: (p) => p.startsWith("/modele") },
  ];
  return (
    <nav aria-label="Ecranele consolei" className="flex h-full items-stretch">
      {tabs.map((t) => {
        const active = t.match(pathname);
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "relative flex items-center gap-2 px-3.5 text-[15px] whitespace-nowrap transition-colors duration-150",
              "after:absolute after:inset-x-3 after:bottom-0 after:h-[3px] after:rounded-t-[2px] after:bg-ink after:opacity-0 after:transition-opacity after:duration-150",
              active ? "font-[620] text-ink after:opacity-100" : "font-[480] text-muted-foreground hover:text-ink",
            )}
          >
            {t.label}
            {t.count ? (
              <span
                className={cn(
                  "inline-grid h-[22px] min-w-[22px] place-items-center rounded-full px-1.5 text-[13px] font-[700] tabular-nums",
                  t.attention ? "bg-att text-white" : "bg-muted text-ink",
                )}
              >
                {t.count}
                <span className="sr-only">{t.attention ? " lucrări așteaptă un om" : " în listă"}</span>
              </span>
            ) : null}
          </Link>
        );
      })}
    </nav>
  );
}
