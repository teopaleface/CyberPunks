# Încercări care nu au intrat în model

SIMULARE. Același test: ferestrele celor 300 de posturi ale hărții, cu defectele de contor ale firului A. Comanda: `uv run python -m cyberpunks.a_bilant.experiments`.

| Varianta | F1 macro | normal | contor_client | furt_inainte_contor | pierdere_tehnica | client_post_gresit | contor_bilant_setat |
|---|---|---|---|---|---|---|---|
| modelul actual (lotul train, clase echilibrate) | 0.703 | 0.912 | 0.384 | 0.670 | 0.505 | 0.758 | 0.988 |
| antrenat doar pe train2 (defecte ca la A) | 0.595 | 0.767 | 0.263 | 0.469 | 0.322 | 0.762 | 0.986 |
| antrenat pe train + train2 | 0.700 | 0.879 | 0.371 | 0.677 | 0.482 | 0.791 | 1.000 |
| clase echilibrate la radical | 0.704 | 0.920 | 0.402 | 0.669 | 0.501 | 0.748 | 0.985 |
| fără echilibrarea claselor | 0.705 | 0.925 | 0.412 | 0.656 | 0.504 | 0.748 | 0.988 |

Concluzii:
- Lotul `train2` (defecte trase pe tot anul) face din „contor de client” clasa dominantă la antrenare, altfel decât la test, unde defectele lui A au apărut doar în ultimele 60 de zile. Rezultatul e mai slab; nu l-am păstrat.
- Ponderile claselor mută puțin echilibrul dintre „contor de client” și „client la postul greșit”, fără câștig la F1 macro. Am păstrat clasele echilibrate.
- Alte încercări, documentate în `error_analysis.md`: comparația cu normalul fără istoric (doar GIS) și extinderea regulii de pereche, ambele fără câștig.
