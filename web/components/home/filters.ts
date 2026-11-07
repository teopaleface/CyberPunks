export type HomeFilter = "toate" | "lucrari" | "echipe" | "trasee" | "posturi" | "alerte" | "vreme" | "tensiune";

export const ITEMS: { id: HomeFilter; label: string; tone?: "blue" | "violet" | "amber" | "red" }[] = [
  { id: "toate", label: "All" },
  { id: "lucrari", label: "Work items", tone: "blue" },
  { id: "echipe", label: "Crews & routes", tone: "violet" },
  { id: "posturi", label: "Substations", tone: "amber" },
  { id: "alerte", label: "Alerts", tone: "red" },
  { id: "vreme", label: "Weather", tone: "violet" },
  { id: "tensiune", label: "Voltage", tone: "amber" },
];

// Keep legacy route links valid while showing one combined option.
export const HOME_FILTERS: HomeFilter[] = [...ITEMS.map((i) => i.id), "trasee"];

