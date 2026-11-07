/** Funcții despre serii, fără cod de client: se pot chema și din paginile de server. */
import type { Series } from "@/lib/contracts";

/** Seria bilanțului pe post: „ieșit din post” (value) față de „suma clienților” (expected). */
export function isBilantSeries(series: Series): boolean {
  return series.points.some((p) => p.flag === "lipsa_peste_normal") || /ieșit din post|bilan/i.test(series.title_ro);
}
