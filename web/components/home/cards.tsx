import { CalendarDays, Coins, Layers, Map as MapIcon, Route, UserRound, Users, Zap } from "lucide-react";
import Link from "next/link";
import { Card, Dot, Gauge, Meter, Pill, TONE, type Tone } from "@/components/ds";
import type { WorkItem } from "@/lib/contracts";
import type { CrewLine } from "@/lib/briefing";
import { fmtInt, fmtLei, fmtTime, hhmm, minutesOfPlanDay, plural } from "@/lib/format";
import type { DotMap, DotRegion } from "@/lib/home-dotmap";
import { roundPct } from "@/lib/human";
import { itemTitle } from "@/lib/plan-screen";
import type { PlanScreenData } from "@/lib/plan-screen";

export const SOURCE_COLOR = { A: "var(--src-a)", B: "var(--src-b)", C: "var(--src-c)" } as const;
const SOURCE_TONE_OF: Record<WorkItem["source"], Tone> = { A: "blue", B: "violet", C: "amber" };

const REGION_COLOR: Record<DotRegion, string> = {
  muntenia_sud: "var(--src-a)",
  dobrogea: "var(--src-b)",
  banat: "var(--src-c)",
  other: "#5a6b82",
};
const LEGEND: { region: DotRegion; label: string }[] = [
  { region: "muntenia_sud", label: "Muntenia Sud" },
  { region: "dobrogea", label: "Dobrogea" },
  { region: "banat", label: "Banat" },
  { region: "other", label: "Alte județe" },
];

export const withQuery = (path: string, scenario: string) => `${path}?scenariu=${encodeURIComponent(scenario)}`;

/** Harta de puncte a României, colorată pe regiunile Rețelelor Electrice. */
export function RomaniaCard({ map, scenario }: { map: DotMap; scenario: string }) {
  const order: DotRegion[] = ["other", "muntenia_sud", "dobrogea", "banat"];
  const pad = map.pitch;
  return (
    <Card
      title="România"
      icon={MapIcon}
      className="h-full"
      action={
        <Link href={withQuery("/harta", scenario)} className="text-[14px] text-ink-soft hover:text-ink hover:underline focus-visible:outline-2 focus-visible:outline-ring">
          Harta mare
        </Link>
      }
    >
      <div className="flex flex-col gap-4 min-[1650px]:flex-row min-[1650px]:items-center">
        <svg
          viewBox={`${-pad / 2} ${-pad / 2} ${map.width + pad} ${map.height + pad}`}
          role="img"
          aria-label="Harta României din puncte, colorată pe regiunile Muntenia Sud, Dobrogea și Banat"
          className="mx-auto h-auto max-h-[300px] w-full min-w-0 flex-1"
        >
          {order.map((r) => (
            <path
              key={r}
              fill="none"
              stroke={REGION_COLOR[r]}
              strokeWidth={pad * 0.7}
              strokeLinecap="round"
              d={map.dots
                .filter((d) => d.region === r)
                .map((d) => `M${d.x} ${d.y}h0`)
                .join("")}
            />
          ))}
        </svg>
        <ul className="flex shrink-0 flex-row flex-wrap gap-x-5 gap-y-2 text-[14px] min-[1650px]:flex-col min-[1650px]:gap-2.5">
          {LEGEND.map((l) => (
            <li key={l.region} className="flex items-center gap-2.5 text-ink-soft">
              <span aria-hidden="true" className="size-3 rounded-full" style={{ background: REGION_COLOR[l.region] }} />
              {l.label}
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}

/** Echipele de mâine: bară în culoarea sursei principale, număr de lucrări, stare. */
export function CrewsCard({ lines, approved, scenario }: { lines: CrewLine[]; approved: boolean; scenario: string }) {
  return (
    <Card
      title="Trasee echipe"
      icon={Route}
      iconTone="violet"
      className="h-full"
      action={
        <Link href={withQuery("/harta", scenario)} className="text-[14px] text-ink-soft hover:text-ink hover:underline focus-visible:outline-2 focus-visible:outline-ring">
          Pe hartă
        </Link>
      }
    >
      {lines.length ? (
        <ul className="divide-y divide-rule">
          {lines.map((c) => (
            <li key={c.crewId} className="grid grid-cols-[22px_minmax(0,1fr)_auto_auto] items-center gap-x-3 py-[7px] text-[15px]">
              <span aria-hidden="true" className="h-[5px] rounded-full" style={{ background: c.firstSource ? SOURCE_COLOR[c.firstSource] : "var(--idle)" }} />
              <span className="font-[560]" translate="no">
                {c.crewId}
              </span>
              <span className="text-ink-soft tabular-nums">{plural(c.stops, "lucrare", "lucrări")}</span>
              <Pill size="sm" tone={c.storm ? "violet" : approved ? "green" : "grey"} className="min-w-[88px] justify-center">
                {c.storm ? "Furtună" : approved ? "Aprobat" : "Planificat"}
              </Pill>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[15px] text-ink-soft">Mâine nu pleacă nicio echipă.</p>
      )}
    </Card>
  );
}

const hourOf = (min: number) => Math.floor(min / 60);

/** Programul echipelor: o bară pentru fiecare oprire, între ora de sosire și sfârșitul lucrării. */
export function GanttCard({ data, dateLabel }: { data: PlanScreenData; dateLabel: string }) {
  const byId = new Map(data.items.map((w) => [w.work_item_id, w]));
  const rows = data.routes.map((r) => ({
    crew: r.crew_id,
    stops: [...r.stops]
      .sort((a, b) => a.seq - b.seq)
      .map((s) => {
        const start = minutesOfPlanDay(s.eta, data.planDate);
        const item = s.workItem ?? byId.get(s.work_item_id) ?? null;
        return { id: s.work_item_id, start, end: start + Math.max(s.duration_min ?? 0, 5), source: item?.source ?? null, title: item ? itemTitle(item) : s.work_item_id };
      }),
    depart: r.depart_at ? minutesOfPlanDay(r.depart_at, data.planDate) : null,
    back: r.return_at ? minutesOfPlanDay(r.return_at, data.planDate) : null,
  }));
  const starts = rows.flatMap((r) => [...r.stops.map((s) => s.start), ...(r.depart !== null ? [r.depart] : [])]);
  const ends = rows.flatMap((r) => [...r.stops.map((s) => s.end), ...(r.back !== null ? [r.back] : [])]);
  const from = hourOf(Math.min(8 * 60, ...starts));
  const to = Math.max(16, Math.ceil(Math.max(16 * 60, ...ends) / 60));
  const span = (to - from) * 60;
  const hours = Array.from({ length: to - from + 1 }, (_, i) => from + i);
  const pct = (min: number) => `${(((min - from * 60) / span) * 100).toFixed(3)}%`;

  return (
    <Card title={`Programul echipelor (${dateLabel})`} icon={CalendarDays} className="h-full">
      <div className="overflow-x-auto">
        <div className="min-w-[640px]">
          <div className="grid grid-cols-[68px_minmax(0,1fr)]">
            <div />
            <div className="relative ml-3 mr-6 h-7 text-[14px] text-ink-soft">
              {hours.filter((h) => (to - from > 10 ? (h - from) % 2 === 0 : true)).map((h) => (
                <span key={h} className="absolute -translate-x-1/2 tabular-nums" style={{ left: pct(h * 60) }}>
                  {hhmm(h * 60)}
                </span>
              ))}
            </div>
            {rows.map((r) => (
              <div key={r.crew} className="contents">
                <div className="flex h-[30px] items-center border-t border-rule text-[14.5px] font-[560]" translate="no">
                  {r.crew}
                </div>
                <div className="relative ml-3 mr-6 h-[30px] border-t border-rule">
                  {hours.map((h) => (
                    <span key={h} aria-hidden="true" className="absolute inset-y-0 w-px border-l border-dashed border-rule" style={{ left: pct(h * 60) }} />
                  ))}
                  {r.stops.map((s) => {
                    const left = ((s.start - from * 60) / span) * 100;
                    const width = Math.max(((s.end - s.start) / span) * 100, 0.7);
                    return (
                      <Link
                        key={s.id}
                        href={withQuery(`/lucrari/${encodeURIComponent(s.id)}`, data.scenario)}
                        aria-label={`${r.crew}: ${s.title}, ${hhmm(s.start)}–${hhmm(s.end)}`}
                        title={`${s.title}, ${hhmm(s.start)}–${hhmm(s.end)}`}
                        className="absolute top-[7px] h-4 rounded-full transition-[filter] duration-150 hover:brightness-125 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                        style={{ left: `${left}%`, width: `${width}%`, background: s.source ? SOURCE_COLOR[s.source] : "var(--idle)" }}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[13.5px] text-ink-soft">
        {(["A", "B", "C"] as const).map((s) => (
          <li key={s} className="flex items-center gap-2">
            <Dot tone={SOURCE_TONE_OF[s]} />
            {s === "A" ? "Contoare" : s === "B" ? "Furtună" : "Tensiune"}
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Întrebarea în cuvinte simple, din cazul real. */
export function questionText(w: WorkItem): string {
  if (w.source === "B") return `Trimitem o echipă la ${itemTitle(w)} înainte de furtună?`;
  if (w.source === "C") return `Aplicăm soluția pe postul ${w.asset_id}?`;
  if (w.asset_type === "meter") return `Trimitem o echipă la contorul ${w.asset_id}?`;
  if (w.asset_type === "transformer_post") return `Verificăm postul ${w.asset_id}?`;
  return `Verificăm ${itemTitle(w)}?`;
}

/** Partea de sus a cardului „Nu sunt sigur.”: întrebarea, scorul modelului, valoarea, fereastra, clienții. */
export function QuestionBody({ item, scenario }: { item: WorkItem | null; scenario: string }) {
  const header = (
    <header className="flex items-center gap-3 px-6 pt-5">
      <Layers aria-hidden="true" size={26} strokeWidth={1.7} className="text-violet" />
      <h2 className="text-[22px] font-[700] tracking-[-0.01em]">Nu sunt sigur.</h2>
    </header>
  );
  if (!item) {
    return (
      <>
        {header}
        <p className="px-6 pt-3 text-[16px] text-ink-soft">Nimic nu așteaptă decizia ta.</p>
      </>
    );
  }
  const score = item.prediction.score;
  const win = item.time_window;
  const rows: { icon: typeof Coins; text: string; label: string }[] = [];
  if (Number.isFinite(item.impact.expected_value_lei)) rows.push({ icon: Coins, text: fmtLei(item.impact.expected_value_lei), label: "Valoare așteptată" });
  if (win?.start && win?.end) rows.push({ icon: CalendarDays, text: `${fmtTime(win.start)}–${fmtTime(win.end)}`, label: "Fereastra de timp" });
  else if (Number.isFinite(item.impact.urgency_hours)) rows.push({ icon: CalendarDays, text: `în ${fmtInt(item.impact.urgency_hours)} h`, label: "Urgență" });
  if (typeof item.impact.customers_affected === "number") rows.push({ icon: Users, text: plural(item.impact.customers_affected, "client", "clienți"), label: "Clienți afectați" });
  const tone: Tone = SOURCE_TONE_OF[item.source];
  return (
    <>
      {header}
      <p className="px-6 pt-2 text-[16.5px] text-ink-soft">
        <Link href={withQuery(`/lucrari/${encodeURIComponent(item.work_item_id)}`, scenario)} className="hover:text-ink hover:underline focus-visible:outline-2 focus-visible:outline-ring">
          {questionText(item)}
        </Link>
      </p>
      <div className="grid grid-cols-1 items-center justify-items-center gap-y-4 px-6 pt-5 @[440px]:grid-cols-[auto_1px_minmax(0,1fr)] @[440px]:justify-items-stretch @[440px]:gap-x-5">
        <div className="flex flex-col items-center gap-3">
          <Gauge value={score} label={roundPct(score)} sub="scorul modelului" tone={tone} size={186} />
          <Pill tone="orange" icon={UserRound} size="md" className="mt-1">
            Necesită o persoană
          </Pill>
        </div>
        <span aria-hidden="true" className="hidden h-[130px] w-px self-center bg-rule @[440px]:block" />
        <ul className="flex min-w-0 flex-col gap-3.5">
          {rows.map((r) => (
            <li key={r.label} className="flex items-center gap-3 text-[17px] font-[560] tabular-nums" title={r.label}>
              <r.icon aria-hidden="true" size={24} strokeWidth={1.6} className={TONE[r.icon === Coins ? "amber" : "grey"].text} />
              <span>
                {r.text}
                <span className="sr-only"> ({r.label})</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

/** Contorul A cu cel mai mare scor care e într-un traseu. */
export function SelectedMeter({ item, scenario }: { item: WorkItem; scenario: string }) {
  const s = item.prediction.score;
  return (
    <div className="px-6 pt-5">
      <div className="border-t border-rule pt-4">
        <p className="flex items-center gap-2.5 text-[15.5px] text-ink-soft">
          <Zap aria-hidden="true" size={20} strokeWidth={1.7} className="text-src-a" />
          Contor selectat
        </p>
        <div className="mt-2 flex items-center justify-between gap-3">
          <Link href={withQuery(`/lucrari/${encodeURIComponent(item.work_item_id)}`, scenario)} translate="no" className="text-[22px] font-[680] tracking-[-0.01em] whitespace-nowrap hover:underline focus-visible:outline-2 focus-visible:outline-ring">
            {item.asset_id}
          </Link>
          <Pill tone="violet" size="md" className="font-[600]">
            {roundPct(s)} defect
          </Pill>
        </div>
        <div className="mt-3">
          <Meter value={s} tone="blue" label={`Scor de defect ${roundPct(s)}`} />
        </div>
      </div>
    </div>
  );
}
