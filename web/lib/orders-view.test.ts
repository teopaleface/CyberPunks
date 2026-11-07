import { describe, expect, test } from "bun:test";
import type { Decision, WorkItem } from "@/lib/contracts";
import type { ResolvedRoute } from "@/lib/data/types";
import { buildChecklist, buildOrder, decisionCost, pickCrew } from "@/lib/orders-view";

const w = { work_item_id: "A-1", source: "A", asset_id: "PT-1", recommended_action: "visit", prediction: { label: "faulty", score: 0.94 } } as unknown as WorkItem;
const d = { work_item_id: "A-1", rule_id: "R-A-VISIT", threshold: { cost_lei: 293 } } as unknown as Decision;
const route = {
  crew_id: "E-1", depart_at: "2025-07-08T08:30:00+03:00", return_at: null, total_km: 5, depot: null, crew: null, path: [],
  stops: [{ seq: 1, work_item_id: "A-1", eta: "2025-07-08T09:00:00+03:00", duration_min: 30, travel_km: 2, workItem: null, decision: null, lat: 0, lon: 0, label: null }],
} as unknown as ResolvedRoute;

describe("ordinul de lucru", () => {
  test("costul și echipa implicită", () => {
    expect(decisionCost(d)).toBe(293);
    expect(decisionCost(null)).toBeNull();
    expect(pickCrew([{ crew_id: "X" }, { crew_id: "Y" }], "nu")).toBe("X");
    expect(pickCrew([{ crew_id: "X" }, { crew_id: "Y" }], "Y")).toBe("Y");
  });
  test("întoarcerea lipsă se estimează din ultima oprire și verificările vin din opriri", () => {
    const o = buildOrder(route, { "A-1": w }, { "A-1": d }, () => "Domnești", () => "PT-1");
    expect(o.returnEstimated).toBe(true);
    expect(o.stops[0].costLei).toBe(293);
    const c = buildChecklist(o);
    expect(c[0].text).toBe("Confirmare sosire la PT-1");
    expect(c.at(-1)?.text.startsWith("Întoarcere la bază")).toBe(true);
  });
});
