import type { Actor } from "./policy";
import type { PendingCommand } from "./types";
export function recoveryControl(
  actor: Pick<Actor, "role" | "permissions">,
  command: PendingCommand,
): "retrieve" | "cancel" | null {
  if (!command.can_recover || command.status !== "reconciling") return null;
  if (
    actor.role === "dispatcher" &&
    !actor.permissions.includes("recover_commands")
  )
    return null;
  if (command.recovery_action === "retrieve") return "retrieve";
  return command.recovery_action === "cancel" &&
    actor.role === "dispatcher" &&
    actor.permissions.includes("recover_commands")
    ? "cancel"
    : null;
}
