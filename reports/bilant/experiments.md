# Încercări care nu au intrat în model

SIMULARE. Același test: ferestrele celor 300 de posturi ale hărții, cu defectele de contor ale firului A. Comanda: `uv run python -m cyberpunks.a_bilant.experiments`.

| Varianta | F1 macro | normal | contor_client | furt_inainte_contor | pierdere_tehnica | client_post_gresit | contor_bilant_setat |
|---|---|---|---|---|---|---|---|
| modelul actual (lotul train, clase echilibrate) | 0.714 | 0.912 | 0.398 | 0.695 | 0.522 | 0.772 | 0.988 |
| antrenat doar pe train2 (defecte ca la A) | 0.594 | 0.762 | 0.262 | 0.475 | 0.326 | 0.750 | 0.990 |
| antrenat pe train + train2 | 0.706 | 0.885 | 0.383 | 0.676 | 0.510 | 0.789 | 0.995 |
| clase echilibrate la radical | 0.716 | 0.920 | 0.412 | 0.691 | 0.524 | 0.758 | 0.990 |
| fără echilibrarea claselor | 0.714 | 0.924 | 0.425 | 0.681 | 0.526 | 0.740 | 0.986 |

Concluzii:
- Lotul `train2` (defecte trase pe tot anul) face din „contor de client” clasa dominantă la antrenare, altfel decât la test, unde defectele lui A au apărut doar în ultimele 60 de zile. Rezultatul e mai slab; nu l-am păstrat.
- Ponderile claselor mută puțin echilibrul dintre „contor de client” și „client la postul greșit”, fără câștig la F1 macro. Am păstrat clasele echilibrate.
- Alte încercări, documentate în `error_analysis.md`: comparația cu normalul fără istoric (doar GIS) și extinderea regulii de pereche, ambele fără câștig.
