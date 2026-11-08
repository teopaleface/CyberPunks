# Agent care decide și execută prin mai multe canale

## Cererea din 8 noiembrie 2026

Teo relatează că un mentor de business a considerat utilă ideea unui agent care ia decizii pentru utilizator. Acesta este feedback de produs transmis de Teo, nu o confirmare a regulamentului sau un acord al juriului.

Teo cere un plan pentru comportament agentic, folosind telefonul și WhatsApp în funcție de cont. Exemplele lui: tehnicianul întreabă ce traseu are, dispecerul întreabă ce sarcini are, iar mesajele pot primi rapoarte mai lizibile, generate ca HTML și transformate în imagine. Cererea curentă este planificarea, nu implementarea sau activarea unor servicii.

## Planul propus

[Planul pentru decizii și execuție](../docs/PLAN-AGENTIC.md) completează catalogul anterior de 80 de cazuri. Agentul coordonează funcții limitate ale aplicației, folosește predicțiile locale și regulile planificatorului, produce analiza întregii cozi și verifică efectul după operațiile confirmate. Propunerea păstrează confirmarea în aplicație pentru schimbări operaționale; confirmarea direct în WhatsApp, aprobarea în grup și simularea capacității au contracte noi și etape separate.

Prima versiune recomandată acoperă cele trei roluri în site și tehnicianul pe numărul WhatsApp deja asociat. Celelalte roluri pe telefon cer numere verificate sau o legare sigură din cont; nu se schimbă rolul prin conversație. Apelul WhatsApp singur nu este presupus că deschide fereastra de mesagerie. Rapoartele PNG sunt propuse, nu implementate sau trimise în această etapă.

Estimarea din plan este 4–7,5 ore pentru implementare și verificare, orientativă, fără aprobare externă și fără promisiune de finalizare. Prioritatea este analiza completă, o operație confirmată și traseul telefonic; imaginea se amână dacă ar consuma timpul verificării.

## Dovezi și limite

Planul se bazează pe codul local, documentele operaționale, tema oficială PPC și documentația Meta/ElevenLabs. Au fost verificate legăturile și coerența documentelor, fără retestarea serviciilor live, apeluri, mesaje, modificări de conturi sau deploy. Demonstrația vizuală din chat descrie comportamentul propus și nu este o interfață implementată. Datele istorice și identitățile sintetice își păstrează etichetele.

## Predare pentru brainstorming, 8 noiembrie 2026

Teo cere publicarea contextului și planului pe `main`, ca un alt coleg să poată propune mai multe idei. În firul principal a cerut și prompturi pentru implementare în paralel. La această predare, prompturile sunt cerute, nu confirmate ca finalizate; implementarea noului plan nu este dovedită.

### Punctul de plecare al colegului

- Citește acest document, [planul agentic](../docs/PLAN-AGENTIC.md), [starea implementării](14-agent-conversational.md) și [tema PPC](07-tema-ppc.md). Catalogul anterior este în [planul conversațional](../docs/PLAN-AGENT-CONVERSATIONAL.md).
- Propune mai multe sarcini pe care utilizatorul le poate delega cap-coadă, separat pentru dispecer, tehnician și client. Exemplele lui Teo sunt analiza a 25 de tichete, traseul cerut prin apel și raportul WhatsApp ca imagine. Acestea sunt puncte de plecare, nu o listă închisă.
- Pentru fiecare idee explică problema, cererea utilizatorului, datele și modelul folosit, ce decide agentul, ce execută, când cere confirmare și cum verifică rezultatul. Spune ce există deja și ce trebuie construit.
- Compară ideile după utilitate pentru PPC, dovada folosirii modelului ML propriu, efort, dependențe externe și claritatea unui demo de cinci minute. Recomandă o ordine de lucru; estimările sunt propuneri, nu rezultate măsurate.
- Explorează cum poate informația din teren să schimbe recomandarea, păstrând separat predicția inițială, decizia omului și motivul. LLM-ul nu inventează probabilități și nu înlocuiește modelul antrenat.
- Identifică sarcini independente care pot fi implementate în paralel și dependențele dintre ele. Brainstormingul nu autorizează activarea serviciilor, plăți, mesaje, schimbări de cont sau deploy.

Feedbackul de business susține direcția de produs. Încadrarea în tema PPC rămâne interpretarea echipei din documentul oficial, fără confirmare separată a mentorilor asupra regulamentului.
