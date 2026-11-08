import { cn } from "cn";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { fmtDec, fmtInt, fmtLei, fmtMoment, fmtSeconds, plural } from "@/lib/format";
import { CopyCommand } from "./copy-command";
import { englishReportText } from "./report-english";
import { fmtTick, niceAxis } from "./metric-labels";

/**
 * Agentul față de strategii simple, din reports/planner/agent_eval.json (GET /metrics → planner).
 * Forma e liberă: citim doar ce există și sărim peste ce lipsește.
 */

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj | null => (v && typeof v === "object" && !Array.isArray(v) ? (v as Obj) : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const str = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v.trim() : null);

const STRATEGY_RO: Record<string, { name: string; how: string }> = {
  agent: { name: "Agent", how: "models, cost rules and OR-Tools routes" },
  top_k_scor: { name: "Top K by score", how: "crews assigned by score, without costs" },
  primul_venit: { name: "First come, first served", how: "work arrival order" },
  aleator: { name: "Random", how: "lower reference" },
  doar_contoare: { name: "Meters only", how: "ignores storm and voltage work" },
};

function strategyName(key: string): string {
  return STRATEGY_RO[key]?.name ?? key.replaceAll("_", " ").replace(/^./, (c) => c.toLocaleUpperCase("en-GB"));
}

/** Numele strategiei în mijlocul frazei: doar prima literă devine mică („primele K după scor”). */
function strategyInline(key: string): string {
  const n = strategyName(key);
  return n.charAt(0).toLocaleLowerCase("en-GB") + n.slice(1);
}

/** Cuvintele scrise numai cu majuscule (de exemplu „SINTETICĂ”) devin litere mici: fără strigăt pe ecran. */
function calm(text: string): string {
  return text.replace(/(?<!\p{L})\p{Lu}{4,}(?!\p{L})/gu, (w) => w.toLocaleLowerCase("en-GB"));
}

interface Strategy {
  key: string;
  s: Obj;
  net: number;
}

function strategiesOf(block: Obj | null): Strategy[] {
  const all = obj(block?.strategies);
  if (!all) return [];
  return Object.entries(all)
    .map(([key, v]) => ({ key, s: obj(v) ?? {}, net: num(obj(v)?.net_value_lei_per_day) ?? NaN }))
    .filter((x) => Number.isFinite(x.net))
    .sort((a, b) => b.net - a.net);
}

const LABEL_COL = 268;

function NetChart({ rows, days }: { rows: Strategy[]; days: number | null }) {
  const max = Math.max(...rows.map((r) => r.net), 0);
  const min = Math.min(...rows.map((r) => r.net), 0);
  // loc la capătul barei pentru valoare: axa merge cu ~25% peste cea mai mare bară
  const axis = niceAxis(max * 1.25, 5);
  const pct = (v: number) => `${(Math.max(0, Math.min(1, v / axis.max)) * 100).toFixed(2)}%`;
  const agent = rows.find((r) => r.key === "agent");
  const grid = { gridTemplateColumns: `${LABEL_COL}px minmax(0,1fr)` };
  const plot = { left: LABEL_COL + 16, right: 0 };

  return (
    <figure aria-labelledby="net-title">
      <figcaption>
        <h3 id="net-title" className="text-[17px] font-[650]">
          Net gain per day
        </h3>
        <p className="mt-0.5 text-[14.5px] text-muted-foreground">
          Recovered value minus costs, in lei per day{days ? `, mean over ${plural(days, "day", "days")}` : ""}. Hover over a bar for details.
        </p>
      </figcaption>
      <div className="relative mt-3">
        <div className="pointer-events-none absolute inset-y-0" style={plot} aria-hidden="true">
          {axis.ticks.map((t) => (
            <span key={t} className="absolute inset-y-0 w-px bg-grid" style={{ left: pct(t) }} />
          ))}
        </div>
        <ul className="relative">
          {rows.map((r) => {
            const isAgent = r.key === "agent";
            const std = num(r.s.net_value_lei_per_day_std);
            const gap = agent && !isAgent ? agent.net - r.net : null;
            const how = STRATEGY_RO[r.key]?.how;
            return (
              <li
                key={r.key}
                tabIndex={0}
                className="group relative grid items-center gap-x-4 rounded-[4px] py-[7px] outline-none focus-visible:ring-2 focus-visible:ring-ink"
                style={grid}
                aria-label={`${strategyName(r.key)}: ${fmtLei(r.net)} per day${gap != null ? `; the agent recovers ${fmtLei(gap)} more per day` : ""}`}
              >
                <span className="min-w-0">
                  <span className={cn("block truncate text-[15.5px] leading-tight", isAgent ? "font-[680]" : "font-[480]")}>{strategyName(r.key)}</span>
                  {how ? <span className="block truncate text-[13px] text-muted-foreground">{how}</span> : null}
                </span>
                <span className="relative h-[22px]">
                  <i
                    className="absolute inset-y-0 left-0 rounded-r-[4px] transition-opacity duration-150 group-hover:opacity-85"
                    style={{ width: pct(r.net), background: isAgent ? "var(--ink)" : "var(--idle)" }}
                    aria-hidden="true"
                  />
                  <span
                    className={cn("absolute top-1/2 -translate-y-1/2 pl-2 text-[16px] whitespace-nowrap tabular-nums", isAgent ? "font-[700]" : "font-[500]")}
                    style={{ left: pct(r.net) }}
                  >
                    {fmtLei(r.net)}
                  </span>
                </span>
                {/* detaliul la trecerea cu mouse-ul sau la focus */}
                <span
                  role="presentation"
                  className="pointer-events-none absolute top-full z-20 mt-1 hidden w-[340px] rounded-[4px] border border-rule bg-popover px-3 py-2 text-[13.5px] shadow-[0_6px_18px_-8px_rgb(19_32_42/0.35)] group-hover:block group-focus-visible:block"
                  style={{ left: LABEL_COL + 16 }}
                >
                  <span className="mb-1 block font-[600]">{strategyName(r.key)}</span>
                  <span className="flex justify-between gap-6">
                    <span className="text-muted-foreground">Net gain per day</span>
                    <span className="font-[560] tabular-nums">{fmtLei(r.net)}</span>
                  </span>
                  {std != null ? (
                    <span className="flex justify-between gap-6">
                      <span className="text-muted-foreground">Variation between days</span>
                      <span className="font-[560] tabular-nums">±{fmtLei(std)}</span>
                    </span>
                  ) : null}
                  {gap != null ? (
                    <span className="flex justify-between gap-6">
                      <span className="text-muted-foreground">Additional agent gain</span>
                      <span className="font-[560] tabular-nums">
                        {fmtLei(gap)} per day{r.net > 0 ? ` (+${fmtDec((gap / r.net) * 100, 0)}%)` : ""}
                      </span>
                    </span>
                  ) : null}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
      <div className="grid gap-x-4" style={grid} aria-hidden="true">
        <span />
        <span className="relative h-5 text-[13px] text-muted-foreground tabular-nums">
          {axis.ticks.map((t, i) => (
            <span
              key={t}
              className={cn("absolute top-1 whitespace-nowrap", i === 0 ? "" : i === axis.ticks.length - 1 ? "-translate-x-full" : "-translate-x-1/2")}
              style={{ left: pct(t) }}
            >
              {fmtTick(t)}
            </span>
          ))}
        </span>
      </div>
      <p className="mt-1 text-right text-[13px] text-muted-foreground">lei per day</p>
      {min < 0 ? <p className="mt-1 text-[13.5px] text-muted-foreground">Some strategies lose money on average; their bars are hidden.</p> : null}
    </figure>
  );
}

interface Kpi {
  key: string;
  of?: string;
  label: string;
  fmt: (v: number) => string;
}

const KPIS: Kpi[] = [
  { key: "value_captured_lei_total", label: "Value recovered", fmt: (v) => fmtLei(v) },
  { key: "costs_lei_total", label: "Costs", fmt: (v) => fmtLei(v) },
  { key: "km_per_day", label: "Km per day", fmt: (v) => fmtInt(v) },
  { key: "urgent_missed_total", of: "urgent_total", label: "Missed urgent cases", fmt: (v) => fmtInt(v) },
  { key: "useless_visits_total", of: "visits_total", label: "Unnecessary visits", fmt: (v) => fmtInt(v) },
  { key: "storms_covered_total", of: "storms_true_total", label: "Storms covered", fmt: (v) => fmtInt(v) },
  { key: "human_review_total", label: "Sent for human review", fmt: (v) => fmtInt(v) },
];

function KpiTable({ rows, days }: { rows: Strategy[]; days: number | null }) {
  const cols = KPIS.filter((k) => rows.some((r) => num(r.s[k.key]) != null));
  if (!cols.length) return null;
  return (
    <div className="min-w-0">
      <h3 className="text-[17px] font-[650]">Strategy comparison</h3>
      <p className="mt-0.5 text-[14.5px] text-muted-foreground">
        Totals across {days ? plural(days, "day", "days") : "the full simulation"}; km per day is an average. &quot;Of&quot; shows the total available cases.
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full border-collapse text-[15px]">
          <thead>
            <tr className="text-[13.5px] text-muted-foreground">
              <th scope="col" className="py-1.5 pr-3 text-left font-[500]">
                Strategy
              </th>
              {cols.map((c) => (
                <th key={c.key} scope="col" className={cn("px-2 py-1.5 text-right font-[500]", c.label.length <= 10 && "whitespace-nowrap")}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const isAgent = r.key === "agent";
              return (
                <tr key={r.key} className={cn("border-t border-rule", isAgent && "bg-panel")}>
                  <th scope="row" className={cn("py-2 pr-3 text-left whitespace-nowrap", isAgent ? "font-[680]" : "font-[450]")}>
                    {strategyName(r.key)}
                  </th>
                  {cols.map((c) => {
                    const v = num(r.s[c.key]);
                    const of = c.of ? num(r.s[c.of]) : null;
                    return (
                      <td key={c.key} className={cn("px-2 py-2 text-right whitespace-nowrap tabular-nums", isAgent && "font-[620]")}>
                        {v == null ? "–" : c.fmt(v)}
                        {v != null && of != null ? <span className="font-[400] text-muted-foreground"> of {fmtInt(of)}</span> : null}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const PARAM_RO: Record<string, string> = {
  cost_per_customer_hour_lei: "Cost of one hour without power, per customer",
  preposition_cost_lei_per_crew_shift: "Cost of pre-positioning a crew, per shift",
  inspection_visit_cost_lei: "Cost of an inspection visit",
};

function Robustness({ planner, main }: { planner: Obj; main: Strategy[] }) {
  const over = obj(planner.robustness_overconfident_model);
  const overRows = strategiesOf(over);
  const overAgent = overRows.find((r) => r.key === "agent");
  const overBest = overRows.find((r) => r.key !== "agent");
  const sens = Array.isArray(planner.sensitivity) ? planner.sensitivity.map(obj).filter((x): x is Obj => x !== null) : [];
  const abl = Object.entries(obj(planner.ablations) ?? {})
    .map(([key, v]) => ({ key, a: obj(v) }))
    .filter((x): x is { key: string; a: Obj } => x.a !== null && num(x.a.net_value_lei_per_day) != null);
  const agent = main.find((r) => r.key === "agent");
  if (!(overAgent && overBest) && !sens.length && !abl.length) return null;

  return (
    <div className="mt-8 grid grid-cols-1 gap-x-10 gap-y-6 border-t border-rule pt-5 xl:grid-cols-3">
      {overAgent && overBest ? (
        <section aria-labelledby="rob-over">
          <h3 id="rob-over" className="text-[17px] font-[650]">
            Overconfident models
          </h3>
          <p className="mt-1 text-[15px] leading-relaxed">
            Scores increased{num(over?.miscalibration) ? ` by ${fmtDec(num(over?.miscalibration) ?? 1, 1)} times` : ""}
            {num(over?.days) ? `, over ${plural(num(over?.days) ?? 0, "day", "days")} new` : ""}. The agent recovers {fmtLei(overAgent.net)} per day, and the best simple strategy ({strategyInline(overBest.key)}) {fmtLei(overBest.net)}.
          </p>
          {overBest.net > 0 ? (
            <p className="mt-1.5 text-[15px] font-[620]">Agent lead {fmtDec(((overAgent.net - overBest.net) / overBest.net) * 100, 0)}%.</p>
          ) : null}
        </section>
      ) : null}

      {sens.length ? (
        <section aria-labelledby="rob-sens">
          <h3 id="rob-sens" className="text-[17px] font-[650]">
            Cost assumptions
          </h3>
          <p className="mt-1 text-[15px]">Agent advantage over top K by score when changing one cost assumption:</p>
          <table className="mt-2 w-full border-collapse text-[14.5px]">
            <tbody>
              {sens.map((s, i) => {
                const p = str(s.parameter) ?? "";
                const v = num(s.value);
                const adv = num(s.agent_advantage_pct);
                return (
                  <tr key={i} className="border-t border-rule">
                    <th scope="row" className="py-1.5 pr-3 text-left font-[450]">
                      {PARAM_RO[p] ?? p.replaceAll("_", " ")}
                      {v != null ? <span className="text-muted-foreground">: {p.endsWith("_lei") || p.includes("_lei_") ? fmtLei(v) : fmtDec(v, 1)}</span> : null}
                    </th>
                    <td className="py-1.5 text-right font-[620] whitespace-nowrap tabular-nums">{adv != null ? `+${fmtDec(adv, 0)}%` : "–"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      ) : null}

      {abl.length ? (
        <section aria-labelledby="rob-abl">
          <h3 id="rob-abl" className="text-[17px] font-[650]">
            Removing an agent component
          </h3>
          <ul className="mt-1">
            {abl.map(({ key, a }) => {
              const net = num(a.net_value_lei_per_day) ?? 0;
              const d = agent ? net - agent.net : null;
              const useless = num(a.useless_visits_total);
              const agentUseless = agent ? num(agent.s.useless_visits_total) : null;
              return (
                <li key={key} className="border-t border-rule py-2 first:border-t-0">
                  <span className="block text-[15px]">{englishReportText(str(a.label_ro) ?? key.replaceAll("_", " "))}</span>
                  <span className="block text-[14.5px] text-muted-foreground tabular-nums">
                    {fmtLei(net)} per day
                    {d != null ? ` (${d >= 0 ? "by " + fmtLei(d) + " more" : "by " + fmtLei(-d) + " less"} than the agent)` : ""}
                    {useless != null && agentUseless != null ? `, unnecessary visits ${fmtInt(useless)} vs. ${fmtInt(agentUseless)}` : ""}
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

export function PlannerSection({ planner }: { planner: Record<string, unknown> | null }) {
  if (!planner) {
    return (
      <section aria-labelledby="planner-title" className="mt-12 border-t border-rule pt-6">
        <h2 id="planner-title" className="text-[24px] font-[650]">
          Agent vs. simple strategies
        </h2>
        <p className="mt-2 max-w-[80ch] text-[15.5px] text-muted-foreground">
          Agent evaluation not published yet (<span className="dense">reports/planner/agent_eval.json</span>). Compares strategies in a synthetic world with known outcomes.
        </p>
        <div className="mt-3 max-w-[640px]">
          <CopyCommand cmd="uv run python -m cyberpunks.planner.evaluate" />
        </div>
      </section>
    );
  }

  const main = obj(planner.main);
  const rows = strategiesOf(main);
  const days = num(main?.days);
  const meters = num(main?.n_meters_per_day);
  const seed = num(main?.seed);
  const agent = rows.find((r) => r.key === "agent");
  const best = rows.find((r) => r.key !== "agent");
  const description = (() => {
    const d = str(planner.description) ? englishReportText(str(planner.description)!) : null;
    if (!d) return null;
    const rest = calm(d).replace(/^Agentul față de strategii simple,?\s*/i, "");
    return rest ? rest.charAt(0).toLocaleUpperCase("en-GB") + rest.slice(1) : null;
  })();
  const cmd = str(planner.reproduce_cmd);
  const version = str(planner.planner_version);
  const created = str(planner.created_at);
  const runtime = num(planner.runtime_s);
  const synthetic = planner.synthetic !== false;

  return (
    <section aria-labelledby="planner-title" className="mt-12 border-t border-rule pt-6">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
        <h2 id="planner-title" className="text-[24px] font-[650]">
          Agent vs. simple strategies
        </h2>
        {synthetic ? (
          <span className="flex h-10 items-center gap-2.5 rounded-[4px] border border-ink px-3 text-[15px] font-[560]">
            <SyntheticGlyph />
            Synthetic simulation with known outcomes
          </span>
        ) : null}
      </div>
      <p className="mt-2 max-w-[100ch] text-[15.5px] leading-relaxed">
        {description ? `${description} ` : ""}
        Each strategy&apos;s hits and misses can be counted directly
        {days ? `: ${plural(days, "day", "days")}` : ""}
        {meters ? `, ${fmtInt(meters)} meters per day` : ""}
        {seed != null ? `, seed ${fmtInt(seed)}` : ""}.
      </p>
      {agent && best && best.net > 0 ? (
        <p className="mt-3 text-[20px] leading-snug font-[650]">
          The agent gains {fmtDec(((agent.net - best.net) / best.net) * 100, 0)}% more per day than the best simple strategy (
          {strategyInline(best.key)}).
        </p>
      ) : null}

      {rows.length ? (
        <div className="mt-6 grid grid-cols-1 gap-x-12 gap-y-8 2xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
          <NetChart rows={rows} days={days} />
          <KpiTable rows={rows} days={days} />
        </div>
      ) : (
        <p className="mt-4 text-[15px] text-muted-foreground">Strategy comparison missing from the report (main.strategies).</p>
      )}

      <Robustness planner={planner} main={rows} />

      <div className="mt-8 grid grid-cols-1 items-end gap-x-10 gap-y-3 border-t border-rule pt-5 xl:grid-cols-[minmax(0,720px)_minmax(0,1fr)]">
        {cmd ? (
          <div>
            <h3 className="text-[16px] font-[650]">Reproduce results</h3>
            <div className="mt-1.5">
              <CopyCommand cmd={cmd} />
            </div>
          </div>
        ) : null}
        <p className="text-[14px] text-muted-foreground empty:hidden">
          {[
            version ? `Planner ${version}` : null,
            created ? `evaluated ${fmtMoment(created)}` : null,
            runtime != null ? `run duration ${fmtSeconds(runtime)}` : null,
          ]
            .filter(Boolean)
            .join(", ")
            .replace(/^(.+)$/, (t) => `${t.charAt(0).toLocaleUpperCase("en-GB")}${t.slice(1)}.`)}
        </p>
      </div>
    </section>
  );
}
