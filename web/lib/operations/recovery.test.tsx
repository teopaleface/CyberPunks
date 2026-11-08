import { expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { PendingCommands } from "../../components/workspace/pending-commands";
import type { Actor } from "./policy";
import type { PendingCommand } from "./types";
import { recoveryControl } from "./recovery";
const dispatcher = {
  role: "dispatcher",
  permissions: ["recover_commands"],
} as const;
function pending(
  action: PendingCommand["recovery_action"],
  can_recover = true,
): PendingCommand {
  return {
    command_id: "pending-command",
    proposal_id: "original-proposal",
    action: "record_verdict",
    status: "reconciling",
    created_at: "2026-11-07T22:00:00Z",
    can_recover,
    recovery_action: action,
  };
}
function render(
  command: PendingCommand,
  actor: Pick<Actor, "role" | "permissions"> = {
    ...dispatcher,
    permissions: [...dispatcher.permissions],
  },
) {
  const calls: string[] = [];
  const html = renderToStaticMarkup(
    <PendingCommands
      commands={[command]}
      actor={actor}
      busy={false}
      onRetrieve={async (id) => {
        calls.push(id);
        return true;
      }}
      onCancel={async (id) => {
        calls.push(id);
        return true;
      }}
    />,
  );
  return { html, calls };
}
test("pending commands are discoverable on a fresh render without retrieving or cancelling", () => {
  const { html, calls } = render(pending("retrieve"));
  expect(html).toContain("Pending commands");
  expect(html).toContain("pending-command");
  expect(html).toContain("original-proposal");
  expect(html).toContain("Retrieve saved result");
  expect(calls).toEqual([]);
});
test("cancellation starts with a review button, without posting or presenting an implicit confirmation", () => {
  const { html, calls } = render(pending("cancel"));
  expect(html).toContain("Review cancellation");
  expect(html).not.toContain("Confirm cancellation");
  expect(calls).toEqual([]);
});
test.each(["manual_review", "requires_dispatcher"] as const)(
  "%s is truthful and has no recovery control",
  (action) => {
    const { html, calls } = render(pending(action));
    expect(html).not.toContain("<button");
    expect(html).toContain(
      action === "manual_review"
        ? "Manual review is required"
        : "authorized dispatcher must recover",
    );
    expect(calls).toEqual([]);
  },
);
test("server recovery flag and current dispatcher permission both gate buttons", () => {
  expect(render(pending("cancel", false)).html).not.toContain("<button");
  expect(
    render(pending("cancel"), { role: "dispatcher", permissions: [] }).html,
  ).not.toContain("<button");
  expect(
    render(pending("cancel"), {
      role: "technician",
      permissions: ["recover_commands"],
    }).html,
  ).not.toContain("<button");
  expect(
    render(pending("retrieve"), { role: "dispatcher", permissions: [] }).html,
  ).not.toContain("<button");
  expect(
    recoveryControl(
      { role: "technician", permissions: [] },
      pending("retrieve"),
    ),
  ).toBe("retrieve");
  expect(
    recoveryControl(
      { role: "dispatcher", permissions: ["recover_commands"] },
      { ...pending("cancel"), status: "cancelled" },
    ),
  ).toBeNull();
});
