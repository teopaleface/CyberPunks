export type HomeFilter = "toate" | "lucrari" | "echipe" | "trasee" | "posturi" | "alerte" | "vreme" | "tensiune";

export const ITEMS: { id: HomeFilter; label: string; tone?: "blue" | "violet" | "amber" | "red" }[] = [
  { id: "toate", label: "Toate" },
  { id: "lucrari", label: "Lucrări", tone: "blue" },
  { id: "echipe", label: "Echipe", tone: "violet" },
  { id: "trasee", label: "Trasee", tone: "blue" },
  { id: "posturi", label: "Posturi", tone: "amber" },
  { id: "alerte", label: "Alerte", tone: "red" },
  { id: "vreme", label: "Vreme", tone: "violet" },
  { id: "tensiune", label: "Tensiune", tone: "amber" },
];

export const HOME_FILTERS = ITEMS.map((i) => i.id);

