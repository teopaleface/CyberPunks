import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { useAuth } from "@/lib/auth"
import { api } from "@/lib/api"

type Row = { post_id: string; decision: Verdict; crew_id: string | null }
type Status = "idle" | "loading" | "ready" | "error"
export type Verdict = "approved" | "deferred" | "rejected"

interface ApprovalsState {
  /** what a person decided for each case the agent sent to them */
  decisions: Map<string, Verdict>
  /** the crew a person assigned to each approved case */
  crews: Map<string, string>
  approved: Set<string>
  deferred: Set<string>
  rejected: Set<string>
  status: Status
  error: string | null
  /** id currently being saved ("*" for the whole list), for a busy state */
  saving: string | null
  /** true when decisions are stored in the account */
  persisted: boolean
  /** set a verdict; choosing the current one again clears it */
  decide: (postId: string, verdict: Verdict) => Promise<void>
  /** assign a crew to an approved case; the same crew again clears it */
  assign: (postId: string, crewId: string) => Promise<void>
  /** kept for the approve-only controls */
  toggle: (postId: string) => Promise<void>
  setAll: (postIds: string[]) => Promise<void>
  retry: () => void
}

const Ctx = createContext<ApprovalsState | null>(null)

/**
 * What a person decided on the cases the agent could not decide alone.
 * Signed in: stored per account in Cloudflare KV, through /api/aprobari.
 * Signed out: kept in memory for this visit only.
 */
export function ApprovalsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [decisions, setDecisions] = useState<Map<string, Verdict>>(new Map())
  const [crews, setCrews] = useState<Map<string, string>>(new Map())
  const [status, setStatus] = useState<Status>("idle")
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!user) {
      setDecisions(new Map())
      setCrews(new Map())
      setStatus("ready")
      setError(null)
      return
    }
    let cancelled = false
    setStatus("loading")
    api<{ rows: Row[] }>("/aprobari").then(({ data: d, error: e }) => {
        const data = d?.rows
        if (cancelled) return
        if (e) {
          setStatus("error")
          setError("Nu am putut încărca deciziile tale. Verifică conexiunea și încearcă din nou.")
          return
        }
        setDecisions(new Map((data ?? []).map((r) => [r.post_id as string, (r.decision as Verdict) ?? "approved"])))
        setCrews(new Map((data ?? []).filter((r) => r.crew_id).map((r) => [r.post_id as string, r.crew_id as string])))
        setStatus("ready")
        setError(null)
      })
    return () => {
      cancelled = true
    }
  }, [user, reloadKey])

  const decide = useCallback(
    async (postId: string, verdict: Verdict) => {
      const prev = decisions
      const next = new Map(decisions)
      const clear = decisions.get(postId) === verdict
      if (clear) next.delete(postId)
      else next.set(postId, verdict)
      setDecisions(next)
      if (clear || verdict !== "approved") {
        // a crew only belongs to an approved case
        setCrews((c) => {
          if (!c.has(postId)) return c
          const n = new Map(c)
          n.delete(postId)
          return n
        })
      }
      if (!user) return
      setSaving(postId)
      const { error: e } = await api("/aprobari", {
        method: "PUT",
        body: { post_id: postId, decision: clear ? null : verdict, crew_id: verdict === "approved" ? (crews.get(postId) ?? null) : null },
      })
      setSaving(null)
      if (e) {
        setDecisions(prev)
        setError("Decizia nu s-a salvat. Încearcă din nou.")
      } else setError(null)
    },
    [decisions, crews, user]
  )

  const assign = useCallback(
    async (postId: string, crewId: string) => {
      const prevC = crews
      const prevD = decisions
      const next = new Map(crews)
      const clear = crews.get(postId) === crewId
      if (clear) next.delete(postId)
      else next.set(postId, crewId)
      setCrews(next)
      if (decisions.get(postId) !== "approved") setDecisions(new Map(decisions).set(postId, "approved"))
      if (!user) return
      setSaving(postId)
      const { error: e } = await api("/aprobari", {
        method: "PUT",
        body: { post_id: postId, decision: "approved", crew_id: clear ? null : crewId },
      })
      setSaving(null)
      if (e) {
        setCrews(prevC)
        setDecisions(prevD)
        setError("Echipajul nu s-a salvat. Încearcă din nou.")
      } else setError(null)
    },
    [crews, decisions, user]
  )

  const toggle = useCallback((postId: string) => decide(postId, "approved"), [decide])

  const setAll = useCallback(
    async (ids: string[]) => {
      const prev = decisions
      const next = new Map<string, Verdict>(ids.map((id) => [id, "approved"]))
      setDecisions(next)
      if (!user) return
      setSaving("*")
      const { error: e } = await api("/aprobari", { method: "POST", body: { ids } })
      setSaving(null)
      if (e) {
        setDecisions(prev)
        setError("Lista nu s-a salvat. Încearcă din nou.")
      } else setError(null)
    },
    [decisions, user]
  )

  const value = useMemo<ApprovalsState>(() => {
    const approved = new Set<string>()
    const deferred = new Set<string>()
    const rejected = new Set<string>()
    decisions.forEach((v, k) => (v === "approved" ? approved : v === "deferred" ? deferred : rejected).add(k))
    return {
      decisions,
      crews,
      approved,
      deferred,
      rejected,
      status,
      error,
      saving,
      persisted: Boolean(user),
      decide,
      assign,
      toggle,
      setAll,
      retry: () => setReloadKey((k) => k + 1),
    }
  }, [decisions, crews, status, error, saving, user, decide, assign, toggle, setAll])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useApprovals() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error("useApprovals must be used inside ApprovalsProvider")
  return ctx
}
