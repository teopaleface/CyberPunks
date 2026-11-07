import { describe, expect, test } from "bun:test";
import type { WorkItem } from "@/lib/contracts";
import { auditActionRo, clampPercentRo, factorLabelRo, thresholdLabelRo, thresholdValueRo } from "@/lib/data/labels";
import { fmtDateLong, fmtLei, fmtScore, plural } from "@/lib/format";
import { itemPlace, itemTitle } from "@/lib/plan-screen";

describe("pragurile, în cuvinte", () => {
  test("scorurile nu se confundă cu minutele", () => {
    expect(thresholdValueRo("score_min", 0.5)).toBe("0.50");
    expect(thresholdValueRo("visit_min_score", 0.62)).toBe("0.62");
    expect(thresholdValueRo("arrive_before_start_min", 60)).toBe("60 min");
  });
  test("lei, pu, zile, steaguri", () => {
    expect(thresholdValueRo("cost_lei", 2953)).toBe("2,953 RON");
    expect(thresholdValueRo("overvoltage_limit_pu", 1.1)).toBe("1.10 pu");
    expect(thresholdValueRo("planned_notice_working_days", 5)).toBe("5 days");
    expect(thresholdValueRo("smart_meter", 1)).toBe("yes");
    expect(thresholdLabelRo("necunoscut_x")).toBe("necunoscut x");
  });
  test("acțiunile din jurnal", () => {
    expect(auditActionRo("review_approve")).toBe("human approved");
    expect(auditActionRo("assigned")).toBe("assigned");
  });
});

describe("textele factorilor", () => {
  test("English decimals and bounded extreme percentages", () => {
    expect(factorLabelRo("Variația în cursul zilei: 0.46 din medie")).toBe("Variation during the day: 0.46 of the mean");
    expect(factorLabelRo("consumul de noapte a crescut cu 18273047% față de istoric")).toBe(
      "Night consumption increased more than 10 times compared with its history",
    );
    expect(factorLabelRo("față de vecini, o scădere bruscă de 1250.5%")).toBe("A sudden fall of more than 10 times compared with neighbours");
    expect(factorLabelRo("consumul a scăzut cu ~18.273.047 %")).toBe("Consumption fell more than 10 times");
    expect(factorLabelRo("consumul de noapte a crescut cu 999% față de istoric")).toBe(
      "Night consumption increased by 999% compared with its history",
    );
    expect(factorLabelRo("cu 72% sub vecini")).toBe("72% below neighbouring customers");
    expect(factorLabelRo("85% din intervalele de 30 de minute sunt negative")).toBe("85% of half-hour readings are negative");
  });

  test("rezumatele trec prin aceeași plasă", () => {
    expect(clampPercentRo("Consumul a crescut cu 5000%, iar bilanțul confirmă.")).toBe("Consumption increased more than 10 times, confirmed by the energy balance.");
    expect(clampPercentRo("Tensiunea 1.12 pu, 40% peste")).toBe("Voltage 1.12 pu, 40% above");
  });
});

describe("English display formatting", () => {
  test("numere, lei, date, plural", () => {
    expect(fmtScore(0.87)).toBe("0.87");
    expect(fmtLei(2741.2)).toBe("2,741 RON");
    expect(fmtLei(2)).toBe("2 RON");
    expect(fmtLei(0)).toBe("0 RON");
    expect(fmtLei(2.7)).toBe("2.70 RON");
    expect(fmtDateLong("2025-07-08")).toBe("Tuesday, 8 July 2025");
    expect(plural(1, "work item", "work items")).toBe("1 work item");
    expect(plural(72, "work item", "work items")).toBe("72 work items");
  });
});

describe("locul unei lucrări, cu diacriticele din date", () => {
  const base = { location: { lat: 44.4, lon: 26.1, zone_id: "IF-AFUMATI", county: "Ilfov", label: "" } } as unknown as WorkItem;
  test("contor, post, zonă", () => {
    const meter = { ...base, asset_type: "meter", asset_id: "MTR-011050", location: { ...base.location, label: "Contor MTR-011050, PT-1208, Chiajna (sintetic)" } } as WorkItem;
    expect(itemTitle(meter)).toBe("Meter MTR-011050");
    expect(itemPlace(meter)).toBe("PT-1208, Chiajna");
    const post = { ...base, asset_type: "transformer_post", asset_id: "PT-1269", location: { ...base.location, label: "PT-1269, Afumați (sintetic)" } } as WorkItem;
    expect(itemTitle(post)).toBe("PT-1269");
    expect(itemPlace(post)).toBe("Afumați, Ilfov");
    const zone = { ...base, asset_type: "zone", asset_id: "IF-BUFTEA", location: { ...base.location, label: "Zona Buftea (Ilfov)" } } as WorkItem;
    expect(itemTitle(zone)).toBe("Buftea area");
    expect(itemPlace(zone)).toBe("Ilfov");
  });
});

describe("orele față de ziua planului", () => {
  test("întoarcerea după miezul nopții rămâne după plecare", async () => {
    const { minutesOfPlanDay, hhmmDay } = await import("@/lib/format");
    const { crewTimeline } = await import("@/lib/plan-derive");
    expect(minutesOfPlanDay("2025-07-08T23:00:00+03:00", "2025-07-08")).toBe(23 * 60);
    expect(minutesOfPlanDay("2025-07-09T00:15:00+03:00", "2025-07-08")).toBe(24 * 60 + 15);
    expect(hhmmDay(24 * 60 + 15)).toBe("00:15 (+1 day)");
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

describe("alertele, față de decizii", () => {
  test("numără ce s-a decis de fapt pentru lucrările alertei", async () => {
    const { alertOutcomeRo } = await import("@/lib/data/labels");
    const d = (decision: string) => ({ decision });
    const decisions = { a: d("assigned"), b: d("remote_action"), c: d("remote_action"), e: d("deferred") };
    expect(alertOutcomeRo(["a", "b", "c", "e", "x"], decisions)).toBe("1 assigned, 2 checked remotely, 1 deferred, 1 without a decision");
    expect(alertOutcomeRo(["a"], decisions)).toBeNull();
    expect(alertOutcomeRo(["x", "y"], decisions)).toBeNull();
  });
});

describe("jurnalul real, în cuvinte", () => {
  test("acțiunea de fuziune, pragurile noi, valorile da/nu", () => {
    expect(auditActionRo("fusion")).toBe("checked against the energy balance");
    expect(thresholdLabelRo("a_score")).toBe("model A score");
    expect(thresholdValueRo("fusion_confirmed", true)).toBe("yes");
    expect(thresholdValueRo("smart_meter", false)).toBe("no");
    expect(thresholdValueRo("post_excess_loss_lei_month", 5019.34)).toBe("5,019 RON per month");
    expect(thresholdValueRo("post_excess_loss_kwh_day", 239.02)).toBe("239.0 kWh/day");
    expect(thresholdValueRo("participation_rate", 0.1)).toBe("10%");
    expect(thresholdValueRo("fusion_a_score", 0.981)).toBe("0.98");
  });
});

describe("zilele scurte", () => {
  test("ziua și luna, cu sau fără miezul nopții", async () => {
    const { fmtDayMonth, isWholeDay } = await import("@/lib/format");
    expect(fmtDayMonth("2025-05-10T00:00:00")).toBe("10/05");
    expect(fmtDayMonth("2025-06-02")).toBe("02/06");
    expect(isWholeDay("2025-06-02T00:00:00")).toBe(true);
    expect(isWholeDay("2025-06-02")).toBe(true);
    expect(isWholeDay("2025-07-08T14:00:00+03:00")).toBe(false);
  });
});

describe("numerele omenești", () => {
  test("lei aproximativi, „de” după numerele mari, încrederea în cuvinte", async () => {
    const { approxLei, withDe, confidenceWord, scoreText, roundPct } = await import("@/lib/human");
    expect(approxLei(5019.34)).toBe("about 5,000 RON");
    expect(approxLei(71802.9)).toBe("about 72,000 RON");
    expect(approxLei(12439)).toBe("about 12,000 RON");
    expect(approxLei(12)).toBe("12 RON");
    expect(approxLei(5000)).toBe("5,000 RON");
    expect(withDe(20, "work items")).toBe("20 work items");
    expect(withDe(19, "work items")).toBe("19 work items");
    expect(withDe(101, "work items")).toBe("101 work items");
    expect(confidenceWord("low", 0.58)).toBe("low confidence");
    expect(confidenceWord(undefined, 0.9)).toBe("high confidence");
    expect(scoreText(1)).toBe("above 0.99");
    expect(scoreText(0.58)).toBe("0.58");
    expect(roundPct(0.2178)).toBe("22%");
  });
});

describe("probabilitățile de 100%", () => {
  test("devin „peste 99%” în texte", () => {
    expect(clampPercentRo("probabilitatea depășirii 100%. Motive: soare")).toBe("Exceedance probability above 99%. Reasons: Sunlight");
    expect(clampPercentRo("pierdere tehnică (probabilitate 100%)")).toBe("Technical loss (probability above 99%)");
    expect(clampPercentRo("Probabilitate de avarii 43%")).toBe("Outage probability 43%");
  });
});
