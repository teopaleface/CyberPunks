import "server-only";

/**
 * Spune lui Next că urmează citiri la momentul cererii (fișiere, API, ora curentă).
 *
 * Next 16 cu Cache Components (activat în next.config.ts) oprește randarea dacă se citește
 * `Date.now()` sau se face I/O înainte de un semnal de „cerere reală”. Stratul de date îl dă
 * singur, prin `connection()`, așa că paginile nu trebuie să-l mai cheme. Paginile trebuie totuși
 * să pună componentele care citesc date într-un `<Suspense>` (sau să aibă `loading.tsx`).
 *
 * În testele bun (NODE_ENV=test) și în scripturile rulate în afara Next nu există cerere: sărim peste.
 */
export async function atRequestTime(): Promise<void> {
  if (process.env.NODE_ENV === "test") return;
  const [{ connection }, { unstable_rethrow }] = await Promise.all([
    import("next/server"),
    import("next/navigation"),
  ]);
  try {
    await connection();
  } catch (err) {
    // Erorile interne Next (prerandare întreruptă etc.) trebuie lăsate să treacă.
    unstable_rethrow(err);
    // Altfel suntem în afara unei cereri (script, "use cache"): citim oricum.
  }
}
