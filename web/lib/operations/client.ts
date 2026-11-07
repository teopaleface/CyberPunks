export class SessionExpired extends Error {}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    cache: "no-store",
    headers: { "content-type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (response.status === 401)
    throw new SessionExpired("Your session ended. Sign in again.");
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error ?? "The request could not complete.");
  return data as T;
}
