# Benchmark: putem bate LightGBM? (ramura Eden, 8 nov. 2026)

Cerut de Eden la 05:58. Lucrat pe ramura `Eden` (cererea inițială spunea `Teo`, dar Eden a precizat „totul pe
branch-ul meu, Eden”). Raportul complet: `reports/benchmark/RAPORT.md`; tabelele: `reports/benchmark/tabele.md`;
cifrele și predicțiile: `reports/benchmark/*.json` și `reports/benchmark/predictions/`.

## Răspunsul

**Nu.** Niciun candidat nu bate LightGBM. Modelele livrate rămân neschimbate (sumele SHA256 verificate).

| Problemă | Candidat | LightGBM → candidat | Diferența, IC 90% | Verdict |
|---|---|---|---|---|
| Bilanț, testul v2 (diagnostice SINTETICE) | CatBoost | F1 macro 0,7535 → 0,7575 | +0,0040 [−0,0032; +0,0129] | egalitate statistică |
| Bilanț, FeederBW (profile reale, diagnostice SINTETICE) | CatBoost | 0,7139 → 0,7048 | −0,0091 [−0,0315; +0,0037] | egalitate statistică |
| Contoare, SGCC (etichete REALE) | CatBoost | PR-AUC 0,3994 → 0,3947 | −0,0047 [−0,0170; +0,0080] | egalitate statistică |
| Contoare, LCL de bază (probleme INJECTATE) | CatBoost | PR-AUC subtil 0,4057 → 0,4174 | +0,0117 [−0,0335; +0,0488] | egalitate statistică |
| Contoare, LCL extins (probleme INJECTATE) | CatBoost | PR-AUC subtil 0,5175 → 0,4889 | −0,0285 [−0,0461; −0,0123] | CatBoost pierde |
| Furtuni, 2025 (date REALE) | XGBoost | PR-AUC 0,2777 → 0,2738 | −0,0039 [−0,0064; −0,0012] | XGBoost pierde (puțin) |
| Furtuni, state nevăzute | XGBoost | 0,2586 → 0,2550 | −0,0036 [−0,0076; +0,0002] | egalitate statistică |
| Furtuni + convecție (separat) | XGBoost | 0,2865 → 0,2845 | −0,0021 [−0,0047; +0,0005] | egalitate statistică |

- Furtul înainte de contor (bilanț) este ușor mai slab la CatBoost pe ambele teste (v2 0,7710 → 0,7641; FeederBW
  0,4686 → 0,4573). Câștigul mediu v2 vine din „contor de client”. Pe validare CatBoost a fost mai slab (0,7612 față
  de 0,7685), deci regula „alegem pe validare” păstra oricum LightGBM.
- Furtuni: la 8 echipe pe zi, clienții acoperiți sunt egali statistic (0,1671 față de 0,1654). Convecția ajută ambele
  modele (+0,009 la LightGBM, +0,011 la XGBoost), deci recomandarea „B cu convecție” rămâne, indiferent de algoritm.
- Avantajul candidaților este numai viteza: CatBoost prezice de 17–180 de ori mai repede, iar XGBoost se antrenează
  de ~4 ori mai repede la furtuni. Nu schimbă decizia, pentru că inferența LightGBM este deja sub o secundă.

## Cum s-a lucrat

- Referințele LightGBM au fost refăcute **exact** înainte de comparație (v2 0,75352, FeederBW 0,70858/0,71393,
  SGCC 0,3994, LCL 0,4057/0,5175, furtuni 0,2777/0,2586/0,2865), deci nu există diferențe de date sau pipeline.
- Aceleași ferestre, trăsături, etichete, teste, reguli după model (bilanț), calibrare (Venn-ABERS la contoare,
  izotonic pe OOF la furtuni) și constrângeri monotone (furtuni). Buget de căutare: 40 de încercări Optuna la bilanț
  pentru ambii, 0 la contoare pentru ambii, grilă de 24 de configurații la furtuni pentru ambii. Alegerea s-a făcut
  numai pe antrenare și validare.
- Bootstrap 90% pe grupuri: cartiere (bilanț v2), plecări reale (FeederBW), clienți (SGCC), gospodării (LCL),
  săptămâni (furtuni).
- Cod: `src/cyberpunks/benchmark/`; dependențe în grupul separat `bench` (CatBoost 1.2.10, XGBoost 3.4.1).
  Comenzi: `make bench-bilant`, `make bench-contoare`, `make bench-furtuni`, `make bench-test`.
- Predicțiile SGCC rămân locale (`data/processed/benchmark/`), pentru că SGCC nu are licență explicită de
  redistribuire. Celelalte predicții sunt în Git.

## Limite

- Bilanțul rămâne evaluat pe etichete sintetice; FeederBW are numai 8 plecări de test, iar intervalele sunt largi.
- Timpii sunt orientativi, din cauza rulărilor suprapuse pe același Mac.
- La furtuni, LightGBM folosește constrângerile monotone „advanced”, iar XGBoost metoda standard; constrângerea
  este aceeași.
- Fuziunea bilanț + contoare și modelul de tensiune C nu au fost comparate.
