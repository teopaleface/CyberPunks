import { Demo } from "@/components/demo";
import { Explain } from "@/components/explain";
import { Footer } from "@/components/footer";
import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { HumanLoop } from "@/components/human-loop";
import { Ladder } from "@/components/ladder";
import { Models } from "@/components/models";
import { Problem } from "@/components/problem";
import { Results } from "@/components/results";
import { SiteHeader } from "@/components/site-header";
import { Team } from "@/components/team";
import { loadAgentEval, loadCityMap, loadHeroMap, loadModelResults, loadStories } from "@/lib/data";

export default function Page() {
  const map = loadHeroMap();
  const city = loadCityMap();
  const models = loadModelResults();
  const agent = loadAgentEval();
  const stories = loadStories();
  return (
    <>
      <SiteHeader />
      <main id="content">
        <Hero map={map} />
        <Problem />
        <HowItWorks city={city} />
        <Models results={models} />
        <Ladder ladder={stories.ladder} />
        <HumanLoop human={stories.human} date={map.plan?.date ?? null} />
        <Explain explain={stories.explain} />
        <Results agent={agent} models={models} />
        <Demo />
        <Team />
      </main>
      <Footer />
    </>
  );
}
