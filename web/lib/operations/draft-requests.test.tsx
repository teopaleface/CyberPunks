import { expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { DraftRequests } from "../../components/workspace/draft-requests";
import type { DraftRequest } from "./types";
function proposal(i: number): DraftRequest {
  return {
    proposal_id: crypto.randomUUID(),
    action: "record_verdict",
    summary: `Synthetic draft ${i} for review`,
    expires_at: "2027-01-01T00:00:00Z",
  };
}
test("own draft requests are discoverable without automatically reading or confirming them", () => {
  const calls: string[] = [];
  const draft = proposal(1);
  const html = renderToStaticMarkup(
    <DraftRequests
      proposals={[draft]}
      busy={false}
      onOpen={(id) => calls.push(id)}
    />,
  );
  expect(html).toContain("Draft requests");
  expect(html).toContain(draft.summary);
  expect(html).toContain("Open for review");
  expect(html).not.toContain("Confirm</button>");
  expect(calls).toEqual([]);
});
test("draft discovery is bounded and invalid IDs cannot expose an open button that is enabled", () => {
  const drafts = Array.from({ length: 11 }, (_, i) => proposal(i));
  const html = renderToStaticMarkup(
    <DraftRequests
      proposals={drafts}
      busy={false}
      onOpen={() => {
        throw new Error("Must remain idle");
      }}
    />,
  );
  expect(html).toContain(drafts[9].summary);
  expect(html).not.toContain(drafts[10].summary);
  const invalid = renderToStaticMarkup(
    <DraftRequests
      proposals={[{ ...proposal(0), proposal_id: "../confirm" }]}
      busy={false}
      onOpen={() => {
        throw new Error("Must remain idle");
      }}
    />,
  );
  expect(invalid).toContain("disabled");
  expect(
    renderToStaticMarkup(
      <DraftRequests proposals={[]} busy={false} onOpen={() => {}} />,
    ),
  ).toBe("");
});
