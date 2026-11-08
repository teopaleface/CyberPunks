/**
 * Construirea site-ului de prezentare pentru consola Next (web/): fișiere statice în web/public/landing/,
 * servite de consolă la /, /bilant, /diagnostic, /plan, /agent, /intra (vezi web/next.config.ts).
 * Fără pluginul Cloudflare: consola întreagă se publică într-un singur loc.
 */
import path from "node:path"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

export default defineConfig({
  base: "/landing/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "./src") },
  },
  build: {
    outDir: path.resolve(import.meta.dirname, "../public/landing"),
    emptyOutDir: true,
  },
})
