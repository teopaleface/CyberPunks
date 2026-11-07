import { REPO_URL } from "./hero";

const LINKS = [
  { href: "#problema", label: "Problema" },
  { href: "#agentul", label: "Agentul" },
  { href: "#sursele", label: "Sursele" },
  { href: "#rezultate", label: "Rezultate" },
  { href: "#demo", label: "Demo" },
  { href: "#echipa", label: "Echipa" },
];

/** Antetul: doar cuvântul „Daybreak” (identitatea vizuală o alege Teo separat), legăturile și repo-ul. */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-rule/70 bg-night/75 backdrop-blur-md supports-[backdrop-filter]:bg-night/60">
      <a
        href="#continut"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:rounded-md focus:bg-ink focus:px-3 focus:py-2 focus:text-night"
      >
        Sari la conținut
      </a>
      <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-8 px-5 sm:px-8 xl:px-12 2xl:max-w-[1680px]">
        <a href="#top" className="text-[1.3rem] font-bold tracking-[-0.03em] text-ink" aria-label="Daybreak, începutul paginii">
          Daybreak
        </a>
        <nav aria-label="Secțiuni" className="hidden flex-1 md:block">
          <ul className="flex items-center gap-1">
            {LINKS.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className="rounded-md px-3 py-2 text-[0.95rem] text-ink-2 transition-colors duration-150 hover:bg-night-3 hover:text-ink"
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <a
          href={REPO_URL}
          className="ml-auto inline-flex h-9 items-center rounded-md border border-rule-strong px-3.5 text-[0.92rem] font-medium text-ink transition-colors duration-150 hover:border-ink-3 hover:bg-night-3 md:ml-0"
        >
          GitHub
        </a>
      </div>
    </header>
  );
}
