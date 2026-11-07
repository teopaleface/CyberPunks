/**
 * Piesele designului „Noapte” (app-01 … app-14): card, cifră mare, pastile, filtre, butoane,
 * indicator semicircular, inel. Fără cod de server; se folosesc din paginile de server și din client.
 */
import type { ComponentType, ReactNode, SVGProps } from "react";
import { cn } from "cn";

export type Tone = "blue" | "violet" | "amber" | "green" | "orange" | "red" | "grey";

/** Culoarea fiecărui ton: text, fundal nuanțat, contur. */
export const TONE: Record<Tone, { text: string; bg: string; border: string; solid: string }> = {
  blue: { text: "text-[#8db8ff]", bg: "bg-[#0f2547]", border: "border-[#2a63c9]", solid: "bg-src-a" },
  violet: { text: "text-[#d6a8f0]", bg: "bg-[#2f1840]", border: "border-[#8c47b3]", solid: "bg-src-b" },
  amber: { text: "text-[#f5c66b]", bg: "bg-[#3a2808]", border: "border-[#b87a12]", solid: "bg-src-c" },
  green: { text: "text-[#7ee2a0]", bg: "bg-[#0b2a18]", border: "border-[#1f8a4a]", solid: "bg-ok" },
  orange: { text: "text-[#ffa27c]", bg: "bg-[#33160a]", border: "border-[#c9471b]", solid: "bg-att" },
  red: { text: "text-[#ff9b9b]", bg: "bg-[#3a1012]", border: "border-[#b93a3a]", solid: "bg-[#ef4444]" },
  grey: { text: "text-ink-soft", bg: "bg-[#121e30]", border: "border-[#2a3a52]", solid: "bg-idle" },
};

/** Tonul sursei A/B/C. */
export const SOURCE_TONE: Record<"A" | "B" | "C", Tone> = { A: "blue", B: "violet", C: "amber" };

type Icon = ComponentType<SVGProps<SVGSVGElement> & { size?: number | string; strokeWidth?: number | string }>;

/** Card: colțuri de 14 px, contur subțire, fundal puțin mai deschis decât pagina. */
export function Card({
  title,
  icon: IconCmp,
  iconTone = "blue",
  action,
  className,
  bodyClassName,
  children,
  as: As = "section",
  id,
}: {
  title?: ReactNode;
  icon?: Icon;
  iconTone?: Tone;
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children?: ReactNode;
  as?: "section" | "div" | "article";
  id?: string;
}) {
  return (
    <As id={id} className={cn("rounded-[14px] border border-rule bg-panel", className)}>
      {title ? (
        <header className="flex items-center gap-3 px-5 pt-4">
          {IconCmp ? <IconCmp aria-hidden="true" size={22} strokeWidth={1.7} className={TONE[iconTone].text} /> : null}
          <h2 className="min-w-0 flex-1 text-[17px] font-[600] tracking-[-0.005em]">{title}</h2>
          {action}
        </header>
      ) : null}
      <div className={cn(title ? "px-5 pt-3 pb-5" : "p-5", bodyClassName)}>{children}</div>
    </As>
  );
}

/** Cifră mare cu iconiță și etichetă (rândul de sus al ecranelor). */
export function Kpi({ icon: IconCmp, tone = "blue", value, label, unit, className }: { icon?: Icon; tone?: Tone; value: ReactNode; label?: ReactNode; unit?: ReactNode; className?: string }) {
  return (
    <div className={cn("flex min-w-0 items-center gap-4 rounded-[14px] border border-rule bg-panel px-5 py-4", className)}>
      {IconCmp ? <IconCmp aria-hidden="true" size={34} strokeWidth={1.5} className={cn("shrink-0", TONE[tone].text)} /> : null}
      <div className="min-w-0">
        <p className="text-[26px] leading-tight font-[700] tracking-[-0.02em] whitespace-nowrap tabular-nums">
          {value}
          {unit ? <span className="ml-1.5 text-[22px] font-[650]">{unit}</span> : null}
        </p>
        {label ? <p className="truncate text-[15px] text-ink-soft">{label}</p> : null}
      </div>
    </div>
  );
}

/** Pastilă de stare: contur colorat, fundal nuanțat. */
export function Pill({ tone = "grey", children, icon: IconCmp, className, size = "md" }: { tone?: Tone; children: ReactNode; icon?: Icon; className?: string; size?: "sm" | "md" | "lg" }) {
  const t = TONE[tone];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-[560] whitespace-nowrap",
        size === "sm" ? "px-2 py-0.5 text-[12.5px]" : size === "lg" ? "px-3.5 py-1.5 text-[16px]" : "px-2.5 py-1 text-[13.5px]",
        t.text,
        t.bg,
        t.border,
        className,
      )}
    >
      {IconCmp ? <IconCmp aria-hidden="true" size={size === "lg" ? 18 : 15} strokeWidth={1.8} /> : null}
      {children}
    </span>
  );
}

/** Punct colorat pentru sursă sau categorie. */
export function Dot({ tone, className }: { tone: Tone; className?: string }) {
  return <span aria-hidden="true" className={cn("inline-block size-2.5 shrink-0 rounded-full", TONE[tone].solid, className)} />;
}

/** Titlul paginii: mare, cu punct, și o frază dedesubt. */
export function PageTitle({ title, subtitle, icon: IconCmp, actions }: { title: ReactNode; subtitle?: ReactNode; icon?: Icon; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start gap-x-6 gap-y-3">
      <div className="min-w-0 flex-1">
        <h1 className="flex items-center gap-3 text-[34px] leading-[1.12] font-[750] tracking-[-0.025em] max-md:text-[28px]">
          {IconCmp ? <IconCmp aria-hidden="true" size={34} strokeWidth={1.5} className="shrink-0 text-violet" /> : null}
          <span className="min-w-0">{title}</span>
        </h1>
        {subtitle ? <p className="mt-1.5 max-w-[90ch] text-[17px] text-ink-soft">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}

/** Clasele butoanelor din design. */
export function btn(kind: "primary" | "danger" | "success" | "outline" | "ghost" = "primary", size: "md" | "lg" | "sm" = "md") {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-[10px] font-[600] whitespace-nowrap transition-[background-color,border-color,transform] duration-150 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
    size === "lg" ? "h-12 px-6 text-[17px]" : size === "sm" ? "h-9 px-3.5 text-[14px]" : "h-11 px-5 text-[15.5px]",
    kind === "primary" && "bg-action text-white hover:bg-[#2459ff]",
    kind === "danger" && "bg-att text-white hover:bg-[#ff6a3a]",
    kind === "success" && "bg-ok text-white hover:bg-[#1fb257]",
    kind === "outline" && "border border-[#2a3a52] bg-transparent text-ink hover:border-[#3d5170] hover:bg-[#0f1a2b]",
    kind === "ghost" && "text-ink-soft hover:bg-[#0f1a2b] hover:text-ink",
  );
}

/** Indicator semicircular (scorul modelului): valoarea între 0 și 1. */
export function Gauge({ value, label, sub, tone = "violet", size = 190 }: { value: number; label?: ReactNode; sub?: ReactNode; tone?: Tone; size?: number }) {
  const v = Math.max(0, Math.min(1, value));
  const r = 80;
  const len = Math.PI * r;
  const color = tone === "violet" ? "var(--violet)" : tone === "blue" ? "var(--src-a)" : tone === "amber" ? "var(--src-c)" : tone === "green" ? "var(--ok)" : "var(--att)";
  return (
    <div className="relative" style={{ width: size, height: size * 0.62 }}>
      <svg viewBox="0 0 200 120" width={size} height={size * 0.62} aria-hidden="true">
        <path d="M20 108 A80 80 0 0 1 180 108" fill="none" stroke="#2a3647" strokeWidth="16" strokeLinecap="round" />
        <path d="M20 108 A80 80 0 0 1 180 108" fill="none" stroke={color} strokeWidth="16" strokeLinecap="round" strokeDasharray={`${len * v} ${len}`} />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        {/* mărimea textului urmează mărimea indicatorului; etichetele lungi („peste 99%”) sunt mai mici */}
        <p className="leading-none font-[700] tracking-[-0.02em] tabular-nums" style={{ fontSize: Math.round(size * (typeof label === "string" && label.length > 5 ? 0.12 : 0.17)) }}>
          {label}
        </p>
        {sub ? (
          <p className="mt-1 text-ink-soft" style={{ fontSize: Math.max(12, Math.round(size * 0.078)) }}>
            {sub}
          </p>
        ) : null}
      </div>
    </div>
  );
}

/** Inel împărțit pe categorii, cu totalul în mijloc. */
export function Donut({ parts, center, sub, size = 150 }: { parts: { value: number; color: string; label: string }[]; center: ReactNode; sub?: ReactNode; size?: number }) {
  const total = parts.reduce((s, p) => s + p.value, 0) || 1;
  const r = 60;
  const c = 2 * Math.PI * r;
  // începutul fiecărui arc, calculat o dată (fără variabile modificate în timpul randării)
  const starts = parts.map((_, i) => parts.slice(0, i).reduce((sum, p) => sum + (p.value / total) * c, 0));
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox="0 0 150 150" width={size} height={size} role="img" aria-label={parts.map((p) => `${p.label}: ${p.value}`).join(", ")}>
        <circle cx="75" cy="75" r={r} fill="none" stroke="#1c2a3e" strokeWidth="16" />
        {parts.map((p, i) => {
          const len = (p.value / total) * c;
          return (
            <circle
              key={p.label}
              cx="75"
              cy="75"
              r={r}
              fill="none"
              stroke={p.color}
              strokeWidth="16"
              strokeDasharray={`${Math.max(0, len - 1.5)} ${c}`}
              strokeDashoffset={-starts[i]}
              transform="rotate(-90 75 75)"
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="text-[26px] leading-none font-[700] tabular-nums">{center}</p>
          {sub ? <p className="mt-1 text-[13.5px] text-ink-soft">{sub}</p> : null}
        </div>
      </div>
    </div>
  );
}

/** Bară de progres subțire (de exemplu scorul unui contor). */
export function Meter({ value, tone = "blue", label }: { value: number; tone?: Tone; label?: string }) {
  return (
    <div className="h-3 w-full overflow-hidden rounded-full bg-[#293648]" role="img" aria-label={label}>
      <div className={cn("h-full rounded-full", TONE[tone].solid)} style={{ width: `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%` }} />
    </div>
  );
}

/** Rând cheie–valoare din carduri (Detalii, Model, Impact). */
export function KV({ k, v, icon: IconCmp }: { k: ReactNode; v: ReactNode; icon?: Icon }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-rule py-2.5 last:border-b-0">
      <span className="flex min-w-0 items-center gap-2.5 text-[15px] text-ink-soft">
        {IconCmp ? <IconCmp aria-hidden="true" size={18} strokeWidth={1.7} className="shrink-0 text-ink-soft" /> : null}
        {k}
      </span>
      <span className="text-right text-[15.5px] font-[600] tabular-nums">{v}</span>
    </div>
  );
}
