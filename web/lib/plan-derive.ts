/**
 * Calcule pentru linia de timp a echipelor, din cifrele planului. Fără cod de server.
 *
 * Planul dă, pentru fiecare oprire, ora estimată de sosire (eta), durata și km de la oprirea dinainte,
 * plus totalurile traseului (km, minute de drum). Nu dă ora de plecare din bază și nici pe cea de
 * întoarcere: le estimăm împărțind minutele de drum proporțional cu km fiecărui segment, și le marcăm
 * ca aproximative („cca”). Dacă planificatorul începe să trimită `depart_at`/`return_at`, le folosim pe acelea.
 */
import type { Route, Stop, WorkItem } from "@/lib/contracts";
import { minutesOfDay, minutesOfPlanDay, parseHHMM } from "@/lib/format";

export interface TimelineBlock {
  stop: Stop;
  workItemId: string;
  /** Minutul zilei la care începe lucrul. */
  start: number;
  end: number;
  /** De unde vine echipa (minutul la care a terminat oprirea dinainte sau a plecat din bază). */
  from: number;
  travelKm: number;
}

export interface CrewTimeline {
  crewId: string;
  depotId: string;
  depart: number;
  departApprox: boolean;
  back: number;
  backApprox: boolean;
  returnKm: number;
  blocks: TimelineBlock[];
  totalKm: number;
  totalWorkMin: number;
  totalTravelMin: number;
}

type RouteLike = Pick<Route, "crew_id" | "depot_id" | "total_km" | "total_work_min" | "total_travel_min"> & {
  stops: Stop[];
  depart_at?: string | null;
  return_at?: string | null;
};

export function crewTimeline(route: RouteLike, shiftStart = "08:00", planDate?: string): CrewTimeline {
  const mins = (iso: string) => (planDate ? minutesOfPlanDay(iso, planDate) : minutesOfDay(iso));
  const stops = route.stops.toSorted((a, b) => a.seq - b.seq);
  const shift0 = parseHHMM(shiftStart);
  const legKm = stops.reduce((s, x) => s + x.travel_km, 0);
  const returnKm = Math.max(0, +(route.total_km - legKm).toFixed(1));
  const kmAll = legKm + returnKm;
  const minPerKm = kmAll > 0 ? route.total_travel_min / kmAll : 0;

  let depart: number;
  let departApprox = true;
  if (route.depart_at) {
    depart = mins(route.depart_at);
    departApprox = false;
  } else if (stops.length) {
    depart = Math.max(shift0, mins(stops[0].eta) - Math.round(stops[0].travel_km * minPerKm));
  } else {
    depart = shift0;
  }

  const blocks: TimelineBlock[] = [];
  let t = depart;
  for (const s of stops) {
    const start = mins(s.eta);
    const end = start + s.duration_min;
    blocks.push({ stop: s, workItemId: s.work_item_id, start, end, from: t, travelKm: s.travel_km });
    t = end;
  }

  let back: number;
  let backApprox = true;
  if (route.return_at) {
    back = mins(route.return_at);
    backApprox = false;
  } else {
    back = t + Math.round(returnKm * minPerKm);
  }

  return {
    crewId: route.crew_id,
    depotId: route.depot_id,
    depart,
    departApprox,
    back,
    backApprox,
    returnKm,
    blocks,
    totalKm: route.total_km,
    totalWorkMin: route.total_work_min,
    totalTravelMin: route.total_travel_min,
  };
}

/** Fereastra de timp a unei lucrări, în minutele zilei (B: înainte și în timpul furtunii; C: la prânz). */
export function workItemWindow(
  w: Pick<WorkItem, "time_window">,
  planDate?: string,
): { start: number; end: number; endsNextDay: boolean } | null {
  if (!w.time_window) return null;
  const mins = (iso: string) => (planDate ? minutesOfPlanDay(iso, planDate) : minutesOfDay(iso));
  const start = mins(w.time_window.start);
  let end = mins(w.time_window.end);
  const endsNextDay = end <= start;
  if (endsNextDay) end += 1440;
  return { start, end, endsNextDay };
}

/** Intervalul orar pe care îl arată linia de timp: tura, extinsă cât să încapă ferestrele importante. */
export function timelineRange(
  shift: { start: string; end: string } | null,
  extras: { start: number; end: number }[] = [],
): { start: number; end: number } {
  const s0 = parseHHMM(shift?.start ?? "08:00");
  const s1 = parseHHMM(shift?.end ?? "16:00");
  let start = s0;
  let end = s1;
  for (const e of extras) {
    start = Math.min(start, e.start);
    end = Math.max(end, e.end);
  }
  // rotunjim la ora întreagă, cu o jumătate de oră de aer la capete
  start = Math.floor((start - 30) / 60) * 60;
  end = Math.ceil((end + 30) / 60) * 60;
  return { start: Math.max(0, start), end: Math.min(30 * 60, end) };
}
