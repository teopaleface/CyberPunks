import { describe, expect, test } from "bun:test";
import { categoryOf, pageList } from "./queue-model";

describe("categoryOf", () => {
  test("grupează abținerile", () => {
    expect(categoryOf("R-ABSTAIN").id).toBe("abtineri");
    expect(categoryOf("R-ABSTAIN-DATA").id).toBe("abtineri");
  });
  test("încredere mică și siguranță", () => {
    expect(categoryOf("R-WIDE-INTERVAL").id).toBe("incredere");
    expect(categoryOf("R-SAFETY-NO-CREW").label).toBe("Safety risk");
  });
  test("restul au eticheta regulii", () => {
    expect(categoryOf("R-NO-CREW").label.length).toBeGreaterThan(3);
  });
});

describe("pageList", () => {
  test("puține pagini", () => expect(pageList(3, 1)).toEqual([1, 2, 3]));
  test("multe pagini", () => expect(pageList(20, 10)).toEqual([1, "…", 9, 10, 11, "…", 20]));
});
