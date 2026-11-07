/**
 * Rulează înaintea testelor (bunfig.toml → [test].preload).
 *
 * - `server-only` aruncă o eroare când e importat în afara Next.js; în teste îl înlocuim cu un modul gol.
 * - REPO_ROOT arată spre rădăcina repo-ului (dacă nu e setat deja).
 * - API_BASE arată spre un port închis, ca testele să nu depindă de un API pornit pe 8710.
 */
import { mock } from "bun:test";
import path from "node:path";

mock.module("server-only", () => ({}));

process.env.REPO_ROOT ??= path.resolve(import.meta.dir, "..", "..");
process.env.API_BASE = "http://127.0.0.1:9/api";
process.env.DATA_SOURCE = "auto";
