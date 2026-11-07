/**
 * Primul ecran, ca briefing: fraza zilei, trei cifre, rezumatul echipelor și următorul caz de decis.
 * Totul vine din PlanScreenData (nicio cifră inventată); funcție pură, fără cod de server.
 */
import type { Decision, WorkItem } from "@/lib/contracts";
import { fmtInt, plural, sentence } from "@/lib/format";
import { predictionLabelRo } from "@/lib/data/labels";
import { approxNumber, confidenceWord } from "@/lib/human";
import type { PlanScreenData } from "@/lib/plan-screen";
import { itemPlace, itemTitle } from "@/lib/plan-screen";

export interface CrewLine {
  crewId: string;
  base: string;
  region: string | null;
  stops: number;
  depart: string | null;
  back: string | null;
  /** Echipele de furtună rămân în zonă până la sfârșitul ferestrei de risc. */
  until: string | null;
  km: number | null;
  storm: boolean;
  firstSource: WorkItem["source"] | null;
}

export interface CrewGroup {
  label: string;
  /** Regiunea, pentru frază („3 echipe în Banat, pentru furtuna de la 15:00”). */
  region: string | null;
  storm: boolean;
  crews: CrewLine[];
  /** „între 08:30 și 15:26” sau „pentru furtuna de la 15:00”. */
  summary: string;
}

export interface Briefing {
  sentence: string;
  subline: string | null;
  numbers: { value: string; label: string; approx?: boolean; attention?: boolean }[];
  crewsUsed: number;
  crewsTotal: number;
  groups: CrewGroup[];
  next: { decision: Decision; item: WorkItem; place: string; what: string; confidence: string } | null;
  queueCount: number;
}

const hhmmOf = (iso: string | null | undefined) => (iso ? iso.slice(11, 16) : null);

function regionLabel(id: string | null, data: PlanScreenData): string {
  if (!id) return "Alte zone";
  const r = data.regions.find((x) => x.id === id);
  return r?.label ?? id;
}

// pe primul ecran opririle vin fără lucrare atașată (date ușoare); lucrarea se ia după ID
function itemsIndex(data: PlanScreenData): Map<string, WorkItem> {
  return new Map(data.items.map((w) => [w.work_item_id, w]));
}

export function crewLines(data: PlanScreenData): CrewLine[] {
  const depots = new Map(data.depots.map((d) => [d.depot_id, d]));
  const items = itemsIndex(data);
  const itemOf = (id: string) => items.get(id) ?? null;
  return data.routes.map((r) => {
    const stops = [...r.stops].sort((a, b) => a.seq - b.seq);
    const storm = stops.some((s) => (s.workItem ?? itemOf(s.work_item_id))?.source === "B");
    let until: string | null = null;
    if (!r.return_at && stops.length) {
      // ora din textul planului (fusul României), nu din fusul browserului
      const last = stops[stops.length - 1];
      const m = last.eta ? /T(\d{2}):(\d{2})/.exec(last.eta) : null;
      if (m) {
        const total = Number(m[1]) * 60 + Number(m[2]) + (last.duration_min ?? 0);
        until = `${String(Math.floor(total / 60) % 24).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
      }
    }
    const depot = depots.get(r.depot_id);
    return {
      crewId: r.crew_id,
      base: (depot?.label_ro ?? r.depot_id).replace(/^Bază operativă\s*/i, "").replace(/\s*\(simulată\)/, ""),
      region: depot?.region ?? null,
      stops: stops.length,
      depart: hhmmOf(r.depart_at),
      back: hhmmOf(r.return_at),
      until,
      km: typeof r.total_km === "number" ? r.total_km : null,
      storm,
      firstSource: stops[0] ? ((stops[0].workItem ?? itemOf(stops[0].work_item_id))?.source ?? null) : null,
    };
  });
}

/** Ora de început a furtunii pentru echipele trimise din timp (cea mai devreme fereastră B din trasee). */
function stormStart(data: PlanScreenData): string | null {
  const items = itemsIndex(data);
  const starts = data.routes
    .flatMap((r) => r.stops)
    .map((s) => s.workItem ?? items.get(s.work_item_id) ?? null)
    .filter((w): w is WorkItem => Boolean(w && w.source === "B" && w.time_window?.start))
    .map((w) => w.time_window!.start)
    .sort();
  return starts.length ? hhmmOf(starts[0]) : null;
}

/** De ce decide un om, într-o frază care nu se contrazice: abținere, încredere mică/medie sau motivul regulii. */
function whyHuman(d: Decision, w: WorkItem, conf: string): string {
  if (w.prediction.abstain) return "Modelul s-a abținut: nu poate decide singur.";
  if (w.prediction.confidence !== "high") return `Modelul nu e sigur: ${conf.replace("încredere ", "încrederea e ")}.`;
  const first = (d.reason_ro ?? "").split(/(?<=\.)\s/)[0]?.trim();
  return first ? sentence(first) : "Agentul cere decizia unui om.";
}

/** Titlul unui caz, cu locul: „Zona Ineu, Arad”, „PT-1182, Sector 3, București”, „Contor MTR-004149, PT-1081, Sector 3”. */
export function placeOf(w: WorkItem): string {
  const title = itemTitle(w);
  const place = itemPlace(w);
  if (!place || title.includes(place)) return title;
  if (place.includes(title)) return place;
  return `${title}, ${place}`;
}

export function toBriefing(data: PlanScreenData): Briefing {
  const s = data.summary;
  const lines = crewLines(data);
  const queue = Object.values(data.decisions).filter((d) => d.decision === "human_review");
  const itemsById = new Map(data.items.map((w) => [w.work_item_id, w]));

  const assigned = s.assigned ?? lines.reduce((n, c) => n + c.stops, 0);
  const crewsUsed = s.crews_used ?? lines.length;
  const first = assigned
    ? `Mâine: ${plural(assigned, "lucrare", "lucrări")} pentru ${plural(crewsUsed, "echipă", "echipe")}.`
    : "Mâine nu pleacă nicio echipă.";
  const second = queue.length
    ? `${plural(queue.length, "caz", "cazuri")} așteaptă decizia ta.`
    : "Nimic nu așteaptă decizia ta.";

  const stormCrews = lines.filter((c) => c.storm);
  const start = stormStart(data);
  const stormRegions = [...new Set(stormCrews.map((c) => regionLabel(c.region, data)))];
  const subline = stormCrews.length
    ? `${plural(stormCrews.length, "echipă pleacă", "echipe pleacă")}${stormRegions.length === 1 ? ` în ${stormRegions[0]}` : ""} înainte de furtuna${start ? ` de la ${start}` : ""}.`
    : null;

  const value = approxNumber(s.expected_value_lei ?? 0);
  const numbers: Briefing["numbers"] = [
    { value: fmtInt(assigned), label: assigned === 1 ? "lucrare în trasee" : "lucrări în trasee" },
    { value: fmtInt(queue.length), label: "așteaptă decizia ta", attention: queue.length > 0 },
    { value: value.value, label: "lei valoare așteptată", approx: value.approx },
  ];

  // grupuri: întâi echipele obișnuite, pe regiuni, apoi cele de furtună
  const groups: CrewGroup[] = [];
  const byRegion = new Map<string, CrewLine[]>();
  for (const c of lines.filter((x) => !x.storm)) {
    const key = regionLabel(c.region, data);
    byRegion.set(key, [...(byRegion.get(key) ?? []), c]);
  }
  for (const [label, crews] of byRegion) {
    const departs = crews.map((c) => c.depart).filter(Boolean).sort() as string[];
    const backs = crews.map((c) => c.back).filter(Boolean).sort() as string[];
    groups.push({
      label,
      region: label,
      storm: false,
      crews,
      summary: departs.length && backs.length ? `între ${departs[0]} și ${backs[backs.length - 1]}` : "",
    });
  }
  if (stormCrews.length) {
    groups.push({
      label: stormRegions.length === 1 ? `${stormRegions[0]}, pentru furtună` : "Pentru furtună",
      region: stormRegions.length === 1 ? stormRegions[0] : null,
      storm: true,
      crews: stormCrews,
      summary: start ? `pentru furtuna de la ${start}` : "înainte de furtună",
    });
  }

  let next: Briefing["next"] = null;
  const d0 = queue[0];
  const w0 = d0 ? itemsById.get(d0.work_item_id) : undefined;
  if (d0 && w0) {
    const conf = confidenceWord(w0.prediction.confidence, w0.prediction.score);
    next = {
      decision: d0,
      item: w0,
      place: placeOf(w0),
      what: `${sentence(predictionLabelRo(w0.prediction.label)).replace(/\.$/, "")}. ${whyHuman(d0, w0, conf)}`,
      confidence: conf,
    };
  }

  return {
    sentence: `${first} ${second}`,
    subline,
    numbers,
    crewsUsed,
    crewsTotal: data.crews.length,
    groups,
    next,
    queueCount: queue.length,
  };
}
