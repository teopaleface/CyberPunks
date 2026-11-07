import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import YAML from "yaml";
import { REPO_ROOT } from "@/lib/data";
import { fmtDec, fmtInt } from "@/lib/format";
import type { ParamRow } from "@/components/queue/run-panel";

type Fmt = (n: number) => string;
const lei: Fmt = (n) => `${fmtInt(n)} lei`;
const pct: Fmt = (n) => `${fmtInt(Math.round(n * 100))}%`;
const dec: Fmt = (n) => fmtDec(n, 2).replace(/,00$/, "");
const int: Fmt = (n) => fmtInt(n);

const WANTED: { path: string[]; label: string; note: string; fmt: Fmt }[] = [
  { path: ["global", "human_review_min_ev_lei"], label: "Valoare minimă ca să întrebe un om", note: "Sub această sumă, un caz nesigur rămâne la urmărire.", fmt: lei },
  { path: ["global", "human_review_max_per_day"], label: "Cazuri pe zi pentru un dispecer", note: "Câte cazuri intră cel mult în „Nu sunt sigur”.", fmt: int },
  { path: ["global", "max_interval_width"], label: "Interval de încredere acceptat", note: "Mai larg de atât înseamnă că modelul nu e sigur.", fmt: dec },
  { path: ["global", "max_missing_ratio"], label: "Date lipsă acceptate", note: "Peste acest procent, scorul nu mai e de încredere.", fmt: pct },
  { path: ["global", "safety_min_score"], label: "Scor minim pentru risc de siguranță", note: "Sub el, semnalul e prea slab ca să treacă peste cost.", fmt: dec },
  { path: ["meters", "visit_min_score"], label: "Scor minim pentru o vizită la contor", note: "Echipa merge la ușa clientului doar peste acest scor.", fmt: dec },
  { path: ["storm", "preposition_min_score"], label: "Scor minim pentru o echipă trimisă din timp", note: "Sub această probabilitate nu se mută echipe înainte de furtună.", fmt: dec },
  { path: ["storm", "max_crews_per_region"], label: "Echipe trimise din timp pe regiune", note: "Restul rămân pentru lucrările curente.", fmt: int },

];

export async function readPlannerParams(): Promise<ParamRow[]> {
  try {
    const doc = YAML.parse(await readFile(path.join(REPO_ROOT, "config", "planner.yaml"), "utf8")) as Record<string, unknown>;
    const rows: ParamRow[] = [];
    for (const w of WANTED) {
      let v: unknown = doc;
      for (const k of w.path) v = (v as Record<string, unknown> | undefined)?.[k];
      if (typeof v === "number" && Number.isFinite(v)) rows.push({ label: w.label, value: w.fmt(v), note: w.note });
    }
    return rows;
  } catch {
    return [];
  }
}
