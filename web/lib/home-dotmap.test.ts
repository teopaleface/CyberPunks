import { describe, expect, test } from "bun:test";
import { computeDots, inPolygon, type GeoJson } from "./home-dotmap";

const square = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] as [number, number][][];

describe("home-dotmap", () => {
  test("punct în poligon, cu gaură", () => {
    expect(inPolygon(0.5, 0.5, square)).toBe(true);
    expect(inPolygon(2, 2, square)).toBe(false);
    const hole = [...square, [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]]] as [number, number][][];
    expect(inPolygon(0.5, 0.5, hole)).toBe(false);
  });
  test("grila păstrează doar punctele din județe și le dă regiunea", () => {
    const geo = { features: [{ properties: { re_region: "banat" }, geometry: { type: "Polygon", coordinates: square } }] } as unknown as GeoJson;
    const m = computeDots(geo, 0.1);
    expect(m.dots.length).toBeGreaterThan(20);
    expect(m.dots.every((d) => d.region === "banat")).toBe(true);
  });
});
