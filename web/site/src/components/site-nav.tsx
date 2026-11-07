import { LogIn, UserPlus, UserRound } from "lucide-react"
import { motion } from "motion/react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { GlassLink } from "@/components/ui/liquid-glass-button"
import { LiquidNavbar } from "@/components/ui/liquid-glass-navbar"
import { displayName, useAuth } from "@/lib/auth"
import { NAV_ITEMS, ROUTES, SITE } from "@/lib/site"

/**
 * The account lives in the top-right corner, apart from the navbar:
 * "Intră în cont" and "Cont nou" when signed out, "Contul meu" when signed in.
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
        <GlassLink href={ROUTES.app} size="sm" variant="signal" title={`Conectat ca ${displayName(user, profile)}`} onClick={go(ROUTES.app)}>
          <UserRound className="size-4" aria-hidden />
          <span className="hidden min-[1400px]:inline">Contul meu</span>
          <span className="sr-only min-[1400px]:hidden">Contul meu</span>
        </GlassLink>
      ) : (
        <>
          <GlassLink href={ROUTES.signIn} size="sm" variant="signal" onClick={go(ROUTES.signIn)}>
            <LogIn className="size-4" aria-hidden />
            <span className="hidden min-[1400px]:inline">Intră în cont</span>
            <span className="sr-only min-[1400px]:hidden">Intră în cont</span>
          </GlassLink>
          <GlassLink href={`${ROUTES.signIn}?mod=cont-nou`} size="sm" variant="frost" onClick={go(`${ROUTES.signIn}?mod=cont-nou`)}>
            <UserPlus className="size-4" aria-hidden />
            <span className="hidden min-[1400px]:inline">Cont nou</span>
            <span className="sr-only min-[1400px]:hidden">Cont nou</span>
          </GlassLink>
        </>
      )}
    </div>
  )
}

export function SiteNav() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const active = NAV_ITEMS.find((i) => pathname === i.href || pathname.startsWith(`${i.href}/`))?.id ?? null

  return (
    <>
      <motion.header
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-4"
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
                    window.scrollTo({ top: 0, behavior: "smooth" })
                  }
                }}
                className="rounded-md font-display text-[15px] font-semibold tracking-[-0.02em] focus-visible:outline-offset-4"
                aria-label={`${SITE.name}, începutul primei pagini`}
              >
                {SITE.name}
              </Link>
            }
          />
        </div>
      </motion.header>
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.05, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-[84px] right-4 z-50 md:top-[22px] lg:right-6"
      >
        <AccountCorner />
      </motion.div>
    </>
  )
}
