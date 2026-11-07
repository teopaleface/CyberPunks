import { describe, expect, test } from "bun:test";
import type { ModelReport, Series, WorkItem } from "@/lib/contracts";
import { intervalText, localityOf, maxGust, metricRows, parseTag, pctText, postOf, puToVolts, ruleCost, seriesSentence, stopFor, voltageContributions, windowHours } from "./item-data";

const w = (over: Partial<WorkItem>) => ({ asset_id: "X", asset_type: "meter", location: { zone_id: "Z", label: "Contor MTR-1, PT-1208, Chiajna (sintetic)" }, ...over }) as WorkItem;

describe("item-data", () => {
  test("locul și postul", () => {
    expect(localityOf(w({}))).toBe("Chiajna");
    expect(postOf(w({}))).toBe("PT-1208");
    expect(localityOf(w({ asset_type: "transformer_post", location: { zone_id: "Z", label: "PT-1269, Afumați (sintetic)" } as never }))).toBe("Afumați");
    expect(localityOf(w({ asset_type: "zone", location: { zone_id: "Z", label: "Zona Timișoara (Timiș)" } as never }))).toBe("Timișoara");
  });
  test("procente și interval", () => {
    expect(pctText(1)).toBe("above 99%");
    expect(pctText(0.58)).toBe("58%");
    expect(intervalText(0.98, 1)).toBe("above 98%");
    expect(intervalText(0.5, 0.8)).toBe("50–80%");
    expect(intervalText(null, 1)).toBeNull();
  });
  test("volți", () => {
    expect(puToVolts(1.1)).toBe(253);
    expect(puToVolts(1.177)).toBe(271);
  });
  test("seria: frază și rafală", () => {
    const s = { points: [{ t: "2025-05-24", value: 1, flag: "negativ" }, { t: "2025-05-25", value: 9 }], annotations: [{ t: "2025-05-24T00:00:00", label_ro: "apar citiri negative" }] } as unknown as Series;
    expect(seriesSentence(s).headline).toContain("Negative readings start from");
    expect(seriesSentence(s).detail).toBe("1 of 2 days with negative readings.");
    expect(maxGust(s)).toEqual({ value: 9, t: "2025-05-25" });
    expect(seriesSentence(null).detail).toBeNull();
  });
  test("fereastra și oprirea", () => {
    expect(windowHours("2025-07-08T15:00:00+03:00", "2025-07-08T21:00:00+03:00")).toBe(6);
    expect(stopFor([{ crew_id: "E-1", stops: [{ seq: 2, work_item_id: "a", eta: "t", duration_min: 5, travel_km: 3 }] as never }], "a")?.seq).toBe(2);
    expect(stopFor([], "a")).toBeNull();
  });
  test("metrici", () => {
    const r = { metrics: { subtle_precision_at_k: 0.625, precision_at_k: 1, pr_auc: 0.6778 }, baseline_metrics: { subtle_precision_at_k: 0.0703 } } as unknown as ModelReport;
    const rows = metricRows("A", r);
    expect(rows.map((x) => x.key)).toEqual(["subtle_precision_at_k", "pr_auc"]);
    expect(rows[1].base).toBeNull();
    expect(metricRows("A", null)).toEqual([]);
  });
  test("contribuții, cost, filtru", () => {
    expect(voltageContributions(w({ extra: { voltage_contributions_pu: { a: 0.001, b: -0.5 } } }))[0].key).toBe("b");
    expect(ruleCost({ visit_cost_lei: 310, cost_lei: 2 })).toBe(310);
    expect(ruleCost(undefined)).toBeNull();
    expect(parseTag("scoruri")).toBe("scoruri");
    expect(parseTag("x")).toBeNull();
  });
});
