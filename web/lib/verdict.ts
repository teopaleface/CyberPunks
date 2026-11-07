/**
 * Verdictul unei lucrări într-o frază: ce se întâmplă și cât de sigur e modelul, apoi (opțional) ce a hotărât agentul.
 * Funcții pure, construite doar din câmpuri reale (nimic inventat); cifrele exacte rămân în detaliile tehnice.
 */
import { englishText } from "@/lib/english";
import type { Decision, WorkItem } from "@/lib/contracts";
import { ACTION_RO, DECISION_LABEL_RO, predictionLabelRo } from "@/lib/data/labels";
import { fmtDec } from "@/lib/format";
import { approxLei, confidenceWord } from "@/lib/human";
import { itemTitle } from "@/lib/plan-screen";

export interface Verdict {
  headline: string;
  detail?: string;
}

export interface VerdictOptions {
  /** Combinația de trepte aleasă pentru tensiune (C), în ordinea scării. */
  chosen?: string[];
  /** Costul combinației alese, în lei. */
  costLei?: number | null;
  /** Cauza completă, cu paranteză („pierdere tehnică (cablu, faze dezechilibrate)”), nu cea scurtă. */
  longCause?: boolean;
}

/** Trepte, pe scurt, ca să încapă într-o frază. */
const STEP_SHORT: Record<string, string> = {
  phase_rebalance: "phase rebalancing",
  offer_battery: "battery offer",
  export_limit: "export limit",
  notify_customers: "customer messages",
  adjust_tap: "tap adjustment",
  transformer_upgrade: "larger transformer",
};

export function stepRo(action: string): string {
  return STEP_SHORT[action] ?? (ACTION_RO as Record<string, string>)[action] ?? action.replaceAll("_", " ");
}

const num = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const lower = (s: string) => s.charAt(0).toLocaleLowerCase("en-GB") + s.slice(1);

/** Ora sosirii echipei, din motivul deciziei („… sosire la 14:00.”). */
function arrivalTime(decision: Decision | null): string | null {
  return /sosire la (\d{1,2}:\d{2})/.exec(decision?.reason_ro ?? "")?.[1] ?? null;
}

const toMinutes = (hhmm: string) => {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
};

/** Decizia, în cuvinte, pentru cazurile fără o frază mai bună. */
function decisionInWords(w: WorkItem, decision: Decision | null): string | undefined {
  if (!decision) return undefined;
  const eta = arrivalTime(decision);
  switch (decision.decision) {
    case "assigned":
      return decision.crew_id
        ? `Agent: crew ${decision.crew_id}${eta ? ` arrives at ${eta}` : " is dispatched"}.`
        : "Agent: assigned to a route.";
    case "remote_action":
      return /plan(ul)? următor/.test(decision.reason_ro)
        ? "Agent: remote reading today; visit carried over to the next plan."
        : "Agent: remote reading, no visit.";
    case "human_review":
      return "The agent needs a human decision.";
    case "deferred":
      return "Agent: deferred from tomorrow's plan.";
    case "notify":
      return "Agent: send a customer message.";
    case "rejected_invalid":
      return "Rejected at intake: invalid data.";
    default:
      return `Agent: ${DECISION_LABEL_RO[decision.decision] ?? w.recommended_action}.`;
  }
}

export function verdictRo(w: WorkItem, decision: Decision | null, opts: VerdictOptions = {}): Verdict {
  const p = w.prediction;
  const conf = confidenceWord(p.confidence, p.score);
  const extra = (w.extra ?? {}) as Record<string, unknown>;

  // contor: defect sau manipulat
  if (w.asset_type === "meter") {
    const what = p.label === "faulty" ? "appears faulty" : p.label === "tamper" ? "shows signs of tampering" : predictionLabelRo(p.label);
    return { headline: `Meter ${w.asset_id} ${what}, with ${conf}.`, detail: decisionInWords(w, decision) };
  }

  // bilanțul pe post
  if (w.source === "A" && w.asset_type === "transformer_post") {
    const lei = extra.lei_per_month;
    const causeFull = predictionLabelRo(p.label);
    const cause = opts.longCause ? causeFull : causeFull.replace(/\s*\([^)]*\)\s*$/, "");
    if (p.label === "normal") return { headline: `Substation ${w.asset_id} has normal losses, with ${conf}.`, detail: decisionInWords(w, decision) };
    const loss = num(lei) ? `loses ${approxLei(lei)} per month` : "has excess energy losses";
    return {
      headline: `Substation ${w.asset_id} ${loss}. ${opts.longCause ? "Cause" : "Likely cause"}: ${cause}.`,
      detail: decisionInWords(w, decision),
    };
  }

  // furtună peste o zonă
  if (w.source === "B") {
    const title = itemTitle(w);
    const headline = `${title}: storm outage risk, with ${conf}.`;
    const eta = arrivalTime(decision);
    if (decision?.decision === "assigned" && decision.crew_id) {
      const start = /T(\d{2}:\d{2})/.exec(w.time_window?.start ?? "")?.[1];
      const before = eta && start && toMinutes(eta) < toMinutes(start) ? ", before the risk window" : "";
      return { headline, detail: `Crew ${decision.crew_id} ${eta ? `arrives at ${eta}${before}` : "is prepositioned in the area"}.` };
    }
    return { headline, detail: decisionInWords(w, decision) };
  }

  // tensiune pe post
  if (w.source === "C") {
    const limit = decision?.threshold?.overvoltage_limit_pu;
    const headline = `Substation ${w.asset_id}: voltage exceeds the limit of ${fmtDec(num(limit) ? limit : 1.1, 2)} at midday, with ${conf}.`;
    const chosen = opts.chosen ?? [];
    const cost = opts.costLei ?? decision?.threshold?.remedy_cost_lei;
    if (chosen.length) {
      return { headline, detail: `Chosen remedy: ${chosen.map(stepRo).join(" + ")}${num(cost) ? `, ${approxLei(cost)}` : ""}.` };
    }
    return { headline, detail: decisionInWords(w, decision) };
  }

  // rezervă
  return {
    headline: `${itemTitle(w)}: ${predictionLabelRo(p.label)}, with ${conf}.`,
    detail: decision ? `Decision: ${lower(DECISION_LABEL_RO[decision.decision])}.` : undefined,
  };
}

export interface PostVerdictInput {
  postId: string;
  lossLeiMonth?: number | null;
  /** Cauza, în cuvinte (de ex. predictionLabelRo al bilanțului). */
  causeRo?: string | null;
  chosen?: string[];
  costLei?: number | null;
  metersFlagged?: number | null;
}

/** Verdictul paginii unui post: banii pierduți, cauza, apoi soluția aleasă pentru tensiune. */
export function postVerdictRo(i: PostVerdictInput): Verdict {
  const loss = num(i.lossLeiMonth) && i.lossLeiMonth > 0 ? i.lossLeiMonth : null;
  const cause = i.causeRo ? ` Cause: ${englishText(i.causeRo)}.` : "";
  const headline = loss != null ? `Substation ${i.postId} loses ${approxLei(loss)} per month.${cause}` : `Substation ${i.postId}: the energy balance shows no excess losses.${cause}`;
  let detail: string | undefined;
  if (i.chosen?.length) {
    detail = `Chosen voltage remedy: ${i.chosen.map(stepRo).join(" + ")}${num(i.costLei) ? `, ${approxLei(i.costLei)}` : ""}.`;
  } else if (num(i.metersFlagged) && i.metersFlagged > 0) {
    detail = `${i.metersFlagged === 1 ? "One flagged meter" : `${i.metersFlagged} flagged meters`} at this substation.`;
  }
  return { headline, detail };
}
