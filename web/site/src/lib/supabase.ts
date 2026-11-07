import { createClient } from "@supabase/supabase-js"

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined

/** True when the project keys are configured (.env.local). */
export const supabaseReady = Boolean(url && key)

export const supabase = createClient(url ?? "http://localhost", key ?? "missing-key", {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
})

export type Team = "Dispecerat" | "Echipa de contoare" | "Echipa de control" | "Echipa de rețea" | "Birou"
export const TEAMS: Team[] = ["Dispecerat", "Echipa de contoare", "Echipa de control", "Echipa de rețea", "Birou"]

export interface Profile {
  id: string
  full_name: string | null
  team: Team | null
}
