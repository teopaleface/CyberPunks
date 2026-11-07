# Regresie logistică în loc de LightGBM? Nu ajută.

Testat pe 8 nov. 2026, 01:00-01:45, de Tudor (cu Claude), pe codul din `main` (commit `cfa4a8d`).
Scripturile și cifrele complete: `reports/lr_vs_lgbm/` (`compare_a.py`, `compare_bilant.py`, `results_*.json`).

## Concluzia

**Rămânem pe LightGBM.** Pe toate cele trei seturi testate, LightGBM e clar mai bun decât regresia logistică.
Diferența e sigură statistic, nu e noroc. Regresia logistică rămâne doar ca rând de comparație (baseline).

## Pentru prezentare (de spus pe scurt)

- „Am încercat și un model mai simplu, regresia logistică, pe aceleași date și același test. Pierde peste tot:
  la furturile reale (SGCC), din 100 de contoare vizitate, 49 au furt; cu LightGBM, 80.”
- „De ce? Semnalele de furt nu sunt linii drepte. Contează combinațiile: o scădere de consum e suspectă mai
  ales dacă vecinii nu scad. Arborii prind singuri combinațiile și pragurile; regresia logistică adună doar
  fiecare semnal cu o pondere fixă.”
- „La problemele greu de văzut (fără contoare oprite sau blocate), regresia logistică prinde de aproape 3 ori
  mai puțin (PR-AUC 0,15 față de 0,41).”
- „La bilanțul pe post, regresia logistică ar trimite jumătate din cazuri la dispecer (nu e sigură), LightGBM
  doar unul din opt.”
- Dacă întreabă de overfitting: „Am verificat. LightGBM ține minte antrenarea, dar pe test, pe date nevăzute,
  rămâne cel mai bun. Regresia logistică are problema opusă: e prea simplă (underfitting).”

## Cum am testat (ca să fie corect)

- Același lot de antrenare, același test nevăzut, aceleași features ca LightGBM. LightGBM reantrenat cu codul
  nostru a dat exact cifrele din repo (SGCC PR-AUC 0,399; Londra 0,678; bilanț macro F1 0,705).
- Regresiei logistice i-am dat cea mai bună șansă: valori lipsă completate cu mediana plus indicator, două
  variante de scalare (standard și pe cuantile), L2, ponderi pe clase. Puterea regularizării (C) am ales-o pe
  calibrare sau prin validare încrucișată pe posturi, **nu pe test**.

## Metrica după care am decis

- **Contoare: PR-AUC.** Problemele sunt rare (5-9% din contoare), iar PR-AUC arată cât de curat e tot
  clasamentul. Precision@K (K = 1% din contoare) am raportat-o și pe ea, dar la Londra e „plină”: primele 130
  sunt probleme evidente (zero, blocat), pe care le găsește orice model. De aceea am verificat separat și
  problemele subtile.
- **Bilanț: macro F1** (metrica noastră): fiecare dintre cele 6 cauze cântărește la fel, deci contează și
  cauzele rare.
- **Regula:** bootstrap pereche (1.000 de reeșantionări, pe gospodării sau pe posturi). Calculăm intervalul de
  încredere 95% pentru diferența „regresie logistică minus LightGBM”. Ar fi fost îmbunătățire doar dacă tot
  intervalul era peste zero.

## Cifrele

| Set | Metrica | LightGBM | Regresie logistică (cea mai bună) | Diferența (IC 95%) |
|---|---|---|---|---|
| SGCC, furt real | PR-AUC | **0,399** | 0,238 | −0,16 [−0,19; −0,13] |
| SGCC | precision@K | **0,80** | 0,49 | −0,31 [−0,44; −0,19] |
| Londra | PR-AUC | **0,678** | 0,475 | −0,20 [−0,24; −0,16] |
| Londra, doar probleme subtile | PR-AUC | **0,406** | 0,146 | −0,26 [−0,34; −0,19] |
| Bilanț, 6 cauze | macro F1 | **0,705** | 0,553 | −0,15 [−0,19; −0,12] |

Bilanț: regresia logistică se abține în 51% din cazuri, LightGBM în 12,5%.

## Singura excepție (de știut, dacă întreabă)

Londra, lei recuperați în primele K contoare: regresia logistică pe cuantile ia 111.097 lei, LightGBM 93.351 lei
(+18.900 lei, IC 95% [+7.100; +33.700]). Amândouă prind doar probleme reale în top, dar regresia logistică
urcă mai sus problemele evidente cu valoare mare. Nu schimbă decizia: niciun model nu e antrenat pe valoare, iar
agentul ordonează oricum după probabilitate × valoare.

## Ce am mai găsit

- **Overfitting LightGBM:** pe antrenare, PR-AUC 0,83 (SGCC) și 0,99 (Londra); la bilanț macro F1 = 1,00 pe
  antrenare. Bilanțul are 400 de arbori ficși, fără oprire timpurie (early stopping): merită adăugată. Pe test
  rămâne totuși cel mai bun.
- **Cifra de pe site e veche:** site-ul arată la bilanț macro F1 0,668, dar `main` dă 0,705. Trebuie regenerat
  `daybreak.json`.
- **Netestat:** B (furtună), care ar fi cerut ~4 GB de date, și C, care are deja un baseline liniar de ~4× mai slab.
