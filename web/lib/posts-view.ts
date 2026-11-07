/**
 * Posturile pentru ecranele „Posturile” și „Post”: regiunea, localitatea, culoarea, recomandarea,
 * filtrele și cuvintele pentru cauze. Cod fără server, ca să poată fi testat.
 */
import type { PostSummary } from "@/lib/data/types";

export type PostColor = "verde" | "galben" | "roșu" | "necunoscut";

/** Planificatorul scrie „rosu”; interfața folosește „roșu”. */
export function postColor(p: Pick<PostSummary, "color" | "loss_lei_month">, t = { yellow: 200, red: 600 }): PostColor {
  const c = (p.color ?? "").toString().trim().toLowerCase();
  if (c === "verde" || c === "green") return "verde";
  if (c === "galben" || c === "yellow") return "galben";
  if (c === "roșu" || c === "rosu" || c === "red") return "roșu";
  const v = p.loss_lei_month;
  if (v == null || !Number.isFinite(v)) return "necunoscut";
  return v >= t.red ? "roșu" : v >= t.yellow ? "galben" : "verde";
}

/** Codul județului din începutul lui `zone_id` („IF-AFUMATI”, „B-S6”) și numele județului. */
export const COUNTY_BY_CODE: Record<string, string> = {
  B: "București",
  IF: "Ilfov",
  GR: "Giurgiu",
  CT: "Constanța",
  TL: "Tulcea",
  CL: "Călărași",
  IL: "Ialomița",
  TM: "Timiș",
  AR: "Arad",
  CS: "Caraș-Severin",
  HD: "Hunedoara",
};

const norm = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

export interface AreaRegions {
  [id: string]: { label_ro?: string; counties?: string[] };
}

export function countyOfPost(p: Pick<PostSummary, "zone_id">): string | null {
  const code = (p.zone_id ?? "").split("-")[0]?.toUpperCase();
  return (code && COUNTY_BY_CODE[code]) || null;
}

/** Regiunea postului (id din config/area.yaml), după județ. */
export function regionOfPost(p: Pick<PostSummary, "zone_id">, regions: AreaRegions): string | null {
  const county = countyOfPost(p);
  if (!county) return null;
  for (const [id, r] of Object.entries(regions)) if ((r.counties ?? []).some((c) => norm(c) === norm(county))) return id;
  return null;
}

/** „PT-1269, Afumați (sintetic)” → „Afumați”. */
export function postPlace(p: Pick<PostSummary, "label" | "post_id" | "zone_id">): string {
  const base = (p.label ?? "").replace(/^PT-[\w-]+,\s*/, "").replace(/\s*\(sintetic\)\s*$/i, "").trim();
  return base && base !== p.post_id ? base : (p.zone_id ?? "");
}

export const RECOMMENDATION: Record<PostColor, { label: string; tone: "amber" | "violet" | "blue" | "grey" }> = {
  roșu: { label: "Inspect", tone: "amber" },
  galben: { label: "Investigate", tone: "violet" },
  verde: { label: "Monitor", tone: "blue" },
  necunoscut: { label: "No energy balance", tone: "grey" },
};

export type StatusFilter = "toate" | "verde" | "galben" | "roșu";

export interface PostRow {
  id: string;
  lat: number;
  lon: number;
  region: string | null;
  place: string;
  loss: number | null;
  color: PostColor;
  meters: number;
  diagnosis: string | null;
  voltage: number | null;
  title: string;
}

export function filterRows(rows: PostRow[], f: { region: string; status: StatusFilter; q: string }): PostRow[] {
  const q = norm(f.q);
  return rows.filter(
    (r) =>
      (f.region === "toate" || r.region === f.region) &&
      (f.status === "toate" || r.color === f.status) &&
      (!q || norm(`${r.id} ${r.place} ${r.title}`).includes(q)),
  );
}

export function sortRows(rows: PostRow[], key: "post" | "loss", dir: "asc" | "desc"): PostRow[] {
  const s = dir === "asc" ? 1 : -1;
  return rows.toSorted((a, b) => {
    if (key === "post") return s * a.id.localeCompare(b.id, "ro", { numeric: true });
    const av = a.loss ?? -Infinity;
    const bv = b.loss ?? -Infinity;
    return av === bv ? a.id.localeCompare(b.id, "ro", { numeric: true }) : s * (av - bv);
  });
}

export function boundsOfRows(rows: { lat: number; lon: number }[], fallback: [number, number, number, number]): [number, number, number, number] {
  if (!rows.length) return fallback;
  let w = Infinity, s = Infinity, e = -Infinity, n = -Infinity;
  for (const r of rows) {
    w = Math.min(w, r.lon);
    e = Math.max(e, r.lon);
    s = Math.min(s, r.lat);
    n = Math.max(n, r.lat);
  }
  const m = Math.max(0.04, (e - w) * 0.06, (n - s) * 0.06);
  return [w - m, s - m, e + m, n + m];
}

export type CauseBand = "Likely" | "Possible" | "Unlikely";

/** Cuvântul pentru probabilitate: nu „Confirmat”, fiindcă nu a confirmat un om. */
export function causeBand(p: number): CauseBand {
  return p >= 0.6 ? "Likely" : p >= 0.2 ? "Possible" : "Unlikely";
}

export function causeProbs(extra: unknown): { key: string; p: number }[] {
  const raw = (extra as Record<string, unknown> | undefined)?.diagnosis_proba;
  if (typeof raw !== "object" || raw === null) return [];
  return Object.entries(raw as Record<string, unknown>)
    .filter((e): e is [string, number] => typeof e[1] === "number" && Number.isFinite(e[1]))
    .map(([key, p]) => ({ key, p }))
    .toSorted((a, b) => b.p - a.p);
}

/** Pagina postului: secțiunile filtrabile din chipuri. */
export const POST_SECTIONS = ["toate", "bilant", "contoare", "tensiune", "cauze", "remediere", "lucrari", "jurnal"] as const;
export type PostSection = (typeof POST_SECTIONS)[number];
export function parseSection(v: string | null | undefined): PostSection {
  return (POST_SECTIONS as readonly string[]).includes(v ?? "") ? (v as PostSection) : "toate";
}
