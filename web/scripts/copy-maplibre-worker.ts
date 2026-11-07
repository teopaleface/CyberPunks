/**
 * MapLibre 6 rulează dalele într-un worker (modul ES). Bundler-ul Next nu-i rezolvă calea, așa că îl
 * servim static din public/maplibre/ și îl indicăm cu maplibregl.setWorkerUrl. Rulează înainte de dev și build.
 */
import { copyFileSync, mkdirSync } from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dir, "..");
const src = path.join(root, "node_modules", "maplibre-gl", "dist", "maplibre-gl-worker.mjs");
const outDir = path.join(root, "public", "maplibre");
mkdirSync(outDir, { recursive: true });
copyFileSync(src, path.join(outDir, "maplibre-gl-worker.mjs"));
console.log("worker MapLibre copiat în public/maplibre/");
