/**
 * Cele trei surse de lucrări și cum le arătăm. Culoarea nu e singurul indiciu: markerii poartă litera.
 * Culorile vin din variabilele CSS ale temei (validate pentru daltonism).
 */
import type { Source } from "@/lib/contracts";

export interface SourceMeta {
  letter: Source;
  /** Numele scurt din interfață. */
  name: string;
  /** Ce problemă estimează modelul, în cuvinte simple. */
  problem: string;
  /** Ce fel de activ e. */
  asset: string;
  color: string;
  /** Culoarea literei pe disc. */
  onColor: string;
  /** Discul are nevoie de contur închis pe fundal deschis (chihlimbarul are contrast mic). */
  outline: boolean;
}

export const SOURCES: Record<Source, SourceMeta> = {
  A: {
    letter: "A",
    name: "Contoare",
    problem: "contoare defecte sau manipulate",
    asset: "contor",
    color: "var(--src-a)",
    onColor: "#ffffff",
    outline: false,
  },
  B: {
    letter: "B",
    name: "Furtună",
    problem: "risc de avarii la furtună",
    asset: "zonă",
    color: "var(--src-b)",
    onColor: "#ffffff",
    outline: false,
  },
  C: {
    letter: "C",
    name: "Tensiune",
    problem: "tensiune peste limită din cauza prosumatorilor",
    asset: "post de transformare",
    color: "var(--src-c)",
    onColor: "var(--ink)",
    outline: true,
  },
};

export const SOURCE_ORDER: Source[] = ["A", "B", "C"];

export function sourceOf(workItemId: string): Source | null {
  const c = workItemId.charAt(0);
  return c === "A" || c === "B" || c === "C" ? c : null;
}
