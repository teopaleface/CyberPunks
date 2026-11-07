import { Balance } from "@/sections/balance"
import { Demo } from "@/sections/demo"
import { Footer } from "@/sections/footer"
import { Hero } from "@/sections/hero"
import { HowItWorks } from "@/sections/how-it-works"
import { Plan } from "@/sections/plan"

export default function Landing() {
  return (
    <>
      <main>
        <Hero />
        <Plan />
        <HowItWorks />
        <Balance />
        <Demo />
      </main>
      <Footer screen />
    </>
  )
}
