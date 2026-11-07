export const REPO_URL = "https://github.com/teopaleface/CyberPunks";

const LINKS = [
  { href: "#problem", label: "Problem" },
  { href: "#how", label: "How it works" },
  { href: "#sources", label: "Models" },
  { href: "#results", label: "Results" },
  { href: "#team", label: "Team" },
];

/** Bara de sus, ca bara de produs Apple: material translucid, numele produsului, legăturile, un buton. */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-hairline bg-night/70 backdrop-blur-xl backdrop-saturate-150 supports-[backdrop-filter]:bg-night/55">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-3 focus:rounded-full focus:bg-ink focus:px-4 focus:py-2 focus:text-night"
      >
        Skip to content
      </a>
      <div className="mx-auto flex h-[52px] max-w-[1180px] items-center gap-6 px-5 sm:px-8">
        <a href="#top" className="text-[1.3rem] font-semibold tracking-[-0.025em] text-ink">
          Daybreak
        </a>
        <nav aria-label="Sections" className="ml-auto hidden md:block">
          <ul className="flex items-center gap-7">
            {LINKS.map((l) => (
              <li key={l.href}>
                <a href={l.href} className="text-[0.82rem] text-ink-2 transition-colors duration-200 hover:text-ink">
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <a
          href="#demo"
          className="ml-auto inline-flex h-7 items-center rounded-full bg-ppc-energy px-3.5 text-[0.8rem] font-medium text-white transition-[background-color,transform] duration-150 ease-out hover:bg-ppc-energy-hover active:scale-[0.96] md:ml-0"
        >
          Watch demo
        </a>
      </div>
    </header>
  );
}
