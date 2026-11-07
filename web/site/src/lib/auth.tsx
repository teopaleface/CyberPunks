import type { Session, User } from "@supabase/supabase-js"
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { supabase, supabaseReady, type Profile, type Team } from "@/lib/supabase"

interface AuthState {
  /** true until the stored session has been read */
  loading: boolean
  session: Session | null
  user: User | null
  profile: Profile | null
  /** set when a password-recovery link was opened */
  recovering: boolean
  signIn: (email: string, password: string) => Promise<string | null>
  signUp: (email: string, password: string, fullName: string) => Promise<{ error: string | null; needsConfirmation: boolean }>
  signOut: () => Promise<void>
  sendReset: (email: string) => Promise<string | null>
  setNewPassword: (password: string) => Promise<string | null>
  saveProfile: (patch: { full_name?: string; team?: Team | null }) => Promise<string | null>
}

const AuthContext = createContext<AuthState | null>(null)

/** Supabase errors, said in Romanian with what to do next. */
function explain(message: string): string {
  const m = message.toLowerCase()
  if (m.includes("invalid login")) return "Emailul sau parola nu se potrivesc. Verifică-le și încearcă din nou."
  if (m.includes("email not confirmed")) return "Contul nu e confirmat încă. Deschide linkul din emailul de confirmare."
  if (m.includes("already registered") || m.includes("already been registered"))
    return "Există deja un cont cu acest email. Intră în cont sau resetează parola."
  if (m.includes("password should be")) return "Parola trebuie să aibă cel puțin 6 caractere."
  if (m.includes("rate limit") || m.includes("too many"))
    return "Prea multe încercări într-un timp scurt. Așteaptă un minut și încearcă din nou."
  if (m.includes("failed to fetch") || m.includes("network"))
    return "Nu ne-am putut conecta la server. Verifică internetul și încearcă din nou."
  return message
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [session, setSession] = useState<Session | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [recovering, setRecovering] = useState(false)

  useEffect(() => {
    if (!supabaseReady) {
      setLoading(false)
      return
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setLoading(false)
    })
    const { data } = supabase.auth.onAuthStateChange((event, s) => {
      setSession(s)
      if (event === "PASSWORD_RECOVERY") setRecovering(true)
    })
    return () => data.subscription.unsubscribe()
  }, [])

  const userId = session?.user.id
  useEffect(() => {
    if (!userId) {
      setProfile(null)
      return
    }
    let cancelled = false
    supabase
      .from("profiles")
      .select("id, full_name, team")
      .eq("id", userId)
      .maybeSingle()
      .then(({ data }) => {
        if (!cancelled) setProfile((data as Profile) ?? { id: userId, full_name: null, team: null })
      })
    return () => {
      cancelled = true
    }
  }, [userId])

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    return error ? explain(error.message) : null
  }, [])

  const signUp = useCallback(async (email: string, password: string, fullName: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName }, emailRedirectTo: `${window.location.origin}/app` },
    })
    if (error) return { error: explain(error.message), needsConfirmation: false }
    return { error: null, needsConfirmation: !data.session }
  }, [])

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
  }, [])

  const sendReset = useCallback(async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/intra`,
    })
    return error ? explain(error.message) : null
  }, [])

  const setNewPassword = useCallback(async (password: string) => {
    const { error } = await supabase.auth.updateUser({ password })
    if (!error) setRecovering(false)
    return error ? explain(error.message) : null
  }, [])

  const saveProfile = useCallback(
    async (patch: { full_name?: string; team?: Team | null }) => {
      if (!userId) return "Intră în cont ca să îți salvezi profilul."
      const { data, error } = await supabase
        .from("profiles")
        .upsert({ id: userId, ...patch, updated_at: new Date().toISOString() })
        .select("id, full_name, team")
        .single()
      if (error) return explain(error.message)
      setProfile(data as Profile)
      return null
    },
    [userId]
  )

  const value = useMemo<AuthState>(
    () => ({
      loading,
      session,
      user: session?.user ?? null,
      profile,
      recovering,
      signIn,
      signUp,
      signOut,
      sendReset,
      setNewPassword,
      saveProfile,
    }),
    [loading, session, profile, recovering, signIn, signUp, signOut, sendReset, setNewPassword, saveProfile]
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
