import type { WorkItem } from "./contracts";

export const CAUSE_LABELS: Record<string, string> = {
  normal: "Normal loss",
  contor_client: "Faulty customer meter",
  furt_inainte_contor: "Theft before the meter",
  pierdere_tehnica: "Technical loss",
  client_post_gresit: "Customer linked to the wrong substation",
  contor_bilant_setat: "Incorrectly configured substation meter",
};

/** A problem can be almost certain while its cause remains ambiguous. */
export function causeConfidence(item: Pick<WorkItem, "extra">) {
  const raw = item.extra?.diagnosis_proba;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const ranked = Object.entries(raw)
    .filter((entry): entry is [string, number] => entry[0] in CAUSE_LABELS && typeof entry[1] === "number" && Number.isFinite(entry[1]) && entry[1] >= 0 && entry[1] <= 1)
    .sort((a, b) => b[1] - a[1]);
  if (ranked.length < 2) return null;
  return {
    top: { key: ranked[0][0], label: CAUSE_LABELS[ranked[0][0]], probability: ranked[0][1] },
    second: { key: ranked[1][0], label: CAUSE_LABELS[ranked[1][0]], probability: ranked[1][1] },
    margin: ranked[0][1] - ranked[1][1],
  };
}
