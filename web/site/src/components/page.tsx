import type { ReactNode } from "react"
import { useNavigate } from "react-router-dom"
import { Reveal } from "@/components/reveal"
import { GlassLink } from "@/components/ui/liquid-glass-button"
import { Footer } from "@/sections/footer"

/** Reading page: title, one sentence under it, then the content and the footer. */
export function PageShell({ title, lead, children }: { title: string; lead: ReactNode; children: ReactNode }) {
  return (
    <>
      <main className="pt-[clamp(120px,18vh,180px)]">
        <header className="container-page">
          <Reveal>
            <h1 className="h-page max-w-[18ch]">{title}</h1>
          </Reveal>
          <Reveal delay={0.06}>
            <p className="mt-6 max-w-[60ch] text-lg text-white/90">{lead}</p>
          </Reveal>
        </header>
        {children}
      </main>
      <Footer />
    </>
  )
}

export function Block({ id, title, intro, children }: { id?: string; title: string; intro?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} className="container-page mt-[clamp(80px,14vh,160px)] scroll-mt-28">
      <Reveal>
        <h2 className="text-[clamp(1.6rem,2.6vw,2.4rem)] leading-tight font-semibold">{title}</h2>
      </Reveal>
      {intro && (
        <Reveal delay={0.05}>
          <p className="mt-4 max-w-[60ch] text-white/85">{intro}</p>
        </Reveal>
      )}
      <Reveal delay={0.1} className="mt-8">
        {children}
      </Reveal>
    </section>
  )
}

export function NextStep({ text, label, to }: { text: string; label: string; to: string }) {
  const navigate = useNavigate()
  return (
    <section className="container-page mt-[clamp(80px,14vh,160px)]">
      <Reveal className="flex flex-col gap-6 rounded-2xl bg-surface p-[clamp(24px,3vw,48px)] md:flex-row md:items-center md:justify-between">
        <p className="max-w-[40ch] font-display text-[clamp(1.3rem,2vw,1.8rem)] leading-snug font-semibold tracking-[-0.02em]">
          {text}
        </p>
        <GlassLink
          href={to}
          size="lg"
          onClick={(e) => {
            e.preventDefault()
            navigate(to)
          }}
        >
          {label}
        </GlassLink>
      </Reveal>
    </section>
  )
}
