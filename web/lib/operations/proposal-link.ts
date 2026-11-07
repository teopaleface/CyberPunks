/** Legăturile de confirmare acceptă numai un identificator UUID, niciodată o destinație liberă. */
const PROPOSAL_ID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function parseProposalId(value: unknown): string | null {
  return typeof value === "string" &&
    value.length === 36 &&
    PROPOSAL_ID.test(value)
    ? value.toLowerCase()
    : null;
}
export function proposalWorkspacePath(value: unknown): string {
  const id = parseProposalId(value);
  return id ? `/workspace?proposal=${id}` : "/app";
}
export function proposalSignInPath(value: unknown): string {
  const id = parseProposalId(value);
  return id ? `/intra?proposal=${id}` : "/intra";
}
export function proposalFromSearch(params: URLSearchParams): string | null {
  const values = params.getAll("proposal");
  return values.length === 1 ? parseProposalId(values[0]) : null;
}
export function signInModeParams(
  params: URLSearchParams,
  mode: string,
): URLSearchParams {
  const next = new URLSearchParams();
  const proposal = proposalFromSearch(params);
  if (proposal) next.set("proposal", proposal);
  if (mode !== "intra") next.set("mod", mode);
  return next;
}
