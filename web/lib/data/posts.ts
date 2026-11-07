import "server-only";
import type { Decision, WorkItem } from "@/lib/contracts";
import { apiPosts, apiUrl, isApiRequestError } from "./api";
import { readDemoPosts, readLossCost } from "./files";
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
}

/** Pragurile de culoare pentru harta posturilor (lei pierduți pe lună). Doar afișare, nu decizie. */
export const POST_COLOR_THRESHOLDS = { yellow: 150, red: 600 } as const;

export function colorFor(lossLeiMonth: number | null | undefined): string {
  if (lossLeiMonth == null || !Number.isFinite(lossLeiMonth)) return "necunoscut";
  if (lossLeiMonth >= POST_COLOR_THRESHOLDS.red) return "roșu";
  if (lossLeiMonth >= POST_COLOR_THRESHOLDS.yellow) return "galben";
  return "verde";
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

export function derivePosts(items: WorkItem[], decisions: Record<string, Decision>, lossCostLeiKwh: number | null): PostSummary[] {
  const posts = new Map<string, PostSummary & { _pts: [number, number][]; _kwh: number }>();
  const get = (id: string) => {
    let p = posts.get(id);
    if (!p) {
      p = { post_id: id, lat: 0, lon: 0, meters_flagged: 0, meter_work_item_ids: [], synthetic: true, derived: true, _pts: [], _kwh: 0 };
      posts.set(id, p);
    }
    return p;
  };
  for (const w of items) {
    if (w.asset_type === "transformer_post") {
      const p = get(w.asset_id);
      p.lat = w.location.lat;
      p.lon = w.location.lon;
      p.zone_id = w.location.zone_id;
      p.label = w.location.label ?? w.asset_id;
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
    if (_kwh > 0) {
      p.loss_kwh_day = +_kwh.toFixed(2);
      p.loss_lei_month = lossCostLeiKwh != null ? +(_kwh * 30 * lossCostLeiKwh).toFixed(0) : null;
    }
    p.color = colorFor(p.loss_lei_month);
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
  const lossCost = await readLossCost();
  if (result.data.length) {
    return { ...result, data: result.data.map((p) => ({ ...p, color: p.color && p.color !== "necunoscut" ? p.color : colorFor(p.loss_lei_month) })), derived: false, lossCost };
  }
  const view = await getPlanView(scenario);
  const data = view.data ? derivePosts(view.data.workItems, view.data.decisionsByWorkItemId, lossCost?.value ?? null) : [];
  return {
    data,
    source: view.source,
    fetchedAt: new Date().toISOString(),
    degradedReason: "posturile sunt derivate din lucrări (contoarele A pe post și posturile C), până vine bilanțul",
    derived: true,
    lossCost,
  };
}
