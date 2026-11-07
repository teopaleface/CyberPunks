import { Footer } from "@/components/footer";
import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { Problem } from "@/components/problem";
import { SiteHeader } from "@/components/site-header";
import { loadCityMap, loadHeroMap } from "@/lib/data";

export default function Page() {
  const map = loadHeroMap();
  const city = loadCityMap();
  return (
    <>
      <SiteHeader />
      <main id="content">
        <Hero map={map} />
        <Problem />
        <HowItWorks city={city} />
      </main>
      <Footer />
    </>
  );
}
