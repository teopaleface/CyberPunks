"use client";
import type { DraftRequest } from "@/lib/operations/types";
import { parseProposalId } from "@/lib/operations/proposal-link";
import { readableDate } from "./scope";
import { ACTION_NAMES } from "./proposal-form";
export function DraftRequests({
  proposals,
  busy,
  onOpen,
}: {
  proposals: DraftRequest[];
  busy: boolean;
  onOpen: (id: string) => void;
}) {
  if (!proposals.length) return null;
  const drafts = proposals.slice(0, 10);
  return (
    <section className="db-panel" aria-label="Draft requests">
      <div className="db-section-title">
        <h2>Draft requests</h2>
        <span className="db-count">{drafts.length}</span>
      </div>
      <p className="db-muted">
        Your current, unconfirmed drafts, including requests started in
        WhatsApp. Opening a draft does not confirm it.
      </p>
      {drafts.map((proposal) => (
        <article key={proposal.proposal_id}>
          <h3>{ACTION_NAMES[proposal.action]}</h3>
          <p>{proposal.summary}</p>
          <p className="db-muted">
            Expires {readableDate(proposal.expires_at)}
          </p>
          <div className="db-actions">
            <button
              type="button"
              className="db-button"
              disabled={busy || !parseProposalId(proposal.proposal_id)}
              onClick={() => onOpen(proposal.proposal_id)}
            >
              Open for review
            </button>
          </div>
        </article>
      ))}
    </section>
  );
}
