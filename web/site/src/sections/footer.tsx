import { ArrowUp } from "lucide-react"
import { Link, useNavigate } from "react-router-dom"
import { Reveal } from "@/components/reveal"
import { HalftoneWordmark } from "@/components/ui/halftone-wordmark-footer"
import { GlassLink } from "@/components/ui/liquid-glass-button"
import { LiquidGlassLogoReveal } from "@/components/ui/liquid-glass-logo-reveal"
import { NAV_ITEMS, ROUTES, SITE } from "@/lib/site"

function FooterLinks() {
  return (
    <nav aria-label="Pages" className="flex flex-wrap gap-x-8 gap-y-3">
      {NAV_ITEMS.map((i) => (
        <Link key={i.id} to={i.href} className="text-white/85 transition-colors duration-150 hover:text-white">
          {i.label}
        </Link>
      ))}
      <Link to={ROUTES.app} className="text-white/85 transition-colors duration-150 hover:text-white">
        Console
      </Link>
    </nav>
  )
}

function BackToTop() {
  return (
    <button
      type="button"
      onClick={() => window.scrollTo({ top: 0, behavior: "auto" })}
      className="group inline-flex cursor-pointer items-center gap-2 text-white/85 transition-colors duration-150 hover:text-white"
    >
      Back to top
      <ArrowUp className="size-4 transition-transform duration-200 group-hover:-translate-y-0.5" aria-hidden />
    </button>
  )
}

/**
 * The close of every page. On the landing page (`screen`) it is the last
 * full screen: the mark, one action, the links, and the name in halftone.
 */
export function Footer({ screen = false }: { screen?: boolean }) {
  const navigate = useNavigate()
  const href = ROUTES.app

  if (!screen) {
    return (
      <footer className="mt-32 overflow-hidden bg-black">
        <div className="container-page flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-display text-2xl font-semibold tracking-[-0.02em]">{SITE.name}</p>
            <p className="mt-2 max-w-[44ch] text-white/80">
              {SITE.pitch} Team {SITE.team}, SmartHack 2026.
            </p>
          </div>
          <div className="flex flex-col gap-6 md:items-end">
            <FooterLinks />
            <BackToTop />
          </div>
        </div>
        <HalftoneWordmark word={SITE.name.toUpperCase()} className="mt-16" />
      </footer>
    )
  }

  return (
    <footer id="final" data-snap className="relative flex h-[100svh] min-h-[600px] flex-col justify-end overflow-hidden bg-black">
      <div className="container-page flex flex-1 items-center pt-[clamp(84px,11vh,120px)]">
        <div className="grid w-full items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <Reveal>
              <h2 className="h-section max-w-[18ch]">Explore the demo plan</h2>
            </Reveal>
            <Reveal delay={0.06}>
              <p className="mt-5 max-w-[48ch] text-white/90 lg:text-lg">
                Inspect the plan, routes, model results and audit log. The demo uses public weather and
                synthetic grid data. No account required.
              </p>
            </Reveal>
            <Reveal delay={0.12} className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-5">
              <GlassLink
                href={href}
                size="lg"
                variant="signal"
                onClick={(e) => {
                  e.preventDefault()
                  navigate(href)
                }}
              >
                Open demo
              </GlassLink>
              <FooterLinks />
            </Reveal>
          </div>
          <Reveal delay={0.08} className="hidden lg:col-span-5 lg:block">
            <LiquidGlassLogoReveal className="mx-auto w-full max-w-[min(340px,34vh)]" />
          </Reveal>
        </div>
      </div>
      <HalftoneWordmark word={SITE.name.toUpperCase()} className="mt-6" />
    </footer>
  )
}
