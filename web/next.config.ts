import type { NextConfig } from "next";
import { initOpenNextCloudflareForDev } from "@opennextjs/cloudflare";

// local (next dev): legăturile Cloudflare din wrangler.jsonc (KV-ul conturilor) sunt simulate de wrangler
initOpenNextCloudflareForDev();

// Pe Cloudflare (OpenNext) randarea parțială a Cache Components blochează workerul: construirea pentru
// Cloudflare (CF_BUILD=1, vezi `bun run cf:build`) o oprește; paginile rămân dinamice și citesc la fiecare cerere.
const onCloudflare = process.env.CF_BUILD === "1";

const nextConfig: NextConfig = {
  distDir: process.env.DAYBREAK_NEXT_DIST ?? ".next",
  cacheComponents: !onCloudflare,
  // fără insigna de dezvoltare în colț: apare în capturi și în înregistrări
  devIndicators: false,
  partialPrefetching: !onCloudflare,
  // Site-ul de prezentare (web/site, construit în public/landing/) e prima pagină; consola începe la /app.
  async rewrites() {
    const landing = ["/", "/bilant", "/diagnostic", "/plan", "/agent", "/intra"];
    return { beforeFiles: landing.map((source) => ({ source, destination: "/site-html" })), afterFiles: [], fallback: [] };
  },
  // Legăturile site-ului spre aplicația lui (/app/...) duc la ecranele consolei.
  async redirects() {
    return [
      { source: "/app/coada/:id", destination: "/coada?caz=:id", permanent: false },
      { source: "/app/cont", destination: "/intra", permanent: false },
      ...["coada", "posturi", "lucrari", "alerte", "jurnal", "modele", "harta", "rulare"].flatMap((p) => [
        { source: `/app/${p}`, destination: `/${p}`, permanent: false },
        { source: `/app/${p}/:rest*`, destination: `/${p}/:rest*`, permanent: false },
      ]),
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
