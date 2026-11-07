"use client";

import { englishText } from "@/lib/english";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Fragment, memo, useCallback, useDeferredValue, useMemo, useState, type ComponentType, type ReactNode, type SVGProps } from "react";
import {
  BotIcon,
  CheckIcon,
  ChevronDownIcon,
  ClockIcon,
  CpuIcon,
  DownloadIcon,
  FileTextIcon,
  GavelIcon,
  LayersIcon,
  RotateCcwIcon,
  SearchIcon,
  TargetIcon,
  TrendingUpIcon,
  UserRoundIcon,
} from "lucide-react";
import { cn } from "cn";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { btn, Card } from "@/components/ds";
import { CopyChip } from "@/components/misc/copy-chip";
import { SolidPill, type SolidTone } from "@/components/misc/solid-pill";
import type { Source } from "@/lib/contracts";
import { fmtInt, plural } from "@/lib/format";
import { roundPct } from "@/lib/human";
import { SOURCES, SOURCE_ORDER } from "@/lib/sources";
import type { ActionOption, JournalRow } from "./types";

type ActorFilter = "all" | "agent" | "human";
type SourceFilter = "all" | Source;

const COLS = 9;
/** Câte rânduri se arată deodată: jurnalul unei zile are sute de decizii. */
const PAGE = 60;
const SRC_TONE: Record<Source, SolidTone> = { A: "blue", B: "violet", C: "amber" };

/** Tonul și textul pastilei „Decizia”. */
const DECISION: Record<string, { tone: SolidTone; label: string; icon?: ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }> }> = {
  assigned: { tone: "green", label: "On route", icon: CheckIcon },
  remote_action: { tone: "blue", label: "Remote" },
  notify: { tone: "violet", label: "Notification only" },
  fusion: { tone: "violet", label: "Energy balance" },
  deferred: { tone: "grey", label: "Deferred" },
  human_review: { tone: "orange", label: "Human review", icon: ClockIcon },
  rejected_invalid: { tone: "red", label: "Invalid data" },
  review_approve: { tone: "green", label: "Approved", icon: CheckIcon },
  review_reject: { tone: "red", label: "Rejected" },
  review_defer: { tone: "grey", label: "Deferred" },
};

const JOURNAL_COPY: Record<string, string> = {
  "aprobată de om": "Approved by reviewer",
  "respinsă de om": "Rejected by reviewer",
  "amânată de om": "Deferred by reviewer",
  "rulare a agentului": "Agent run",
  "plan refăcut după decizia omului": "Replanned after review",
  "modelul nu e sigur": "Model is uncertain",
  "decis de om": "Decided by reviewer",
  "marja cerută la încredere medie": "Required margin at medium confidence",
  "scor minim pentru vizită": "Minimum visit score",
  "contor citit la distanță": "Remotely readable meter",
  "preaviz pentru clienți": "Customer notice period",
  "da": "Yes",
  "nu": "No",
};
function journalText(text: string): string {
  const exact = JOURNAL_COPY[text.trim().toLocaleLowerCase("ro-RO")];
  if (exact) return exact;
  const days = /^(\d+) (?:de )?(?:zi lucrătoare|zile lucrătoare)$/.exec(text);
  if (days) return `${days[1]} working ${days[1] === "1" ? "day" : "days"}`;
  return englishText(text);
}

function DecisionPill({ r }: { r: JournalRow }) {
  const d = DECISION[r.action];
  return (
    <SolidPill tone={d?.tone ?? "grey"} icon={d?.icon}>
      {journalText(d?.label ?? r.actionLabel)}
    </SolidPill>
  );
}

function Dash() {
  return (
    <span className="text-muted-foreground">
      <span aria-hidden="true">—</span>
      <span className="sr-only">no value</span>
    </span>
  );
}

function Field({ label, icon: Icon, children }: { label: string; icon: ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <span className="flex items-center gap-2.5 text-[15px] font-[600]">
        <Icon size={20} aria-hidden="true" className="text-ink-soft" />
        {label}
      </span>
      {children}
    </div>
  );
}

const TRIGGER =
  "h-11 w-full rounded-[10px] border-rule bg-surface-2 px-4 text-[15.5px] text-ink hover:bg-[#101d30] dark:bg-surface-2 dark:hover:bg-[#101d30]";

const th = "border-b border-rule px-2.5 py-3.5 text-left align-middle text-[15px] font-[600] text-ink";

function TH({ icon: Icon, children, className }: { icon: ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>; children: ReactNode; className?: string }) {
  return (
    <th scope="col" className={cn(th, className)}>
      <span className="flex items-center gap-2.5">
        <Icon size={19} aria-hidden="true" className="shrink-0 text-ink-soft" />
        {children}
      </span>
    </th>
  );
}

/**
 * Filtrele și tabelul jurnalului. Datele vin gata făcute de pe server; aici doar se filtrează.
 * Rulările agentului apar ca rânduri-titlu deasupra deciziilor pe care le-au scris.
 */
// filtrele în adresă: ?cine=agent|om&sursa=A|B|C&decizia=<acțiune>&cauta=<text>
const ACTOR_PARAM: Record<ActorFilter, string | null> = { all: null, agent: "agent", human: "om" };

function readFilters(sp: URLSearchParams | null, options: ActionOption[]) {
  const cine = sp?.get("cine");
  const sursa = sp?.get("sursa");
  const decizia = sp?.get("decizia");
  return {
    actor: (cine === "agent" ? "agent" : cine === "om" ? "human" : "all") as ActorFilter,
    source: (SOURCE_ORDER as readonly string[]).includes(sursa ?? "") ? (sursa as Source) : ("all" as SourceFilter),
    action: decizia && options.some((o) => o.action === decizia) ? decizia : "all",
    query: (sp?.get("cauta") ?? "").slice(0, 80),
  };
}

function writeFilters(f: { actor: ActorFilter; source: SourceFilter; action: string; query: string }) {
  const url = new URL(window.location.href);
  const set = (k: string, v: string | null) => (v ? url.searchParams.set(k, v) : url.searchParams.delete(k));
  set("cine", ACTOR_PARAM[f.actor]);
  set("sursa", f.source === "all" ? null : f.source);
  set("decizia", f.action === "all" ? null : f.action);
  set("cauta", f.query.trim() || null);
  window.history.replaceState(window.history.state, "", url);
}

export function JournalTable({ rows, options, scenario }: { rows: JournalRow[]; options: ActionOption[]; scenario: string }) {
  const searchParams = useSearchParams();
  const [initial] = useState(() => readFilters(searchParams, options));
  const [actor, setActorState] = useState<ActorFilter>(initial.actor);
  const [source, setSourceState] = useState<SourceFilter>(initial.source);
  const [action, setActionState] = useState(initial.action);
  const [query, setQueryState] = useState(initial.query);
  const [limit, setLimit] = useState(PAGE);
  const [open, setOpen] = useState<ReadonlySet<string>>(() => new Set());
  const q = useDeferredValue(query).trim().toUpperCase();

  // Orice filtru nou pornește iar de la primele rânduri.
  const current = { actor, source, action, query };
  const setActor = (v: ActorFilter) => {
    setActorState(v);
    setLimit(PAGE);
    writeFilters({ ...current, actor: v });
  };
  const setSource = (v: SourceFilter) => {
    setSourceState(v);
    setLimit(PAGE);
    writeFilters({ ...current, source: v });
  };
  const setAction = (v: string) => {
    setActionState(v);
    setLimit(PAGE);
    writeFilters({ ...current, action: v });
  };
  const setQuery = (v: string) => {
    setQueryState(v);
    setLimit(PAGE);
    writeFilters({ ...current, query: v });
  };

  const decisions = useMemo(() => rows.filter((r) => r.kind !== "run"), [rows]);
  const filtered = useMemo(
    () =>
      rows.filter((r) => {
        if (actor !== "all" && r.actor !== actor) return false;
        if (source !== "all" && r.source !== source) return false;
        if (action !== "all" && r.action !== action) return false;
        if (q && !(r.workItemId ?? "").toUpperCase().includes(q)) return false;
        return true;
      }),
    [rows, actor, source, action, q],
  );

  const shown = filtered.filter((r) => r.kind !== "run").length;
  const visible = filtered.slice(0, limit);
  const hidden = filtered.length - visible.length;
  const active = actor !== "all" || source !== "all" || action !== "all" || query.trim() !== "";
  const reset = () => {
    setActorState("all");
    setSourceState("all");
    setActionState("all");
    setQueryState("");
    setLimit(PAGE);
    writeFilters({ actor: "all", source: "all", action: "all", query: "" });
  };
  // stabilă, ca rândurile memorate să nu se redeseneze toate la fiecare deschidere
  const toggle = useCallback(
    (id: string) =>
      setOpen((prev) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
      }),
    [],
  );

  return (
    <div className="flex min-w-0 max-w-full flex-col gap-5">
      <Card as="section" className="rounded-[18px]" bodyClassName="p-5">
        <div className="flex flex-wrap items-end gap-x-5 gap-y-4" role="search" aria-label="History filters">
          <div className="grid min-w-0 flex-1 basis-[560px] grid-cols-2 gap-x-4 gap-y-4 md:grid-cols-4">
            <Field label="Source" icon={LayersIcon}>
              <Select value={source} onValueChange={(v) => setSource(v as SourceFilter)}>
                <SelectTrigger aria-label="Work source" className={TRIGGER}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All sources</SelectItem>
                  {SOURCE_ORDER.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s} {SOURCES[s].name}
                      <span className="ml-1 text-muted-foreground tabular-nums">{fmtInt(decisions.filter((r) => r.source === s).length)}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Actor" icon={UserRoundIcon}>
              <Select value={actor} onValueChange={(v) => setActor(v as ActorFilter)}>
                <SelectTrigger aria-label="Decision maker" className={TRIGGER}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All actors</SelectItem>
                  <SelectItem value="agent">
                    Agent
                    <span className="ml-1 text-muted-foreground tabular-nums">{fmtInt(decisions.filter((r) => r.actor === "agent").length)}</span>
                  </SelectItem>
                  <SelectItem value="human">
                    Human
                    <span className="ml-1 text-muted-foreground tabular-nums">{fmtInt(decisions.filter((r) => r.actor === "human").length)}</span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Decision" icon={GavelIcon}>
              <Select value={action} onValueChange={setAction}>
                <SelectTrigger aria-label="Decision type" className={TRIGGER}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All decisions</SelectItem>
                  {options.map((o) => (
                    <SelectItem key={o.action} value={o.action}>
                      {journalText(o.label)}
                      <span className="ml-1 text-muted-foreground tabular-nums">{fmtInt(o.count)}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Work item" icon={SearchIcon}>
              <input
                type="search"
                name="cauta"
                aria-label="Search by work item ID"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="PT-1269…"
                spellCheck={false}
                autoComplete="off"
                className="h-11 w-full rounded-[10px] border border-rule bg-surface-2 px-4 text-[15.5px] placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring"
              />
            </Field>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button type="button" onClick={reset} disabled={!active} className={btn("outline")}>
              <RotateCcwIcon size={18} aria-hidden="true" />
              Reset filters
            </button>
            <a href={`/jurnal/descarca?scenariu=${encodeURIComponent(scenario)}`} download={`jurnal-${scenario}.jsonl`} className={btn("primary")}>
              <DownloadIcon size={18} aria-hidden="true" />
              Download JSONL
            </a>
          </div>
        </div>
      </Card>

      <Card as="section" className="min-w-0 max-w-full overflow-hidden rounded-[18px]" bodyClassName="min-w-0 p-0">
        <div className="relative overflow-x-auto">
          <table className="w-full min-w-[1010px] table-fixed border-separate border-spacing-0 text-[15.5px]">
            <caption className="sr-only">
              Decision history, newest first ({active ? `${fmtInt(shown)} of ${plural(decisions.length, "decision", "decisions")}` : plural(decisions.length, "decision", "decisions")})
            </caption>
            <colgroup>
              <col className="w-[70px]" />
              <col className="w-[104px]" />
              <col className="w-[132px]" />
              <col className="w-[150px]" />
              <col className="w-[160px]" />
              <col className="w-[140px]" />
              <col className="w-[108px]" />
              <col />
              <col className="w-[40px]" />
            </colgroup>
            <thead>
              <tr>
                <TH icon={ClockIcon} className="pl-4">
                  Time
                </TH>
                <TH icon={UserRoundIcon}>Actor</TH>
                <TH icon={GavelIcon}>Decision</TH>
                <TH icon={LayersIcon}>Work item</TH>
                <TH icon={FileTextIcon}>Rule</TH>
                <TH icon={TargetIcon}>Threshold</TH>
                <TH icon={TrendingUpIcon}>Prediction</TH>
                <TH icon={CpuIcon}>Model version</TH>
                <th scope="col" className={cn(th, "pr-4")}>
                  <span className="sr-only">Full record</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={COLS} className="px-7 py-14 text-center">
                    <p className="text-[17px] font-[600]">No records match these filters.</p>
                    <p className="mt-1 text-[15px] text-ink-soft">Change a filter or reset to see all records.</p>
                    <button type="button" className={cn(btn("outline"), "mt-4")} onClick={reset}>
                      Show all history
                    </button>
                  </td>
                </tr>
              ) : (
                visible.map((r) =>
                  r.kind === "run" ? (
                    <RunRow key={r.id} r={r} />
                  ) : (
                    <DecisionRow key={r.id} r={r} scenario={scenario} expanded={open.has(r.id)} onToggle={toggle} />
                  ),
                )
              )}
            </tbody>
          </table>
        </div>
        {hidden > 0 ? (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-rule px-5 py-4">
            <span className="text-[15px] text-ink-soft">
              Showing the first {plural(visible.length, "record", "records")} of {fmtInt(filtered.length)}, newest first.
            </span>
            <button type="button" className={btn("outline", "sm")} onClick={() => setLimit((n) => n + PAGE)}>
              Show another {fmtInt(Math.min(PAGE, hidden))}
            </button>
            <button type="button" className={btn("ghost", "sm")} onClick={() => setLimit(filtered.length)}>
              Show all {fmtInt(filtered.length)}
            </button>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

function RunRow({ r }: { r: JournalRow }) {
  return (
    <tr style={{ contentVisibility: "auto", containIntrinsicSize: "auto 44px" }}>
      <td colSpan={COLS} className="border-b border-rule bg-surface-2 px-5 py-2.5">
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-[15px]">
          <BotIcon size={18} aria-hidden="true" className="shrink-0 text-violet" />
          <span className="shrink-0 font-[620]">
            {r.action === "replan" ? "Agent replanned after a human decision" : "Agent created the plan"}
          </span>
          <time dateTime={r.ts} className="shrink-0 text-ink-soft">
            {r.moment}
          </time>
          {r.decisions ? (
            <>
              <span className="h-4 w-px shrink-0 bg-rule" aria-hidden="true" />
              <span className="shrink-0 text-ink-soft">{plural(r.decisions, "decision", "decisions")}</span>
            </>
          ) : null}
          {r.note ? (
            <span className="min-w-0 truncate text-[13.5px] text-muted-foreground md:ml-auto md:pl-6" title={englishText(r.note)}>
              {englishText(r.note)}
            </span>
          ) : null}
        </div>
      </td>
    </tr>
  );
}

const DecisionRow = memo(DecisionRowImpl);

function DecisionRowImpl({
  r,
  scenario,
  expanded,
  onToggle,
}: {
  r: JournalRow;
  scenario: string;
  expanded: boolean;
  onToggle: (id: string) => void;
}) {
  const human = r.actor === "human";
  const href = r.workItemId ? `/lucrari/${encodeURIComponent(r.workItemId)}?scenariu=${encodeURIComponent(scenario)}` : null;
  const detailId = `jurnal-${r.id}`;
  const td = cn("px-2.5 py-2.5 align-middle", expanded ? "border-b-0" : "border-b border-rule");
  const what = r.workItemId ?? englishText(r.actionLabel);

  return (
    <>
      <tr style={expanded ? undefined : { contentVisibility: "auto", containIntrinsicSize: "auto 56px" }}>
        <td className={cn(td, "pl-4")}>
          <time dateTime={r.ts} title={r.moment} className="text-[16px] tabular-nums">
            {r.time}
          </time>
        </td>
        <td className={td}>
          <span className="flex items-center gap-2.5">
            {human ? <UserRoundIcon size={20} aria-hidden="true" className="text-ink-soft" /> : <BotIcon size={20} aria-hidden="true" className="text-ink-soft" />}
            {human ? "Human" : "Agent"}
          </span>
        </td>
        <td className={td}>
          <DecisionPill r={r} />
        </td>
        <td className={td}>
          {r.assetId && href ? (
            <Link
              href={href}
              translate="no"
              title={r.itemTitle ? `${r.workItemId}: ${englishText(r.itemTitle)}` : r.workItemId ?? undefined}
              className="inline-flex max-w-full items-center rounded-[8px] border border-rule bg-surface-2 px-2.5 py-1 text-[14px] tabular-nums transition-colors duration-150 hover:border-ink-soft hover:bg-[#101d30] focus-visible:outline-2 focus-visible:outline-ring"
            >
              <span className="truncate">{r.assetId}</span>
            </Link>
          ) : (
            <Dash />
          )}
        </td>
        <td className={td}>
          {r.ruleId ? (
            <div className="min-w-0 leading-snug">
              <span translate="no" className="block truncate text-[14.5px] font-[560]" title={r.ruleId}>
                {r.ruleId}
              </span>
              {r.ruleText ? (
                <span className="line-clamp-1 text-[13px] text-muted-foreground" title={journalText(r.ruleText)}>
                  {journalText(r.ruleText)}
                </span>
              ) : null}
            </div>
          ) : (
            <Dash />
          )}
        </td>
        <td className={cn(td, "tabular-nums")}>
          {r.mainThreshold ? <span className="text-[14.5px]">{journalText(r.mainThreshold)}</span> : <Dash />}
        </td>
        <td className={td}>
          {r.score !== null && r.source ? (
            <SolidPill tone={SRC_TONE[r.source]} className="px-2.5 tabular-nums">
              <span translate="no" className="font-[700]">
                {r.source}
              </span>
              {roundPct(r.score)}
            </SolidPill>
          ) : (
            <Dash />
          )}
        </td>
        <td className={td}>{r.modelVersion ? <CopyChip text={r.modelVersion} label={`Copy model version ${r.modelVersion}`} /> : <Dash />}</td>
        <td className={cn(td, "pr-4 text-right")}>
          <button
            type="button"
            onClick={() => onToggle(r.id)}
            aria-expanded={expanded}
            aria-controls={detailId}
            aria-label={expanded ? `Hide details for ${what}` : `Show full record for ${what}`}
            className="inline-grid size-9 place-items-center rounded-[8px] text-ink-soft transition-colors duration-150 hover:bg-surface-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-ring"
          >
            <ChevronDownIcon className={cn("size-5 transition-transform duration-150", expanded && "rotate-180")} aria-hidden="true" />
          </button>
        </td>
      </tr>
      {expanded ? (
        <tr id={detailId}>
          <td colSpan={COLS} className="border-b border-rule bg-surface-2 px-5 pt-3 pb-5">
            <div className="grid grid-cols-1 gap-x-10 gap-y-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.25fr)]">
              <section>
                <h3 className="text-[15px] font-[620]">All thresholds</h3>
                {r.thresholds.length ? (
                  <dl className="mt-1.5 grid grid-cols-[minmax(0,1fr)_auto] gap-x-6 text-[14.5px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-1 [&>dd]:text-right [&>dd]:font-[560] [&>dd]:tabular-nums [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-1 [&>dt]:text-ink-soft">
                    {r.thresholds.map((t) => (
                      <Fragment key={t.key}>
                        <dt title={t.key}>{journalText(t.label)}</dt>
                        <dd>{journalText(t.value)}</dd>
                      </Fragment>
                    ))}
                  </dl>
                ) : (
                  <p className="mt-1.5 text-[14.5px] text-ink-soft">This rule used no numeric thresholds.</p>
                )}
              </section>
              <section>
                <h3 className="text-[15px] font-[620]">Full trace</h3>
                <dl className="mt-1.5 grid grid-cols-[132px_minmax(0,1fr)] gap-x-4 text-[14.5px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-1 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-1 [&>dt]:text-ink-soft">
                  <dt>Decision ID</dt>
                  <dd translate="no" className="font-[560] break-all">{r.id}</dd>
                  <dt>Prediction ID</dt>
                  <dd translate="no" className="font-[560] break-all">{r.predictionId ?? "–"}</dd>
                  <dt>Model version</dt>
                  <dd translate="no" className="font-[560] break-all">{r.modelVersion ?? "–"}</dd>
                  <dt>Input fingerprint</dt>
                  <dd translate="no" className="font-[560] break-all">{r.inputsSha ?? "–"}</dd>
                  <dt>Timestamp</dt>
                  <dd>{r.moment}</dd>
                </dl>
              </section>
              <section>
                <h3 className="text-[15px] font-[620]">{human ? "Reviewer note" : "Agent reason"}</h3>
                <p className="mt-1.5 max-w-[72ch] text-[15.5px] leading-relaxed">
                  {human ? (
                    <>
                      <b className="font-[640]">{r.reviewer ?? "Dispatcher"}</b>
                      {r.note ? `: „${r.note}”` : ", without a note."}
                    </>
                  ) : (
                    englishText(r.note ?? "The agent did not record a reason for this decision.")
                  )}
                </p>
                {r.itemTitle ? <p className="mt-1 text-[14px] text-ink-soft">{englishText(r.itemTitle)}</p> : null}
                {href ? (
                  <Link href={href} className="mt-2.5 inline-block text-[15px] font-[600] text-[#8db8ff] underline decoration-rule underline-offset-4 hover:decoration-current">
                    Open work item <span translate="no">{r.workItemId}</span>
                  </Link>
                ) : null}
              </section>
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}
