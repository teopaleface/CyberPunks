import { describe, expect, test } from "bun:test";
import type { Decision, WorkItem } from "@/lib/contracts";
import { postVerdictRo, verdictRo } from "@/lib/verdict";

function item(o: Partial<WorkItem> & { label?: string; score?: number; confidence?: string; pl?: string }): WorkItem {
  return {
    work_item_id: "X",
    source: "A",
    kind: "meter_inspection",
    asset_id: "MTR-011050",
    asset_type: "meter",
    location: { lat: 0, lon: 0, zone_id: "Z", county: "Ilfov", label: o.label ?? null },
    target_date: "2025-07-08",
    time_window: null,
    prediction: { label: o.pl ?? "faulty", score: o.score ?? 0.98, confidence: o.confidence ?? "high" },
    recommended_action: "inspect_on_site",
    extra: {},
    ...o,
  } as unknown as WorkItem;
}
const dec = (d: Partial<Decision>): Decision => ({ work_item_id: "X", decision: "assigned", reason_ro: "", rule_id: "R", audit_id: "a", ...d }) as Decision;

describe("verdictRo", () => {
  test("contor defect, citire la distanță", () => {
    const v = verdictRo(item({}), dec({ decision: "remote_action", reason_ro: "echipele sunt pline: citire la distanță azi, vizita în planul următor." }));
    expect(v.headline).toBe("Contorul MTR-011050 pare defect, cu încredere mare.");
    expect(v.detail).toBe("Agentul: citire la distanță azi; vizita rămâne pentru planul următor.");
  });

  test("bilanț pe post", () => {
    const w = item({ source: "A", asset_type: "transformer_post", asset_id: "PT-1269", pl: "pierdere_tehnica", extra: { lei_per_month: 5019.34 } });
    const v = verdictRo(w, dec({ crew_id: "E-BE-2", reason_ro: "Echipa E-BE-2, oprirea 2, sosire la 11:30." }));
    expect(v.headline).toBe("Postul PT-1269 pierde circa 5.000 de lei pe lună. Cauza probabilă: pierdere tehnică.");
    expect(v.detail).toBe("Agentul: echipa E-BE-2 ajunge la 11:30.");
  });

  test("furtună, echipă asignată înainte de fereastră", () => {
    const w = item({
      source: "B", asset_type: "zone", asset_id: "TM-TIMISOARA", pl: "outage_risk", confidence: "medium", score: 0.43,
      label: "Zona Timișoara (Timiș)", time_window: { start: "2025-07-08T15:00:00+03:00", end: "2025-07-08T21:00:00+03:00" },
    });
    const v = verdictRo(w, dec({ crew_id: "E-TM-1", reason_ro: "Echipa E-TM-1, oprirea 1, sosire la 14:00." }));
    expect(v.headline).toBe("Zona Timișoara: risc de avarii la furtună, cu încredere medie.");
    expect(v.detail).toBe("Echipa E-TM-1 ajunge la 14:00, înainte de fereastra de risc.");
  });

  test("furtună fără echipă: decizia în cuvinte", () => {
    const w = item({ source: "B", asset_type: "zone", asset_id: "TM-X", pl: "outage_risk", confidence: "low", label: "Zona X (Timiș)" });
    const v = verdictRo(w, dec({ decision: "deferred" }));
    expect(v.headline).toBe("Zona X: risc de avarii la furtună, cu încredere mică.");
    expect(v.detail).toContain("amânată");
  });

  test("tensiune cu soluție aleasă", () => {
    const w = item({ source: "C", asset_type: "transformer_post", asset_id: "PT-1269", pl: "overvoltage" });
    const v = verdictRo(w, dec({ decision: "notify", threshold: { overvoltage_limit_pu: 1.1 } }), {
      chosen: ["phase_rebalance", "offer_battery", "export_limit"],
      costLei: 12439.34,
    });
    expect(v.headline).toBe("Postul PT-1269: tensiunea trece de limita de 1,10 la prânz, cu încredere mare.");
    expect(v.detail).toBe("Soluția aleasă: reechilibrarea fazelor + oferta de baterii + limitarea injecției, circa 12.000 de lei.");
  });

  test("tensiune fără soluție: decizia în cuvinte", () => {
    const w = item({ source: "C", asset_type: "transformer_post", asset_id: "PT-9", pl: "overvoltage" });
    expect(verdictRo(w, dec({ decision: "human_review" })).detail).toBe("Agentul nu e sigur: decide un om.");
  });

  test("rezervă", () => {
    const w = item({ source: "B", asset_type: "feeder" as never, asset_id: "F-1", label: null as never });
    // sursa B are propria ramură; rezerva se atinge doar pentru surse necunoscute
    const odd = { ...w, source: "Z" } as unknown as WorkItem;
    const v = verdictRo(odd, dec({ decision: "deferred" }));
    expect(v.headline).toContain("F-1");
    expect(v.detail).toBe("Decizia: amânată.");
  });
});

describe("postVerdictRo", () => {
  test("pierdere + soluție", () => {
    const v = postVerdictRo({ postId: "PT-1269", lossLeiMonth: 5019, causeRo: "pierdere tehnică", chosen: ["phase_rebalance", "export_limit"], costLei: 12439 });
    expect(v.headline).toBe("Postul PT-1269 pierde circa 5.000 de lei pe lună. Cauza: pierdere tehnică.");
    expect(v.detail).toBe("Soluția aleasă pentru tensiune: reechilibrarea fazelor + limitarea injecției, circa 12.000 de lei.");
  });
  test("fără pierdere, contoare semnalate", () => {
    const v = postVerdictRo({ postId: "PT-1208", lossLeiMonth: null, metersFlagged: 3 });
    expect(v.headline).toBe("Postul PT-1208: bilanțul nu arată pierderi peste normal.");
    expect(v.detail).toBe("3 contoare semnalate pe post.");
  });
});
