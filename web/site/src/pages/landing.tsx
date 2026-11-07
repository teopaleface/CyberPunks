import { SectionSnap } from "@/components/section-snap"
import { Footer } from "@/sections/footer"
import { Hero } from "@/sections/hero"
import { HowItWorks } from "@/sections/how-it-works"
import { Plan } from "@/sections/plan"

export default function Landing() {
  return (
    <SectionSnap>
      <main>
        <Hero />
        <Plan />
        <HowItWorks />
      </main>
      <Footer screen />
    </SectionSnap>
  )
}
