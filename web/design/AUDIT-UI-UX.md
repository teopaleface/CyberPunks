# Audit UI/UX Daybreak

7 noiembrie 2026. Audit și modificări locale pe ramura Teo, la cererea lui Teo.

## Concluzie

Landingul integrat în `web/site` este reperul vizual. Consola avea altă paletă, o legătură incorectă între variabilele fonturilor și prea multe informații prezentate simultan. Am păstrat compoziția landingului și am adus identitatea lui în consolă.

## Ce am găsit și ce am schimbat

1. **Două identități vizuale.** Landingul are fundal negru, suprafețe neutre, Geist pentru corp și Unbounded pentru titluri. Consola avea bleumarin, butoane albastre și titluri fără aceeași personalitate. Acum ambele folosesc negru, alb și galben `#ffc502` pentru acțiuni. Sursele A/B/C și stările de siguranță păstrează culori distincte, însoțite de text.
2. **Fonturi legate incorect.** Variabilele Tailwind `--font-sans` și `--font-display` se refereau la ele însele. Acum folosesc variabile separate pentru fonturile încărcate. Browserul confirmă Geist în corp și Unbounded la titlul paginii. Cardurile și cifrele rămân în Geist.
3. **Primul ecran era aglomerat.** Șase cifre, opt filtre, hartă, echipe, cronologie, scor și acțiuni se concurau în trei coloane. Acum sunt trei cifre cu etichete complete, planul propus și următorul caz de decis. Harta, cronologia, celelalte cifre și toate filtrele sunt în secțiunea „Detalii despre plan”.
4. **Aprobarea planului se amesteca cu un caz individual.** Sunt acum două carduri separate, care explică ce aprobi. „Analizează și decide” deschide exact cazul afișat, cu scenariul păstrat. Butonul aprobării și cel al rulării folosesc aceleași acțiuni de server ca înainte.
5. **Navigare repetată și nume ambigue.** Am grupat meniul în Dispecerat, Rețeaua și Cum decide agentul. „Nu sunt sigur” devine „De verificat”. Pe telefon există patru destinații frecvente jos și toate ecranele în meniul de sus. Căutarea rămâne accesibilă și prin tastatură.
6. **Decizia era prea jos pe telefon.** La 390 × 844, cardul următorului caz apare înaintea planului și a cifrelor. Butonul „Analizează și decide” este vizibil pe primul ecran.
7. **Coada de verificare repeta cifrele și ascundea butoanele sub detalii.** Am scos rezumatul duplicat al categoriilor, am pus datele și graficul într-o secțiune care se deschide și am adus acțiunile lângă motiv. Coloana care afișa scorul predicției se numește acum „Scor model”, nu „Încredere”. Selecția rândului este neutră; punctul sursei își păstrează culoarea.
8. **Landingul avea încă butoane albastre de cont.** Contul, intrarea și acțiunea din subsol folosesc acum galben cu text negru. Hero-ul, efectele și compoziția paginii sunt păstrate.

## Verificări

- Build Next.js și build Vite reușite. Vite avertizează în continuare că pachetul JavaScript principal depășește 500 kB.
- TypeScript, ESLint pe componentele modificate și `git diff --check` pentru `web` trec.
- Cele 72 de teste existente ale interfeței trec. Testele cu exemple sunt teste unitare; verificarea vizuală folosește API-ul local existent, fără a declanșa rulări sau aprobări.
- Fonturile, culorile, cardurile principale și stările de navigare au fost verificate în Helium, prin CDP, cu capturi randate. Cele nouă pagini principale, detaliile unei lucrări A și B, un post și modul demo nu depășesc lățimea ecranului la 1440 și la 390 px. Căutarea după PT-1182 întoarce postul și lucrările lui, iar meniul mobil conține toate destinațiile.
- Galbenul `#ffc502` cu text negru are contrast 13,24:1. Reperul pentru text normal este 4,5:1 în [WCAG 2.2](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Aceasta este verificarea combinației de culori, nu o certificare de accesibilitate a întregii aplicații.

## Limite și lucruri rămase

- Nu am publicat schimbările. Nu am testat scrierea aprobărilor, rularea agentului, autentificarea sau trimiterea mesajelor.
- Landingul ascunde bara de derulare și ignoră intenționat preferința sistemului pentru reducerea animațiilor, conform setării existente de demo. Auditul le consemnează; nu am schimbat această alegere.
- Printarea și dispozitivele fizice nu au fost verificate.
- La început exista un conflict Git în `memory/journal.md` și modificări de conturi/API. Alt fir le-a integrat în timpul lucrului, în commitul `a1862c1`; acest task nu a rezolvat conflictul și nu a modificat logica de conturi/API. Nu s-a făcut push sau deploy pentru acest audit.
