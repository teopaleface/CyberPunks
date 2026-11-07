import { describe, expect, test } from "bun:test";
import type { WorkItem } from "@/lib/contracts";
import { placeOf } from "@/lib/briefing";

const item = (o: Partial<WorkItem> & { label: string; county?: string }): WorkItem =>
  ({
    work_item_id: "X",
    source: "B",
    asset_id: "TM-INEU",
    asset_type: "zone",
    location: { lat: 46, lon: 21, zone_id: "AR-INEU", county: o.county ?? "Arad", label: o.label },
    ...o,
  }) as unknown as WorkItem;

describe("briefingul", () => {
  test("titlul cazului poartă și locul", () => {
    expect(placeOf(item({ label: "Zona Ineu (Arad)" }))).toBe("Zona Ineu, Arad");
  });
});
