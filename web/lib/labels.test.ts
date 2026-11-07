import { describe, expect, test } from "bun:test";
import type { WorkItem } from "@/lib/contracts";
import { auditActionRo, clampPercentRo, factorLabelRo, thresholdLabelRo, thresholdValueRo } from "@/lib/data/labels";
import { fmtDateLong, fmtLei, fmtScore, plural } from "@/lib/format";
import { itemPlace, itemTitle } from "@/lib/plan-screen";

describe("pragurile, în cuvinte", () => {
  test("scorurile nu se confundă cu minutele", () => {
    expect(thresholdValueRo("score_min", 0.5)).toBe("0,50");
    expect(thresholdValueRo("visit_min_score", 0.62)).toBe("0,62");
    expect(thresholdValueRo("arrive_before_start_min", 60)).toBe("60 min");
  });
  test("lei, pu, zile, steaguri", () => {
    expect(thresholdValueRo("cost_lei", 2953)).toBe("2.953 lei");
    expect(thresholdValueRo("overvoltage_limit_pu", 1.1)).toBe("1,10 pu");
    expect(thresholdValueRo("planned_notice_working_days", 5)).toBe("5 zile");
    expect(thresholdValueRo("smart_meter", 1)).toBe("da");
    expect(thresholdLabelRo("necunoscut_x")).toBe("necunoscut x");
  });
  test("acțiunile din jurnal", () => {
    expect(auditActionRo("review_approve")).toBe("omul a aprobat");
    expect(auditActionRo("assigned")).toBe("în traseu");
  });
});

describe("textele factorilor", () => {
  test("zecimale cu virgulă, procentele peste 999% devin „de peste 10 ori”", () => {
    expect(factorLabelRo("Variația în cursul zilei: 0.46 din medie")).toBe("Variația în cursul zilei: 0,46 din medie");
    expect(factorLabelRo("consumul de noapte a crescut cu 18273047% față de istoric")).toBe(
      "Consumul de noapte a crescut de peste 10 ori față de istoric",
    );
    expect(factorLabelRo("față de vecini, o scădere bruscă de 1250.5%")).toBe("Față de vecini, o scădere bruscă de peste 10 ori");
    expect(factorLabelRo("consumul a scăzut cu ~18.273.047 %")).toBe("Consumul a scăzut de peste 10 ori");
    expect(factorLabelRo("consumul de noapte a crescut cu 999% față de istoric")).toBe(
      "Consumul de noapte a crescut cu 999% față de istoric",
    );
    expect(factorLabelRo("cu 72% sub vecini")).toBe("Cu 72% sub vecini");
    expect(factorLabelRo("85% din intervalele de 30 de minute sunt negative")).toBe("85% din intervalele de 30 de minute sunt negative");
  });

  test("rezumatele trec prin aceeași plasă", () => {
    expect(clampPercentRo("Consumul a crescut cu 5000%, iar bilanțul confirmă.")).toBe("Consumul a crescut de peste 10 ori, iar bilanțul confirmă.");
    expect(clampPercentRo("Tensiunea 1.12 pu, 40% peste")).toBe("Tensiunea 1.12 pu, 40% peste");
  });
});

describe("formatare ro-RO", () => {
  test("numere, lei, date, plural", () => {
    expect(fmtScore(0.87)).toBe("0,87");
    expect(fmtLei(2741.2)).toBe("2.741 lei");
    expect(fmtDateLong("2025-07-08")).toBe("Marți, 8 iulie 2025");
    expect(plural(1, "lucrare", "lucrări")).toBe("1 lucrare");
    expect(plural(72, "lucrare", "lucrări")).toBe("72 de lucrări");
  });
});

describe("locul unei lucrări, cu diacriticele din date", () => {
  const base = { location: { lat: 44.4, lon: 26.1, zone_id: "IF-AFUMATI", county: "Ilfov", label: "" } } as unknown as WorkItem;
  test("contor, post, zonă", () => {
    const meter = { ...base, asset_type: "meter", asset_id: "MTR-011050", location: { ...base.location, label: "Contor MTR-011050, PT-1208, Chiajna (sintetic)" } } as WorkItem;
    expect(itemTitle(meter)).toBe("Contor MTR-011050");
    expect(itemPlace(meter)).toBe("PT-1208, Chiajna");
    const post = { ...base, asset_type: "transformer_post", asset_id: "PT-1269", location: { ...base.location, label: "PT-1269, Afumați (sintetic)" } } as WorkItem;
    expect(itemTitle(post)).toBe("PT-1269");
    expect(itemPlace(post)).toBe("Afumați, Ilfov");
    const zone = { ...base, asset_type: "zone", asset_id: "IF-BUFTEA", location: { ...base.location, label: "Zona Buftea (Ilfov)" } } as WorkItem;
    expect(itemTitle(zone)).toBe("Zona Buftea");
    expect(itemPlace(zone)).toBe("Ilfov");
  });
});

describe("orele față de ziua planului", () => {
  test("întoarcerea după miezul nopții rămâne după plecare", async () => {
    const { minutesOfPlanDay, hhmmDay } = await import("@/lib/format");
    const { crewTimeline } = await import("@/lib/plan-derive");
    expect(minutesOfPlanDay("2025-07-08T23:00:00+03:00", "2025-07-08")).toBe(23 * 60);
    expect(minutesOfPlanDay("2025-07-09T00:15:00+03:00", "2025-07-08")).toBe(24 * 60 + 15);
    expect(hhmmDay(24 * 60 + 15)).toBe("00:15 (+1 zi)");
    const tl = crewTimeline(
      {
        crew_id: "E-X-1",
        depot_id: "D",
        total_km: 10,
        total_work_min: 60,
        total_travel_min: 30,
        depart_at: "2025-07-08T22:30:00+03:00",
        return_at: "2025-07-09T00:15:00+03:00",
        stops: [{ seq: 1, work_item_id: "B-20250708-Z", eta: "2025-07-08T23:00:00+03:00", duration_min: 60, travel_km: 5 }],
      },
      "08:00",
      "2025-07-08",
    );
    expect(tl.back).toBeGreaterThan(tl.depart);
    expect(tl.back).toBe(24 * 60 + 15);
  });
});
