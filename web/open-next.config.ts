import { defineCloudflareConfig } from "@opennextjs/cloudflare";
import staticAssetsIncrementalCache from "@opennextjs/cloudflare/overrides/incremental-cache/static-assets-incremental-cache";

// Consola pe Cloudflare Workers (OpenNext). Cache doar de citit, din fișierele statice ale construirii:
// învelișurile pre-randate ale paginilor (Cache Components) vin de acolo, datele se citesc la fiecare cerere.
export default defineCloudflareConfig({
  incrementalCache: staticAssetsIncrementalCache,
  enableCacheInterception: true,
});
