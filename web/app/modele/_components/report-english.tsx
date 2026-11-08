import { englishText } from "@/lib/english";
import type { Source } from "@/lib/contracts";
import { fmtDec } from "@/lib/format";
import { compare, fmtMetric, metricMeta, type MetricMeta } from "./metric-labels";

const METRIC: Record<string, string> = {
  precision_at_k: "Precision in the top K",
  recall_at_k: "Recall in the top K",
  value_at_k_lei: "Value found in the top K",
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  brier: "Brier score, calibration",
  ece: "Calibration error, ECE",
  log_loss: "Log loss",
  precision_at_thr: "Precision at threshold",
  recall_at_thr: "Recall at threshold",
  f1_at_thr: "F1 at threshold",
  recall_severe_at_thr: "Recall on severe events",
  recall_extreme_at_thr: "Recall on extreme events",
  alerts_per_100_zone_days: "Alerts per 100 area-days",
  pinball_q10: "P10 pinball loss",
  pinball_q50: "P50 pinball loss",
  pinball_q90: "P90 pinball loss",
  pinball_mean: "Mean pinball loss",
  coverage_p10_p90: "P10–P90 interval coverage, target 0.80",
  prevalence: "Test set prevalence",
  decision_threshold: "Decision threshold",
  pr_auc_gust_rule: "Gust rule PR-AUC",
  pr_auc_clim_month: "Monthly climatology PR-AUC",
  loso_pr_auc_mean: "PR-AUC on unseen states, mean",
  loso_clim_month_pr_auc_mean: "Climatology PR-AUC on unseen states",
  mae_vmax_pu: "Mean absolute error of maximum voltage",
  rmse_vmax_pu: "RMSE of maximum voltage",
  interval_width_pu: "P10–P90 interval width",
  pr_auc_exceed: "PR-AUC for voltage above 1.10 pu",
  roc_auc_exceed: "ROC-AUC for voltage above 1.10 pu",
  recall_exceed: "Overvoltage recall",
  precision_exceed: "Overvoltage precision",
  exceed_rate: "Overvoltage frequency",
  surrogate_seconds_300_posts_day: "Compute time for 300 substations, one day",
  surrogate_seconds_300_posts_hourly_series: "Compute time for 300 substations, hourly series",
  powerflow_seconds_300_posts_day_pandapower: "Full pandapower load flow, 300 substations",
};
const PREFIX: [string, string][] = [
  ["subtle_vee_", "VEE rule on subtle anomalies"],
  ["sgcc_vee_", "VEE rule on SGCC"],
  ["sgcc_iforest_", "Isolation Forest on SGCC"],
  ["iforest_", "Isolation Forest"],
  ["vee_", "VEE rule"],
  ["subtle_", "subtle anomalies"],
  ["sgcc_", "SGCC real theft labels"],
  ["sunny_", "sunny days"],
  ["loso_", "unseen states"],
];

export function englishMetricMeta(key: string): MetricMeta {
  const meta = metricMeta(key);
  if (METRIC[key]) return { ...meta, label: METRIC[key] };
  for (const [prefix, context] of PREFIX) {
    const label = key.startsWith(prefix) ? METRIC[key.slice(prefix.length)] : null;
    if (label) return { ...meta, label: `${label}, ${context}` };
  }
  return { ...meta, label: key.replaceAll("_", " ") };
}

export function englishMetricExplanation(source: Source, key: string): string | null {
  if (key.includes("precision_at_k")) return "Share of genuine problems among the top K ranked meters. K follows the inspection capacity used in the report.";
  if (key.includes("recall_at_k")) return "Share of all genuine problems found in the top K ranked meters.";
  if (key === "pr_auc") return source === "A"
    ? "How well the model ranks faulty or tampered meters above normal meters across decision thresholds. Higher is better."
    : "How well the model ranks outage days above quiet days across decision thresholds. Higher is better.";
  if (key === "roc_auc") return "How often a positive case ranks above a negative case. 0.5 is random ordering; 1 is perfect.";
  if (key === "mae_vmax_pu") return "Average error in a substation's daily maximum voltage. 1 pu is nominal voltage; the upper limit is 1.10 pu.";
  return null;
}

export function englishMetricDelta(key: string, meta: MetricMeta, model: number, baseline: number): string {
  const c = compare(meta, model, baseline);
  if (c === 0) return meta.better === "none" ? "" : "Equal to the baseline.";
  const delta = fmtMetric(key, Math.abs(model - baseline));
  if (c === -1) return `${delta} worse than the baseline.`;
  if (meta.better === "lower") {
    const ratio = model > 0 ? baseline / model : null;
    const suffix = ratio && ratio >= 1.2 ? `, ${fmtDec(ratio, 1)} times lower` : "";
    return meta.error ? `Error is ${delta} lower than the baseline${suffix}.` : `${delta} better than the baseline${suffix}.`;
  }
  const ratio = baseline > 0 ? model / baseline : null;
  return `${delta} better than the baseline${ratio && ratio >= 1.2 ? `, ${fmtDec(ratio, 1)} times higher` : ""}.`;
}

// Complete report phrases only. These translations leave source IDs and values intact.
const REPORT: [string, string][] = [
  ["Agentul față de strategii simple, pe o lume SINTETICĂ cu adevărul cunoscut (scoruri calibrate prin construcție).", "Scores are calibrated by construction in a synthetic world with known outcomes."],
  ["Agentul față de strategii simple, pe o lume sintetică cu adevărul cunoscut (scoruri calibrate prin construcție).", "Agent vs. simple strategies in a synthetic world with known outcomes. Scores are calibrated by construction."],
  ["Pe o lume sintetică cu adevărul cunoscut (scoruri calibrate prin construcție).", "Synthetic world with known outcomes. Scores are calibrated by construction."],
  ["pe o lume sintetică cu adevărul cunoscut (scoruri calibrate prin construcție).", "Synthetic world with known outcomes. Scores are calibrated by construction."],
  ["Fără pragul etic (vizită și sub scorul 0,5, dacă merită)", "Without the ethical score threshold: visits below a score of 0.5 if economically worthwhile"],
  ["Aceleași reguli, trasee făcute greedy în loc de OR-Tools", "Same rules, with greedy routing instead of OR-Tools"],
  ["Londra: gospodării nevăzute și perioadă ulterioară (test sept. 2013 - feb. 2014, antrenare dec. 2012 - aug. 2013); SGCC: 20% din clienți, stratificat, nevăzuți. K = 1% din contoare.", "London: unseen households and a later period. Test September 2013 to February 2014; training December 2012 to August 2013. SGCC: stratified 20% holdout of unseen customers. K = 1% of meters."],
  ["Metrica principală: precizia@K pe problemele subtile (testul Londra fără defectele evidente pe care le prinde orice regulă VEE: contor oprit, blocat, citiri negative, goluri); a doua: precizia@K pe SGCC, cu etichete reale de furt.", "Primary metric: precision at K on subtle London anomalies, excluding stopped or stuck meters, negative readings and missing data. Secondary metric: precision at K on SGCC real theft labels."],
  ["pe timp: antrenare 2023-2024, test 2025 (an nevăzut), 80 comitate din 8 state SUA; plus state nevăzute (leave-one-state-out) în reports/B/metrics_detail.json", "Time split: training 2023–2024, test 2025, an unseen year, across 80 counties in 8 US states. Leave-one-state-out results are in reports/B/metrics_detail.json."],
  ["leave-one-topology-out (6 topologii SimBench) × luni nevăzute (antrenare < 2025-01-01, test ≥ 2025-01-01)", "Leave-one-topology-out across 6 SimBench topologies and unseen months. Training before 2025-01-01; test from 2025-01-01."],
  ["clasificare dezechilibrată: contor normal / defect / manipulat (scor calibrat de problemă, clasament sub capacitate)", "Classify normal, faulty or tampered meters. Calibrated problem scores rank cases within available capacity."],
  ["clasificare dezechilibrată calibrată (vârf ≥ 1% din clienți fără curent, zonă × zi) + regresie cuantilă P10/P50/P90 a vârfului, în zilele cu eveniment", "Predict outages affecting at least 1% of customers per area-day, with calibrated probability and P10/P50/P90 estimates of the outage peak on event days."],
  ["regresie cuantilă a tensiunii maxime zilnice pe post (P10, P50, P90) + clasificare calibrată P(tensiune > 1,10 pu)", "Predict daily maximum substation voltage at P10/P50/P90 and the calibrated probability of voltage above 1.10 pu."],
  ["zero >= 7 zile sau scădere >= 50% față de propriul istoric", "Zero readings for at least 7 days or a drop of at least 50% against the meter's own history"],
  ["regula VEE completă e în metrics, cu prefixul vee_", "The full VEE rule is included in metrics under the vee_ prefix"],
  ["rata istorică pe comitat și lună, 2023-2024", "Historical rate per county and month, 2023–2024"],
  ["Low Carbon London, UK Power Networks, consum real la 30 min, CC BY 4.0 (London Datastore); defecte și furturi injectate de noi (SINTETIC)", "Low Carbon London, UK Power Networks. Real 30-minute consumption, CC BY 4.0, London Datastore. Fault and theft labels injected by our team are SYNTHETIC."],
  ["SGCC, State Grid Corporation of China, consum zilnic cu etichete reale de furt (Zheng et al. 2018, IEEE TII, DOI 10.1109/TII.2017.2785963); metricile sgcc_* sunt ale modelului a-lgbm-sgcc", "SGCC, State Grid Corporation of China. Daily consumption with real theft labels. Zheng et al. 2018, IEEE TII, DOI 10.1109/TII.2017.2785963. Metrics with the sgcc_* prefix use model a-lgbm-sgcc."],
  ["Open-Meteo Historical Weather API (archive, best_match: ERA5/ERA5-Land/ECMWF IFS), variabile zilnice, CC BY 4.0", "Open-Meteo Historical Weather API, archive best_match: ERA5/ERA5-Land/ECMWF IFS. Daily variables, CC BY 4.0."],
  ["ORNL MCC (clienți modelați pe comitat, 2022), din același set EAGLE-I", "ORNL MCC, modelled customer counts per county, 2022, from the same EAGLE-I dataset"],
  ["US Census Bureau, 2024 Gazetteer (centroizii și suprafața comitatelor)", "US Census Bureau, 2024 Gazetteer, county centroids and areas"],
  ["SimBench 1.6.3, 6 rețele JT (ODbL), variante SINTETICE de posturi", "SimBench 1.6.3, 6 low-voltage networks, ODbL. SYNTHETIC substation variants."],
  ["Etichete din fizică: circulație de puteri orară (pandapower 3.5.6 + calcul vectorizat verificat față de runpp)", "Physics-based labels from hourly load flow. pandapower 3.5.6 and vectorised calculations checked against runpp."],
  ["Profile de consum SimBench H0/G pe calendarul românesc; kWp și baterii calibrate pe ANRE (iun. 2026)", "SimBench H0/G consumption profiles on the Romanian calendar. Solar capacity and batteries calibrated against ANRE, June 2026."],
];

export function englishReportText(text: string): string {
  let translated = text;
  for (const [original, english] of REPORT) translated = translated.replaceAll(original, english);
  return translated !== text ? translated : englishText(text);
}
