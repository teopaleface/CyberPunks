import { expect, test } from "bun:test";
import { fmtMetric, stageCounts, totalOf } from "./queue-run";

test("numără pe pași și surse", () => {
  const c = stageCounts({
    items: [{ work_item_id: "A-1" }, { work_item_id: "A-2" }, { work_item_id: "B-1" }],
    invalidIds: ["C-9"],
    decisions: [
      { work_item_id: "A-1", decision: "assigned" },
      { work_item_id: "A-2", decision: "deferred" },
      { work_item_id: "B-1", decision: "human_review" },
      { work_item_id: "C-9", decision: "rejected_invalid" },
    ],
  });
  expect(totalOf(c.perceive)).toBe(4);
  expect(totalOf(c.estimate)).toBe(3);
  expect(totalOf(c.decide)).toBe(3);
  expect(c.act).toEqual({ A: 1, B: 0, C: 0 });
});

test("metrici", () => {
  expect(fmtMetric(0.2777, "pr_auc")).toBe("0,278");
  expect(fmtMetric(1, "precision_at_k")).toBe("peste 0,99");
  expect(fmtMetric(0.00543, "mae_vmax_pu")).toBe("0,00543");
});
