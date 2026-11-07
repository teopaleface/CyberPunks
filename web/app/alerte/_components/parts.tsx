import { englishText } from "@/lib/english";
import Link from "next/link";
import type { Alert, Decision, WorkItem } from "@/lib/contracts";
import { markerKind, markerSvg } from "@/lib/marker-svg";
import { itemPlace, itemTitle } from "@/lib/plan-screen";
import { sourceOf } from "@/lib/sources";

export type Severity = Alert["severity"];

export const SEVERITY_ORDER: Record<Severity, number> = { critical: 0, warning: 1, info: 2 };
export const SEVERITY_RO: Record<Severity, string> = { critical: "Critical", warning: "Warning", info: "Information" };

/**
 * Forma spune gravitatea și fără culoare: octogon = critic, triunghi = avertisment, cerc = informare.
 * Critic în `--destructive`, avertisment în `--att`, informare în cerneală.
 */
export function SeverityIcon({ severity, size = 22 }: { severity: Severity; size?: number }) {
  if (severity === "critical") {
    return (
      <svg width={size} height={size} viewBox="0 0 22 22" aria-hidden="true" className="shrink-0">
        <path d="M7.1 1.5h7.8l5.6 5.6v7.8l-5.6 5.6H7.1l-5.6-5.6V7.1z" style={{ fill: "var(--destructive)" }} />
        <rect x="10" y="5.6" width="2" height="7.4" fill="#fff" />
        <rect x="10" y="14.6" width="2" height="2" fill="#fff" />
      </svg>
    );
  }
  if (severity === "warning") {
    return (
      <svg width={size} height={size} viewBox="0 0 22 22" aria-hidden="true" className="shrink-0">
        <path d="M11 1.8 21 19.6H1z" style={{ fill: "var(--att)" }} />
        <rect x="10" y="8" width="2" height="6.2" fill="#fff" />
        <rect x="10" y="15.6" width="2" height="2" fill="#fff" />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 22 22" aria-hidden="true" className="shrink-0">
      <circle cx="11" cy="11" r="9.2" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth="1.7" />
      <rect x="10.1" y="9.4" width="1.8" height="6.4" style={{ fill: "var(--ink)" }} />
      <rect x="10.1" y="5.9" width="1.8" height="1.8" style={{ fill: "var(--ink)" }} />
    </svg>
  );
}

/** Eticheta de transparență de pe fiecare mesaj: nimic nu pleacă din consolă. */
export function DemoStamp() {
  return (
    <span className="inline-flex shrink-0 items-center gap-1.5 rounded-[4px] border border-ink bg-panel px-2 py-[3px] text-[14px] leading-tight font-[600] whitespace-nowrap text-ink">
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" className="shrink-0">
        <circle cx="7" cy="7" r="5.7" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M3 11 11 3" stroke="currentColor" strokeWidth="1.5" />
      </svg>
      Demo, not sent
    </span>
  );
}

/** Lucrarea legată: markerul sursei, ID-ul ca legătură spre detaliu și, dacă o avem, ce și unde e. */
export function WorkItemRef({
  id,
  workItem,
  decision,
  scenario,
}: {
  id: string;
  workItem?: WorkItem;
  decision?: Decision;
  scenario: string;
}) {
  const source = workItem?.source ?? sourceOf(id);
  return (
    <Link
      href={`/lucrari/${encodeURIComponent(id)}?scenariu=${encodeURIComponent(scenario)}`}
      className="group inline-flex max-w-full items-center gap-2 rounded-[4px] text-[15px]"
    >
      {source ? (
        <span
          className="block size-8 shrink-0"
          dangerouslySetInnerHTML={{ __html: markerSvg({ source, kind: markerKind(decision?.decision) }, 32) }}
        />
      ) : null}
      <span translate="no" className="code-id shrink-0 text-ink underline decoration-rule underline-offset-4 group-hover:decoration-ink">{id}</span>
      {workItem ? <span className="min-w-0 truncate text-[14.5px] text-muted-foreground">{englishText(shortTitle(workItem))}</span> : null}
    </Link>
  );
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Ce e și unde, fără să repete ID-ul și cu diacriticele din eticheta locului:
 * „Contor la PT 9979, Tineretului”, „Zona Timișoara (Timiș)”, „Post de transformare, Afumați (sintetic)”.
 */
export function shortTitle(w: WorkItem): string {
  const label = w.location.label?.trim() ?? "";
  const rest = label.replace(new RegExp(`^(Contor\\s+)?${escapeRe(w.asset_id)},?\\s*`), "").trim();
  if (w.asset_type === "meter") return rest ? `Meter at ${rest}` : `Meter, ${itemPlace(w)}`;
  if (w.asset_type === "transformer_post") return `Substation, ${rest || itemPlace(w)}`;
  return label || itemTitle(w);
}

/** Pastila cu numărul de lângă titlurile de secțiune (ca în taburile din antet). */
export function CountPill({ n }: { n: number }) {
  return (
    <span className="inline-grid h-6 min-w-6 place-items-center rounded-full bg-muted px-1.5 text-[14px] font-[700] tabular-nums">{n}</span>
  );
}
