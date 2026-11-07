import { Hero } from "@/components/hero";
import { SiteHeader } from "@/components/site-header";
import { loadHeroMap } from "@/lib/data";

export default function Page() {
  const map = loadHeroMap();
  return (
    <>
      <SiteHeader />
      <main id="continut">
        <Hero map={map} />
      </main>
    </>
  );
}
