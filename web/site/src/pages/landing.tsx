import { SectionSnap } from "@/components/section-snap"
import { Footer } from "@/sections/footer"
import { Global } from "@/sections/global"
import { Hero } from "@/sections/hero"
import { HowItWorks } from "@/sections/how-it-works"
import { Plan } from "@/sections/plan"
import { Screens } from "@/sections/screens"

export default function Landing() {
  return (
    <SectionSnap>
      <main>
        <Hero />
        <Plan />
        <HowItWorks />
        <Screens />
        <Global />
      </main>
      <Footer screen />
    </SectionSnap>
  )
}
