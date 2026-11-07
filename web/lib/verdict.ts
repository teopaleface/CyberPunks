/**
 * Verdictul unei lucrări într-o frază: ce se întâmplă și cât de sigur e modelul, apoi (opțional) ce a hotărât agentul.
 * Funcții pure, construite doar din câmpuri reale (nimic inventat); cifrele exacte rămân în detaliile tehnice.
 */
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
  phase_rebalance: "reechilibrarea fazelor",
  offer_battery: "oferta de baterii",
  export_limit: "limitarea injecției",
  notify_customers: "mesaje către clienți",
  adjust_tap: "schimbarea prizei",
  transformer_upgrade: "transformator mai mare",
};

export function stepRo(action: string): string {
  return STEP_SHORT[action] ?? (ACTION_RO as Record<string, string>)[action] ?? action.replaceAll("_", " ");
}

const num = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const lower = (s: string) => s.charAt(0).toLocaleLowerCase("ro-RO") + s.slice(1);

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
        ? `Agentul: echipa ${decision.crew_id}${eta ? ` ajunge la ${eta}` : " e trimisă"}.`
        : "Agentul: intră în traseu.";
    case "remote_action":
      return /plan(ul)? următor/.test(decision.reason_ro)
        ? "Agentul: citire la distanță azi; vizita rămâne pentru planul următor."
        : "Agentul: citire la distanță, fără vizită.";
    case "human_review":
      return "Agentul nu e sigur: decide un om.";
    case "deferred":
      return "Agentul: amânată, nu intră în planul de mâine.";
    case "notify":
      return "Agentul: trimite mesaj către clienți.";
    case "rejected_invalid":
      return "Respinsă la intrare: datele sunt greșite.";
    default:
      return `Agentul: ${DECISION_LABEL_RO[decision.decision] ?? w.recommended_action}.`;
  }
}

export function verdictRo(w: WorkItem, decision: Decision | null, opts: VerdictOptions = {}): Verdict {
  const p = w.prediction;
  const conf = confidenceWord(p.confidence, p.score);
  const extra = (w.extra ?? {}) as Record<string, unknown>;

  // contor: defect sau manipulat
  if (w.asset_type === "meter") {
    const what = p.label === "faulty" ? "pare defect" : p.label === "tamper" ? "pare manipulat" : predictionLabelRo(p.label);
    return { headline: `Contorul ${w.asset_id} ${what}, cu ${conf}.`, detail: decisionInWords(w, decision) };
  }

  // bilanțul pe post
  if (w.source === "A" && w.asset_type === "transformer_post") {
    const lei = extra.lei_per_month;
    const causeFull = predictionLabelRo(p.label);
    const cause = opts.longCause ? causeFull : causeFull.replace(/\s*\([^)]*\)\s*$/, "");
    if (p.label === "normal") return { headline: `Postul ${w.asset_id} are pierderi normale, cu ${conf}.`, detail: decisionInWords(w, decision) };
    const loss = num(lei) ? `pierde ${approxLei(lei)} pe lună` : "pierde energie peste normal";
    return {
      headline: `Postul ${w.asset_id} ${loss}. ${opts.longCause ? "Cauza" : "Cauza probabilă"}: ${cause}.`,
      detail: decisionInWords(w, decision),
    };
  }

  // furtună peste o zonă
  if (w.source === "B") {
    const title = itemTitle(w);
    const headline = `${title}: risc de avarii la furtună, cu ${conf}.`;
    const eta = arrivalTime(decision);
    if (decision?.decision === "assigned" && decision.crew_id) {
      const start = /T(\d{2}:\d{2})/.exec(w.time_window?.start ?? "")?.[1];
      const before = eta && start && toMinutes(eta) < toMinutes(start) ? ", înainte de fereastra de risc" : "";
      return { headline, detail: `Echipa ${decision.crew_id} ${eta ? `ajunge la ${eta}${before}` : "e trimisă din timp în zonă"}.` };
    }
    return { headline, detail: decisionInWords(w, decision) };
  }

  // tensiune pe post
  if (w.source === "C") {
    const limit = decision?.threshold?.overvoltage_limit_pu;
    const headline = `Postul ${w.asset_id}: tensiunea trece de limita de ${fmtDec(num(limit) ? limit : 1.1, 2)} la prânz, cu ${conf}.`;
    const chosen = opts.chosen ?? [];
    const cost = opts.costLei ?? decision?.threshold?.remedy_cost_lei;
    if (chosen.length) {
      return { headline, detail: `Soluția aleasă: ${chosen.map(stepRo).join(" + ")}${num(cost) ? `, ${approxLei(cost)}` : ""}.` };
    }
    return { headline, detail: decisionInWords(w, decision) };
  }

  // rezervă
  return {
    headline: `${itemTitle(w)}: ${predictionLabelRo(p.label)}, cu ${conf}.`,
    detail: decision ? `Decizia: ${lower(DECISION_LABEL_RO[decision.decision])}.` : undefined,
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
  const cause = i.causeRo ? ` Cauza: ${i.causeRo}.` : "";
  const headline = loss != null ? `Postul ${i.postId} pierde ${approxLei(loss)} pe lună.${cause}` : `Postul ${i.postId}: bilanțul nu arată pierderi peste normal.${cause}`;
  let detail: string | undefined;
  if (i.chosen?.length) {
    detail = `Soluția aleasă pentru tensiune: ${i.chosen.map(stepRo).join(" + ")}${num(i.costLei) ? `, ${approxLei(i.costLei)}` : ""}.`;
  } else if (num(i.metersFlagged) && i.metersFlagged > 0) {
    detail = `${i.metersFlagged === 1 ? "Un contor semnalat" : `${i.metersFlagged} contoare semnalate`} pe post.`;
  }
  return { headline, detail };
}
