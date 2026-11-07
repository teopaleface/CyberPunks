import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { api } from "@/lib/api"
import type { Profile, Team } from "@/lib/supabase"

export interface User {
  id: string
  email: string
}
interface Session {
  user: User
}

interface AuthState {
  /** true until the session has been read */
  loading: boolean
  session: Session | null
  user: User | null
  profile: Profile | null
  /** kept for the sign-in page; there are no email recovery links any more */
  recovering: boolean
  signIn: (email: string, password: string) => Promise<string | null>
  signUp: (email: string, password: string, fullName: string) => Promise<{ error: string | null; needsConfirmation: boolean }>
  signOut: () => Promise<void>
  sendReset: (email: string) => Promise<string | null>
  setNewPassword: (password: string) => Promise<string | null>
  saveProfile: (patch: { full_name?: string; team?: Team | null }) => Promise<string | null>
}

type Me = { user: User | null; profile: Profile | null }

const AuthContext = createContext<AuthState | null>(null)

/** Conturi în Cloudflare KV (prin /api/cont), active imediat, fără confirmare pe email. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)

  useEffect(() => {
    api<Me>("/cont").then(({ data }) => {
      setUser(data?.user ?? null)
      setProfile(data?.profile ?? null)
      setLoading(false)
    })
  }, [])

  const accept = (data?: Me) => {
    setUser(data?.user ?? null)
    setProfile(data?.profile ?? null)
  }

  const signIn = useCallback(async (email: string, password: string) => {
    const { data, error } = await api<Me>("/cont/intrare", { method: "POST", body: { email, password } })
    if (error) return error
    accept(data)
    return null
  }, [])

  const signUp = useCallback(async (email: string, password: string, full_name: string) => {
    const { data, error } = await api<Me>("/cont/inregistrare", { method: "POST", body: { email, password, full_name } })
    if (error) return { error, needsConfirmation: false }
    accept(data)
    return { error: null, needsConfirmation: false }
  }, [])

  const signOut = useCallback(async () => {
    await api("/cont/iesire", { method: "POST" })
    accept()
  }, [])

  const sendReset = useCallback(
    async () => "Resetarea pe email nu e disponibilă. Cere-i administratorului o parolă nouă sau fă-ți alt cont.",
    []
  )

  const setNewPassword = useCallback(async (password: string) => {
    const { error } = await api("/cont/parola", { method: "POST", body: { password } })
    return error ?? null
  }, [])

  const saveProfile = useCallback(async (patch: { full_name?: string; team?: Team | null }) => {
    const { data, error } = await api<{ profile: Profile }>("/cont", { method: "PATCH", body: patch })
    if (error) return error
    if (data) setProfile(data.profile)
    return null
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      loading,
      session: user ? { user } : null,
      user,
      profile,
      recovering: false,
      signIn,
      signUp,
      signOut,
      sendReset,
      setNewPassword,
      saveProfile,
    }),
    [loading, user, profile, signIn, signUp, signOut, sendReset, setNewPassword, saveProfile]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider")
  return ctx
}

/** The name to greet someone by: profile name, else the part of the email before @. */
export function displayName(user: User | null, profile: Profile | null) {
  return profile?.full_name?.trim() || user?.email?.split("@")[0] || "cont"
}
