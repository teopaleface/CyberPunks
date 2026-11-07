import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  // fără insigna de dezvoltare în colț: apare în capturi și în înregistrări
  devIndicators: false,
  partialPrefetching: true,
  // Site-ul de prezentare (web/site, construit în public/landing/) e prima pagină; consola începe la /app.
  async rewrites() {
    const landing = ["/", "/bilant", "/diagnostic", "/plan", "/agent", "/intra"];
    return { beforeFiles: landing.map((source) => ({ source, destination: "/landing/index.html" })), afterFiles: [], fallback: [] };
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
