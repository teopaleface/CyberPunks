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
    if (!res.ok) return { error: json.error ?? "Ceva n-a mers. Încearcă din nou." }
    return { data: json }
  } catch {
    return { error: "Nu ne-am putut conecta la server. Verifică internetul și încearcă din nou." }
  }
}
