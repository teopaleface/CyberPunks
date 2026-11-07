# Bilanț pe post și scara de soluții pentru tensiune

Decizia lui Teo, 7 nov. 2026, 13:45: două funcționalități noi. Conceptul original (PDF de la Teo) e în `materiale/Bilant_pe_post_concept.pdf` (local, nu intră în git).

## 1. Bilanț pe post (fir nou: `Teo-bilant`, modulul `src/cyberpunks/a_bilant/`)

Întrebarea: la ce posturi de transformare se pierd cei mai mulți bani, din ce cauză și pe cine trimitem acolo?

- Date de intrare: contorul de bilanț al postului (energia ieșită, la 15 minute), contoarele clienților de sub post (consum, producție, opțional tensiune), lista client → post, vremea, prețul energiei.
- Pasul 1, bilanțul: lipsa = energia ieșită din post − suma contoarelor clienților, în kWh, procente și lei, pe post și pe zi.
- Pasul 2, normalul: un model învață pierderea normală a fiecărui post (încărcare, lungimea cablurilor, vreme; la încărcare mare cablurile pierd mai mult). Lipsa mult peste normal sau crescută brusc înseamnă post suspect.
- Pasul 3, diagnosticul (tabelul din concept):
  - contor blocat, ceas decalat sau valori negative: contor defect, merge echipa de contoare;
  - lipsa apare brusc într-o zi și rămâne constantă, iar contoarele par normale: furt înainte de contor, merge echipa de control;
  - lipsa crește mult la încărcare și fazele sunt dezechilibrate: problemă tehnică (cablu, faze), merge echipa de rețea;
  - un contor seamănă cu clienții altui post: client trecut la postul greșit în bază, corecție în birou, fără deplasare;
  - contorul de bilanț arată exact de 2× mai mult: contorul de post setat greșit, merge echipa de contoare.
- Pasul 4, prioritizarea: valoare = probabilitatea să fie real × energia pierdută × preț. Exemplu: "Postul 1234: aproximativ 600 lei pe lună, 85% contor defect la clientul X."
- Pasul 5, agentul: întâi verificări ieftine de la distanță (recitirea contorului, jurnalul de evenimente), apoi lista zilnică pe echipe după lei pe oră de lucru; un om aprobă lista; după vizită, verdictul echipei devine etichetă nouă; toate deciziile intră în jurnal.
- Ce vede utilizatorul: harta posturilor (verde, galben, roșu după lei pierduți), pagina postului cu graficul "ieșit din post" față de "suma clienților" și lipsa colorată, lista echipelor cu buton de aprobare, contorul de lei recuperați.
- Demo fără date PPC: rețelele SimBench simulate (pierderile normale din calculul de rețea), casele din SimBench sau Londra, probleme ascunse de noi. Eticheta: simulare pe date publice, gândită pentru datele PPC.
- De confirmat cu PPC (întrebarea pentru mentor, o pune Teo): există contoare de bilanț în posturi și la ce procent (concentratorul de date din post nu e contor de bilanț)? E de încredere lista client → post? Planul B: dacă nu toate posturile au contor de bilanț, estimăm energia intrată din modelul rețelei și clasăm unde merită montat primul contor.
- De ce e mai bun decât detecția simplă de contoare ciudate: confirmare independentă (mai puține deplasări degeaba), problema în lei, prinde ce contoarele nu văd, atacă un cost real (energia pierdută peste ce recunoaște ANRE), e nou pentru PPC.
- Cifra principală pentru prezentare: precizia în primele K și deplasările degeaba, cu bilanț față de fără, pe același test.

## 2. Scara de soluții pentru C (în firul C și în planificator)

Când un post depășește 1,10 pu (253 V), agentul alege dintre soluții ordonate după cost și verifică efectul fiecăreia cu calculul de rețea al lui C:
1. Mută 3 case pe altă fază (o oră de lucru, cost mic). Dezechilibrul de faze găsit de bilanț e intrarea pentru varianta asta.
2. Coboară priza transformatorului pe sezonul de vară (cost mic).
3. Mesaje "consumă la prânz" pentru clienții Ore Smart de pe post (cost zero, efect incert; rata de participare din config, IPOTEZĂ).
4. Ofertă de baterii pentru prosumatorii de pe post (venit pentru PPC Energie; magazinele PPC și Flanco după preluare, anunțată pe 3 nov. 2026).
5. Limită de export pe oră (ultima variantă înainte de investiție).
6. Transformator nou (cost mare, doar dacă nimic nu ajunge; intră în raportul de investiții al lui C).

Regula: cea mai ieftină combinație care aduce P90 al tensiunii sub 1,10 pu; explicația spune și de ce nu s-a ales o variantă mai ieftină. C pune variantele în `extra.remedy_options` (contractul `RemedyOption`), planificatorul alege și jurnalizează (`R-REMEDY-LADDER`).

## Contracte schimbate (orchestrator, 14:00)

- `RecommendedAction`: `office_correction`, `grid_inspection`, `phase_rebalance`, `offer_battery`, `export_limit`, `transformer_upgrade`.
- Modele noi: `RemedyOption`, `BilantFusion`.
- Bilanțul scrie lucrări cu sursa A în `outputs/work_items/<s>/A_bilant.jsonl`; fuziunea cu A prin `cyberpunks.a_bilant.fuse.fuse`.
- Postul de transformare e unitatea comună: registrul posturilor îl deține C (`cyberpunks.c_prosumatori.posts.load_posts()`, `data/samples/C/posts.csv`).
- Detalii: `docs/CONTRACTS.md`, secțiunea "Extinderea din 7 nov., 14:00".

Regula echipei de la 21:30 rămâne: dacă A, B sau C nu bate metoda simplă la M2, efortul merge întâi acolo.

## Completări pentru scara C (Teo, 7 nov., 14:00)

- **Treapta 3, mesaje țintite pe post** (inspirat de Take Charge, CSIRO Solar Hackathon 2016): mesajul pleacă doar către clienții Ore Smart de pe posturile cu P90 peste 1,10 pu și doar pentru orele cu risc. Efectul se calculează cu simularea C, pentru o rată de participare din config (IPOTEZĂ, interval 10/20/30%): cât scade tensiunea și câte opriri ale invertoarelor se evită. Textul e de grup, pe post sau stradă, din șablon cu cifre verificate în cod, fără date personale ("Strada ta a evitat ieri 3 opriri ale panourilor solare. Mâine între 12 și 15, pornește mașina de spălat și boilerul."). Dacă la participarea minimă P90 nu coboară sub 1,10 pu, treapta se combină cu următoarea.
- **Treapta 4, baterie calculată pe profil** (inspirat de YellowGrid, locul 1 la CleanTech Hackathon 2025, eveniment susținut de PPC): pentru fiecare prosumator de pe un post cu risc, variante de 5, 10, 15 kWh: energia neinjectată la prânz, efectul pe tensiunea postului (simularea C, cu bateriile tuturor celor care acceptă), perioada de recuperare (prețuri și costuri în config, cu SURSĂ sau IPOTEZĂ). Oferta merge doar la cei la care bateria ajută postul. Rezultat: listă pentru PPC Energie, ordonată după efectul pe tensiune și după venit, plus textul ofertei. Canal: magazinele PPC și Flanco după preluare.
- Contract: `RemedyOption` are câmpuri opționale noi: `participation_rate`, `risk_hours`, `inverter_trips_avoided`, `message_preview_ro`, `customers_targeted`, `battery_kwh_total`, `revenue_lei`, `payback_years`.
- Respinse de Teo: prognoza pentru cumpărarea de energie a furnizorului (PPC o are în producție) și jocul Take Charge ca funcție separată (rămâne doar textul de grup).

## Contorul martor și datele reale pentru posturi (Teo a confirmat la 17:25)

- Răspunsul mentorului PPC: există un contor care verifică zone mai mari, numit "contor martor"; e normal să se piardă puțină energie, "poate 0,1%".
- Ce înseamnă corect: Codul de măsurare ANRE 2015 (Ordinul 103/2015, https://reteleelectrice.ro/wp-content/uploads/cod-masurare-2015.pdf) definește contorul martor ca "contor de energie electrică având rolul de a măsura energia electrică în paralel cu contorul de decontare", cu cel puțin aceeași clasă de exactitate, pe aceleași circuite. Deci 0,1% e precizia dintre două contoare pe același punct, nu pierderea din rețeaua de sub post.
- Baza legală a bilanțului (același cod): "Sistemele de măsurare inteligentă trebuie să permită integrarea a cel puţin un contor de balanţă la fiecare post de transformare, pentru a facilita identificarea pierderilor tehnice şi netehnice."
- Pierderile normale sub post: câteva procente, cresc cu încărcarea (CPT Muntenia 8,66% în 2023, 63,54% din CPT la JT).
- Schimbări în model: (1) regulă martor față de contorul postului, prag ~0,5% din clasa de exactitate, în config cu sursa: peste prag înseamnă contor defect sau setat greșit (cazul "2×"); (2) bilanțul post față de suma clienților rămâne pe pierderea normală învățată (câteva procente), nu pe 0,1%; (3) termenii folosiți: "contor martor", "contor de balanță".
- Date reale pentru curbe: Weave (Centre for AI and Climate), consum însumat pe post și fider, la 30 de minute, 4 distribuitori UK, ~100.000 de fideri, 2 mil. de contoare (https://github.com/centre-for-ai-and-climate/lv-feeder-smart-meter-data; fișierul complet ~700 MB). Licența nu e scrisă: folosit doar ca profile de încărcare, citat, nu ca etichete. Limită: în UK nu toți clienții au contor inteligent, deci nu dă un bilanț curat; etichetele rămân sintetice. Opțional: NGED "LV Load Monitor Data" (pe faze, câteva sute de posturi, cere cont), legătura cu Weave neverificată.
