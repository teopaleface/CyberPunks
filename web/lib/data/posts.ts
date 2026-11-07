import "server-only";
import type { Decision, WorkItem } from "@/lib/contracts";
import { apiPosts, apiUrl, isApiRequestError } from "./api";
import { readDemoPosts, readLossCost, readPostThresholds } from "./files";
import { predictionLabelRo } from "./labels";
import { getPlanView } from "./index";
import { missing, ok, resolveData } from "./source";
import type { PostSummary, Sourced } from "./types";

/**
 * Posturile de transformare: întâi GET /posts (planificatorul), apoi posts.json din instantaneul demo.
 * Dacă niciuna nu există, le derivăm din lucrări: posturile C (tensiune) și contoarele A grupate pe
 * `extra.post_id`. Pierderea derivată vine din estimările modelului A (kWh pe zi), nu din bilanț, și e marcată așa.
 */

export interface PostsResult extends Sourced<PostSummary[]> {
  /** Posturile au fost derivate din lucrări (fără API, fără instantaneu). */
  derived: boolean;
  /** Costul energiei pierdute folosit la derivare, cu sursa din config/economics.yaml. */
  lossCost: { value: number; note: string } | null;
  /** Pragurile de culoare (lei pe lună), din config/planner.yaml. */
  thresholds: PostThresholds;
}

export interface PostThresholds {
  yellow: number;
  red: number;
}

/**
 * Pragurile de culoare pentru harta posturilor (lei pierduți pe lună), dacă lipsește config/planner.yaml.
 * Aceleași valori ca acolo (`posts`): galben de la 200, roșu de la 600. Doar afișare, nu decizie.
 */
export const DEFAULT_POST_THRESHOLDS: PostThresholds = { yellow: 200, red: 600 };

export function colorFor(lossLeiMonth: number | null | undefined, t: PostThresholds = DEFAULT_POST_THRESHOLDS): string {
  if (lossLeiMonth == null || !Number.isFinite(lossLeiMonth)) return "necunoscut";
  if (lossLeiMonth >= t.red) return "roșu";
  if (lossLeiMonth >= t.yellow) return "galben";
  return "verde";
}

// Planificatorul scrie culorile fără diacritice („rosu”); interfața folosește „roșu”.
const COLOR_ALIASES: Record<string, string> = {
  verde: "verde",
  green: "verde",
  galben: "galben",
  yellow: "galben",
  roșu: "roșu",
  rosu: "roșu",
  red: "roșu",
  necunoscut: "necunoscut",
  unknown: "necunoscut",
};

/** O culoare primită (API sau instantaneu) în forma interfeței; necunoscută sau lipsă: din pierdere. */
export function normalizePostColor(color: unknown, lossLeiMonth: number | null | undefined, t: PostThresholds = DEFAULT_POST_THRESHOLDS): string {
  const known = typeof color === "string" ? COLOR_ALIASES[color.trim().toLowerCase()] : undefined;
  return known && known !== "necunoscut" ? known : colorFor(lossLeiMonth, t);
}

/** Cauza din bilanț: codurile („furt_inainte_contor”) devin cuvinte; textul deja scris rămâne. */
export function postDiagnosisRo(diagnosis: unknown): string | null {
  if (typeof diagnosis !== "string" || !diagnosis.trim()) return null;
  const d = diagnosis.trim();
  return /^[a-z0-9_]+$/.test(d) ? predictionLabelRo(d) : d;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function normalize(list: unknown): PostSummary[] {
  if (!Array.isArray(list)) return [];
  return list.filter(
    (p): p is PostSummary =>
      typeof p === "object" && p !== null && typeof (p as PostSummary).post_id === "string" && num((p as PostSummary).lat) !== null && num((p as PostSummary).lon) !== null,
  );
}

export function derivePosts(
  items: WorkItem[],
  decisions: Record<string, Decision>,
  lossCostLeiKwh: number | null,
  thresholds: PostThresholds = DEFAULT_POST_THRESHOLDS,
): PostSummary[] {
  const posts = new Map<string, PostSummary & { _pts: [number, number][]; _kwh: number }>();
  const get = (id: string) => {
    let p = posts.get(id);
    if (!p) {
      p = { post_id: id, lat: 0, lon: 0, meters_flagged: 0, meter_work_item_ids: [], synthetic: true, derived: true, _pts: [], _kwh: 0 };
      posts.set(id, p);
    }
    return p;
  };
  const bilantPosts = new Set<string>();
  for (const w of items) {
    if (w.asset_type === "transformer_post") {
      const p = get(w.asset_id);
      p.lat = w.location.lat;
      p.lon = w.location.lon;
      p.zone_id = w.location.zone_id;
      p.label = w.location.label ?? w.asset_id;
      if (w.source === "A") {
        // lucrarea bilanțului pe post: pierderea și cauza vin de aici
        const extra = (w.extra ?? {}) as Record<string, unknown>;
        bilantPosts.add(w.asset_id);
        p.bilant_work_item_id = w.work_item_id;
        p.bilant_score = w.prediction.score;
        p.bilant_decision = decisions[w.work_item_id]?.decision ?? null;
        p.bilant_rule_id = decisions[w.work_item_id]?.rule_id ?? null;
        p.loss_lei_month = num(extra.lei_per_month) ?? p.loss_lei_month ?? null;
        p.loss_kwh_day = w.prediction.point_estimate ?? p.loss_kwh_day ?? null;
        p.diagnosis = predictionLabelRo(w.prediction.label);
      }
      if (w.source === "C") {
        p.voltage_p90_pu = w.prediction.point_interval?.[1] ?? w.prediction.point_estimate ?? null;
        p.c_work_item_id = w.work_item_id;
        p.c_decision = decisions[w.work_item_id]?.decision ?? null;
        p.c_rule_id = decisions[w.work_item_id]?.rule_id ?? null;
      }
      p.synthetic = w.data_quality.synthetic;
      continue;
    }
    const postId = (w.extra as Record<string, unknown> | undefined)?.post_id;
    if (w.source === "A" && typeof postId === "string") {
      const p = get(postId);
      p.meters_flagged = (p.meters_flagged ?? 0) + 1;
      p.meter_work_item_ids = [...(p.meter_work_item_ids ?? []), w.work_item_id];
      p._pts.push([w.location.lon, w.location.lat]);
      const kwh = num((w.extra as Record<string, unknown>).estimated_kwh_lost_per_day);
      // pierderea contează doar cât e de probabilă: scorul × kWh estimați
      if (kwh !== null) p._kwh += kwh * w.prediction.score;
    }
  }
  return [...posts.values()].map(({ _pts, _kwh, ...p }) => {
    if (!p.lat && _pts.length) {
      p.lon = _pts.reduce((s, x) => s + x[0], 0) / _pts.length;
      p.lat = _pts.reduce((s, x) => s + x[1], 0) / _pts.length;
      p.approx_position = true;
      p.label = p.label ?? p.post_id;
    }
    if (bilantPosts.has(p.post_id)) {
      p.derived = false; // pierderea vine din bilanț
    } else if (_kwh > 0) {
      p.loss_kwh_day = +_kwh.toFixed(2);
      p.loss_lei_month = lossCostLeiKwh != null ? +(_kwh * 30 * lossCostLeiKwh).toFixed(0) : null;
    }
    p.color = colorFor(p.loss_lei_month, thresholds);
    return p;
  });
}

export async function getPosts(scenario: string): Promise<PostsResult> {
  const result = await resolveData<PostSummary[]>(
    {
      api: async () => {
        const url = apiUrl("/posts", { scenario });
        try {
          const list = normalize(await apiPosts(scenario));
          return list.length ? ok(list, { detail: url }) : missing("API-ul nu are încă posturi");
        } catch (err) {
          if (isApiRequestError(err) && err.status === 404) return missing("API-ul nu are încă /posts");
          throw err;
        }
      },
      demo: async () => {
        const read = await readDemoPosts(scenario);
        const list = normalize(read?.data);
        return list.length ? ok(list, { detail: read!.files.join(", ") }) : missing("instantaneul demo nu are posturi");
      },
      fixtures: async () => missing("fixture-urile nu au posturi"),
    },
    [],
    { scenario },
  );
  const [lossCost, thresholds] = await Promise.all([readLossCost(), readPostThresholds().then((t) => t ?? DEFAULT_POST_THRESHOLDS)]);
  if (result.data.length) {
    const data = result.data.map((p) => ({
      ...p,
      color: normalizePostColor(p.color, p.loss_lei_month, thresholds),
      diagnosis: postDiagnosisRo(p.diagnosis),
    }));
    return { ...result, data, derived: false, lossCost, thresholds };
  }
  const view = await getPlanView(scenario);
  const data = view.data ? derivePosts(view.data.workItems, view.data.decisionsByWorkItemId, lossCost?.value ?? null, thresholds) : [];
  return {
    data,
    source: view.source,
    fetchedAt: new Date().toISOString(),
    degradedReason: data.some((p) => p.bilant_work_item_id)
      ? "posturile sunt adunate din lucrările planului: bilanțul pe post, contoarele A și posturile C"
      : "posturile sunt derivate din lucrări (contoarele A pe post și posturile C), până vine bilanțul",
    derived: !data.some((p) => p.bilant_work_item_id),
    lossCost,
    thresholds,
  };
}
