import { useEffect } from "react"
import { BrowserRouter, Link, Outlet, Route, Routes, useLocation } from "react-router-dom"
import { SiteNav } from "@/components/site-nav"
import { SmoothScroll } from "@/components/smooth-scroll"
import { ApprovalsProvider } from "@/lib/approvals"
import { AuthProvider } from "@/lib/auth"
import { AgentPage, BilantPage, DiagnosticPage, PlanPage } from "@/pages/features"
import Landing from "@/pages/landing"
import SignInPage from "@/pages/sign-in"

const TITLES: Record<string, string> = {
  "/": "Daybreak, unde merg mâine echipele",
  "/plan": "Planul de mâine, Daybreak",
  "/bilant": "Bilanțul pe post, Daybreak",
  "/diagnostic": "De ce lipsește energia, Daybreak",
  "/agent": "Agentul, Daybreak",
  "/intra": "Intră în cont, Daybreak",
}

/** Same navbar on every page; smooth wheel everywhere except the landing page, which moves screen by screen. */
function SiteLayout() {
  const { pathname } = useLocation()
  const landing = pathname === "/"

  useEffect(() => {
    window.scrollTo(0, 0)
    document.title = TITLES[pathname] ?? (pathname.startsWith("/app") ? "Aplicația, Daybreak" : "Daybreak")
  }, [pathname])

  return (
    <SmoothScroll enabled={!landing}>
      <SiteNav />
      <Outlet />
    </SmoothScroll>
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
      <p className="text-lg text-white/85">Se deschide aplicația…</p>
    </main>
  )
}

function NotFound() {
  return (
    <main className="container-page flex min-h-[100svh] flex-col justify-center">
      <h1 className="h-page">Pagina nu există</h1>
      <p className="mt-6 max-w-[48ch] text-lg text-white/85">Linkul e greșit sau pagina a fost mutată.</p>
      <Link to="/" className="mt-8 self-start text-white underline underline-offset-4 hover:text-ember-soft">
        Înapoi la prima pagină
      </Link>
    </main>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ApprovalsProvider>
          <Routes>
            <Route element={<SiteLayout />}>
              <Route index element={<Landing />} />
              <Route path="bilant" element={<BilantPage />} />
              <Route path="diagnostic" element={<DiagnosticPage />} />
              <Route path="plan" element={<PlanPage />} />
              <Route path="agent" element={<AgentPage />} />
              <Route path="intra" element={<SignInPage />} />
              {/* Aplicația e consola Daybreak (Next), nu o copie statică: orice link spre /app pleacă acolo. */}
              <Route path="app/*" element={<ToConsole />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </ApprovalsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
