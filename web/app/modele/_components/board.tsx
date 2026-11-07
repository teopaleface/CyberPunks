import {
  ActivityIcon,
  BotIcon,
  ChartColumnIcon,
  FileSearchIcon,
  FlaskConicalIcon,
  Layers2Icon,
  TerminalIcon,
  TrendingUpIcon,
} from "lucide-react";
import { Card, Pill, TONE, type Tone } from "@/components/ds";
import { ChipGrid, type GridCard } from "@/components/misc/chip-grid";
import { SyntheticGlyph } from "@/components/shell/provenance";
import type { ModelReport, Source } from "@/lib/contracts";
import { fmtDec, fmtInt, fmtLei, plural } from "@/lib/format";
import { SOURCES, SOURCE_ORDER } from "@/lib/sources";
import { CopyCommand } from "./copy-command";
import { parseFirstSection } from "./error-analysis";
import { fmtMetric, metricMeta } from "./metric-labels";

const TONE_OF: Record<Source, Tone> = { A: "blue", B: "violet", C: "amber" };
const SOLID: Record<Source, string> = { A: "var(--src-a)", B: "var(--src-b)", C: "var(--src-c)" };

/** Procente pentru precizie și recall („62,5%”), formatul metricii pentru restul. */
function fmtVal(key: string, v: number): string {
  if (/precision|recall/.test(key)) {
    if (v >= 0.995) return "peste 99%";
    const p = Math.round(v * 1000) / 10;
    return `${Number.isInteger(p) ? fmtInt(p) : fmtDec(p, 1)}%`;
  }
  return fmtMetric(key, v);
}

interface Row {
  id: string;
  source: Source;
  key: string;
  label: string;
  model: number;
  base: number;
  better: "higher" | "lower";
}

/** Rândurile reale: metrica principală a fiecărui raport și, la A, precizia pe furturi reale (SGCC), cu valoarea baseline-ului. */
function rowsOf(bundle: Record<Source, ModelReport | null>): Row[] {
  const out: Row[] = [];
  for (const s of SOURCE_ORDER) {
    const r = bundle[s];
    if (!r) continue;
    const key = r.primary_metric;
    const m = r.metrics[key];
    const b = r.baseline_metrics[key];
    const meta = metricMeta(key);
    if (typeof m === "number" && typeof b === "number" && meta.better !== "none" && meta.better !== "target") {
      out.push({ id: `${s}-${key}`, source: s, key, label: meta.label, model: m, base: b, better: meta.better });
    }
    if (s === "A" && key !== "sgcc_precision_at_k") {
      const sm = r.metrics.sgcc_precision_at_k;
      const sb = r.baseline_metrics.sgcc_precision_at_k;
      if (typeof sm === "number" && typeof sb === "number") {
        out.push({ id: "A-sgcc", source: "A", key: "sgcc_precision_at_k", label: metricMeta("sgcc_precision_at_k").label, model: sm, base: sb, better: "higher" });
      }
    }
  }
  return out;
}

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj | null => (v && typeof v === "object" && !Array.isArray(v) ? (v as Obj) : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

interface Strat {
  key: string;
  s: Obj;
  net: number;
}

function strategies(planner: Obj | null): Strat[] {
  const all = obj(obj(planner?.main)?.strategies);
  if (!all) return [];
  return Object.entries(all)
    .map(([key, v]) => ({ key, s: obj(v) ?? {}, net: num(obj(v)?.net_value_lei_per_day) ?? NaN }))
    .filter((x) => Number.isFinite(x.net))
    .sort((a, b) => b.net - a.net);
}

const STRATEGY_NAME: Record<string, string> = {
  agent: "Agentul",
  top_k_scor: "primele K după scor",
  primul_venit: "primul venit, primul servit",
  aleator: "la întâmplare",
  doar_contoare: "doar contoare",
};
const strategyName = (k: string) => STRATEGY_NAME[k] ?? k.replaceAll("_", " ");

function SourcePill({ s, children }: { s: Source; children: React.ReactNode }) {
  return (
    <Pill tone={TONE_OF[s]} size="md" className="min-w-[64px] justify-center">
      {children}
    </Pill>
  );
}

function Pale({ children }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex min-w-[84px] justify-center rounded-full border border-[#2a3a52] bg-[#121e30] whitespace-nowrap px-2.5 py-1 text-[14px] text-ink-soft">{children ?? "—"}</span>
  );
}

function ValPill({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  const t = TONE[tone];
  return <span className={`inline-flex min-w-[84px] justify-center rounded-full border px-2.5 py-1 text-[14.5px] whitespace-nowrap font-[560] tabular-nums ${t.text} ${t.bg} ${t.border}`}>{children}</span>;
}

/** Perechea de bare model / baseline, pentru o metrică. */
function MiniBars({ row }: { row: Row }) {
  const max = Math.max(row.model, row.base) || 1;
  const bars = [
    { name: "Model", v: row.model, color: SOLID[row.source] },
    { name: "Reguli", v: row.base, color: "var(--idle)" },
  ];
  return (
    <figure className="min-w-0" aria-label={`${row.label}: model ${fmtVal(row.key, row.model)}, reguli simple ${fmtVal(row.key, row.base)}`}>
      <div className="flex h-[150px] items-end justify-center gap-4 border-b border-rule px-2">
        {bars.map((b) => (
          <div key={b.name} className="flex h-full w-[62px] flex-col justify-end text-center">
            <span className="mb-1 text-[13px] font-[600] whitespace-nowrap tabular-nums">{fmtVal(row.key, b.v)}</span>
            <i className="block rounded-t-[5px]" style={{ height: `${Math.max(3, (b.v / max) * 100 * 0.78)}%`, background: b.color }} aria-hidden="true" />
          </div>
        ))}
      </div>
      <div className="mt-1.5 flex justify-center gap-4 text-[12.5px] text-ink-soft">
        <span className="w-[62px] text-center">Model</span>
        <span className="w-[62px] text-center">Reguli</span>
      </div>
      <figcaption className="mt-2 text-center text-[13.5px] leading-snug">
        <b className="font-[620]" style={{ color: SOLID[row.source] }}>
          {row.source}
        </b>
        <span className="text-ink-soft"> · {row.better === "lower" ? "mai mic e mai bine" : "mai mare e mai bine"}</span>
      </figcaption>
    </figure>
  );
}

export function ModelsBoard({
  bundle,
  planner,
  analysisBy,
}: {
  bundle: Record<Source, ModelReport | null>;
  planner: Record<string, unknown> | null;
  analysisBy: Record<Source, string | null>;
}) {
  const rows = rowsOf(bundle);
  const strat = strategies(planner);
  const agent = strat.find((x) => x.key === "agent");
  const best = strat.find((x) => x.key !== "agent");
  const gainPct = agent && best && best.net > 0 ? ((agent.net - best.net) / best.net) * 100 : null;
  const days = num(obj(planner?.main)?.days);
  const synthetic = planner?.synthetic !== false;
  const cards: GridCard[] = [];
  const cardClass = "rounded-[18px]";

  // 1. Performanță
  if (rows.length) {
    cards.push({
      id: "performanta",
      tags: ["A", "B", "C", "reguli"],
      span: "lg:col-span-6",
      node: (
        <Card title="Performanță: modele vs. reguli simple" icon={Layers2Icon} className={cardClass}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] border-separate border-spacing-y-1.5 text-[15px]">
              <caption className="sr-only">Metrica principală a fiecărui model, față de regula simplă pe același test</caption>
              <thead>
                <tr>
                  <th scope="col" className="pr-3 pb-1 text-left text-[14.5px] font-[600]">
                    Metrica
                  </th>
                  {SOURCE_ORDER.map((s) => (
                    <th key={s} scope="col" className="px-1 pb-1 text-center">
                      <SourcePill s={s}>
                        <span translate="no">{s}</span>
                      </SourcePill>
                    </th>
                  ))}
                  <th scope="col" className="px-1 pb-1 text-center">
                    <Pill tone="grey" className="min-w-[64px] justify-center">
                      Reguli
                    </Pill>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <th scope="row" className="pr-3 text-left text-[14.5px] leading-snug font-[450]" title={r.key}>
                      {r.label}
                    </th>
                    {SOURCE_ORDER.map((s) => (
                      <td key={s} className="px-1 text-center">
                        {s === r.source ? <ValPill tone={TONE_OF[s]}>{fmtVal(r.key, r.model)}</ValPill> : <Pale />}
                      </td>
                    ))}
                    <td className="px-1 text-center">
                      <Pale>{fmtVal(r.key, r.base)}</Pale>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[13.5px] text-ink-soft">
            „Reguli” e baseline-ul simplu al modelului din rând (regula simplă sau media istorică), pe același set de test. Un „—” înseamnă că modelul nu are metrica.
          </p>
        </Card>
      ),
    });
  }

  // 2. Agentul: câștig net
  if (agent && best) {
    cards.push({
      id: "agent",
      tags: ["agent"],
      span: "lg:col-span-3",
      node: (
        <Card title="Agent: câștig net" icon={BotIcon} className={cardClass} bodyClassName="flex h-full flex-col px-5 pt-3 pb-5">
          {gainPct !== null ? (
            <p className="mt-2 text-center text-[44px] leading-none font-[750] tracking-[-0.03em] text-[#4be08a] tabular-nums">
              {gainPct >= 0 ? "+" : "−"}
              {fmtDec(Math.abs(gainPct), 0)}% <span className="text-[30px]">net/zi</span>
            </p>
          ) : null}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <span className="rounded-[12px] border border-[#1f8a4a] bg-[#0b2a18] px-4 py-2 text-[20px] font-[650] tabular-nums">{fmtLei(agent.net)}/zi</span>
            <span className="text-[14px] text-ink-soft">vs.</span>
            <span className="rounded-[12px] border border-[#2a3a52] px-4 py-2 text-[20px] font-[650] tabular-nums">{fmtLei(best.net)}/zi</span>
          </div>
          <p className="mt-4 text-center text-[14.5px] leading-snug text-ink-soft">
            Agentul față de cea mai bună strategie simplă ({strategyName(best.key)}).
          </p>
          <p className="mt-auto flex items-center justify-center gap-2 pt-3 text-center text-[14.5px] text-ink-soft">
            {synthetic ? <SyntheticGlyph size={14} /> : null}
            Simulare: {days ? plural(days, "zi", "zile") : "mai multe zile"}, {synthetic ? "lume sintetică" : "date reale"}
          </p>
        </Card>
      ),
    });
  } else {
    cards.push({
      id: "agent",
      tags: ["agent"],
      span: "lg:col-span-3",
      node: (
        <Card title="Agent: câștig net" icon={BotIcon} className={cardClass}>
          <p className="text-[15.5px] leading-relaxed text-ink-soft">
            Evaluarea agentului nu e publicată încă (<span translate="no">reports/planner/agent_eval.json</span>).
          </p>
        </Card>
      ),
    });
  }

  // 3. Scoruri rapide
  if (rows.length) {
    cards.push({
      id: "scoruri",
      tags: ["A", "B", "C"],
      span: "lg:col-span-3",
      node: (
        <Card title="Scoruri rapide" icon={TrendingUpIcon} className={cardClass}>
          <table className="w-full text-[15px]">
            <caption className="sr-only">Cifra principală a fiecărui model</caption>
            <thead>
              <tr className="text-left text-[14px] text-ink-soft">
                <th scope="col" className="border-b border-rule pb-2 font-[600] text-ink">
                  Model
                </th>
                <th scope="col" className="border-b border-rule pb-2 text-right font-[600] text-ink">
                  Valoare
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <th scope="row" className="border-b border-rule py-2 pr-2 text-left font-[450] last:border-b-0">
                    <span className="flex items-start gap-2.5">
                      <i className="mt-[7px] size-2.5 shrink-0 rounded-full" style={{ background: SOLID[r.source] }} aria-hidden="true" />
                      <span className="leading-snug">
                        <span translate="no">{r.source}</span>: {r.label}
                      </span>
                    </span>
                  </th>
                  <td className="border-b border-rule py-2 text-right">
                    <ValPill tone={TONE_OF[r.source]}>{fmtVal(r.key, r.model)}</ValPill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ),
    });
  }

  // 4. Comparație model vs. reguli
  if (rows.length) {
    cards.push({
      id: "comparatie",
      tags: ["A", "B", "C", "reguli"],
      span: "lg:col-span-5",
      node: (
        <Card title="Comparație: model vs. reguli simple" icon={ChartColumnIcon} className={cardClass}>
          <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4">
            {rows.map((r) => (
              <div key={r.id} className="flex min-w-0 flex-col">
                <MiniBars row={r} />
                <p className="mt-1 text-center text-[12.5px] leading-snug text-ink-soft">{r.label}</p>
              </div>
            ))}
          </div>
        </Card>
      ),
    });
  }

  // 5. Analiza erorilor
  const withAnalysis = SOURCE_ORDER.filter((s) => analysisBy[s]);
  cards.push({
    id: "erori",
    tags: ["erori", ...withAnalysis],
    span: "lg:col-span-7",
    node: (
      <Card title="Analiză erori" icon={FileSearchIcon} className={cardClass}>
        {withAnalysis.length ? (
          <div className="flex max-h-[430px] flex-col gap-6 overflow-y-auto pr-1" tabIndex={0} role="region" aria-label="Analiza erorilor, pe modele">
            {withAnalysis.map((s) => (
              <ErrorBlock key={s} source={s} md={analysisBy[s]!} />
            ))}
          </div>
        ) : (
          <p className="text-[15px] text-ink-soft">
            Nicio analiză a erorilor nu e publicată încă (<span translate="no">reports/&lt;A|B|C&gt;/error_analysis.md</span>).
          </p>
        )}
      </Card>
    ),
  });

  // 6. Simulare
  if (agent && best) {
    const bySrc = (s: Obj) => obj(s.value_by_source_lei);
    const av = bySrc(agent.s);
    const bv = bySrc(best.s);
    const total = (v: Obj | null) => (v ? Object.values(v).reduce<number>((t, x) => t + (num(x) ?? 0), 0) : null);
    const stat = (label: string, a: number | null, b: number | null, f: (n: number) => string) =>
      a !== null && b !== null ? { label, a: f(a), b: f(b) } : null;
    const lines = [
      stat("Câștig net pe zi", agent.net, best.net, (n) => fmtLei(n)),
      stat("Vizite degeaba", num(agent.s.useless_visits_total), num(best.s.useless_visits_total), fmtInt),
      stat("Urgențe ratate", num(agent.s.urgent_missed_total), num(best.s.urgent_missed_total), fmtInt),
      stat("Km pe zi", num(agent.s.km_per_day), num(best.s.km_per_day), fmtInt),
    ].filter((x): x is { label: string; a: string; b: string } => x !== null);
    cards.push({
      id: "simulare",
      tags: ["agent"],
      span: "lg:col-span-6",
      node: (
        <Card title={`Simulare: sumar pe ${days ? plural(days, "zi", "zile") : "mai multe zile"}`} icon={FlaskConicalIcon} className={cardClass}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px] border-separate border-spacing-y-1.5 text-[15px]">
              <caption className="sr-only">Agentul și cea mai bună strategie simplă, pe sursele de lucrări</caption>
              <thead>
                <tr>
                  <th scope="col" className="pr-3 pb-1 text-left text-[14.5px] font-[600]">
                    Valoare recuperată
                  </th>
                  {SOURCE_ORDER.map((s) => (
                    <th key={s} scope="col" className="px-1 pb-1 text-center">
                      <SourcePill s={s}>
                        <span translate="no">{s}</span>
                      </SourcePill>
                    </th>
                  ))}
                  <th scope="col" className="px-1 pb-1 text-center">
                    <Pill tone="grey" className="min-w-[64px] justify-center">
                      Total
                    </Pill>
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: "Agentul", v: av, bold: true },
                  { name: `Reguli: ${strategyName(best.key)}`, v: bv, bold: false },
                ].map((r) => (
                  <tr key={r.name}>
                    <th scope="row" className={`pr-3 text-left text-[14.5px] ${r.bold ? "font-[650]" : "font-[450]"}`}>
                      {r.name}
                    </th>
                    {SOURCE_ORDER.map((s) => {
                      const v = num(r.v?.[s]);
                      return (
                        <td key={s} className="px-1 text-center">
                          {v === null ? <Pale /> : <ValPill tone={TONE_OF[s]}>{fmtLei(v)}</ValPill>}
                        </td>
                      );
                    })}
                    <td className="px-1 text-center">{total(r.v) === null ? <Pale /> : <Pale>{fmtLei(total(r.v) ?? 0)}</Pale>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {lines.length ? (
            <dl className="mt-3 grid grid-cols-[minmax(0,1fr)_auto_auto] gap-x-5 text-[14.5px]">
              <dt className="sr-only">Indicator</dt>
              <dd className="sr-only">Agentul / regula simplă</dd>
              {lines.map((l) => (
                <div key={l.label} className="col-span-3 grid grid-cols-subgrid items-center border-t border-rule py-2">
                  <dt className="text-ink-soft">{l.label}</dt>
                  <dd className="font-[650] tabular-nums">{l.a}</dd>
                  <dd className="text-ink-soft tabular-nums">vs. {l.b}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          <p className="mt-2 flex items-center gap-2 text-[13.5px] text-ink-soft">
            {synthetic ? <SyntheticGlyph size={14} /> : null}
            {synthetic ? "Date sintetice: o lume simulată, cu adevărul cunoscut." : "Date reale."}
          </p>
        </Card>
      ),
    });
  }

  // 7. Reproducere
  const cmds: { id: string; tone: Tone | null; name: string; cmd: string }[] = SOURCE_ORDER.flatMap((s) => {
    const r = bundle[s];
    return r ? [{ id: s, tone: TONE_OF[s], name: `Model ${s}, ${SOURCES[s].name.toLowerCase()}`, cmd: r.reproduce_cmd }] : [];
  });
  const pcmd = typeof planner?.reproduce_cmd === "string" ? planner.reproduce_cmd : null;
  if (pcmd) cmds.push({ id: "planner", tone: null, name: "Agentul, simularea", cmd: pcmd });
  cards.push({
    id: "reproducere",
    tags: ["reproducere"],
    span: "lg:col-span-6",
    node: (
      <Card title="Reproducere: comenzi de confirmat" icon={TerminalIcon} className={cardClass}>
        {cmds.length ? (
          <ul className="flex flex-col gap-3">
            {cmds.map((c) => (
              <li key={c.id}>
                <p className="mb-1 flex items-center gap-2 text-[14.5px] font-[600]">
                  {c.tone ? <i className="size-2.5 rounded-full" style={{ background: SOLID[c.id as Source] }} aria-hidden="true" /> : <ActivityIcon size={14} aria-hidden="true" />}
                  {c.name}
                </p>
                <CopyCommand cmd={c.cmd} label={`Copiază comanda pentru ${c.name}`} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[15px] text-ink-soft">Niciun raport publicat încă, deci nicio comandă de arătat.</p>
        )}
        <p className="mt-3 text-[13.5px] text-ink-soft">Fiecare comandă refă cifrele raportului din care vine. Rulează-le tu, din rădăcina proiectului.</p>
      </Card>
    ),
  });

  return (
    <ChipGrid
      label="Filtrează cardurile"
      columns="lg:grid-cols-12"
      chips={[
        { id: "A", label: "Model A", tone: "blue" },
        { id: "B", label: "Model B", tone: "violet" },
        { id: "C", label: "Model C", tone: "amber" },
        { id: "reguli", label: "Reguli simple" },
        { id: "agent", label: "Agent" },
        { id: "erori", label: "Analiză erori" },
        { id: "reproducere", label: "Reproducere" },
      ]}
      cards={cards}
    />
  );
}

/** Prima secțiune din error_analysis.md, ca listă și tabel compact. */
function ErrorBlock({ source, md }: { source: Source; md: string }) {
  const parsed = parseFirstSection(md);
  const blocks = parsed.blocks.length ? parsed.blocks : parsed.intro;
  return (
    <section aria-label={`Modelul ${source}`}>
      <h3 className="flex flex-wrap items-center gap-2.5 text-[16px] font-[650]">
        <SourcePill s={source}>
          <span translate="no">{source}</span>
        </SourcePill>
        {SOURCES[source].name}
        {parsed.title ? <span className="font-[450] text-ink-soft">: {parsed.title.toLocaleLowerCase("ro-RO")}</span> : null}
      </h3>
      {blocks.map((b, i) =>
        b.kind === "p" ? (
          <p key={i} className="mt-2 text-[14.5px] leading-relaxed text-ink-soft">
            {b.text.replace(/\*\*|__|`/g, "")}
          </p>
        ) : (
          <div key={i} className="mt-2 overflow-x-auto">
            <table className="w-full min-w-[460px] border-collapse text-[14px]">
              <thead>
                <tr className="text-[13px] text-ink-soft">
                  {b.head.map((h, j) => (
                    <th key={j} scope="col" className={`border-b border-rule py-1.5 pr-3 font-[600] text-ink ${j === 0 ? "text-left" : "text-right"}`}>
                      {h.charAt(0).toLocaleUpperCase("ro-RO") + h.slice(1)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {b.rows.map((row, r) => (
                  <tr key={r}>
                    {row.map((c, j) =>
                      j === 0 ? (
                        <th key={j} scope="row" className="border-b border-rule py-1.5 pr-3 text-left font-[450]">
                          {c}
                        </th>
                      ) : (
                        <td key={j} className="border-b border-rule py-1.5 pr-3 text-right tabular-nums">
                          {/^-?\d+(\.\d+)?$/.test(c) ? new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 3 }).format(Number(c)) : c}
                        </td>
                      ),
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ),
      )}
      <p className="mt-1.5 text-[12.5px] text-muted-foreground">
        Din <span translate="no">reports/{source}/error_analysis.md</span>
        {parsed.more ? `, prima secțiune (încă ${parsed.more === 1 ? "una" : parsed.more} în fișier)` : ""}.
      </p>
    </section>
  );
}
