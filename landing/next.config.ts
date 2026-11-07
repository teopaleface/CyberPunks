import type { NextConfig } from "next";

/**
 * Landing-ul Daybreak: o singură pagină, export static (`out/`), ca să meargă și de pe disc,
 * fără server, în sala de prezentare. După build, `scripts/relativize.ts` face căile relative.
 */
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  // fără insigna de dezvoltare în colț: apare în capturi
  devIndicators: false,
  experimental: {
    // CSS-ul intră în <style> în pagină: o cerere mai puțin și merge de pe disc
    inlineCss: true,
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
