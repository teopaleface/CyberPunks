import { CheckCircle2, Loader2 } from "lucide-react"
import { useEffect, useId, useState, type FormEvent, type ReactNode } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { GlassButton } from "@/components/ui/liquid-glass-button"
import { displayName, useAuth } from "@/lib/auth"
import { proposalFromSearch, proposalWorkspacePath, signInModeParams } from "../../../lib/operations/proposal-link"
import { supabaseReady } from "@/lib/supabase"
import { accountErrorMessage } from "@/lib/account-errors"
import { cn } from "@/lib/utils"

type Mode = "intra" | "cont-nou" | "resetare"

const TITLES: Record<Mode | "parola-noua", string> = {
  intra: "Account access",
  "cont-nou": "Account access",
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
          "h-12 w-full rounded-2xl bg-surface-2 px-4 text-foreground outline-none transition-[box-shadow] duration-150",
          "placeholder:text-foreground/60 focus-visible:ring-2 focus-visible:ring-accent-ink disabled:opacity-60",
          error && "ring-2 ring-bad"
        )}
      />
      {error ? (
        <p id={`${id}-err`} className="mt-1.5 text-sm text-bad">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-sm text-foreground/65">
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
        tone === "error" ? "bg-bad/15 text-foreground" : "bg-ok/12 text-foreground"
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
  const [params, setParams] = useSearchParams()
  const openWorkspace = () => window.location.assign(new URL(proposalWorkspacePath(proposalFromSearch(params)), window.location.origin).href)
  const mode: Mode = (["intra", "cont-nou", "resetare"] as Mode[]).includes(params.get("mod") as Mode)
    ? (params.get("mod") as Mode)
    : "intra"
  const view = auth.recovering ? "parola-noua" : mode
  const localPreview = ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname)

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

  const setMode = (m: Mode) => setParams(signInModeParams(params, m))

  const emailErr = touched && !emailOk(email) ? "Enter a valid email, such as name@example.com." : null
  const passErr = touched && (view === "intra" ? !password.length : password.length < 6)
    ? (view === "intra" ? "Enter your password." : "Use at least 6 characters.") : null
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
      else openWorkspace()
      return
    }
    if (view === "resetare") return
    if (!emailOk(email)) return
    if (view === "intra" ? !password.length : password.length < 6) return
    if (view === "cont-nou" && !name.trim()) return
    setBusy(true)
    if (view === "intra") {
      const err = await auth.signIn(email.trim(), password)
      setBusy(false)
      if (err) setError(accountErrorMessage(err))
      else openWorkspace()
    } else if (view === "cont-nou") {
      const res = await auth.signUp(email.trim(), password, name.trim())
      setBusy(false)
      if (res.error) setError(accountErrorMessage(res.error))
      else if (res.needsConfirmation)
        setDone(`Check your email at ${email.trim()} for the account confirmation link.`)
      else openWorkspace()
    }
  }

  // Already signed in: say who, offer the way in or out.
  if (auth.user && !auth.recovering) {
    return (
      <Shell title="You are signed in">
        <p className="text-foreground/90">
          Signed in as <span className="font-medium">{displayName(auth.user, auth.profile)}</span> ({auth.user.email}).
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <GlassButton size="lg" variant="signal" onClick={() => openWorkspace()}>
            Open workspace
          </GlassButton>
          <button type="button" onClick={() => auth.signOut()} className="cursor-pointer text-foreground/80 underline-offset-4 hover:text-foreground hover:underline">
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
                view === m ? "bg-foreground text-background" : "text-foreground/80 hover:text-foreground"
              )}
            >
              {m === "intra" ? "Sign in" : "Create account"}
            </button>
          ))}
        </div>
      )}

      {localPreview && (
        <p className="mb-6 text-sm text-foreground/70">
          Account data in this preview is stored locally.{" "}
          <a href="https://daybreak.ghiseateodor245.workers.dev/intra" className="text-foreground underline underline-offset-4">Open live sign in</a>
        </p>
      )}

      {!supabaseReady && (
        <Notice tone="error">
          Accounts are unavailable on this server. You can still explore the demo without an account.
        </Notice>
      )}

      <form
        noValidate
        onSubmit={submit}
        className="mt-2 space-y-5"
      >
        {done ? (
          <Notice tone="success">{done}</Notice>
        ) : (
          <>
            {view === "resetare" && (
              <p className="text-foreground/85">Email password recovery is unavailable. Ask the administrator for help or create a new account.</p>
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
                hint={view === "intra" ? undefined : "At least 6 characters."}
                disabled={busy}
              />
            )}

            {view !== "parola-noua" && view !== "resetare" && (
              // Reserve the name row so shared fields and actions stay put when switching modes.
              <div className="min-h-[5.25rem]">
                {view === "cont-nou" && (
                  <Field label="Name" value={name} onChange={setName} autoComplete="name" error={nameErr} disabled={busy} />
                )}
              </div>
            )}

            {error && <Notice tone="error">{error}</Notice>}

            <div className="grid items-center justify-items-start gap-x-6 gap-y-4 pt-2 sm:flex sm:flex-wrap">
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
              <div className="min-h-7">
                {view === "intra" && (
                  <button type="button" onClick={() => setMode("resetare")} className="cursor-pointer text-foreground/80 underline-offset-4 hover:text-foreground hover:underline">
                    Forgot password?
                  </button>
                )}
                {view === "resetare" && (
                  <button type="button" onClick={() => setMode("intra")} className="cursor-pointer text-foreground/80 underline-offset-4 hover:text-foreground hover:underline">
                    Back to sign in
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </form>

      <p className="mt-12 text-foreground/70">
        The public site explains how Daybreak works.{" "}
        <Link to="/agent" className="text-foreground underline underline-offset-4 hover:text-accent-ink">
          Explore Daybreak
        </Link>
        . Sign in to open your workspace.
      </p>
    </Shell>
  )
}

function Shell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className="container-page flex min-h-[100svh] items-start py-[clamp(172px,18vh,200px)]">
      <div className="grid w-full items-start gap-12 lg:grid-cols-12">
        <div className="lg:col-span-6 lg:pt-44">
          <h1 className="text-[clamp(2.2rem,min(4.2vw,7.5vh),3.9rem)] leading-[1.02] font-semibold tracking-[-0.03em]">
            Your Daybreak workspace
          </h1>
          <p className="mt-6 max-w-[40ch] text-lg text-foreground/80">Sign in to track your cases or assigned work. Your verified account determines which connections and work you can access.</p>
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
