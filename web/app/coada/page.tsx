import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  CloudRain,
  Database,
  CalendarDays,
  Gauge as GaugeIcon,
  Layers,
  Network,
  Users,
  Wind,
  Zap,
} from "lucide-react";
import type { ComponentType } from "react";
import { cn } from "cn";
import { Card, Dot, Gauge, PageTitle, Pill, SOURCE_TONE, btn, type Tone } from "@/components/ds";
import { ReviewActions } from "@/components/detail/review-actions";
import { CaseChart, type CasePoint } from "@/components/queue/case-chart";
import { AppShell } from "@/components/shell/app-shell";
import type { Decision, Series, WorkItem } from "@/lib/contracts";
import { getSeries } from "@/lib/data";
import { fmtDayMonth, fmtInt, fmtLei, fmtTime, plural } from "@/lib/format";
import { placeOf } from "@/lib/briefing";
import { roundPct } from "@/lib/human";
import { caseFacts, categoryOf, pageList, questionFor, whenText, type Category, type Fact } from "@/lib/queue-model";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { itemPlace } from "@/lib/plan-screen";

export const metadata: Metadata = { title: "Nu sunt sigur" };

const PER_PAGE = 10;

export default function QueuePage({ searchParams }: PageProps<"/coada">) {
  return (
    <Suspense
      fallback={
        <div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
          <span className="sr-only">Se încarcă lucrările care așteaptă un om…</span>
        </div>
      }
    >
      <Queue searchParams={searchParams} />
    </Suspense>
  );
}

interface Waiting {
  decision: Decision;
  w: WorkItem;
  cat: Category;
}

const FACT_ICON: Record<Fact["icon"], ComponentType<{ size?: number; strokeWidth?: number; className?: string; "aria-hidden"?: boolean | "true" }>> = {
  rain: CloudRain,
  wind: Wind,
  data: Database,
  kwh: Zap,
  volt: Zap,
  limit: GaugeIcon,
};
const FACT_TONE: Record<Fact["icon"], string> = {
  rain: "text-[#8db8ff]",
  wind: "text-[#8db8ff]",
  data: "text-[#d6a8f0]",
  kwh: "text-[#f5c66b]",
  volt: "text-[#f5c66b]",
  limit: "text-[#ffa27c]",
};
const CAT_TONE: Record<Category["tone"], Tone> = { blue: "blue", violet: "violet", amber: "amber", orange: "orange", grey: "grey" };
const SRC_VAR = { A: "var(--src-a)", B: "var(--src-b)", C: "var(--src-c)" } as const;

async function Queue({ searchParams }: { searchParams: PageProps<"/coada">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, params] = await Promise.all([loadShellInfo(scenario), searchParams]);
  const plan = view.data;
  const str = (k: string) => (typeof params[k] === "string" ? (params[k] as string) : undefined);

  const waiting: Waiting[] = [];
  for (const decision of plan?.plan.decisions ?? []) {
    if (decision.decision !== "human_review") continue;
    const w = plan?.workItemsById[decision.work_item_id];
    if (w) waiting.push({ decision, w, cat: categoryOf(decision.rule_id) });
  }
  waiting.sort(
    (a, b) =>
      Number(Boolean(b.w.impact.safety_flag)) - Number(Boolean(a.w.impact.safety_flag)) ||
      b.w.impact.expected_value_lei - a.w.impact.expected_value_lei,
  );

  const cats = new Map<string, { cat: Category; count: number }>();
  for (const x of waiting) {
    const e = cats.get(x.cat.id);
    if (e) e.count += 1;
    else cats.set(x.cat.id, { cat: x.cat, count: 1 });
  }
  const catList = [...cats.values()].toSorted((a, b) => b.count - a.count);
  const motiv = catList.some((c) => c.cat.id === str("motiv")) ? str("motiv")! : null;
  const list = motiv ? waiting.filter((x) => x.cat.id === motiv) : waiting;
  const pages = Math.max(1, Math.ceil(list.length / PER_PAGE));
  const selected = list.find((x) => x.w.work_item_id === str("caz")) ?? list[0] ?? null;
  const selIndex = selected ? list.indexOf(selected) : 0;
  // pagina cerută; dacă lipsește, pagina cazului ales
  const reqPage = Number(str("pagina"));
  const page = Math.min(pages, Math.max(1, Number.isInteger(reqPage) && reqPage > 0 ? reqPage : Math.floor(selIndex / PER_PAGE) + 1));
  const rows = list.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  const href = (o: { caz?: string | null; motiv?: string | null; pagina?: number | null }) => {
    const q = new URLSearchParams();
    q.set("scenariu", scenario);
    const m = "motiv" in o ? o.motiv : motiv;
    if (m) q.set("motiv", m);
    const c = "caz" in o ? o.caz : selected?.w.work_item_id;
    if (c) q.set("caz", c);
    if (o.pagina && o.pagina > 1) q.set("pagina", String(o.pagina));
    return `/coada?${q.toString()}`;
  };

  const seriesResult = selected ? await getSeries(selected.w.work_item_id, scenario) : null;
  const series = seriesResult?.data ?? null;

  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4">
        <PageTitle
          title="Nu sunt sigur: decizii care cer o persoană."
          subtitle="Cazuri în care agentul nu e sigur și așteaptă judecata unui om, înainte de planul de mâine."
        />

        {!plan ? (
          <Card className="mt-6" bodyClassName="py-6">
            <p className="text-[18px] font-[620]">Nu există încă un plan pentru „{scenario}”.</p>
            <p className="mt-1.5 text-[15.5px] text-ink-soft">
              {view.degradedReason ?? "Agentul n-a rulat încă pentru acest scenariu."} Pornește-l din pagina{" "}
              <Link href={`/rulare?scenariu=${encodeURIComponent(scenario)}`} className="underline underline-offset-4">
                Rulare agent
              </Link>
              .
            </p>
          </Card>
        ) : !waiting.length ? (
          <Card className="mt-6" bodyClassName="py-7">
            <p className="text-[20px] font-[620]">Agentul a decis singur tot ce a primit. Nimic nu așteaptă un om acum.</p>
            <Link href={`/?scenariu=${encodeURIComponent(scenario)}`} className={cn(btn("outline"), "mt-4")}>
              Înapoi la planul de mâine
            </Link>
          </Card>
        ) : (
          <>
            <nav aria-label="Filtrează după motiv" className="mt-5 flex flex-wrap gap-2.5">
              <FilterChip href={href({ motiv: null, caz: null, pagina: null })} on={!motiv}>
                Toate ({waiting.length})
              </FilterChip>
              {catList.map(({ cat, count }) => (
                <FilterChip key={cat.id} href={href({ motiv: cat.id, caz: null, pagina: null })} on={motiv === cat.id} tone={CAT_TONE[cat.tone]}>
                  {cat.label} ({count})
                </FilterChip>
              ))}
            </nav>

            <div className="mt-5 grid grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)]">
              {selected ? <Approval key={selected.w.work_item_id} sel={selected} scenario={scenario} series={series} /> : null}

              <Card
                title={`Lista cazurilor (${list.length})`}
                action={<span className="text-[14.5px] font-[450] text-ink-soft">Pagina {page} din {pages}</span>}
                bodyClassName="pt-4"
              >
                {catList.length > 1 ? (
                  <ul className="mb-4 grid grid-cols-3 gap-2.5 max-sm:grid-cols-1">
                    {catList.slice(0, 3).map(({ cat, count }) => (
                      <li key={cat.id}>
                        <Link
                          href={href({ motiv: cat.id, caz: null, pagina: null })}
                          className={cn(
                            "flex h-full items-center gap-3 rounded-[12px] border bg-surface-2 px-3.5 py-2.5 transition-colors hover:border-[#3d5170] focus-visible:outline-2 focus-visible:outline-ring",
                            motiv === cat.id ? "border-[#3d5170]" : "border-rule",
                          )}
                        >
                          <Dot tone={CAT_TONE[cat.tone]} className="size-3.5" />
                          <span className="min-w-0">
                            <span className="block text-[19px] leading-tight font-[650] tabular-nums">{fmtInt(count)}</span>
                            <span className="block text-[13.5px] leading-tight text-ink-soft">{cat.label}</span>
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : null}

                <table className="w-full border-collapse sm:table-fixed text-[15px]">
                  <caption className="sr-only">Cazurile care așteaptă o decizie, cu motivul, încrederea și impactul</caption>
                  <thead>
                    <tr className="border-b border-rule text-left text-[14px] text-ink-soft">
                      <th scope="col" className="w-9 py-2 pl-2 font-[450]">#</th>
                      <th scope="col" className="py-2 font-[450]">Post/loc</th>
                      <th scope="col" className="w-[22%] py-2 font-[450] max-sm:hidden">Motiv</th>
                      <th scope="col" className="w-[18%] py-2 text-right font-[450]">Încredere</th>
                      <th scope="col" className="w-[20%] py-2 pr-1 text-right font-[450]">Impact</th><td className="w-8" />
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((x, i) => {
                      const on = x.w.work_item_id === selected?.w.work_item_id;
                      return (
                        <tr key={x.w.work_item_id} className={cn("relative border-b border-rule/60 last:border-b-0", on && "bg-[#0f2547] outline outline-2 -outline-offset-2 outline-[#3b82f6]")}>
                          <td className="py-2.5 pl-2 tabular-nums">{(page - 1) * PER_PAGE + i + 1}</td>
                          <td className="py-2.5 pr-2 font-[560]">
                            <Link
                              href={href({ caz: x.w.work_item_id })}
                              scroll={false}
                              prefetch={false}
                              aria-current={on ? "true" : undefined}
                              className="flex items-center gap-2 after:absolute after:inset-0 focus-visible:outline-2 focus-visible:outline-ring"
                            >
                              <Dot tone={CAT_TONE[x.cat.tone]} className="size-2 sm:hidden" />
                              <span className="truncate max-sm:max-w-[110px]" translate="no" title={placeOf(x.w)}>{placeOf(x.w)}</span>
                            </Link>
                          </td>
                          <td className="py-2.5 pr-2 max-sm:hidden">
                            <Pill tone={CAT_TONE[x.cat.tone]} size="sm" className="max-w-full border-transparent bg-transparent px-0 text-ink">
                              <Dot tone={CAT_TONE[x.cat.tone]} className="size-2" />
                              <span className="truncate">{x.cat.label}</span>
                            </Pill>
                          </td>
                          <td className="py-2.5 pl-2 text-right font-[560] whitespace-nowrap tabular-nums">{roundPct(x.w.prediction.score)}</td>
                          <td className="py-2.5 pr-2 text-right font-[560] whitespace-nowrap tabular-nums">
                            {fmtLei(x.w.impact.expected_value_lei)}
                          </td>
                          <td className="w-6 pr-2 text-ink-soft">
                            <ChevronRight aria-hidden="true" size={18} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {pages > 1 ? (
                  <nav aria-label="Paginile listei" className="mt-6 flex flex-wrap items-center justify-between gap-3">
                    <PageNav href={page > 1 ? href({ pagina: page - 1, caz: null }) : null}>
                      <ChevronLeft aria-hidden="true" size={16} />
                      Înapoi
                    </PageNav>
                    <ul className="flex items-center gap-2">
                      {pageList(pages, page).map((n, i) => (
                        <li key={`${n}-${i}`}>
                          {n === "…" ? (
                            <span className="px-1 text-ink-soft">…</span>
                          ) : (
                            <Link
                              href={href({ pagina: n, caz: null })}
                              scroll={false}
                              prefetch={false}
                              aria-label={`Pagina ${n}`}
                              aria-current={n === page ? "page" : undefined}
                              className={cn(
                                "grid size-10 place-items-center rounded-[10px] border text-[15px] font-[600] tabular-nums focus-visible:outline-2 focus-visible:outline-ring",
                                n === page ? "border-action bg-action text-white" : "border-[#2a3a52] hover:border-[#3d5170] hover:bg-[#0f1a2b]",
                              )}
                            >
                              {n}
                            </Link>
                          )}
                        </li>
                      ))}
                    </ul>
                    <PageNav href={page < pages ? href({ pagina: page + 1, caz: null }) : null}>
                      Înainte
                      <ChevronRight aria-hidden="true" size={16} />
                    </PageNav>
                  </nav>
                ) : null}
                <p className="sr-only">{plural(list.length, "caz", "cazuri")} în listă</p>
              </Card>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function FilterChip({ href, on, tone, children }: { href: string; on: boolean; tone?: Tone; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      prefetch={false}
      aria-current={on ? "true" : undefined}
      className={cn(
        "inline-flex h-9 items-center gap-2 rounded-full border px-4 text-[14.5px] font-[520] whitespace-nowrap transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        on ? "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]" : "border-[#2a3a52] text-ink hover:border-[#3d5170] hover:bg-[#0f1a2b]",
      )}
    >
      {tone && !on ? <Dot tone={tone} /> : null}
      {children}
    </Link>
  );
}

function PageNav({ href, children }: { href: string | null; children: React.ReactNode }) {
  const cls = cn(btn("outline", "sm"), "h-10 gap-1.5 px-4");
  return href ? (
    <Link href={href} scroll={false} prefetch={false} className={cls}>
      {children}
    </Link>
  ) : (
    <span aria-disabled="true" className={cn(cls, "pointer-events-none opacity-45")}>
      {children}
    </span>
  );
}

function chartData(series: Series | null): { data: CasePoint[]; limit: number | null } {
  if (!series) return { data: [], limit: null };
  const hourly = series.points.some((p) => /T\d\d:\d\d/.test(String(p.t)) && !/T00:00:00$/.test(String(p.t)));
  const data: CasePoint[] = [];
  for (const p of series.points) {
    const v = p.value ?? p.expected;
    if (typeof v !== "number" || !Number.isFinite(v)) continue;
    data.push({ x: hourly ? fmtTime(String(p.t)) : fmtDayMonth(String(p.t)), v });
  }
  const th = series.thresholds ?? {};
  const limit = typeof th.limita_tensiune_pu === "number" ? th.limita_tensiune_pu : null;
  return { data, limit };
}

function Approval({ sel, scenario, series }: { sel: Waiting; scenario: string; series: Series | null }) {
  const { w, cat } = sel;
  const p = w.prediction;
  const place = itemPlace(w);
  const q = questionFor(w, place);
  const { data, limit } = chartData(series);
  const facts = caseFacts(w, limit);
  const tone = CAT_TONE[cat.tone];
  const srcTone = SOURCE_TONE[w.source];
  const customers = w.impact.customers_affected;
  return (
    <Card
      title="Aprobare"
      icon={ClipboardCheck}
      action={
        <Pill tone={tone} size="lg">
          <Dot tone={tone} className="size-3" />
          {cat.label}
        </Pill>
      }
      bodyClassName="pt-4"
    >
      <h2 className="text-[27px] leading-[1.2] font-[720] tracking-[-0.02em] max-md:text-[22px]">
        {q.before}
        {q.id ? <span translate="no">{q.id}</span> : null}
        {q.after}
      </h2>
      <p className="mt-1.5 text-[15px] text-ink-soft">{sel.decision.reason_ro}</p>

      <div className="mt-4 grid grid-cols-[auto_minmax(0,1fr)_minmax(0,1fr)] items-center gap-x-4 gap-y-3 rounded-[12px] border border-rule bg-surface-2 px-4 py-4 max-md:grid-cols-1 max-md:justify-items-start">
        <div className="shrink-0">
          <Gauge value={p.score} label={<span className={p.score >= 0.995 ? "text-[21px]" : undefined}>{roundPct(p.score)}</span>} sub="scorul modelului" tone={srcTone} size={150} />
        </div>
        <div className="flex min-w-0 flex-col gap-3.5 border-l border-rule pl-4 max-md:border-l-0 max-md:pl-0">
          <div className="flex min-w-0 items-center gap-3">
            <Network aria-hidden="true" size={26} strokeWidth={1.5} className="shrink-0 text-violet" />
            <div className="min-w-0">
              <p className="text-[13.5px] text-ink-soft">Model</p>
              <p className="truncate text-[16px] font-[650]" translate="no">{p.model_version}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <CalendarDays aria-hidden="true" size={26} strokeWidth={1.5} className="shrink-0 text-violet" />
            <div>
              <p className="text-[13.5px] text-ink-soft">{w.time_window ? "Fereastră" : "Urgență"}</p>
              <p className="text-[16px] font-[650] whitespace-nowrap tabular-nums">{whenText(w)}</p>
            </div>
          </div>
        </div>
        <div className="flex min-w-0 flex-col gap-3.5 border-l border-rule pl-4 max-md:border-l-0 max-md:pl-0">
          <div className="flex items-center gap-3">
            <Users aria-hidden="true" size={26} strokeWidth={1.5} className="shrink-0 text-violet" />
            <div>
              <p className="text-[13.5px] text-ink-soft">Clienți afectați</p>
              <p className="text-[16px] font-[650] tabular-nums">{customers != null ? fmtInt(customers) : "–"}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Layers aria-hidden="true" size={26} strokeWidth={1.5} className="shrink-0 text-violet" />
            <div>
              <p className="text-[13.5px] text-ink-soft">Valoare așteptată</p>
              <p className="text-[16px] font-[650] tabular-nums">{fmtLei(w.impact.expected_value_lei)}</p>
            </div>
          </div>
        </div>
      </div>

      {facts.length ? (
        <ul className="mt-3 grid grid-cols-2 rounded-[12px] border border-rule bg-surface-2 max-sm:grid-cols-1">
          {facts.map((f, i) => {
            const Icon = FACT_ICON[f.icon];
            return (
              <li key={f.icon} className={cn("flex items-center justify-center gap-4 px-4 py-3.5", i > 0 && "border-l border-rule max-sm:border-t max-sm:border-l-0")}>
                <Icon aria-hidden="true" size={34} strokeWidth={1.4} className={FACT_TONE[f.icon]} />
                <div>
                  <p className="text-[22px] leading-tight font-[650] tabular-nums">{f.value}</p>
                  <p className="text-[14px] text-ink-soft">{f.label}</p>
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}

      {data.length > 1 ? (
        <figure className="mt-3 rounded-[12px] border border-rule bg-surface-2 px-4 pt-3 pb-2">
          <figcaption className="mb-1 text-[15px] font-[560]">{series?.title_ro}</figcaption>
          <CaseChart data={data} unit={series?.unit ?? ""} color={SRC_VAR[w.source]} limit={limit} label={series?.title_ro ?? "Serie"} />
        </figure>
      ) : (
        <p className="mt-3 rounded-[12px] border border-rule bg-surface-2 px-4 py-4 text-[14.5px] text-ink-soft">Nu există o serie pentru acest caz.</p>
      )}

      <div className="mt-4">
        <ReviewActions workItemId={w.work_item_id} scenario={scenario} layout="card" />
      </div>
      <p className="mt-3 text-[13.5px] text-ink-soft">
        Lucrarea{" "}
        <Link href={`/lucrari/${encodeURIComponent(w.work_item_id)}?scenariu=${encodeURIComponent(scenario)}`} translate="no" className="code-id underline underline-offset-4 hover:text-ink">
          {w.work_item_id}
        </Link>{" "}
        {w.data_quality.synthetic ? "· date sintetice" : ""}
      </p>
    </Card>
  );
}
