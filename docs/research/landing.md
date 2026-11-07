# Landing-ul Daybreak: research vizual

> **Actualizare 17:55 (Teo):** pagina e acum **în engleză** și în **stilul paginilor de produs Apple** („mai wow, mai premium, mai minimalist”). Ce s-a schimbat față de direcția de mai jos: hero centrat (numele produsului, o frază mare, o propoziție, două acțiuni) cu harta înclinată ca un peisaj în zori și răsăritul PPC în spatele orizontului; fontul sistemului (SF Pro pe Mac, cu dimensiuni optice), cu Inter (OFL) pe celelalte sisteme, în locul lui Figtree; secțiuni cu o singură idee fiecare, text care se aprinde la derulare, povestea pe derulare în „How it works”, plăci (bento) pentru modele, cifra agentului ca la keynote, note de subsol pentru surse. Paleta PPC, culorile surselor A/B/C și regula „cifrele doar din reports/” rămân.

Firul Teo-landing, 7 nov. 2026, 17:16-17:40. Scopul: un landing premium, ușor de ținut minte, pentru juriul PPC și pentru repo, în paleta și designul PPC, inspirat din cele 10 site-uri date de Teo.

## Cum am studiat

- Capturi cu `agent-browser` în mod headless (doar vizualizare, fără conturi și fără formulare), la 1440×900, câte 5-8 poziții de derulare pe site, plus prima ecranare pe mobil (390×844). Din pagină am citit fonturile încărcate, culorile din variabilele CSS, bibliotecile de animație și structura titlurilor.
- Capturile stau local, în `/tmp/landing-research/` (nu intră în git: sunt site-urile altora).
- ppcgroup.com și reteleelectrice.ro blochează browserele automate (Imperva, „Error 15”). Paleta lor vine din verificarea firului Interfață pe CSS-ul site-urilor (`status/Teo-ui.md`, 12:50); designul PPC l-am studiat pe ppcenergy.ro, care s-a deschis.

## Ce iau din fiecare site

| Site | Ce am văzut | Ce iau și de ce | Ce nu iau |
|---|---|---|---|
| bencho.dev | Negru, hero centrat și compact, insignă care se rotește („10,232 members”, „107 signed up today”), plăci cu micro-interacțiuni vii; forme din puncte (hexagon în rețea de puncte), selector de oră cu riglă, „Hold to record”. Inter + Google Sans. | **Rețeaua de puncte** devine harta din hero: România desenată din puncte, ca luminile unui oraș noaptea. Rigla cu ore e modelul pentru ziua unei echipe (08:00-16:00). | Fundalul negru pur (noi avem bleumarinul PPC), insigna rotativă (zgomot fără informație). |
| beautifului.dev | Componente pentru interfețe cu agenți: „Approval Card” („Human-in-the-loop questions the agent asks before acting”), „Recommendation Card” cu nivel de încredere și Accept / Alternatives, „Thinking” cu pașii, „Task Rows”. Inter, gri închis, margini hașurate. | **Exact vocabularul de care avem nevoie**: cardul de aprobare pentru „Nu sunt sigur” (decide un om), cardul de recomandare cu încrederea modelului, pașii agentului ca rânduri cu stare. Le refacem în stilul nostru, pe datele reale ale planului. | Nu copiem cod (licență neclară, „Built by Turbo”); doar tiparul. |
| reactbits.dev | Fundaluri animate (unde, aurore), „Tech Text”, „Hold Button” („Hold to confirm”), terminal cu comanda de instalare, secțiuni ritmate „What's inside / See them in action / One command”. Geist, violet. | **Butonul ținut apăsat** pentru aprobarea listei de către om (interacțiune care răspunde unei acțiuni, nu decor). **Blocul de comandă** pentru reproducere („o comandă refăce cifrele”). Ritmul titlurilor scurte, câte o idee pe secțiune. | Violetul și fundalurile WebGL pe toată pagina: ar concura cu harta. |
| beui.dev | Titlu mare cu cuvinte evidențiate în „pastilă”, sponsori, grile de componente, „Number Animation” (48,273), „Swipeable List” (Priority queue), FAQ cu acordeon. Geist. | **Numerele care se numără** pentru cifrele modelelor (doar la apariție, o dată). **Lista de priorități** ca model pentru coada „Nu sunt sigur”. FAQ-ul, pentru întrebările juriului (`docs/QA-JURIU.md`). | Cuvintele evidențiate în titlu (tic de pagină generată). |
| sceneai.art | Bibliotecă de prompturi, grile dense de capturi, buton cu degradeu roz, Lenis pentru derulare. | Puțin: confirmă că o grilă de imagini mari obosește; noi ținem o singură imagine puternică (harta). | Derularea „netezită” (Lenis): pe proiector e greu de controlat. |
| amicro.vercel.app | „Small motion. Big difference.”, butoane cu micro-tranziții (morph, ring, glare), Outfit. | **Măsura**: mișcarea apare doar ca răspuns la o acțiune (copiere, aprobare). Butoanele noastre au doar apăsarea (scale 0,97) și culoarea. | Galeria de butoane. |
| ui.shadcn.com | Hero centrat, mozaic de componente reale (formulare, grafice, carduri de plată), Geist, gri neutru. | **Disciplina**: componente reale în loc de ilustrații. La noi, cardurile din pagină arată date reale din planul agentului, nu exemple inventate. | Mozaicul de carduri identice (tiparul „SaaS”). |
| koboyo.com/icons | 361.595 de iconițe desenate de mână (stiluri Original, Ink brush, Geometric), alb-negru. | Posibil pentru sursele A, B, C și bilanț (contor, furtună, panou solar, post): un desen de mână dă căldură unei pagini tehnice. Se descarcă direct (`/icons/svg/<nume>.svg`), fără cont. | Le folosim doar dacă arată bine pe bleumarin (inversate). |
| is-agentic.com | Negru, o singură coloană îngustă, scoruri pe rânduri („100 /100”) cu linii subțiri, apoi text lung despre metodă. Geist și Geist Mono. Foarte sobru. | **Rândurile de scor** pentru rezultate: model, metrica, cifra noastră față de metoda simplă, pe același rând, aliniate. **Textul despre metodă** într-o coloană îngustă, ușor de citit (setul de test, ce e sintetic, comanda de reproducere). | Monospace-ul pentru cifre (tic); folosim cifre tabulare din fontul nostru. |
| originkit.dev | Galerie de 805 componente cu previzualizări video, filtre pe categorii (Background 295, Text 91), fereastră promoțională la intrare. Inter. | Puțin: fără ferestre la intrare. Categoriile cu număr confirmă eticheta cu cifră (ex. „25 la un om”). | Fereastra modală, galeria. |
| ppcenergy.ro (designul PPC) | Fundal alb și gri deschis, carduri cu colțuri de 8-12 px, footer negru rotunjit, butoane cu raza de 8 px, albastrul `#163fe8` pe câmpuri active, font PingLCG (300-700), mult foto. | **Raza de 8 px** pe butoane, **albastrul `#163fe8`** pe butonul principal (alb pe albastru, contrast 7,2), titluri drepte, fără efecte. | Fotografiile de stoc, logoul, fontul PingLCG (proprietar). |

## Licențele componentelor (dacă copiem cod)

Până acum nu am copiat nicio componentă: hero-ul și harta sunt scrise de noi. Dacă preluăm cod, regula e:

| Sursă | Licența | Ce înseamnă pentru noi |
|---|---|---|
| React Bits (DavidHDev/react-bits) | MIT + Commons Clause (citit din fișierul LICENSE prin API-ul GitHub) | Se poate folosi într-un site sau o aplicație, păstrând nota de copyright; nu se pot revinde sau redistribui componentele ca atare. Un landing care le folosește e permis. |
| shadcn/ui (shadcn-ui/ui) | MIT | Liber, cu nota de copyright. |
| beUI (beui.dev) | MIT pentru componentele gratuite („MIT licensed for personal and commercial projects”, pe pagina lor); Pro e plătit | Doar componentele gratuite, cu nota MIT. |
| Amicro (Subhan-code/Amicro--Micro-transitions-) | MIT | Liber, cu nota de copyright. |
| Originkit (originkit.dev) | Nu am găsit o licență publică a componentelor | Nu copiem cod. |
| bencho.dev, beautifului.dev, sceneai.art | Produse comerciale, fără licență deschisă găsită | Doar inspirație, fără cod. |
| Koboyo Icons | Gratuite pentru uz personal și comercial, fără atribuire obligatorie; interzisă redistribuirea colecției (pagina koboyo.com/icons/license) | Câteva iconițe în pagină sunt permise. |

Orice componentă copiată primește un comentariu în fișier cu sursa, licența și data, iar tabelul de aici se actualizează.

## Fontul

PingLCG (PPC) e proprietar. Am comparat 12 fonturi libere, randate pe același text românesc (`/tmp/landing-research/fonts/compare.png`): Figtree, Plus Jakarta Sans, Onest, DM Sans, Albert Sans, Manrope, Instrument Sans, Archivo, Geologica, Golos Text, Red Hat Display, Schibsted Grotesk. Cel mai apropiat de PingLCG (geometric, rotund, „a” cu două niveluri, „g” cu un nivel, x-height mare): **Figtree** (OFL), cu Onest pe locul doi.

Verificat în fișierele woff2 de la Google Fonts (fontTools): ș, ț, Ș, Ț cu virgulă dedesubt (U+0219, U+021B, U+0218, U+021A) în subsetul latin-ext; ă, â, î în latin; cifre tabulare (`tnum`); axa de greutate 300-900. Consola folosește Archivo; landing-ul e mai aproape de PPC, iar culorile surselor rămân aceleași, ca să se vadă că e același produs.

## Paleta și contrastul (WCAG, pe `#000f1e`)

| Rol | Culoare | Contrast |
|---|---|---|
| Fundal (bleumarin PPC) | `#000f1e` | |
| Text | `#eef3f8` | 17,3 |
| Text secundar | `#a9bccd` | 9,9 |
| Text terțiar | `#8197ac` | 6,4 |
| Albastru PPC (agentul, focus) | `#00a3e0` | 6,7 |
| Portocaliu PPC (decide un om, soarele) | `#fa4616` | 5,5 |
| Albastru PPC Energie (butonul principal, alb pe el) | `#163fe8` | 7,2 (alb pe albastru) |
| A contoare și bilanț (din consolă) | `#3b82f0` | 5,2 |
| B furtună (din consolă) | `#b84fc0` | 4,5 |
| C tensiune (din consolă) | `#c4880a` | 6,3 |

Culorile surselor sunt varianta pentru fundal închis din consolă (validate pentru daltonism de firul Interfață). Pe `#0a2238` (plăci), B coboară la 3,8: B apare doar pe puncte și semne, nu pe text mic.

## Direcția vizuală

- **Ideea**: culorile PPC formează un răsărit (noaptea bleumarin, albastrul, cianul, soarele portocaliu). Agentul lucrează seara, planul e gata în zori. Hero-ul se termină cu un arc de orizont în culorile PPC, cu soarele portocaliu la mijloc.
- **Lucrul care se ține minte**: harta României din puncte, cu zona Rețele Electrice aprinsă și lucrările reale ale zilei demo (8 iulie 2025) pe aceeași grilă: contoarele, furtuna și tensiunea în culorile consolei, traseele echipelor în alb, o lupă peste București și Ilfov, cercuri portocalii la cazurile trimise la un om. O singură secvență la încărcare (circa 4 secunde): Perceive, Estimate, Decide (cele mai multe lucrări se sting: merg la verificare de la distanță), Act (traseele se desenează).
- **Tipografie**: Figtree, o singură familie. Titluri scurte în engleză (cel mult 5 cuvinte, ca în film), mari, cu spațiere strânsă; textul în română, 18-21 px, rânduri sub 70 de caractere.
- **Liniștea din jur**: fără mozaic de carduri, fără degradeuri decorative, fără etichete cu majuscule deasupra titlurilor. Culoarea apare doar când înseamnă ceva (sursa, omul, agentul).
- **Mișcarea**: secvența din hero, cifrele care se numără o dată, butonul ținut apăsat pentru aprobare. Totul se oprește cu `prefers-reduced-motion`.

## Structura secțiunilor (propunere)

1. **Hero**: „Tomorrow’s crews, planned tonight.” Harta cu planul real, cei 4 pași.
2. **Problema** („Where do crews go first?”): cifre publice cu sursa și data (3,18 mil. de utilizatori RE, 385.791 de prosumatori, pierderi 8,66% în Muntenia, circa 85% din compensațiile automate).
3. **Agentul** („Perceive. Estimate. Decide. Act.”): ce citește, ce estimează, cum decide (praguri, cost, capacitate), ce face.
4. **Sursele** („Fallen poles. Stolen power. Too much sun.”): A contoare, bilanțul pe post, B furtună, C tensiune, fiecare cu modelul și acțiunea.
5. **Scara de soluții C** („Cheapest fix first.”): cele 6 trepte, cu un post real din planul demo (P90 înainte și după).
6. **Omul în buclă** („Not sure? It asks you.”): cardul de aprobare pe un caz real din coadă, butonul ținut apăsat.
7. **Explicabilitate** („Every decision has a reason.”): urmărirea unei decizii până la predicție, model, factori, regulă și prag.
8. **Rezultate** („Better than the simple way.”): rândurile de scor, cifrele doar din `reports/*/metrics.json` și `reports/planner/agent_eval.json`; ce lipsește rămâne „în lucru”.
9. **Demo** („See it run.”): consola (`make web-demo`, `/demo`), locul filmului de 30 s, comenzile.
10. **Echipa și repo**: CyberPunks, SmartHack XI 2026; subsolul cu „Nu este un produs oficial PPC”.
