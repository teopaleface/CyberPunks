import { LogIn, UserRound } from "lucide-react"
import { motion } from "motion/react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { GlassLink } from "@/components/ui/liquid-glass-button"
import { LiquidNavbar } from "@/components/ui/liquid-glass-navbar"
import { ThemeToggle } from "@/components/theme-toggle"
import { displayName, useAuth } from "@/lib/auth"
import { useReduced } from "@/lib/motion"
import { NAV_ITEMS, ROUTES, SITE } from "@/lib/site"

/**
 * The account lives in the top-right corner, apart from the navbar:
 * "Sign in" when signed out, "My account" when signed in.
 * Hidden while the auth state loads, so the wrong buttons never flash.
 */
function AccountCorner() {
  const { user, profile, loading } = useAuth()
  const navigate = useNavigate()
  const go = (href: string) => (e: React.MouseEvent) => {
    e.preventDefault()
    navigate(href)
  }
  if (loading) return null
  return (
    <div className="flex items-center gap-2">
      {user ? (
        <GlassLink href={ROUTES.app} size="sm" variant="signal" title={`Signed in as ${displayName(user, profile)}`} onClick={go(ROUTES.app)}>
          <UserRound className="size-4" aria-hidden />
          <span className="inline">My account</span>

        </GlassLink>
      ) : (
        <>
          <GlassLink href={ROUTES.signIn} size="sm" variant="signal" onClick={go(ROUTES.signIn)}>
            <LogIn className="size-4" aria-hidden />
            <span className="inline">Sign in</span>

          </GlassLink>

        </>
      )}
    </div>
  )
}

export function SiteNav() {
  const reduce = useReduced()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const active = NAV_ITEMS.find((i) => pathname === i.href || pathname.startsWith(`${i.href}/`))?.id ?? null

  return (
    <>
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-2 sm:px-4"
      >
        <div className="pointer-events-auto">
          <LiquidNavbar
            items={NAV_ITEMS}
            activeId={active}
            onNavigate={(href) => navigate(href)}
            logo={
              <Link
                to={ROUTES.home}
                onClick={(e) => {
                  if (pathname === ROUTES.home) {
                    e.preventDefault()
                    window.scrollTo({ top: 0, behavior: "auto" })
                  }
                }}
                className="rounded-md font-display text-[13px] font-semibold tracking-[-0.02em] focus-visible:outline-offset-4 sm:text-[15px]"
                aria-label={`${SITE.name}, home`}
              >
                {SITE.name}
              </Link>
            }
          />
        </div>
      </motion.header>
      <motion.div
        initial={reduce ? false : { opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.05, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-[84px] right-4 z-50 flex items-center gap-2 min-[1280px]:top-[22px] lg:right-6"
      >
        <ThemeToggle />
        <AccountCorner />
      </motion.div>
    </>
  )
}
