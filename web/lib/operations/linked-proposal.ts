import { parseProposalId } from "./proposal-link";
import type { Proposal } from "./types";
/** Citire exclusivă. Confirmarea rămâne o acțiune separată a interfeței. */
export async function loadLinkedProposal(
  value: unknown,
  read: (path: string) => Promise<Proposal>,
): Promise<Proposal> {
  const id = parseProposalId(value);
  if (!id)
    throw new Error(
      "This proposal link is invalid. Open your workspace to prepare a new proposal.",
    );
  const proposal = await read(`operations/proposals/${id}`);
  if (
    !proposal ||
    proposal.proposal_id !== id ||
    ![
      "create_case",
      "record_verdict",
      "review_work_item",
      "approve_plan",
      "set_availability",
      "request_human",
    ].includes(proposal.action) ||
    typeof proposal.summary !== "string" ||
    !proposal.data ||
    typeof proposal.data !== "object" ||
    Array.isArray(proposal.data) ||
    typeof proposal.expires_at !== "string" ||
    Number.isNaN(Date.parse(proposal.expires_at))
  )
    throw new Error(
      "The service did not return a valid proposal. No action has been confirmed.",
    );
  return proposal;
}
