import type { Membership } from "./policy";
export const DEMO_DISPATCHER_PERMISSIONS = [
  "approve_plan",
  "review_work_item",
  "create_case",
  "view_console",
  "recover_commands",
];
const sameValues = (a: string[], b: string[]) =>
  JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());
export function sameMembership(
  a: Membership | undefined,
  b: Membership,
): boolean {
  return Boolean(
    a &&
    a.role === b.role &&
    a.organization_id === b.organization_id &&
    a.crew_id === b.crew_id &&
    Array.isArray(a.connection_ids) &&
    Array.isArray(a.permissions) &&
    sameValues(a.connection_ids, b.connection_ids) &&
    sameValues(a.permissions, b.permissions),
  );
}
/** Singura extindere administrativă permisă contului sintetic deja verificat. */
export function mayAddDemoRecovery(
  current: Membership | undefined,
  expected: Membership,
): boolean {
  if (
    !current ||
    current.role !== "dispatcher" ||
    current.organization_id !== "daybreak-demo" ||
    current.crew_id !== null ||
    !Array.isArray(current.connection_ids) ||
    current.connection_ids.length !== 0 ||
    !Array.isArray(current.permissions)
  )
    return false;
  if (
    expected.role !== "dispatcher" ||
    !sameValues(expected.permissions, DEMO_DISPATCHER_PERMISSIONS)
  )
    return false;
  return sameMembership(current, {
    ...expected,
    permissions: DEMO_DISPATCHER_PERMISSIONS.filter(
      (permission) => permission !== "recover_commands",
    ),
  });
}
