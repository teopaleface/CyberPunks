/** Rândurile jurnalului, gata de afișat. Fără cod de server: le folosește și tabelul (componentă client). */
import type { Source } from "@/lib/contracts";
import type { MarkerKind } from "@/lib/marker-svg";

/** `run`: o rulare a agentului (despărțitor în tabel); `decision`: decizia agentului; `review`: decizia omului. */
export type JournalKind = "run" | "decision" | "review";

export interface JournalThreshold {
  key: string;
  label: string;
  value: string;
}

export interface JournalRow {
  id: string;
  ts: string;
  /** „13:42” */
  time: string;
  /** „sâmbătă, 7 noiembrie, la 13:42” */
  moment: string;
  actor: "agent" | "human";
  kind: JournalKind;
  /** Valoarea brută din jurnal (`assigned`, `review_approve`, `run`…), pentru filtru. */
  action: string;
  /** „În traseu”, „Aprobată de om”… */
  actionLabel: string;
  /** Agentul a dat lucrarea unui om („decide un om”). */
  attention: boolean;
  workItemId: string | null;
  /** ID-ul scurt al activului: „MTR-011050”, „PT-1269”. */
  assetId: string | null;
  /** Scorul predicției, 0–1, din decizie sau din lucrare. */
  score: number | null;
  /** Pragul principal în cuvinte: „695 lei > 293 lei”. */
  mainThreshold: string | null;
  source: Source | null;
  marker: MarkerKind;
  /** „Contor MTR-004217, București, sectorul 6”, dacă lucrarea e în planul curent. */
  itemTitle: string | null;
  ruleId: string | null;
  ruleText: string | null;
  thresholds: JournalThreshold[];
  predictionId: string | null;
  modelVersion: string | null;
  inputsSha: string | null;
  /** Motivul agentului sau nota omului (fără numele lui). */
  note: string | null;
  /** Doar la deciziile omului: cine a decis. */
  reviewer: string | null;
  /** Doar la rulări: câte decizii a scris rularea. */
  decisions: number;
}

export interface ActionOption {
  action: string;
  label: string;
  count: number;
}
