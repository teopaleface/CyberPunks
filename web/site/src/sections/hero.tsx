import { motion } from "motion/react"
import { useSnap } from "@/components/section-snap"
import EnergyBeam from "@/components/ui/energy-beam"
import { EnergyBeamShader } from "@/components/ui/energy-beam-shader"
import { GlassLink } from "@/components/ui/liquid-glass-button"
import { useReduced } from "@/lib/motion"
import { SITE } from "@/lib/site"

const ease = [0.22, 1, 0.36, 1] as const

/**
 * The Unicorn Studio scene from the brief (project hRFfUymDGOHwtFe7evR2) now
 * renders an eclipse, not the beam in the reference frame, so the hero uses
 * a shader drawn to match that frame. Set to true to use the Unicorn scene.
 */
const USE_UNICORN_SCENE = false

export function Hero() {
  const snap = useSnap()
  const reduce = useReduced()

  const go = (id: string) => (e: React.MouseEvent) => {
    if (!snap) return
    e.preventDefault()
    snap.goTo(id)
  }

  const drop = (delay: number) => ({
    initial: { opacity: 0, y: reduce ? 0 : -16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay, ease },
  })

  return (
    <section id="top" data-snap className="relative h-[100svh] min-h-[760px] overflow-hidden bg-background sm:min-h-[600px]">
      <div className="absolute inset-0" aria-hidden>
        {USE_UNICORN_SCENE ? <EnergyBeam className="!h-full" /> : <EnergyBeamShader />}
      </div>

      {/* Fade to black, short and steep, so the next screen starts on pure black. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-[16vh] bg-[linear-gradient(to_bottom,transparent_0%,var(--bg-dark)_90%)]"
      />

      <div className="container-page relative z-10 flex h-full flex-col items-center justify-start pt-[max(172px,19vh)] text-center">
        <motion.h1
          {...drop(0.1)}
          className="max-w-[16ch] text-[clamp(2.6rem,min(7.2vw,12vh),6.6rem)] leading-[0.98] font-semibold"
        >
          Where crews go tomorrow
        </motion.h1>
        <motion.p {...drop(0.18)} className="mt-8 max-w-[56ch] text-[clamp(1rem,1.3vw,1.2rem)] text-foreground/90">
          {SITE.name} uses meter, weather and grid data to plan field work for Rețele Electrice.
          Every decision has a reason. Uncertain cases go to a dispatcher.
        </motion.p>
        {/* Two equal columns: the gap between the buttons is the page centre, where the beam runs. */}
        <motion.div
          {...drop(0.26)}
          data-beam-anchor
          className="mt-10 flex flex-col items-center gap-3 sm:grid sm:w-full sm:grid-cols-2 sm:gap-4"
        >
          <GlassLink href="#plan" size="lg" onClick={go("plan")} className="sm:justify-self-end">
            See tomorrow's plan
          </GlassLink>
          <GlassLink href="#cum" size="lg" variant="frost" onClick={go("cum")} className="sm:justify-self-start">
            How it works
          </GlassLink>
        </motion.div>
      </div>
    </section>
  )
}
