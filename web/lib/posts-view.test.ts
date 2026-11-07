import { describe, expect, test } from "bun:test";
import { boundsOfRows, causeBand, causeProbs, filterRows, postColor, postPlace, regionOfPost, sortRows, type PostRow } from "@/lib/posts-view";

const regions = { muntenia_sud: { label_ro: "Muntenia Sud", counties: ["București", "Ilfov", "Giurgiu"] }, dobrogea: { counties: ["Constanța"] } };
const row = (o: Partial<PostRow>): PostRow => ({ id: "PT-1", lat: 44, lon: 26, region: "muntenia_sud", place: "Afumați", loss: 10, color: "verde", meters: 0, diagnosis: null, voltage: null, title: "PT-1, Afumați", ...o });

describe("posts-view", () => {
  test("culoarea fără diacritice și din pierdere", () => {
    expect(postColor({ color: "rosu" })).toBe("roșu");
    expect(postColor({ color: null, loss_lei_month: 250 })).toBe("galben");
    expect(postColor({ color: null, loss_lei_month: null })).toBe("necunoscut");
  });
  test("regiunea și localitatea", () => {
    expect(regionOfPost({ zone_id: "IF-AFUMATI" }, regions)).toBe("muntenia_sud");
    expect(regionOfPost({ zone_id: "B-S6" }, regions)).toBe("muntenia_sud");
    expect(regionOfPost({ zone_id: "XX-1" }, regions)).toBeNull();
    expect(postPlace({ post_id: "PT-1269", label: "PT-1269, Afumați (sintetic)", zone_id: "IF-AFUMATI" })).toBe("Afumați");
  });
  test("filtre, sortare, margini", () => {
    const rows = [row({ id: "PT-2", loss: 700, color: "roșu" }), row({ id: "PT-10", loss: 5 }), row({ id: "PT-3", region: "dobrogea", place: "Medgidia", loss: null, color: "necunoscut" })];
    expect(filterRows(rows, { region: "toate", status: "roșu", q: "" }).map((r) => r.id)).toEqual(["PT-2"]);
    expect(filterRows(rows, { region: "dobrogea", status: "toate", q: "medgidia" }).length).toBe(1);
    expect(sortRows(rows, "loss", "desc").map((r) => r.id)).toEqual(["PT-2", "PT-10", "PT-3"]);
    expect(sortRows(rows, "post", "asc").map((r) => r.id)).toEqual(["PT-2", "PT-3", "PT-10"]);
    const b = boundsOfRows([{ lat: 44, lon: 26 }, { lat: 45, lon: 27 }], [0, 0, 1, 1]);
    expect(b[0]).toBeLessThan(26);
    expect(b[3]).toBeGreaterThan(45);
  });
  test("cauzele", () => {
    expect(causeBand(0.99)).toBe("Likely");
    expect(causeBand(0.3)).toBe("Possible");
    expect(causeBand(0.01)).toBe("Unlikely");
    expect(causeProbs({ diagnosis_proba: { a: 0.1, b: 0.8 } }).map((c) => c.key)).toEqual(["b", "a"]);
    expect(causeProbs({})).toEqual([]);
  });
});
