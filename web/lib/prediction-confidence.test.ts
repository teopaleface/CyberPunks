import { expect, test } from "bun:test";
import { causeConfidence } from "./prediction-confidence";

test("PT-1182: separate an almost certain problem from two competing causes", () => {
  // Probabilities from the published demo case, not generated test results.
  const result = causeConfidence({ extra: { diagnosis_proba: { normal: 0.0007, contor_client: 0.4259, furt_inainte_contor: 0.5723, pierdere_tehnica: 0.0008, client_post_gresit: 0.0003, contor_bilant_setat: 0 } } });
  expect(result?.top.probability).toBe(0.5723);
  expect(result?.second.probability).toBe(0.4259);
  expect(result?.margin).toBeCloseTo(0.1464);
});

test("missing or invalid cause scores never become a confidence percentage", () => {
  expect(causeConfidence({ extra: {} })).toBeNull();
  expect(causeConfidence({ extra: { diagnosis_proba: { normal: -1, contor_client: 4 } } })).toBeNull();
});
