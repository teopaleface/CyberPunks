/** Cereri JSON către /api din consolă (același domeniu, cookie-ul de sesiune merge singur). */
export async function api<T>(path: string, init?: { method?: string; body?: unknown }): Promise<{ data?: T; error?: string }> {
  try {
    const res = await fetch(`/api${path}`, {
      method: init?.method ?? "GET",
      credentials: "same-origin",
      headers: init?.body !== undefined ? { "content-type": "application/json" } : undefined,
      body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
    })
    const json = (await res.json().catch(() => ({}))) as T & { error?: string }
    if (!res.ok) return { error: json.error ?? "Something went wrong. Try again." }
    return { data: json }
  } catch {
    return { error: "Could not connect to the server. Check your connection and try again." }
  }
}
