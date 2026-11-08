import "server-only";
import path from "node:path";
import type { DataSourceMode } from "./types";

const MODES: readonly DataSourceMode[] = ["auto", "api", "demo", "fixtures"];

export interface DataConfig {
  /** Rădăcina repo-ului (contracts/, config/, outputs/, reports/). */
  repoRoot: string;
  /** Adresa API-ului planificatorului, fără `/` la final. */
  apiBase: string;
  dataSource: DataSourceMode;
  /** Valoarea DATA_SOURCE când nu e una cunoscută (atunci se folosește `auto`). */
  invalidDataSource?: string;
  defaultScenario: string;
}

/**
 * Citește configurarea din variabilele de mediu la fiecare apel (e ieftin), ca testele
 * și pagina de diagnostic să vadă mereu valorile curente.
 */
export function getConfig(): DataConfig {
  const rawMode = (process.env.DATA_SOURCE ?? "auto").trim().toLowerCase();
  const known = (MODES as readonly string[]).includes(rawMode);
  return {
    repoRoot: path.resolve(process.env.REPO_ROOT ?? path.resolve(process.cwd(), "..")),
    apiBase: (process.env.API_BASE ?? "http://127.0.0.1:8710/api").replace(/\/+$/, ""),
    dataSource: known ? (rawMode as DataSourceMode) : "auto",
    invalidDataSource: known ? undefined : rawMode,
    defaultScenario: process.env.DEFAULT_SCENARIO ?? "demo-vara",
  };
}

// Valorile de la pornirea serverului, pentru pagini și afișare.
export const REPO_ROOT = getConfig().repoRoot;
export const API_BASE = getConfig().apiBase;
export const DATA_SOURCE = getConfig().dataSource;
export const DEFAULT_SCENARIO = getConfig().defaultScenario;

export const TIMEOUTS = {
  /** GET-urile către API. */
  getMs: 1500,
  /** POST /review/{id} și POST /plan/approve: API-ul reface planul (~5 s). */
  reviewMs: 30_000,
  /** POST /run: agentul rulează cap-coadă. */
  runMs: 120_000,
  /** Verificarea GET /health. */
  probeMs: 1200,
  /** Cât ținem minte rezultatul verificării. */
  probeCacheMs: 5000,
} as const;

/** Nume de scenariu sau ID sigur de pus într-o cale de fișier (fără `/`, `..` etc.). */
export function isSafeSegment(value: string): boolean {
  return /^[A-Za-z0-9_.-]{1,128}$/.test(value) && value !== "." && value !== "..";
}
