import { Scale } from "lucide-react"
import { SourceIcon } from "@/components/ui/animated-icons"
import { DB, SOURCES } from "@/data/daybreak"
import { cn, fmt } from "@/lib/utils"

/**
 * The ML part on one screen, for the one-minute pitch on /agent: for each of the four models,
 * the data it learned from, the algorithm, what the agent uses it for, and its main test metric
 * next to a simple baseline on the same held-out data. Every number is read from DB.modelCards.
 */

type Key = "A" | "B" | "C" | "bilant"
const M = DB.modelCards

/**
 * Checks added after the shipped model cards, copied from reports/ml/README.md (`make ml-report`).
 * They are extra evidence, not new scores of the shipped models.
 */
const NEW_CHECKS = {
  /** FeederBW measured voltages, next-day max at the feeder head; 40 real feeders, unseen feeders and months. */
  feederbwVoltage: { modelV: 0.724, persistenceV: 0.825 },
  /** 300 new synthetic transformers; protocol and model hashes fixed in 3deadcc before the batch was generated. */
  bilantFreshAudit: { model: 0.77539, rules: 0.42059 },
  testsPassed: 208,
  scoresRecomputed: 30,
}

interface Metric {
  label: string
  model: number
  base: number
  baseLabel: string
  digits: number
  lowerIsBetter?: boolean
}

interface Row {
  key: Key
  name: string
  color: string
  usedFor: string
  data: { text: string; kind: "real" | "synthetic" | "mixed" }
  model: string
  test: string
  metrics: Metric[]
  /** A later check on other data, shown under the bars. */
  check?: string
}

const ROWS: Row[] = [
  {
    key: "A",
    name: SOURCES.A.name,
    color: SOURCES.A.color,
    usedFor: "Ranks meters that are faulty or tampered, so crews check the top 1% first.",
    data: { text: "Low Carbon London (real consumption, injected faults) + SGCC (real theft labels)", kind: "mixed" },
    model: "LightGBM classifier, Venn-ABERS calibration",
    test: "Unseen households and a later period",
    metrics: [
      { label: "Precision in top 1%, subtle faults", model: M.A.metrics.subtle_precision_at_k, base: M.A.baseline.subtle_precision_at_k, baseLabel: "simple rule", digits: 2 },
      { label: "PR-AUC, real theft labels (SGCC)", model: M.A.metrics.sgcc_pr_auc, base: M.A.baseline.sgcc_pr_auc, baseLabel: "simple rule", digits: 2 },
    ],
  },
  {
    key: "B",
    name: SOURCES.B.name,
    color: SOURCES.B.color,
    usedFor: "Outage risk per area for tomorrow, so crews are placed before the storm.",
    data: { text: "EAGLE-I outages (real, 80 US counties) + Open-Meteo weather", kind: "real" },
    model: "LightGBM, monotone constraints, isotonic calibration + P10/P50/P90 quantiles",
    test: "Unseen year (2025) and unseen states",
    metrics: [
      { label: "PR-AUC, outage ≥ 1% of customers", model: M.B.metrics.pr_auc, base: M.B.metrics.pr_auc_gust_rule, baseLabel: "gust rule", digits: 2 },
      { label: "PR-AUC, states never seen in training", model: M.B.metrics.loso_pr_auc_mean, base: M.B.metrics.loso_clim_month_pr_auc_mean, baseLabel: "climatology", digits: 2 },
    ],
  },
  {
    key: "C",
    name: SOURCES.C.name,
    color: SOURCES.C.color,
    usedFor: "Max voltage per transformer from solar export; above 1.10 pu the agent alerts.",
    data: { text: "SimBench grids + Open-Meteo; labels from pandapower power flow", kind: "synthetic" },
    model: "LightGBM quantile surrogate of the power flow",
    test: "Unseen grid topologies and months",
    metrics: [
      { label: "Mean error of max voltage (pu)", model: M.C.metrics.mae_vmax_pu, base: M.C.baseline.mae_vmax_pu, baseLabel: "linear model", digits: 4, lowerIsBetter: true },
      { label: "PR-AUC, voltage above 1.10 pu", model: M.C.metrics.pr_auc_exceed, base: M.C.baseline.pr_auc_exceed, baseLabel: "linear model", digits: 2 },
    ],
    check: `On real measured voltages (FeederBW, 40 feeders): next-day peak error ${fmt(NEW_CHECKS.feederbwVoltage.modelV, 2)}\u00a0V vs ${fmt(NEW_CHECKS.feederbwVoltage.persistenceV, 2)}\u00a0V for "same as last day". That test has no overvoltages.`,
  },
  {
    key: "bilant",
    name: "Energy balance",
    color: "#34d399",
    usedFor: "Normal loss per transformer and the cause of any excess, priced in lei.",
    data: { text: "SimBench + Open-Meteo + OSM transformers; hidden causes injected by us", kind: "synthetic" },
    model: "LightGBM quantile regression + 6-class cause classifier",
    test: "300 transformers never seen in training",
    metrics: [
      { label: "Macro F1, cause of the loss", model: M.bilant.metrics.diagnoza_macro_f1, base: M.bilant.baseline.diagnoza_macro_f1, baseLabel: "rule table", digits: 2 },
      { label: "Normal-loss error (kWh/day)", model: M.bilant.metrics.normal_mae_kwh_day, base: M.bilant.baseline.normal_mae_kwh_day, baseLabel: "I²R formula", digits: 1, lowerIsBetter: true },
    ],
    check: `Fresh audit, rules locked before the data was generated: 300 new transformers, macro F1 ${fmt(NEW_CHECKS.bilantFreshAudit.model, 2)} vs ${fmt(NEW_CHECKS.bilantFreshAudit.rules, 2)} for the rule table.`,
  },
]

const KIND_LABEL = { real: "Real data", synthetic: "Synthetic labels", mixed: "Real + synthetic" } as const

function Icon({ k, color }: { k: Key; color: string }) {
  return (
    <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-foreground/[0.05]" style={{ color }}>
      {k === "bilant" ? <Scale size={26} strokeWidth={1.75} /> : <SourceIcon s={k} size={32} accent={color} className="text-foreground/85" />}
    </span>
  )
}

function Bars({ m, color }: { m: Metric; color: string }) {
  const max = Math.max(m.model, m.base) || 1
  const ratio = m.lowerIsBetter ? m.base / m.model : m.model / m.base
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 text-sm">
        <span className="text-foreground/75">{m.label}</span>
        <span className="tabular shrink-0 font-semibold text-foreground">
          {fmt(ratio, 1)}× {m.lowerIsBetter ? "lower" : "better"}
        </span>
      </div>
      <div className="tabular mt-2 grid grid-cols-[6.5rem_1fr_3.75rem] items-center gap-x-3 gap-y-1.5 text-sm">
        <span className="text-foreground/85">Model</span>
        <span className="h-2 overflow-hidden rounded-full bg-foreground/10">
          <span className="block h-full rounded-full" style={{ width: `${(m.model / max) * 100}%`, background: color }} />
        </span>
        <span className="text-right font-semibold">{fmt(m.model, m.digits)}</span>
        <span className="truncate text-foreground/60" title={m.baseLabel}>
          {m.baseLabel}
        </span>
        <span className="h-2 overflow-hidden rounded-full bg-foreground/10">
          <span className="block h-full rounded-full bg-foreground/35" style={{ width: `${(m.base / max) * 100}%` }} />
        </span>
        <span className="text-right text-foreground/65">{fmt(m.base, m.digits)}</span>
      </div>
    </div>
  )
}

export function ModelOverview() {
  return (
    <div className="space-y-6">
      <ul className="grid gap-6 lg:grid-cols-2">
        {ROWS.map((r) => (
          <li key={r.key} data-ui className="flex flex-col gap-5 rounded-2xl bg-surface p-[clamp(20px,2.4vw,32px)]">
            <div className="flex items-start gap-4">
              <Icon k={r.key} color={r.color} />
              <div className="min-w-0">
                <h3 className="font-sans text-xl font-semibold tracking-[-0.01em]">{r.name}</h3>
                <p className="mt-1 text-foreground/85">{r.usedFor}</p>
              </div>
            </div>

            <dl className="grid grid-cols-[5.5rem_1fr] gap-x-3 gap-y-2 text-[15px]">
              <dt className="text-foreground/55">Data</dt>
              <dd>
                {r.data.text}{" "}
                <span
                  className={cn(
                    "ml-1 inline-block rounded-full px-2 py-0.5 align-middle text-xs font-medium",
                    r.data.kind === "real" ? "bg-ok/15 text-ok" : "bg-foreground/10 text-foreground/75"
                  )}
                >
                  {KIND_LABEL[r.data.kind]}
                </span>
              </dd>
              <dt className="text-foreground/55">Model</dt>
              <dd>{r.model}</dd>
              <dt className="text-foreground/55">Tested on</dt>
              <dd>{r.test}</dd>
            </dl>

            <div className="mt-auto space-y-5 border-t border-foreground/10 pt-5">
              {r.metrics.map((m) => (
                <Bars key={m.label} m={m} color={r.color} />
              ))}
              {r.check && (
                <p className="flex gap-2 text-sm text-foreground/75">
                  <span aria-hidden className="mt-[0.45em] size-1.5 shrink-0 rounded-full" style={{ background: r.color }} />
                  <span>
                    <span className="font-medium text-foreground">New check. </span>
                    {r.check}
                  </span>
                </p>
              )}
            </div>
          </li>
        ))}
      </ul>
      <p className="max-w-[80ch] text-sm text-foreground/70">
        Every metric is measured on held-out data, next to a simple baseline on the same split. CatBoost and XGBoost were tested
        on the same splits and none beat LightGBM. {NEW_CHECKS.scoresRecomputed} of {NEW_CHECKS.scoresRecomputed} scores are recomputed from the saved predictions,
        and all {NEW_CHECKS.testsPassed} ML tests pass from a clean clone. Synthetic labels are marked as synthetic.
      </p>
    </div>
  )
}
