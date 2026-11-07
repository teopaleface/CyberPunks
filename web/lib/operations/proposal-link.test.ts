import { expect, test } from "bun:test";
import { loadLinkedProposal } from "./linked-proposal";
import {
  parseProposalId,
  proposalFromSearch,
  proposalSignInPath,
  proposalWorkspacePath,
  signInModeParams,
} from "./proposal-link";
import type { Proposal } from "./types";
const id = "6d57ebca-af8d-4da4-afcb-3080dca9a671";
const saved: Proposal = {
  proposal_id: id,
  action: "record_verdict",
  summary: "Record the actual field finding.",
  data: {
    work_item_id: "assigned-work",
    outcome: "no_access",
    plan_version: "pinned-version",
  },
  expires_at: "2027-01-01T00:00:00Z",
  scenario: "demo-vara",
};
test("a proposal link survives sign-in and sign-up mode changes as a fixed same-origin destination", () => {
  const signIn = proposalSignInPath(id);
  expect(signIn).toBe(`/intra?proposal=${id}`);
  const params = new URLSearchParams(signIn.split("?")[1]);
  for (const mode of ["cont-nou", "resetare", "intra"]) {
    const next = signInModeParams(params, mode);
    expect(proposalWorkspacePath(proposalFromSearch(next))).toBe(
      `/workspace?proposal=${id}`,
    );
    expect(next.get("mod")).toBe(mode === "intra" ? null : mode);
  }
});
test.each([
  "https://foreign.example",
  "//foreign.example",
  "/workspace?proposal=anything",
  "javascript:alert(1)",
  "../confirm",
  `${id}/confirm`,
  `${id}?confirm=true`,
  `${id}\n`,
  "p-one",
  "",
])("rejects unsafe or ambiguous proposal input %s", (value) => {
  expect(parseProposalId(value)).toBeNull();
  expect(proposalSignInPath(value)).toBe("/intra");
  expect(proposalWorkspacePath(value)).toBe("/app");
});
test("duplicate query values and arbitrary redirect parameters never choose a destination", () => {
  expect(parseProposalId([id, id])).toBeNull();
  expect(
    proposalFromSearch(new URLSearchParams(`proposal=${id}&proposal=${id}`)),
  ).toBeNull();
  const input = new URLSearchParams(
    `proposal=${id}&next=https://foreign.example&returnTo=//foreign.example`,
  );
  expect(signInModeParams(input, "intra").toString()).toBe(`proposal=${id}`);
  expect(proposalWorkspacePath(proposalFromSearch(input))).toBe(
    `/workspace?proposal=${id}`,
  );
});
test("loading a linked proposal makes one read and returns the exact server object, with no confirmation", async () => {
  const calls: string[] = [];
  expect(
    await loadLinkedProposal(id, async (path) => {
      calls.push(path);
      return saved;
    }),
  ).toBe(saved);
  expect(calls).toEqual([`operations/proposals/${id}`]);
});
test("invalid identifiers never reach the gateway and server refusals do not create a local substitute", async () => {
  const calls: string[] = [];
  await expect(
    loadLinkedProposal(`${id}/confirm`, async (path) => {
      calls.push(path);
      return saved;
    }),
  ).rejects.toThrow("invalid");
  expect(calls).toEqual([]);
  const expired = new Error(
    "This proposal has expired or its source data changed.",
  );
  await expect(
    loadLinkedProposal(id, async () => {
      throw expired;
    }),
  ).rejects.toBe(expired);
});
test("a different or malformed response never initializes a confirmation card", async () => {
  for (const value of [
    { ...saved, proposal_id: crypto.randomUUID() },
    { ...saved, action: "send_whatsapp" },
    { ...saved, data: null },
    { ...saved, expires_at: "unknown" },
  ])
    await expect(
      loadLinkedProposal(id, async () => value as Proposal),
    ).rejects.toThrow("valid proposal");
});
