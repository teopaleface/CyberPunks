import { useEffect } from "react"
import { MotionConfig } from "motion/react"
import { BrowserRouter, Link, Outlet, Route, Routes, useLocation } from "react-router-dom"
import { SiteNav } from "@/components/site-nav"
import { AuthProvider } from "@/lib/auth"
import { AgentPage, BilantPage, DiagnosticPage, PlanPage } from "@/pages/features"
import Landing from "@/pages/landing"
import SignInPage from "@/pages/sign-in"

const TITLES: Record<string, string> = {
  "/": "Daybreak, where crews go tomorrow",
  "/plan": "Tomorrow's plan, Daybreak",
  "/bilant": "Transformer energy balance, Daybreak",
  "/diagnostic": "Where the energy goes, Daybreak",
  "/agent": "The agent, Daybreak",
  "/intra": "Sign in, Daybreak",
}

/** Shared navigation with native page scrolling. */
function SiteLayout() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
    document.title = TITLES[pathname] ?? (pathname.startsWith("/app") ? "Console, Daybreak" : "Daybreak")
  }, [pathname])

  return (
    <>
      <SiteNav />
      <Outlet />
    </>
  )
}

/** Pleacă din site-ul static spre consola Daybreak (o încărcare completă, servită de Next). */
function ToConsole() {
  const { pathname, search } = useLocation()
  useEffect(() => {
    window.location.replace(pathname + search)
  }, [pathname, search])
  return (
    <main className="container-page flex min-h-[100svh] flex-col justify-center">
      <p className="text-lg text-white/85">Opening the console…</p>
    </main>
  )
}

function NotFound() {
  return (
    <main className="container-page flex min-h-[100svh] flex-col justify-center">
      <h1 className="h-page">Page not found</h1>
      <p className="mt-6 max-w-[48ch] text-lg text-white/85">This link is incorrect or the page has moved.</p>
      <Link to="/" className="mt-8 self-start text-white underline underline-offset-4 hover:text-ember-soft">
        Back to home
      </Link>
    </main>
  )
}

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<SiteLayout />}>
              <Route index element={<Landing />} />
              <Route path="bilant" element={<BilantPage />} />
              <Route path="diagnostic" element={<DiagnosticPage />} />
              <Route path="plan" element={<PlanPage />} />
              <Route path="agent" element={<AgentPage />} />
              <Route path="intra" element={<SignInPage />} />
              {/* The operational console is served by Next, with a full page load. */}
              <Route path="app/*" element={<ToConsole />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </MotionConfig>
  )
}
