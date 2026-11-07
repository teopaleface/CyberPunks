/** Etichete în română pentru valorile din contracte. Fără cod de server: se pot folosi și în client. */
import type { DecisionType } from "@/lib/contracts";
import type { DataSource } from "./types";

export const SOURCE_LABEL_RO: Record<DataSource, string> = {
  api: "API (în direct)",
  demo: "instantaneu demo",
  fixtures: "date de test (fixtures)",
};

export const DECISION_LABEL_RO: Record<DecisionType, string> = {
  assigned: "în traseu",
  deferred: "amânată",
  human_review: "decide un om",
  remote_action: "acțiune la distanță",
  notify: "mesaj către clienți",
  rejected_invalid: "respinsă (date greșite)",
};
