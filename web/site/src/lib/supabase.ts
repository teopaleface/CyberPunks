/**
 * Conturile nu mai folosesc Supabase: stau în Cloudflare KV, prin /api/cont (consola Next, web/app/api).
 * Fișierul păstrează numele vechi ca să nu schimbăm importurile paginilor.
 */
export const supabaseReady = true

export type Team = "Dispecerat" | "Echipa de contoare" | "Echipa de control" | "Echipa de rețea" | "Birou"
export const TEAMS: Team[] = ["Dispecerat", "Echipa de contoare", "Echipa de control", "Echipa de rețea", "Birou"]

export interface Profile {
  id: string
  full_name: string | null
  team: Team | null
}
