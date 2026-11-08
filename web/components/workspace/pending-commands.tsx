"use client";
import { useState } from "react";
import type { Actor } from "@/lib/operations/policy";
import type { PendingCommand } from "@/lib/operations/types";
import { label } from "@/lib/operations/types";
import { recoveryControl } from "@/lib/operations/recovery";
import { readableDate } from "./scope";
import { ACTION_NAMES } from "./proposal-form";
export function PendingCommands({
  commands,
  actor,
  busy,
  onRetrieve,
  onCancel,
}: {
  commands: PendingCommand[];
  actor: Pick<Actor, "role" | "permissions">;
  busy: boolean;
  onRetrieve: (id: string) => Promise<boolean>;
  onCancel: (id: string, reason: string) => Promise<boolean>;
}) {
  const [draft, setDraft] = useState<{
    commandId: string;
    reason: string;
    reviewed: boolean;
  } | null>(null);
  if (!commands.length) return null;
  const selected = commands.find(
    (command) => command.command_id === draft?.commandId,
  );
  const cancellable = selected && recoveryControl(actor, selected) === "cancel";
  return (
    <section className="db-panel" aria-label="Pending commands">
      <div className="db-section-title">
        <h2>Pending commands</h2>
        <span className="db-count">{commands.length}</span>
      </div>
      <p className="db-muted">
        These commands are saved on the server and remain visible after
        reopening this workspace. Resolve them before confirming new operations.
        Refreshing this list does not cancel or execute a command.
      </p>
      {commands.map((command) => {
        const control = recoveryControl(actor, command);
        return (
          <article key={command.command_id}>
            <h3>{ACTION_NAMES[command.action] ?? label(command.action)}</h3>
            <p>
              Command {command.command_id} · {label(command.status)}
            </p>
            <p className="db-muted">
              Created {readableDate(command.created_at)}. Proposal{" "}
              {command.proposal_id}.
            </p>
            {command.recovery_action === "manual_review" ? (
              <p>
                Manual review is required because the saved effect is uncertain.
                Automatic retrieval and cancellation are unavailable.
              </p>
            ) : command.recovery_action === "requires_dispatcher" ? (
              <p>
                An authorized dispatcher must recover this command. Your
                previous membership will not be restored.
              </p>
            ) : !control ? (
              <p>
                Your current account does not have permission to recover this
                command. Contact an authorized dispatcher.
              </p>
            ) : control === "retrieve" ? (
              <div className="db-actions">
                <button
                  type="button"
                  className="db-button"
                  disabled={busy}
                  onClick={() => void onRetrieve(command.command_id)}
                >
                  Retrieve saved result
                </button>
              </div>
            ) : (
              <div className="db-actions">
                <button
                  type="button"
                  className="db-button"
                  disabled={busy}
                  onClick={() =>
                    setDraft({
                      commandId: command.command_id,
                      reason: "",
                      reviewed: false,
                    })
                  }
                >
                  Review cancellation
                </button>
              </div>
            )}
          </article>
        );
      })}
      {draft && cancellable && (
        <form
          className="db-form"
          aria-label="Cancel pending command"
          onSubmit={(event) => {
            event.preventDefault();
            if (draft.reason.trim().length >= 3)
              setDraft({
                ...draft,
                reason: draft.reason.trim(),
                reviewed: true,
              });
          }}
        >
          <h3>Cancel command {draft.commandId}</h3>
          {draft.reviewed ? (
            <>
              <p>
                No effect has been published according to the latest server
                check. The server checks this again before cancellation.
              </p>
              <p>Reason: {draft.reason}</p>
              <p>
                This cancels the pending command. It does not execute the
                original operation or restore previous permissions.
              </p>
              <div className="db-actions">
                <button
                  type="button"
                  className="db-primary"
                  disabled={busy}
                  onClick={() => {
                    void (async () => {
                      if (await onCancel(draft.commandId, draft.reason))
                        setDraft(null);
                    })();
                  }}
                >
                  Confirm cancellation
                </button>
                <button
                  type="button"
                  className="db-button"
                  disabled={busy}
                  onClick={() => setDraft({ ...draft, reviewed: false })}
                >
                  Edit reason
                </button>
                <button
                  type="button"
                  className="db-button"
                  disabled={busy}
                  onClick={() => setDraft(null)}
                >
                  Keep pending
                </button>
              </div>
            </>
          ) : (
            <>
              <label>
                Cancellation reason
                <textarea
                  required
                  minLength={3}
                  maxLength={2000}
                  disabled={busy}
                  value={draft.reason}
                  onChange={(event) =>
                    setDraft({ ...draft, reason: event.target.value })
                  }
                />
              </label>
              <div className="db-actions">
                <button
                  className="db-primary"
                  disabled={busy || draft.reason.trim().length < 3}
                >
                  Review reason
                </button>
                <button
                  type="button"
                  className="db-button"
                  disabled={busy}
                  onClick={() => setDraft(null)}
                >
                  Keep pending
                </button>
              </div>
            </>
          )}
        </form>
      )}
    </section>
  );
}
