/** Fixed same-origin destination. Keep proposal/selection/scenario through old links and sign-in. */
export function compatibilityAppPath(query: Record<string, string | string[] | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (key === "console") continue;
    if (typeof value === "string") params.set(key, value);
    else if (Array.isArray(value)) for (const item of value) params.append(key, item);
  }
  return params.size ? `/app?${params}` : "/app";
}
