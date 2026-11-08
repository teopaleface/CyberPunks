"use client";

import { ArrowDown, ArrowUp, ArrowUpDown, ChartColumn, ChartPie, ListFilter, Map as MapIcon, Search, UserRound, UtilityPole, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useId, useMemo, useState } from "react";
import { Card, Donut, Pill, TONE, btn, type Tone } from "@/components/ds";
import { Chips } from "@/components/ds/chips";
import { PlanMap, type MapPost } from "@/components/plan/plan-map";
import { fmtDec, fmtInt, plural } from "@/lib/format";
import { RE_BOUNDS } from "@/lib/plan-screen";
import { boundsOfRows, filterRows, RECOMMENDATION, sortRows, type PostColor, type PostRow, type StatusFilter } from "@/lib/posts-view";
import { cn } from "cn";

export interface RegionInfo {
  id: string;
  label: string;
}

const COLOR_HEX: Record<PostColor, string> = { verde: "#22c55e", galben: "#eab308", roșu: "#ef4444", necunoscut: "#4a5a70" };
const COLOR_TEXT: Record<PostColor, string> = { verde: "text-ok-ink", galben: "text-src-c-ink", roșu: "text-red-700 dark:text-red-300", necunoscut: "text-ink-soft" };
const COLOR_NAME: Record<PostColor, string> = { verde: "Under RON 200", galben: "RON 200 to 600", roșu: "Over RON 600", necunoscut: "No energy balance" };
const REGION_TONES: Tone[] = ["blue", "violet", "amber"];
const STATUS_ITEMS: { id: Exclude<StatusFilter, "toate">; tone: Tone }[] = [
  { id: "verde", tone: "green" },
  { id: "galben", tone: "amber" },
  { id: "roșu", tone: "red" },
];

const lei2 = (n: number) => `${fmtDec(n, 2)}`;

export function PostsScreen({
  rows,
  regions,
  scenario,
  thresholds,
  initial,
  derived,
}: {
  rows: PostRow[];
  regions: RegionInfo[];
  scenario: string;
  thresholds: { yellow: number; red: number };
  initial: { region: string; status: StatusFilter; q: string };
  derived: boolean;
}) {
  const router = useRouter();
  const searchId = useId();
  const [region, setRegionState] = useState(regions.some((r) => r.id === initial.region) ? initial.region : "toate");
  const [status, setStatusState] = useState<StatusFilter>(initial.status);
  const [q, setQState] = useState(initial.q);
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState<{ key: "post" | "loss"; dir: "asc" | "desc" }>({ key: "loss", dir: "desc" });

  const persist = useCallback((next: { region: string; status: StatusFilter; q: string }) => {
    const url = new URL(window.location.href);
    const set = (k: string, v: string, empty: string) => (v === empty ? url.searchParams.delete(k) : url.searchParams.set(k, v));
    set("regiune", next.region, "toate");
    set("status", next.status, "toate");
    set("q", next.q.trim(), "");
    window.history.replaceState(window.history.state, "", url);
  }, []);
  const setRegion = (v: string) => (setRegionState(v), setPage(0), persist({ region: v, status, q }));
  const setStatus = (v: StatusFilter) => (setStatusState(v), setPage(0), persist({ region, status: v, q }));
  const setQ = (v: string) => (setQState(v), setPage(0), persist({ region, status, q: v }));

  const regionLabel = useMemo(() => new Map(regions.map((r) => [r.id, r.label])), [regions]);
  const filtered = useMemo(() => filterRows(rows, { region, status, q }), [rows, region, status, q]);
  const sorted = useMemo(() => sortRows(filtered, sort.key, sort.dir), [filtered, sort]);
  const currentPage = Math.min(page, Math.max(0, Math.ceil(sorted.length / 8) - 1));
  const href = useCallback((id: string) => `/posturi/${encodeURIComponent(id)}?scenariu=${encodeURIComponent(scenario)}`, [scenario]);

  // cifrele de jos urmăresc filtrele, ca lista și harta
  const total = filtered.reduce((s, r) => s + (r.loss ?? 0), 0);
  const counts = useMemo(() => {
    const c: Record<PostColor, number> = { verde: 0, galben: 0, roșu: 0, necunoscut: 0 };
    for (const r of filtered) c[r.color] += 1;
    return c;
  }, [filtered]);
  const overRed = useMemo(() => rows.filter((r) => r.color === "roșu").length, [rows]);

  const mapPosts: MapPost[] = useMemo(() => {
    const maxLoss = Math.max(1, ...filtered.map((r) => r.loss ?? 0));
    return filtered.map((r) => {
      const parts: string[] = [];
      if (r.loss != null) parts.push(`${fmtInt(r.loss)} RON lost per month${derived ? " (estimated from model A)" : ""}`);
      if (r.meters) parts.push(plural(r.meters, "flagged meter", "flagged meters"));
      if (r.voltage != null) parts.push(`P90 voltage ${fmtDec(r.voltage, 3).replace(/0$/, "")} pu`);
      if (r.diagnosis) parts.push(r.diagnosis);
      return { id: r.id, lat: r.lat, lon: r.lon, color: r.color, title: r.title, sub: parts.join("; ") || "No signals", weight: Math.sqrt((r.loss ?? 0) / maxLoss) };
    });
  }, [filtered, derived]);
  const bounds = useMemo(() => boundsOfRows(filtered, RE_BOUNDS), [filtered]);
  const onPostClick = useCallback((id: string) => router.push(href(id)), [router, href]);
  const noop = useCallback(() => {}, []);

  const toggleSort = (key: "post" | "loss") =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: key === "post" ? "asc" : "desc" }));
  const sortIcon = (key: "post" | "loss") =>
    sort.key !== key ? <ArrowUpDown aria-hidden="true" size={13} /> : sort.dir === "asc" ? <ArrowUp aria-hidden="true" size={13} /> : <ArrowDown aria-hidden="true" size={13} />;
  const ariaSort = (key: "post" | "loss") => (sort.key === key ? (sort.dir === "asc" ? "ascending" : "descending") : "none");

  const regionItems = [{ id: "toate", label: "All" }, ...regions.map((r) => ({ id: r.id, label: r.label, count: rows.filter((x) => x.region === r.id).length }))];
  const regionRows = regions
    .map((r, i) => ({ ...r, tone: REGION_TONES[i % REGION_TONES.length], sum: filtered.filter((x) => x.region === r.id).reduce((s, x) => s + (x.loss ?? 0), 0), n: filtered.filter((x) => x.region === r.id).length }))
    .filter((r) => r.n > 0);
  const donutParts = (["verde", "galben", "roșu", "necunoscut"] as const).filter((c) => counts[c] > 0 || c !== "necunoscut").map((c) => ({ value: counts[c], color: COLOR_HEX[c], label: COLOR_NAME[c] }));
  const pct = (n: number) => (filtered.length ? `${fmtDec((n / filtered.length) * 100, 1)}%` : "–");

  return (
    <>
      <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-3">
        <Chips
          label="Region"
          value={region}
          onChange={setRegion}
          items={regionItems.map((r) => ({ ...r, tone: undefined }))}
        />
        <span className="h-7 w-px bg-rule max-md:hidden" aria-hidden="true" />
        <div role="group" aria-label="Estimated status" className="flex flex-wrap items-center gap-2.5">
          <span className="text-[14.5px] text-ink-soft">Estimated status</span>
          {STATUS_ITEMS.map((s) => {
            const on = status === s.id;
            const label = s.id === "verde" ? `< ${fmtInt(thresholds.yellow)} RON` : s.id === "galben" ? `${fmtInt(thresholds.yellow)}–${fmtInt(thresholds.red)} RON` : `> ${fmtInt(thresholds.red)} RON`;
            return (
              <button
                key={s.id}
                type="button"
                aria-pressed={on}
                onClick={() => setStatus(on ? "toate" : s.id)}
                className={cn(
                  "inline-flex h-9 items-center gap-2 rounded-full border px-4 text-[14.5px] font-[520] whitespace-nowrap transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
                  on ? "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]" : "border-rule text-ink hover:border-ink-soft hover:bg-surface-2",
                )}
              >
                <span aria-hidden="true" className={cn("size-2.5 rounded-full", TONE[s.tone].solid)} />
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)] items-start gap-4 2xl:grid-cols-[minmax(0,.9fr)_minmax(0,1.4fr)]">
        <Card title="Estimated losses by location (RON/month)" icon={MapIcon} iconTone="violet" className="flex min-h-[340px] flex-col" bodyClassName="relative min-h-0 flex-1 !p-0 px-0">
          <div className="relative mx-5 mt-0 mb-5 h-[calc(100%-1.25rem)] min-h-[280px] overflow-hidden rounded-[10px] border border-rule max-xl:h-[300px]">
            <PlanMap
              items={[]}
              routes={[]}
              depots={[]}
              bounds={bounds}
              selectedId={null}
              onSelect={noop}
              posts={mapPosts}
              mode="posts"
              onPostClick={onPostClick}
              padding={{ top: 28, bottom: 28, left: 28, right: 28 }}
              className="absolute inset-0"
            />
            <div className="absolute bottom-3 left-3 rounded-[10px] border border-rule bg-panel/95 px-3.5 py-2.5 text-[13.5px]" role="group" aria-label="Map legend">
              <p className="mb-1 font-[600]">RON lost per month</p>
              {(["verde", "galben", "roșu"] as const).map((c) => (
                <p key={c} className="flex items-center gap-2 leading-[1.55]">
                  <span aria-hidden="true" className="size-3 rounded-full" style={{ background: COLOR_HEX[c] }} />
                  {c === "verde" ? `below ${fmtInt(thresholds.yellow)}` : c === "galben" ? `${fmtInt(thresholds.yellow)}–${fmtInt(thresholds.red)}` : `above ${fmtInt(thresholds.red)}`}
                </p>
              ))}
            </div>
          </div>
        </Card>

        <Card
          title="Substation list"
          icon={ListFilter}
          iconTone="blue"
          className="flex min-h-[340px] flex-col"
          bodyClassName="flex min-h-0 flex-1 flex-col"
          action={<span className="text-[14.5px] font-[400] text-ink-soft tabular-nums">{plural(filtered.length, "substation", "substations")}</span>}
        >
          <div className="relative">
            <label htmlFor={searchId} className="sr-only">

              Search substations
            </label>
            <Search aria-hidden="true" size={18} className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-ink-soft" />
            <input
              id={searchId}
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by substation or locality…"
              autoComplete="off"
              spellCheck={false}
              className="h-11 w-full rounded-[10px] border border-rule bg-surface-2 pr-10 pl-11 text-[14.5px] text-ink placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring [&::-webkit-search-cancel-button]:hidden"
            />
            {q ? (
              <button type="button" aria-label="Clear search" onClick={() => setQ("")} className="absolute top-1/2 right-2.5 grid size-7 -translate-y-1/2 place-items-center rounded-full text-ink-soft hover:text-ink focus-visible:outline-2 focus-visible:outline-ring">
                <X aria-hidden="true" size={16} />
              </button>
            ) : null}
          </div>
          <div className="mt-3 min-h-0 overflow-x-auto rounded-[10px]">
            <table className="w-full min-w-[600px] border-collapse text-[14px] whitespace-nowrap">
              <thead className="sticky top-0 z-10 bg-panel text-left text-[13px] text-ink-soft">
                <tr className="border-b border-rule">
                  <th scope="col" aria-sort={ariaSort("post")} className="py-2 pr-2 font-[500]">
                    <button type="button" onClick={() => toggleSort("post")} className="inline-flex items-center gap-1.5 hover:text-ink focus-visible:outline-2 focus-visible:outline-ring">

                      Substation {sortIcon("post")}
                    </button>
                  </th>
                  <th scope="col" className="px-2 py-2 font-[500]">Region</th>
                  <th scope="col" className="px-2 py-2 font-[500]">Locality</th>
                  <th scope="col" aria-sort={ariaSort("loss")} className="px-2 py-2 text-right font-[500] whitespace-normal">
                    <button type="button" onClick={() => toggleSort("loss")} className="inline-flex items-center gap-1.5 hover:text-ink focus-visible:outline-2 focus-visible:outline-ring">

                      Losses (RON/month) {sortIcon("loss")}
                    </button>
                  </th>
                  <th scope="col" className="py-2 pl-2 font-[500]">Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {sorted.slice(currentPage * 8, (currentPage + 1) * 8).map((r) => {
                  const rec = RECOMMENDATION[r.color];
                  return (
                    <tr key={r.id} className="border-b border-rule/60 hover:bg-surface-2" style={{ contentVisibility: "auto", containIntrinsicSize: "auto 40px" }}>
                      <td className="py-2 pr-2">
                        <Link href={href(r.id)} className="flex items-center gap-2 font-[600] hover:underline focus-visible:outline-2 focus-visible:outline-ring" translate="no">
                          <UtilityPole aria-hidden="true" size={17} strokeWidth={1.8} className={cn("shrink-0", COLOR_TEXT[r.color])} />
                          {r.id}
                          <span className="sr-only">, {COLOR_NAME[r.color]}</span>
                        </Link>
                      </td>
                      <td className="px-2 py-2 text-ink-soft">{(r.region && regionLabel.get(r.region)) || "–"}</td>
                      <td className="max-w-[110px] truncate px-2 py-2" title={r.place}>{r.place || "–"}</td>
                      <td className="px-2 py-2 text-right font-[500] tabular-nums">{r.loss != null ? lei2(r.loss) : "–"}</td>
                      <td className="py-2 pl-2">
                        <Pill tone={rec.tone} size="sm">{rec.label}</Pill>
                      </td>
                    </tr>
                  );
                })}
                {!sorted.length ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-ink-soft">

                      No substations match these filters.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
          <nav className="mt-4 flex items-center justify-between gap-3 border-t border-rule pt-3 text-sm text-ink-soft" aria-label="Substation pages"><span>{sorted.length ? `${currentPage * 8 + 1}–${Math.min(sorted.length, (currentPage + 1) * 8)} of ${sorted.length}` : "No results"}</span><div className="flex gap-2"><button type="button" className="min-h-9 rounded-lg border border-rule px-3 disabled:opacity-40" disabled={currentPage === 0} onClick={() => setPage(Math.max(0, currentPage - 1))}>Previous</button><button type="button" className="min-h-9 rounded-lg border border-rule px-3 disabled:opacity-40" disabled={currentPage >= Math.ceil(sorted.length / 8) - 1} onClick={() => setPage(Math.min(currentPage + 1, Math.ceil(sorted.length / 8) - 1))}>Next</button></div></nav>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-2 xl:grid-cols-[1fr_1.2fr_1fr]">
        <Card title="Estimated losses" icon={ChartColumn} iconTone="blue">
          <div className="rounded-[10px] border border-rule bg-surface-2 px-4 py-3">
            <p className="text-[14.5px] text-ink-soft">Total estimated losses{derived ? " (from model A meters)" : ""}</p>
            <p className="mt-0.5 text-[30px] leading-tight font-[700] tracking-[-0.02em] tabular-nums">
              {lei2(total)} <span className="text-[20px] font-[600]">RON/month</span>
            </p>
          </div>
          <ul className="mt-2.5 space-y-2">
            {regionRows.map((r) => (
              <li key={r.id} className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3.5 py-2 text-[14.5px]">
                <span aria-hidden="true" className={cn("size-3 rounded-full", TONE[r.tone].solid)} />
                <span className="flex-1 whitespace-nowrap">{r.label}</span>
                <span className="font-[500] whitespace-nowrap tabular-nums">{lei2(r.sum)} <span className="text-ink-soft">RON/month</span></span>
              </li>
            ))}
            {!regionRows.length ? <li className="text-[14.5px] text-ink-soft">No substations in the selected filters.</li> : null}
          </ul>
        </Card>

        <Card title="Substations by loss level" icon={ChartPie} iconTone="blue">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3 max-sm:justify-center">
            <Donut parts={donutParts} center={fmtInt(filtered.length)} sub={filtered.length === 1 ? "substation" : "substations"} size={116} />
            <ul className="min-w-[170px] flex-1 space-y-2.5 text-[14.5px]">
              {(["verde", "galben", "roșu", "necunoscut"] as const)
                .filter((c) => counts[c] > 0 || c !== "necunoscut")
                .map((c) => (
                  <li key={c} className="grid grid-cols-[auto_1fr_auto_auto] items-center gap-x-3">
                    <span aria-hidden="true" className="size-3 rounded-full" style={{ background: COLOR_HEX[c] }} />
                    <span>{c === "necunoscut" ? "No energy balance" : c === "verde" ? `below ${fmtInt(thresholds.yellow)}` : c === "galben" ? `${fmtInt(thresholds.yellow)}–${fmtInt(thresholds.red)}` : `above ${fmtInt(thresholds.red)}`}</span>
                    <span className="text-right font-[600] tabular-nums">{fmtInt(counts[c])}</span>
                    <span className="w-[52px] text-right text-ink-soft tabular-nums">{pct(counts[c])}</span>
                  </li>
                ))}
            </ul>
          </div>
        </Card>

        <Card title="Human decision" icon={UserRound} iconTone="blue" className="lg:col-span-2 xl:col-span-1">
          <div className="rounded-[10px] border border-rule bg-surface-2 px-4 py-3.5">
            <p className="text-[22px] leading-tight font-[700] tracking-[-0.015em]">
              {overRed ? `${plural(overRed, "substation exceeds", "substations exceed")} ${fmtInt(thresholds.red)} RON/month.` : `No substation exceeds ${fmtInt(thresholds.red)} RON/month.`}
            </p>
            <p className="mt-1.5 text-[14.5px] text-ink-soft">Review the evidence before confirming tomorrow&apos;s action.</p>
            <div className="mt-3.5 flex flex-wrap gap-2.5">
              <button
                type="button"
                className={btn("primary")}
                disabled={!overRed}
                onClick={() => (setRegionState("toate"), setStatusState("roșu"), setQState(""), persist({ region: "toate", status: "roșu", q: "" }))}
              >

                Show only substations above {fmtInt(thresholds.red)}  RON
              </button>
              <Link href={`/coada?scenariu=${encodeURIComponent(scenario)}`} className={btn("outline")}>

                Review pending work items
              </Link>
            </div>
          </div>
        </Card>
      </div>
      <p className="sr-only" aria-live="polite">{plural(filtered.length, "substation shown", "substations shown")}</p>
    </>
  );
}
