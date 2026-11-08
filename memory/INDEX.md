# Memoria proiectului CyberPunks

Tot ce știm despre hackathon, PPC și proiect. Se citește la începutul fiecărei sesiuni și se actualizează când apare ceva nou.

| Fișier | Ce e în el |
|---|---|
| `01-smarthack-2026.md` | Regulament, premii, parteneri, calendar, reguli de predare și prezentare |
| `02-ppc-firma.md` | Raportul complet despre PPC Group: istoric, acționari, cifre, planul 2026-2030, România, cariere, peste 40 de surse |
| `03-ppc-tehnologie-si-digital.md` | Echipele IT, stack-ul (SAP, Salesforce, Claude Enterprise), contoare, AI, tarife dinamice, probleme declarate de PPC |
| `04-surse-de-date.md` | API-uri publice (Transelectrica, Open-Meteo, ENTSO-E) și seturi de date pentru antrenat modele (SGCC, Londra, EAGLE-I, PVGIS) |
| `05-unghiuri-pentru-idei.md` | Direcțiile de proiect după temă, comparate pe grila PPC, cu recomandarea |
| `06-intrebari-deschise.md` | Ce s-a aflat, ce e de decis și ce mai e de întrebat |
| `07-tema-ppc.md` | **Tema PPC** (slideuri plus PDF-ul oficial): cerințe obligatorii, ce înseamnă proiect complet, grila de 100 de puncte, termene, checklist |
| `08-ppc-workshop-ai.md` | Workshopul PPC: cifre, platforma de date a contoarelor, cele 9 proiecte AI ale lor, guvernanță și EU AI Act |
| `09-rsystems-workshop.md` | Workshopul R Systems: codul decide, modelul formulează; verificări în cod |
| `10-implementare.md` | **Implementarea**: A, B, C în paralel, cele 6 fire, orchestratorul, alegerile tehnice |
| `11-bilant-pe-post.md` | **Bilanț pe post** (fir nou) și **scara de soluții pentru tensiune** (C), decizia lui Teo de la 13:45 |
| `12-probleme-reale-ppc-2026.md` | Research primit de Teo (14:30), neverificat: probleme reale 2026 pe cele 4 companii, cifre pentru B, C, bilanț, A, prezentare |
| `13-stare-infrastructura.md` | Verificarea unei copii curate a ramurii integrate, demo și ce mai rămâne pentru predare |
| `14-date-furtuni-eden.md` | Datele românești descărcate local pentru testarea modelului de furtuni |
| `15-date-experimente-eden.md` | Datele A, B și C de pe Eden: ce este în Git, reproducere, rezultate și limite |
| `17-date-noi-si-optuna-eden.md` | Experimentele lui Eden din noaptea de 7-8 nov.: date noi, variabile meteo noi, Optuna pentru A, B, C |
| `18-bilant-feederbw-optuna-eden.md` | Bilanț: profile reale FeederBW, limitele etichetelor sintetice și Optuna pentru LightGBM |
| `13-design-console.md` | Audit UI/UX cerut de Teo: consola aliniată cu landingul, lizibilitate, navigare și limitele verificării |
| `14-agent-conversational.md` | Planul cu 80 de cazuri și implementarea locală: trei conturi, modele locale, Codex, voce reală și WhatsApp text verificat; nota vocală Meta încă neverificată |
| `10-raspunsuri-mentor.md` | Răspunsurile mentorului PPC: contoare la 5 minute, echipele așteaptă sfârșitul săptămânii dacă nu e urgent |
| `13-regresie-logistica-vs-lightgbm.md` | Regresia logistică în loc de LightGBM nu ajută: cifre, metrica de decizie, ce spunem la prezentare |
| `journal.md` | Ce s-a întâmplat și ce s-a decis, cu ora |

## Reguli

- Orice decizie (temă, idee aleasă, stack, împărțirea pe oameni) intră în `journal.md`, cu ora.
- Materialele originale (prezentări, poze) stau în `materiale/`, care nu intră în git.
- Fără parole, tokenuri sau chei în memorie. Cheile stau în `.env`, care nu intră în git.
- Datele sintetice se etichetează clar ca sintetice, în cod și în prezentare.

## Pe scurt

- Hackathon: SmartHack 2026 (ASMI), 7-8 nov. 2026, Politehnica Business Tower, București. 24 de ore, echipe de 3-5.
- Partener: PPC Group, compania greacă de energie care a cumpărat Enel România în 2023. În România: distribuție (Rețele Electrice, 3,2 mil. puncte de consum), furnizare (PPC Energie, cotă 14%), regenerabile (1,56 GW), încărcare mașini electrice (PPC blue). Au cumpărat Flanco pe 3 nov. 2026.
- Premii PPC: 1.500 € (marele premiu), 1.000 € (locul 2). O echipă ia un singur premiu.
- Tema: un agent AI bazat pe un model ML antrenat de noi, care decide și acționează pe o problemă reală de energie (Perceive, Estimate, Decide, Act). Doar date publice sau sintetice.
- Jurizare PPC: 25 relevanță, 25 calitate ML, 25 agent, 10 robustețe, 10 explicabilitate, 5 demo și repo.
- Predare: repo GitHub **public**, cu commit-uri pe parcursul celor 24 de ore, până duminică, 8 nov., la 12:00. Demo live de la 13:00: 5 minute plus 2 minute de întrebări.
