import { describe, expect, test } from "bun:test";
import { englishText } from "./english";

describe("English display boundaries", () => {
  test("place names and opaque IDs are preserved", () => {
    expect(englishText("Ștefăneștii de Jos")).toBe("Ștefăneștii de Jos");
    expect(englishText("A-20250708-PT-1182")).toBe("A-20250708-PT-1182");
  });
  test("translates evidence without changing its quantities", () => {
    expect(englishText("La post lipsesc ~42.7 kWh/zi peste pierderea normală (10.2% din energie), 14 din 14 zile peste P90"))
      .toBe("Missing energy at the substation is ~42.7 kWh/day above normal loss (10.2% of energy); 14 of 14 days exceed P90");
  });
  test("unrecognised evidence is not replaced with an invented explanation", () => {
    const source = "Explicație necunoscută, păstrează sursa.";
    expect(englishText(source)).toBe(source);
  });
});

test("paragraph wrappers preserve remedy values and synthetic annotations", () => {
  const source = "Soluția aleasă: oferta de baterii (24 lei): P90 scade de la 1,177 la 1,094 pu, sub limita de 1,10. Mâine: mesajele către clienți.";
  expect(englishText(source)).toBe("Chosen remedy: Battery offer (24 RON). P90 falls from 1.177 to 1.094 pu, below the 1.10 limit. Tomorrow: customer messages.");
  expect(englishText("PT-1 (sintetic), Ștefăneștii de Jos (sintetic)")).toBe("PT-1 (synthetic), Ștefăneștii de Jos (synthetic)");
  expect(englishText("Valoare așteptată 36.762 lei: Zona Lugoj (Timiș), Zona Deva (Hunedoara) și încă 1."))
    .toBe("Expected value 36,762 RON: Lugoj (Timiș) area, Deva (Hunedoara) area and 1 more.");
});
