import { describe, expect, test } from "bun:test";
import type { Series } from "@/lib/contracts";
import { bilantRows, isBilantSeries, seriesTimeMs } from "@/lib/series-utils";

const series = (points: Series["points"]): Series => ({
  contract_version: "1.0",
  work_item_id: "A-20250708-PT-0001",
  source: "A",
  title_ro: "PT-0001: ieșit din post față de suma clienților (SIMULARE)",
  unit: "kWh",
  points,
  thresholds: {},
  annotations: [],
  synthetic: true,
});

describe("bilanțul pe post", () => {
  test("ora punctelor zilnice, cu sau fără fus orar", () => {
    expect(seriesTimeMs("2025-05-10T00:00:00")).toBe(Date.UTC(2025, 4, 10));
    expect(seriesTimeMs("2025-05-10")).toBe(Date.UTC(2025, 4, 10));
    expect(seriesTimeMs("2025-05-10T00:00:00+03:00")).toBe(Date.UTC(2025, 4, 10));
  });

  test("recunoaște seria și după surplus", () => {
    expect(isBilantSeries(series([{ t: "2025-05-10T00:00:00", value: 1, expected: 2, low: 2, high: 3, flag: "surplus_sub_normal" }]))).toBe(true);
  });

  test("lipsa peste normal începe exact unde linia trece de bandă", () => {
    const rows = bilantRows(
      series([
        { t: "2025-05-10T00:00:00", value: 100, expected: 90, low: 95, high: 105, flag: null },
        { t: "2025-05-11T00:00:00", value: 130, expected: 90, low: 95, high: 110, flag: "lipsa_peste_normal" },
      ]),
    );
    expect(rows).toHaveLength(3);
    const [a, cross, b] = rows;
    expect(a.over).toEqual([105, 105]);
    expect(cross.crossing).toBe(true);
    // 100-105 = -5, 130-110 = +20: trece la 1/5 din zi
    expect(cross.x).toBe(Date.UTC(2025, 4, 10) + 0.2 * 86_400_000);
    expect(cross.out).toBeCloseTo(106, 6);
    expect(cross.high).toBeCloseTo(106, 6);
    const [lo, hi] = cross.over ?? [Number.NaN, Number.NaN];
    expect(hi - lo).toBeCloseTo(0, 6);
    expect(cross.ref).toBe(a);
    expect(b.over).toEqual([110, 130]);
    expect(b.band).toEqual([95, 110]);
  });

  test("surplusul sub normal și valorile negative (postul dă energie înapoi)", () => {
    const rows = bilantRows(
      series([
        { t: "2025-05-10T00:00:00", value: -507.7, expected: -885.62, low: -755.02, high: -689.46, flag: "lipsa_peste_normal" },
        { t: "2025-05-11T00:00:00", value: -800, expected: -885.62, low: -755.02, high: -689.46, flag: "surplus_sub_normal" },
      ]),
    );
    // iese de deasupra benzii și coboară sub ea: două treceri, în ordine
    expect(rows.map((r) => Boolean(r.crossing))).toEqual([false, true, true, false]);
    expect(rows[1].x).toBeLessThan(rows[2].x);
    expect(rows[0].over).toEqual([-689.46, -507.7]);
    expect(rows[3].under).toEqual([-800, -755.02]);
  });

  test("golurile din date rămân goluri", () => {
    const rows = bilantRows(
      series([
        { t: "2025-05-10T00:00:00", value: null, expected: 90, low: 95, high: 105, flag: null },
        { t: "2025-05-11T00:00:00", value: 130, expected: 90, low: 95, high: 110, flag: null },
      ]),
    );
    expect(rows).toHaveLength(2);
    expect(rows[0].over).toBeNull();
  });
});
