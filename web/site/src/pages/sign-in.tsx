import { CheckCircle2, Loader2 } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { useEffect, useId, useState, type FormEvent, type ReactNode } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { GlassButton } from "@/components/ui/liquid-glass-button"
import { displayName, useAuth } from "@/lib/auth"
import { ROUTES } from "@/lib/site"
import { supabaseReady } from "@/lib/supabase"
import { accountErrorMessage } from "@/lib/account-errors"
import { cn } from "@/lib/utils"

type Mode = "intra" | "cont-nou" | "resetare"

const TITLES: Record<Mode | "parola-noua", string> = {
  intra: "Sign in",
  "cont-nou": "Create account",
  resetare: "Password help",
  "parola-noua": "New password",
}

function Field({
  label,
  type = "text",
  value,
  onChange,
  autoComplete,
  error,
  hint,
  disabled,
}: {
  label: string
  type?: string
  value: string
  onChange: (v: string) => void
  autoComplete?: string
  error?: string | null
  hint?: string
  disabled?: boolean
}) {
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="mb-2 block font-medium">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        autoComplete={autoComplete}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-err` : hint ? `${id}-hint` : undefined}
        className={cn(
          "h-12 w-full rounded-2xl bg-surface-2 px-4 text-white outline-none transition-[box-shadow] duration-150",
          "placeholder:text-white/40 focus-visible:ring-2 focus-visible:ring-ember disabled:opacity-60",
          error && "ring-2 ring-bad"
        )}
      />
      {error ? (
        <p id={`${id}-err`} className="mt-1.5 text-sm text-bad">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-sm text-white/65">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

function Notice({ tone, children }: { tone: "error" | "success"; children: ReactNode }) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "flex gap-3 rounded-2xl p-4",
        tone === "error" ? "bg-bad/15 text-white" : "bg-ok/12 text-white"
      )}
    >
      {tone === "success" && <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-ok" aria-hidden />}
      <div>{children}</div>
    </div>
  )
}

const emailOk = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim())

export default function SignInPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const mode: Mode = (["intra", "cont-nou", "resetare"] as Mode[]).includes(params.get("mod") as Mode)
    ? (params.get("mod") as Mode)
    : "intra"
  const view = auth.recovering ? "parola-noua" : mode

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState<string | null>(null)
  const [touched, setTouched] = useState(false)

  useEffect(() => {
    setError(null)
    setDone(null)
    setTouched(false)
  }, [view])

  const setMode = (m: Mode) => setParams(m === "intra" ? {} : { mod: m })

  const emailErr = touched && !emailOk(email) ? "Enter a valid email, such as name@example.com." : null
  const passErr = touched && password.length < 6 ? "Use at least 6 characters." : null
  const nameErr = touched && view === "cont-nou" && !name.trim() ? "Enter your name so the team can identify your approvals." : null

  async function submit(e: FormEvent) {
    e.preventDefault()
    setTouched(true)
    setError(null)
    if (view === "parola-noua") {
      if (password.length < 6) return
      setBusy(true)
      const err = await auth.setNewPassword(password)
      setBusy(false)
      if (err) setError(accountErrorMessage(err))
      else navigate(ROUTES.app)
      return
    }
    if (view === "resetare") return
    if (!emailOk(email)) return
    if (password.length < 6) return
    if (view === "cont-nou" && !name.trim()) return
    setBusy(true)
    if (view === "intra") {
      const err = await auth.signIn(email.trim(), password)
      setBusy(false)
      if (err) setError(accountErrorMessage(err))
      else navigate(ROUTES.app)
    } else if (view === "cont-nou") {
      const res = await auth.signUp(email.trim(), password, name.trim())
      setBusy(false)
      if (res.error) setError(accountErrorMessage(res.error))
      else if (res.needsConfirmation)
        setDone(`Check your email at ${email.trim()} for the account confirmation link.`)
      else navigate(ROUTES.app)
    }
  }

  // Already signed in: say who, offer the way in or out.
  if (auth.user && !auth.recovering) {
    return (
      <Shell title="You are signed in">
        <p className="text-white/90">
          Signed in as <span className="font-medium">{displayName(auth.user, auth.profile)}</span> ({auth.user.email}).
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <GlassButton size="lg" variant="signal" onClick={() => navigate(ROUTES.app)}>
            Open console
          </GlassButton>
          <button type="button" onClick={() => auth.signOut()} className="cursor-pointer text-white/80 underline-offset-4 hover:text-white hover:underline">
            Sign out
          </button>
        </div>
      </Shell>
    )
  }

  return (
    <Shell title={TITLES[view]}>
      {view !== "parola-noua" && view !== "resetare" && (
        <div role="group" aria-label="Account access" className="mb-8 inline-flex rounded-full bg-surface-2 p-1">
          {(["intra", "cont-nou"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              aria-pressed={view === m}
              onClick={() => setMode(m)}
              className={cn(
                "h-10 cursor-pointer rounded-full px-5 text-sm font-medium transition-colors duration-200",
                view === m ? "bg-white text-black" : "text-white/80 hover:text-white"
              )}
            >
              {m === "intra" ? "Sign in" : "Create account"}
            </button>
          ))}
        </div>
      )}

      {!supabaseReady && (
        <Notice tone="error">
          Accounts are unavailable on this server. You can still explore the demo without an account.
        </Notice>
      )}

      <AnimatePresence mode="wait" initial={false}>
        <motion.form
          key={view}
          noValidate
          onSubmit={submit}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 6 }}
          transition={{ duration: 0.2 }}
          className="mt-2 space-y-5"
        >
          {done ? (
            <Notice tone="success">{done}</Notice>
          ) : (
            <>
              {view === "resetare" && (
                <p className="text-white/85">Email password recovery is unavailable. Ask the administrator for help or create a new account.</p>
              )}
              {view === "cont-nou" && (
                <Field label="Name" value={name} onChange={setName} autoComplete="name" error={nameErr} disabled={busy} />
              )}
              {view !== "parola-noua" && view !== "resetare" && (
                <Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" error={emailErr} disabled={busy} />
              )}
              {view !== "resetare" && (
                <Field
                  label={view === "parola-noua" ? "New password" : "Password"}
                  type="password"
                  value={password}
                  onChange={setPassword}
                  autoComplete={view === "intra" ? "current-password" : "new-password"}
                  error={passErr}
                  hint={view !== "intra" ? "At least 6 characters." : undefined}
                  disabled={busy}
                />
              )}

              {error && <Notice tone="error">{error}</Notice>}

              <div className="flex flex-wrap items-center gap-x-6 gap-y-4 pt-2">
                {view !== "resetare" && <GlassButton type="submit" size="lg" variant="signal" disabled={busy || !supabaseReady} aria-busy={busy}>
                  {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
                  {view === "intra"
                    ? busy
                      ? "Signing in…"
                      : "Sign in"
                    : view === "cont-nou"
                      ? busy
                        ? "Creating account…"
                        : "Create account"
                      : busy
                        ? "Saving…"
                        : "Save password"}
                </GlassButton>}
                {view === "intra" && (
                  <button type="button" onClick={() => setMode("resetare")} className="cursor-pointer text-white/80 underline-offset-4 hover:text-white hover:underline">
                    Forgot password?
                  </button>
                )}
                {view === "resetare" && (
                  <button type="button" onClick={() => setMode("intra")} className="cursor-pointer text-white/80 underline-offset-4 hover:text-white hover:underline">
                    Back to sign in
                  </button>
                )}
              </div>
            </>
          )}
        </motion.form>
      </AnimatePresence>

      <p className="mt-12 text-white/70">
        The demo is public.{" "}
        <Link to={ROUTES.app} className="text-white underline underline-offset-4 hover:text-ember-soft">
          Continue without an account
        </Link>
        . Sign in to save your approvals and profile.
      </p>
    </Shell>
  )
}

function Shell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className="container-page flex min-h-[100svh] items-center py-[clamp(112px,14vh,150px)]">
      <div className="grid w-full items-center gap-12 lg:grid-cols-12">
        <div className="lg:col-span-6">
          <h1 className="text-[clamp(2.2rem,min(4.2vw,7.5vh),3.9rem)] leading-[1.02] font-semibold tracking-[-0.03em]">
            Save your decisions
          </h1>
          <p className="mt-6 max-w-[40ch] text-lg text-white/80">Use an account to keep your approvals and profile. You can explore the plan without signing in.</p>
        </div>
        <div className="lg:col-span-6">
          <div className="rounded-2xl bg-surface p-[clamp(24px,3vw,40px)]">
            <h2 className="mb-6 font-sans text-2xl font-semibold tracking-[-0.01em]">{title}</h2>
            {children}
          </div>
        </div>
      </div>
    </main>
  )
}
