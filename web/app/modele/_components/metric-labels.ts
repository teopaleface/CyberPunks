/**
 * Metricile din rapoartele de evaluare (reports/<A|B|C>/metrics.json), în cuvinte simple:
 * eticheta, sensul (mai mare e mai bine sau mai mic e mai bine) și formatul românesc.
 * Cheile necunoscute rămân lizibile (underscore → spațiu), fără sens presupus.
 */
import type { Source } from "@/lib/contracts";
import { fmtDec, fmtInt, fmtLei, fmtSeconds } from "@/lib/format";

export type Better = "higher" | "lower" | "target" | "none";

export interface MetricMeta {
  label: string;
  better: Better;
  /** Metrica e o eroare (MAE, pinball, Brier): fraza de diferență spune „greșește mai puțin”. */
  error?: boolean;
  /** Pentru acoperirea intervalului: valoarea țintă (0,80 pentru P10–P90). */
  target?: number;
  /** Ce măsoară, pentru metrica principală. */
  explain?: string;
}

const BASE: Record<string, MetricMeta> = {
  precision_at_k: {
    label: "Precizie în primele K",
    better: "higher",
    explain: "Din contoarele puse de model în capul listei (primele K), câte au într-adevăr o problemă. 1 înseamnă că nicio vizită nu e degeaba.",
  },
  recall_at_k: { label: "Recall în primele K", better: "higher" },
  value_at_k_lei: { label: "Valoare găsită în primele K", better: "higher" },
  pr_auc: {
    label: "PR-AUC",
    better: "higher",
    explain: "Cât de bine pune modelul zilele cu avarii înaintea celor liniștite, pe toate pragurile. 1 e perfect; o ordine la întâmplare ia cât prevalența.",
  },
  roc_auc: { label: "ROC-AUC", better: "higher" },
  brier: { label: "Scor Brier (calibrare)", better: "lower", error: true },
  ece: { label: "Eroare de calibrare (ECE)", better: "lower", error: true },
  log_loss: { label: "Log loss", better: "lower", error: true },
  precision_at_thr: { label: "Precizie la prag", better: "higher" },
  recall_at_thr: { label: "Recall la prag", better: "higher" },
  f1_at_thr: { label: "F1 la prag", better: "higher" },
  recall_severe_at_thr: { label: "Recall pe evenimente severe", better: "higher" },
  recall_extreme_at_thr: { label: "Recall pe evenimente extreme", better: "higher" },
  alerts_per_100_zone_days: { label: "Alarme la 100 de zile-zonă", better: "lower" },
  pinball_q10: { label: "Pierdere pinball P10", better: "lower", error: true },
  pinball_q50: { label: "Pierdere pinball P50", better: "lower", error: true },
  pinball_q90: { label: "Pierdere pinball P90", better: "lower", error: true },
  pinball_mean: { label: "Pierdere pinball medie", better: "lower", error: true },
  coverage_p10_p90: { label: "Acoperirea intervalului P10–P90 (ținta 0,80)", better: "target", target: 0.8 },
  prevalence: { label: "Prevalența în setul de test", better: "none" },
  decision_threshold: { label: "Pragul de decizie", better: "none" },
  pr_auc_gust_rule: { label: "PR-AUC al regulii rafalelor", better: "none" },
  pr_auc_clim_month: { label: "PR-AUC al climatologiei pe lună", better: "none" },
  loso_pr_auc_mean: { label: "PR-AUC pe state nevăzute (medie)", better: "higher" },
  loso_clim_month_pr_auc_mean: { label: "PR-AUC al climatologiei pe state nevăzute", better: "none" },
  mae_vmax_pu: {
    label: "Eroarea medie a tensiunii maxime (MAE)",
    better: "lower",
    error: true,
    explain: "Cu cât greșește, în medie, tensiunea maximă a zilei pe un post. 1 pu e tensiunea nominală; limita e 1,10 pu.",
  },
  rmse_vmax_pu: { label: "RMSE al tensiunii maxime", better: "lower", error: true },
  interval_width_pu: { label: "Lățimea intervalului P10–P90", better: "lower" },
  pr_auc_exceed: { label: "PR-AUC pentru depășirea de 1,10 pu", better: "higher" },
  roc_auc_exceed: { label: "ROC-AUC pentru depășirea de 1,10 pu", better: "higher" },
  recall_exceed: { label: "Recall pe depășiri", better: "higher" },
  precision_exceed: { label: "Precizie pe depășiri", better: "higher" },
  exceed_rate: { label: "Cât de des apar depășiri", better: "none" },
  surrogate_seconds_300_posts_day: { label: "Timp de calcul pentru 300 de posturi, o zi", better: "lower" },
  surrogate_seconds_300_posts_hourly_series: { label: "Timp de calcul pentru 300 de posturi, serie orară", better: "lower" },
  powerflow_seconds_300_posts_day_pandapower: { label: "Circulație de puteri completă (pandapower), 300 de posturi", better: "none" },
};

/** Prefixe: alt set de test sau altă metodă de referință. Metodele de referință nu primesc sens. */
const CONTEXT: [prefix: string, label: string, reference: boolean][] = [
  ["subtle_vee_", "regula VEE pe anomalii subtile", true],
  ["sgcc_vee_", "regula VEE pe SGCC", true],
  ["sgcc_iforest_", "Isolation Forest pe SGCC", true],
  ["iforest_", "Isolation Forest", true],
  ["vee_", "regula VEE", true],
  ["subtle_", "pe anomalii subtile", false],
  ["sgcc_", "pe SGCC (furturi reale)", false],
  ["sunny_", "în zilele însorite", false],
  ["loso_", "pe state nevăzute", false],
];

export function metricMeta(key: string): MetricMeta {
  const direct = BASE[key];
  if (direct) return direct;
  for (const [prefix, context, reference] of CONTEXT) {
    if (!key.startsWith(prefix)) continue;
    const base = BASE[key.slice(prefix.length)];
    if (base) {
      return { label: `${base.label}, ${context}`, better: reference ? "none" : base.better, error: base.error, target: base.target };
    }
  }
  return { label: key.replaceAll("_", " "), better: "none" };
}

/** Valoarea unei metrici, în format românesc, cu unitatea din numele cheii. */
export function fmtMetric(key: string, v: number): string {
  if (!Number.isFinite(v)) return "–";
  if (key.endsWith("_lei")) return fmtLei(v);
  if (key.includes("seconds")) return fmtSeconds(v);
  if (key.endsWith("_pct")) return `${fmtDec(v, 1)}%`;
  if (key.endsWith("_kwh_day")) return `${fmtDec(v, 1)} kWh`;
  if (key.endsWith("_pu")) return `${fmtDec(v, Math.abs(v) < 0.1 ? 4 : 3)} pu`;
  const a = Math.abs(v);
  if (Number.isInteger(v) && a >= 10) return fmtInt(v);
  if (a >= 100) return fmtInt(v);
  if (a >= 10) return fmtDec(v, 1);
  if (a >= 0.1 || a === 0) return fmtDec(v, 2);
  if (a >= 0.01) return fmtDec(v, 3);
  return fmtDec(v, 4);
}

/** 1: modelul e mai bun; -1: baseline-ul e mai bun; 0: egal sau fără sens. */
export function compare(meta: MetricMeta, model: number, baseline: number): 1 | -1 | 0 {
  if (meta.better === "none" || model === baseline) return 0;
  if (meta.better === "higher") return model > baseline ? 1 : -1;
  if (meta.better === "lower") return model < baseline ? 1 : -1;
  const t = meta.target ?? 0.8;
  const dm = Math.abs(model - t);
  const db = Math.abs(baseline - t);
  return dm === db ? 0 : dm < db ? 1 : -1;
}

/** Diferența în cuvinte: „Cu 0,48 mai bun decât baseline-ul (de 1,9 ori mai mare).” */
export function deltaSentence(key: string, meta: MetricMeta, model: number, baseline: number): string {
  const c = compare(meta, model, baseline);
  const d = fmtMetric(key, Math.abs(model - baseline));
  if (c === 0) return meta.better === "none" ? "" : "La egalitate cu baseline-ul.";
  if (c === -1) return `Cu ${d} mai slab decât baseline-ul.`;
  if (meta.better === "lower") {
    const ratio = model > 0 ? baseline / model : null;
    const times = ratio && ratio >= 1.2 ? `, de ${fmtDec(ratio, 1)} ori mai puțin` : "";
    return meta.error ? `Greșește cu ${d} mai puțin decât baseline-ul${times}.` : `Cu ${d} mai bun decât baseline-ul${times}.`;
  }
  const ratio = baseline > 0 ? model / baseline : null;
  return `Cu ${d} mai bun decât baseline-ul${ratio && ratio >= 1.2 ? ` (de ${fmtDec(ratio, 1)} ori mai mare)` : ""}.`;
}

/** Pas „rotund” pentru axă (1, 2, 2,5, 5 × 10^k). */
export function niceStep(raw: number): number {
  if (!(raw > 0)) return 1;
  const exp = 10 ** Math.floor(Math.log10(raw));
  const f = raw / exp;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * exp;
}

/** Axa de la zero: capătul (multiplu de pas) și gradațiile. */
export function niceAxis(max: number, count = 4): { max: number; ticks: number[] } {
  const step = niceStep((max || 1) / count);
  const top = Math.max(step, Math.ceil(max / step - 1e-9) * step);
  const ticks: number[] = [];
  for (let t = 0; t <= top + step / 2; t += step) ticks.push(+t.toFixed(10));
  return { max: top, ticks };
}

const tickFmt = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 3 });
export function fmtTick(v: number): string {
  return tickFmt.format(v);
}

/** Seturile publice externe pe care e validat un model (din sursele citate în raport). */
export const EXTERNAL_DATASET = /SGCC|London|Londra|EAGLE|SimBench|PVGIS/i;

/** Numele sursei (până la prima virgulă sau „:” din afara parantezelor) și restul citării. */
export function splitCitation(s: string): { name: string; rest: string } {
  let depth = 0;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch === "(") depth++;
    else if (ch === ")") depth = Math.max(0, depth - 1);
    else if (depth === 0 && (ch === "," || ch === ":") && i > 0) {
      return { name: s.slice(0, i).trim(), rest: s.slice(i + 1).trim() };
    }
  }
  return { name: s.trim(), rest: "" };
}

/** Baseline-ul: ID-ul scurt și explicația din paranteză, dacă există. */
export function splitBaseline(id: string): { short: string; detail: string } {
  const m = /^([^()]+?)\s*\((.+)\)\s*$/.exec(id);
  return m ? { short: m[1].trim(), detail: m[2].trim() } : { short: id.trim(), detail: "" };
}

/** Comanda așteptată pentru fiecare model, pentru ecranul gol (modulele din src/cyberpunks). */
export const EXPECTED_CMD: Record<Source, string> = {
  A: "uv run python -m cyberpunks.a_contoare.evaluate",
  B: "uv run python -m cyberpunks.b_furtuna.evaluate",
  C: "uv run python -m cyberpunks.c_prosumatori.evaluate",
};
