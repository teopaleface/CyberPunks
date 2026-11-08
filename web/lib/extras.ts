/**
 * Câmpurile din `WorkItem.extra` care au contract (src/cyberpunks/common/contracts.py), citite cu grijă:
 * `extra` e liber, deci verificăm forma înainte să afișăm ceva.
 */
import type { Confidence, CrewSkill, RecommendedAction, WorkItem } from "@/lib/contracts";

/** O treaptă din scara de soluții pentru tensiune (C). */
export interface RemedyOption {
  action: RecommendedAction;
  cost_lei: number;
  p90_after_pu: number;
  effect_pu: number;
  confidence: Confidence;
  duration_min: number;
  needs_crew: boolean;
  crew_skill?: CrewSkill | null;
  combinable?: boolean;
  note_ro: string;
  participation_rate?: number | null;
  risk_hours?: string[];
  inverter_trips_avoided?: number | null;
  message_preview_ro?: string | null;
  customers_targeted?: number | null;
  battery_kwh_total?: number | null;
  revenue_lei?: number | null;
  payback_years?: number | null;
}

/** Confirmarea independentă bilanț + contor (lucrări A pe contoare). */
export interface BilantFusion {
  post_id: string;
  bilant_prediction_id: string;
  post_excess_loss_kwh_day: number;
  post_excess_loss_lei_month: number;
  a_score: number;
  combined_score: number;
  note_ro: string;
}

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const num = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

export function remedyOptions(w: WorkItem): RemedyOption[] {
  const raw = (w.extra as Record<string, unknown> | undefined)?.remedy_options;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (o): o is RemedyOption =>
      isObj(o) && typeof o.action === "string" && num(o.cost_lei) && num(o.p90_after_pu) && typeof o.note_ro === "string",
  );
}

export function bilantFusion(w: WorkItem): BilantFusion | null {
  const raw = (w.extra as Record<string, unknown> | undefined)?.fusion;
  if (!isObj(raw) || typeof raw.post_id !== "string" || !num(raw.combined_score) || !num(raw.a_score)) return null;
  return raw as unknown as BilantFusion;
}

/** Lucrare a bilanțului pe post (sursa A, la nivel de post de transformare). */
export function isBilantPost(w: WorkItem): boolean {
  return w.source === "A" && w.asset_type === "transformer_post";
}

export const BILANT_LABEL = "Simulation using public data, designed for PPC data";

/**
 * P90 de pornire al scării de soluții (punctul gol): `extra.ladder_base_p90_pu`, baza din care pornesc treptele;
 * altfel cel din combinația aleasă, apoi P90 al modelului.
 */
export function ladderBaseP90(w: WorkItem, choice?: { p90_before_pu?: number | null } | null): number | null {
  const extra = (w.extra ?? {}) as Record<string, unknown>;
  const value = (v: unknown): number | null => (num(v) ? v : null);
  return value(extra.ladder_base_p90_pu) ?? value(choice?.p90_before_pu) ?? w.prediction.point_interval?.[1] ?? null;
}

/** Combinația de trepte aleasă de agent pentru tensiune: `extra.ladder_choice`, altfel cea din /remedies. */
export function ladderChoice(w: WorkItem, choice?: { chosen?: string[] | null } | null): string[] {
  const extra = (w.extra ?? {}) as Record<string, unknown>;
  const fromItem = Array.isArray(extra.ladder_choice) ? extra.ladder_choice.filter((a): a is string => typeof a === "string") : [];
  return fromItem.length ? fromItem : (choice?.chosen ?? []).filter((a): a is string => typeof a === "string");
}
