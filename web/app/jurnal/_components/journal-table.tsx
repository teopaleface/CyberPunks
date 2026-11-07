"use client";

import Link from "next/link";
import { Fragment, useDeferredValue, useMemo, useState, type ReactNode } from "react";
import { ChevronDownIcon, SearchIcon } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Source } from "@/lib/contracts";
import { fmtInt, plural } from "@/lib/format";
import { markerSvg } from "@/lib/marker-svg";
import { SOURCES, SOURCE_ORDER } from "@/lib/sources";
import { AgentGlyph, HumanGlyph } from "./glyphs";
import type { ActionOption, JournalRow } from "./types";

type ActorFilter = "all" | "agent" | "human";
type SourceFilter = "all" | Source;

const MAX_THRESHOLDS = 3;
const COLS = 9;
/** Câte rânduri se arată deodată: jurnalul unei zile are sute de decizii. */
const PAGE = 60;
const HUMAN_TINT = "bg-[color-mix(in_oklab,var(--ink)_4%,var(--panel))]";

/** Butoane lipite, ca alegerea zonei de pe hartă: unul singur apăsat. */
function Segmented<T extends string>({
  label,
  value,
  onChange,
  items,
}: {
  label: string;
  value: T;
  onChange: (v: T) => void;
  items: { id: T; label: ReactNode; count: number }[];
}) {
  return (
    <div role="group" aria-label={label} className="flex h-10 overflow-hidden rounded-[4px] border border-input bg-panel text-[15px]">
      {items.map((it) => {
        const on = it.id === value;
        return (
          <button
            key={it.id}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(it.id)}
            className={cn(
              "flex items-center gap-2 border-l border-rule px-3.5 whitespace-nowrap transition-colors duration-150 first:border-l-0",
              on ? "bg-ink font-[600] text-panel" : "font-[500] text-ink hover:bg-muted",
            )}
          >
            {it.label}
            <span className={cn("tabular-nums", on ? "text-panel/75" : "text-muted-foreground")}>{fmtInt(it.count)}</span>
          </button>
        );
      })}
    </div>
  );
}

function SourceDot({ source }: { source: Source }) {
  const meta = SOURCES[source];
  return (
    <span
      className="size-2.5 shrink-0 rounded-full"
      style={{ background: meta.color, boxShadow: meta.outline ? "inset 0 0 0 1px var(--ink)" : undefined }}
      aria-hidden="true"
    />
  );
}

/**
 * Filtrele și tabelul jurnalului. Datele vin gata făcute de pe server; aici doar se filtrează.
 * Rulările agentului apar ca rânduri-titlu deasupra deciziilor pe care le-au scris.
 */
export function JournalTable({ rows, options, scenario }: { rows: JournalRow[]; options: ActionOption[]; scenario: string }) {
  const [actor, setActorState] = useState<ActorFilter>("all");
  const [source, setSourceState] = useState<SourceFilter>("all");
  const [action, setActionState] = useState("all");
  const [query, setQueryState] = useState("");
  const [limit, setLimit] = useState(PAGE);
  const [open, setOpen] = useState<ReadonlySet<string>>(() => new Set());
  const q = useDeferredValue(query).trim().toUpperCase();

  // Orice filtru nou pornește iar de la primele rânduri.
  const setActor = (v: ActorFilter) => {
    setActorState(v);
    setLimit(PAGE);
  };
  const setSource = (v: SourceFilter) => {
    setSourceState(v);
    setLimit(PAGE);
  };
  const setAction = (v: string) => {
    setActionState(v);
    setLimit(PAGE);
  };
  const setQuery = (v: string) => {
    setQueryState(v);
    setLimit(PAGE);
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
  };
  const toggle = (id: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const actionLabel = options.find((o) => o.action === action)?.label;
  const th = "sticky top-0 z-[1] border-b border-rule bg-panel px-3 py-2.5 text-left align-bottom text-[14px] font-[560] text-muted-foreground";

  return (
    <section aria-label="Deciziile din jurnal" className="bg-panel">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-rule px-7 py-3.5">
        <Segmented<ActorFilter>
          label="Cine a decis"
          value={actor}
          onChange={setActor}
          items={[
            { id: "all", label: "Toți", count: decisions.length },
            {
              id: "agent",
              label: (
                <>
                  <AgentGlyph /> Agentul
                </>
              ),
              count: decisions.filter((r) => r.actor === "agent").length,
            },
            {
              id: "human",
              label: (
                <>
                  <HumanGlyph /> Omul
                </>
              ),
              count: decisions.filter((r) => r.actor === "human").length,
            },
          ]}
        />
        <Segmented<SourceFilter>
          label="Sursa lucrării"
          value={source}
          onChange={setSource}
          items={[
            { id: "all", label: "Toate", count: decisions.length },
            ...SOURCE_ORDER.map((s) => ({
              id: s,
              label: (
                <>
                  <SourceDot source={s} />
                  {s} {SOURCES[s].name}
                </>
              ),
              count: decisions.filter((r) => r.source === s).length,
            })),
          ]}
        />
        <Select value={action} onValueChange={setAction}>
          <SelectTrigger
            aria-label="Tipul deciziei"
            className="h-10 min-w-[232px] gap-2 rounded-[4px] border-input bg-panel px-3 text-[15px] font-[520]"
          >
            <span className="text-muted-foreground">Decizia</span>
            <SelectValue className="flex-1 text-left">{action === "all" ? "Toate" : (actionLabel ?? action)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all" className="text-[15px]">
              Toate
            </SelectItem>
            {options.map((o) => (
              <SelectItem key={o.action} value={o.action} className="text-[15px]">
                {o.label}
                <span className="ml-1 text-muted-foreground tabular-nums">{fmtInt(o.count)}</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <label className="relative flex items-center">
          <span className="sr-only">Caută după ID-ul lucrării</span>
          <SearchIcon className="pointer-events-none absolute left-3 size-[18px] text-muted-foreground" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Caută după ID-ul lucrării"
            spellCheck={false}
            autoComplete="off"
            className="h-10 w-[320px] rounded-[4px] border border-input bg-panel pr-3 pl-10 text-[15px] placeholder:text-muted-foreground"
          />
        </label>
        <span className="flex-1" />
        <span className="text-[15px] text-muted-foreground tabular-nums" aria-live="polite">
          {active ? `${fmtInt(shown)} din ${plural(decisions.length, "decizie", "decizii")}` : plural(decisions.length, "decizie", "decizii")}
        </span>
        {active ? (
          <Button variant="ghost" size="panel" className="-mr-3 rounded-[4px] px-3 underline decoration-rule underline-offset-4" onClick={reset}>
            Șterge filtrele
          </Button>
        ) : null}
      </div>

      <table className="w-full table-fixed border-separate border-spacing-0 text-[15px]">
        <caption className="sr-only">Jurnalul deciziilor, cele mai noi primele</caption>
        <colgroup>
          <col className="w-[100px]" />
          <col className="w-[104px]" />
          <col className="w-[184px]" />
          <col className="w-[312px]" />
          <col className="w-[244px]" />
          <col className="w-[292px]" />
          <col className="w-[224px]" />
          <col />
          <col className="w-[76px]" />
        </colgroup>
        <thead>
          <tr>
            <th scope="col" className={cn(th, "pl-7")}>
              Ora
            </th>
            <th scope="col" className={th}>
              Cine
            </th>
            <th scope="col" className={th}>
              Decizia
            </th>
            <th scope="col" className={th}>
              Lucrarea
            </th>
            <th scope="col" className={th}>
              Regula
            </th>
            <th scope="col" className={th}>
              Pragurile
            </th>
            <th scope="col" className={th}>
              Urmărirea până la model
            </th>
            <th scope="col" className={th}>
              Motivul sau nota
            </th>
            <th scope="col" className={cn(th, "pr-7")}>
              <span className="sr-only">Tot rândul</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan={COLS} className="px-7 py-14 text-center">
                <p className="text-[17px] font-[600]">Niciun rând nu se potrivește cu filtrele alese.</p>
                <p className="mt-1 text-[15px] text-muted-foreground">Schimbă un filtru sau arată din nou tot jurnalul.</p>
                <Button variant="outline" size="panel" className="mt-4" onClick={reset}>
                  Arată tot jurnalul
                </Button>
              </td>
            </tr>
          ) : (
            visible.map((r) =>
              r.kind === "run" ? (
                <RunRow key={r.id} r={r} />
              ) : (
                <DecisionRow key={r.id} r={r} scenario={scenario} expanded={open.has(r.id)} onToggle={() => toggle(r.id)} />
              ),
            )
          )}
        </tbody>
      </table>
      {hidden > 0 ? (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-rule px-7 py-4">
          <span className="text-[15px] text-muted-foreground">
            Se văd primele {plural(visible.length, "rând", "rânduri")} din {fmtInt(filtered.length)}, cele mai noi.
          </span>
          <Button variant="outline" size="panel" className="rounded-[4px] border-input bg-panel" onClick={() => setLimit((n) => n + PAGE)}>
            Arată încă {fmtInt(Math.min(PAGE, hidden))}
          </Button>
          <Button variant="ghost" size="panel" className="rounded-[4px]" onClick={() => setLimit(filtered.length)}>
            Arată toate cele {fmtInt(filtered.length)}
          </Button>
        </div>
      ) : null}
    </section>
  );
}

function RunRow({ r }: { r: JournalRow }) {
  return (
    <tr>
      <td colSpan={COLS} className="border-b border-rule bg-canvas px-7 py-2.5">
        <div className="flex min-w-0 items-center gap-3 text-[15px]">
          <AgentGlyph />
          <span className="shrink-0 font-[620]">
            {r.action === "replan" ? "Agentul a refăcut planul după decizia omului" : "Agentul a făcut planul"}
          </span>
          <time dateTime={r.ts} className="shrink-0 text-muted-foreground">
            {r.moment}
          </time>
          {r.decisions ? (
            <>
              <span className="h-4 w-px shrink-0 bg-rule" aria-hidden="true" />
              <span className="shrink-0 text-muted-foreground">{plural(r.decisions, "decizie", "decizii")}</span>
            </>
          ) : null}
          {r.note ? (
            <span className="dense ml-auto min-w-0 truncate pl-6 text-[13.5px] text-muted-foreground" title={r.note}>
              {r.note}
            </span>
          ) : null}
        </div>
      </td>
    </tr>
  );
}

function DecisionRow({
  r,
  scenario,
  expanded,
  onToggle,
}: {
  r: JournalRow;
  scenario: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  const human = r.actor === "human";
  const href = r.workItemId ? `/lucrari/${encodeURIComponent(r.workItemId)}?scenariu=${encodeURIComponent(scenario)}` : null;
  // Cel mult trei rânduri în celulă: trei praguri, sau două și „+N praguri”.
  const shown = r.thresholds.length > MAX_THRESHOLDS ? r.thresholds.slice(0, MAX_THRESHOLDS - 1) : r.thresholds;
  const extra = r.thresholds.length - shown.length;
  const detailId = `jurnal-${r.id}`;
  const td = cn("px-3 py-3 align-top", expanded ? "border-b-0" : "border-b border-rule");
  const what = r.workItemId ?? r.actionLabel;

  return (
    <>
      <tr className={cn(human && HUMAN_TINT)}>
        <td className={cn(td, "pl-7", human && "shadow-[inset_3px_0_0_var(--ink)]")}>
          <time dateTime={r.ts} title={r.moment} className="num-tall text-[18px]">
            {r.time}
          </time>
        </td>
        <td className={td}>
          <span className={cn("flex items-center gap-2", human ? "font-[640] text-ink" : "text-muted-foreground")}>
            {human ? <HumanGlyph /> : <AgentGlyph />}
            {human ? "Om" : "Agent"}
          </span>
        </td>
        <td className={td}>
          <span className={cn("inline-flex items-center gap-2 font-[580]", r.attention && "text-att-ink")}>
            {r.attention ? <span className="size-2 shrink-0 rounded-full bg-att" aria-hidden="true" /> : null}
            {r.actionLabel}
          </span>
        </td>
        <td className={td}>
          {r.workItemId && href ? (
            <div className="flex items-start gap-2.5">
              {r.source ? (
                <span
                  className="-mt-[5px] block size-8 shrink-0"
                  dangerouslySetInnerHTML={{ __html: markerSvg({ source: r.source, kind: r.marker }, 32) }}
                />
              ) : null}
              <div className="min-w-0">
                <Link href={href} className="code-id text-[15px] break-all underline decoration-rule underline-offset-4 hover:decoration-ink">
                  {r.workItemId}
                </Link>
                {r.itemTitle ? (
                  <p className="truncate text-[13.5px] leading-snug text-muted-foreground" title={r.itemTitle}>
                    {r.itemTitle}
                  </p>
                ) : null}
              </div>
            </div>
          ) : (
            <span className="text-muted-foreground">–</span>
          )}
        </td>
        <td className={td}>
          {r.ruleId ? (
            <>
              <span className="code-id text-[15px] break-all">{r.ruleId}</span>
              {r.ruleText ? <p className="text-[13.5px] leading-snug text-muted-foreground">{r.ruleText}</p> : null}
            </>
          ) : (
            <span className="text-muted-foreground">–</span>
          )}
        </td>
        <td className={td}>
          {shown.length ? (
            <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-0.5 text-[14px] leading-snug">
              {shown.map((t) => (
                <Fragment key={t.key}>
                  <dt className="truncate text-muted-foreground" title={`${t.label} (${t.key})`}>
                    {t.label}
                  </dt>
                  <dd className="text-right font-[560] whitespace-nowrap tabular-nums">{t.value}</dd>
                </Fragment>
              ))}
            </dl>
          ) : (
            <span className="text-[14px] text-muted-foreground">fără praguri</span>
          )}
          {extra > 0 ? (
            <button
              type="button"
              onClick={onToggle}
              aria-expanded={expanded}
              aria-controls={detailId}
              className="mt-1 text-[14px] font-[560] text-muted-foreground underline decoration-rule underline-offset-4 hover:text-ink hover:decoration-ink"
            >
              {expanded ? "mai puține" : `+${plural(extra, "prag", "praguri")}`}
            </button>
          ) : null}
        </td>
        <td className={td}>
          <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-2.5 gap-y-0.5 text-[14px] leading-snug">
            <dt className="text-muted-foreground">predicția</dt>
            <dd className="dense truncate font-[560]" title={r.predictionId ?? undefined}>
              {r.predictionId ? `${r.predictionId.slice(0, 8)}…` : "–"}
            </dd>
            <dt className="text-muted-foreground">modelul</dt>
            <dd className="dense truncate font-[560]" title={r.modelVersion ?? undefined}>
              {r.modelVersion ?? "–"}
            </dd>
            {r.inputsSha ? (
              <>
                <dt className="text-muted-foreground">intrările</dt>
                <dd className="dense truncate font-[560]" title={`Amprenta SHA-256 a datelor de intrare: ${r.inputsSha}`}>
                  {r.inputsSha.slice(0, 8)}…
                </dd>
              </>
            ) : null}
          </dl>
        </td>
        <td className={td}>
          {human ? (
            <p className="text-[15px] leading-snug">
              <b className="font-[640]">{r.reviewer ?? "Dispecerul"}</b>
              {r.note ? <>: „{r.note}”</> : <span className="text-muted-foreground">, fără notă</span>}
            </p>
          ) : r.note ? (
            <p className="line-clamp-2 text-[14px] leading-snug text-muted-foreground">{r.note}</p>
          ) : (
            <span className="text-muted-foreground">–</span>
          )}
        </td>
        <td className={cn(td, "pr-7 text-right")}>
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={expanded}
            aria-controls={detailId}
            aria-label={expanded ? `Ascunde detaliile pentru ${what}` : `Arată tot rândul pentru ${what}`}
            className="-mt-1.5 inline-grid size-9 place-items-center rounded-[4px] border border-transparent text-muted-foreground transition-colors duration-150 hover:border-rule hover:text-ink"
          >
            <ChevronDownIcon className={cn("size-5 transition-transform duration-150", expanded && "rotate-180")} aria-hidden="true" />
          </button>
        </td>
      </tr>
      {expanded ? (
        <tr id={detailId} className={cn(human && HUMAN_TINT)}>
          <td colSpan={COLS} className={cn("border-b border-rule px-7 pt-0 pb-5", human && "shadow-[inset_3px_0_0_var(--ink)]")}>
            <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.25fr)] gap-x-10 border-t border-dashed border-rule pt-3.5">
              <section>
                <h3 className="text-[15px] font-[620]">Toate pragurile</h3>
                {r.thresholds.length ? (
                  <dl className="mt-1.5 grid grid-cols-[minmax(0,1fr)_auto] gap-x-6 text-[14.5px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-1 [&>dd]:text-right [&>dd]:font-[560] [&>dd]:tabular-nums [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-1 [&>dt]:text-muted-foreground">
                    {r.thresholds.map((t) => (
                      <Fragment key={t.key}>
                        <dt title={t.key}>{t.label}</dt>
                        <dd>{t.value}</dd>
                      </Fragment>
                    ))}
                  </dl>
                ) : (
                  <p className="mt-1.5 text-[14.5px] text-muted-foreground">Regula n-a folosit praguri numerice.</p>
                )}
              </section>
              <section>
                <h3 className="text-[15px] font-[620]">Urmărirea completă</h3>
                <dl className="mt-1.5 grid grid-cols-[132px_minmax(0,1fr)] gap-x-4 text-[14.5px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-1 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-1 [&>dt]:text-muted-foreground">
                  <dt>ID decizie</dt>
                  <dd className="dense font-[560] break-all">{r.id}</dd>
                  <dt>ID predicție</dt>
                  <dd className="dense font-[560] break-all">{r.predictionId ?? "–"}</dd>
                  <dt>Versiunea modelului</dt>
                  <dd className="dense font-[560] break-all">{r.modelVersion ?? "–"}</dd>
                  <dt>Amprenta intrărilor</dt>
                  <dd className="dense font-[560] break-all">{r.inputsSha ?? "–"}</dd>
                  <dt>Momentul</dt>
                  <dd>{r.moment}</dd>
                </dl>
              </section>
              <section>
                <h3 className="text-[15px] font-[620]">{human ? "Nota omului" : "Motivul agentului"}</h3>
                <p className="mt-1.5 max-w-[72ch] text-[15.5px] leading-relaxed">
                  {human ? (
                    <>
                      <b className="font-[640]">{r.reviewer ?? "Dispecerul"}</b>
                      {r.note ? `: „${r.note}”` : ", fără notă."}
                    </>
                  ) : (
                    (r.note ?? "Agentul n-a scris un motiv pentru această decizie.")
                  )}
                </p>
                {href ? (
                  <Link
                    href={href}
                    className="mt-2.5 inline-block text-[15px] font-[600] underline decoration-rule underline-offset-4 hover:decoration-ink"
                  >
                    Deschide lucrarea {r.workItemId}
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
