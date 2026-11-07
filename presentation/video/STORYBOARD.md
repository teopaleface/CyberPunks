---
format: 1920x1080
duration: 30s
message: "Un scor de 0,87 nu e un plan. Tura de mâine face planul echipelor, îl verifică și întreabă un om când nu e sigură."
arc: Cârlig → Trei probleme, aceleași echipe → Consola → Agentul (Perceive, Estimate, Decide, Act) → Răsplata → Bilanțul → Tensiunea → Omul → Dovada → Logo
audience: juriul PPC la SmartHack XI 2026
music: originală, 120 BPM (o bătaie = 0,5 s = 15 cadre; o măsură = 2 s), -14 LUFS la export
reference: presentation/research/REFERINTA-trust.md (gramatica filmului Trust "Meme trading is instant")
---

Varianta 2 (după referința lui Teo, 14:30). Fond alb pur, text uriaș în cerneala produsului, obiecte 3D, consola reală, final pe cerneală. Culorile A, B, C apar doar în capturile din produs; în rest alb, cerneală și soarele din logo. Etichetele mici au cel puțin 28 px. Cadrele-cheie: `boards/kf/`.

## Frame 1 — Cârligul (0-3s)

- duration: 3s
- reads: "Un scor de 0,87" (0,0-1,4 s); "nu e" (1,5-1,9 s); "un plan." (2,0-2,9 s)
- sound: lovituri pe 0,0 / 0,5 / 1,5 / 2,0 (accent)
- src: compositions/k1-carlig.html

## Frame 2 — Trei probleme, aceleași echipe (3-6,5s)

- duration: 3.5s
- reads: "Contoare." (3,0) "Furtuni." (3,5) "Tensiune." (4,0) "Aceleași echipe." (4,5-5,9); "Imagini generate cu AI" (28 px)
- sound: lovituri pe fiecare cuvânt; accent pe 4,5; ridicare spre 6,5
- scene: obiectele 3D (contor, nor de furtună, panou solar, cască) intră rotindu-se din colțuri; la final zboară în consolă și devin markeri
- src: compositions/k2-semnale.html

## Frame 3 — Consola reală (6,5-8s)

- duration: 1.5s
- scene: consola reală (captură din http://localhost:3710/, planul pentru 8 iulie 2025, date sintetice pe hartă reală), ca un ecran pe alb; inele pe markeri; zoom în "Rulează agentul"
- sound: intră ritmul (kick pe fiecare bătaie)
- src: compositions/k3-consola.html

## Frame 4 — Agentul lucrează (8-11,5s)

- duration: 3.5s
- reads: "Rulează agentul" (8,0-9,2); "Perceive" (9,5) "Estimate" (10,0) "Decide" (10,5) "Act" (11,0)
- sound: apăsarea pe 9,0; motivul de 4 note pe 9,5 / 10 / 10,5 / 11
- src: compositions/k4-agent.html

## Frame 5 — Răsplata (11,5-14,5s)

- duration: 3s
- reads: cifrele zilei din consolă, harta cu traseele; "Un plan." (13,0) "9 echipe." (13,5); cifra din outputs/demo/plans/demo-vara/plan.json (summary.crews_used), scrisă de scripts/cifre_film.py
- src: compositions/k5-harta.html

## Frame 6 — Bilanțul (14,5-17,5s)

- duration: 3s
- reads: "Bilanțul confirmă." (14,5-17,3); etichete "ieșit din post", "facturat", "lipsă"; "date sintetice, ilustrativ"
- scene: cele două curbe se despart, lipsa se colorează cu soarele; ilustrativ până intră bilanțul calculat în consolă
- src: compositions/k6-lucrare.html

## Frame 7 — Tensiunea (17,5-20,5s)

- duration: 3s
- reads: "Cea mai ieftină soluție." (17,5-20,3); "1,10"; "Alte faze pentru 3 case" (18,75)
- scene: curba trece de 1,10 la prânz, apoi coboară sub limită după soluție (curba de după e ilustrativă; seria vine din fixture-ul sintetic al lui C)
- src: compositions/k7-tensiune.html

## Frame 8 — Omul decide (20,5-24s)

- duration: 3.5s
- reads: "Nu sunt sigur." (20,5-21,3); cardul real din consolă (21,3-21,7); "Aprobă" apăsat de deget (22,0); "Aprobat de dispecer" (22,3-23,4)
- sound: tobele scad la cardul "Nu sunt sigur"; accent pe apăsare (22,0); ridicare spre 24,0
- scene: pastila "Aprobat" crește și acoperă tot cadrul: trecerea spre finalul pe cerneală
- src: compositions/k8-om.html

## Frame 9 — Dovada și logoul (24-30s)

- duration: 6s
- reads: cifra (24,0-26,4), din reports/planner/agent_eval.json prin scripts/cifre_film.py (provizorie până la 21:30); logoul cu soarele care răsare (26,5); "CyberPunks · SmartHack XI 2026 · tema PPC" (27,1-30)
- sound: drop pe 24,0; lovitura finală pe 26,5; liniște de la 29,9
- src: compositions/k9-final.html
