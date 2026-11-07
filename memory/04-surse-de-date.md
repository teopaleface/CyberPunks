# Surse de date publice pentru demo

Starea "verificat" înseamnă că am apelat sursa pe 7 nov. 2026 și a răspuns.

## Transelectrica, sistemul energetic național în timp real (verificat)

- URL: https://www.transelectrica.ro/sen-filter
- Fără cheie. Merge cu un User-Agent de browser.
- Întoarce JSON: o listă de obiecte cu câte o cheie, de forma `[{"PROD":"7337"}, {"CONS":"4862"}, ...]`. Valorile sunt în MW, ca text.
- La 7 nov. 2026, 11:48:40: producție 7.337 MW, consum 4.862 MW, sold -2.475 MW (export), eolian 2.704, solar 1.783, gaze 1.521, cărbune 513, hidro 439, nuclear 275, biomasă 71.
- Câmpuri: `PROD` producție, `CONS` consum, `SOLD` schimb net (negativ = export), `CARB` cărbune, `GAZE` gaze, `APE` hidro, `NUCL` nuclear, `EOLIAN` eolian, `FOTO` fotovoltaic, `BMASA` biomasă, `IS` / `ISPOZ` (probabil stocare, de verificat), `row1_HARTASEN_DATA` ora citirii. Variantele cu sufixul `15` par medii pe 15 minute. Restul (`VULC`, `DOBR`, `VARN`, `KOZL1`, `KOZL2`, `MUKA`, `SAND`, `DJER`, `PANCEVO21`, `BEKE1` etc.) sunt fluxuri pe liniile de interconexiune cu țările vecine.
- Exemplu:

```bash
curl -s -A "Mozilla/5.0" https://www.transelectrica.ro/sen-filter
```

## Open-Meteo, vreme și radiație solară (verificat)

- URL: https://api.open-meteo.com/v1/forecast
- Fără cheie, gratuit pentru uz necomercial.
- Are radiație solară (`shortwave_radiation`), vânt la 100 m (`wind_speed_100m`), temperatură și altele, pe ore. Bun pentru prognoza producției eoliene și solare sau a consumului.
- Exemplu pentru București:

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=44.43&longitude=26.10&hourly=shortwave_radiation,wind_speed_100m&forecast_days=1"
```

## ENTSO-E Transparency Platform (parțial verificat)

- URL API: https://web-api.tp.entsoe.eu/api. Răspunde cu 401 fără token, deci serviciul e pornit.
- Tokenul e gratuit, dar se cere: cont pe transparency.entsoe.eu, apoi email la suport. Poate dura, deci nu e sigur pentru azi.
- Are prețurile pentru ziua următoare (PZU), consumul, producția pe tipuri și prognoze, pentru toată Europa. Codul zonei România e `10YRO-TEL------P` (din memorie, de verificat).

## OPCOM, bursa de energie din România (neverificat ca API)

- https://www.opcom.ro/ răspunde (redirect). Publică rezultatele PZU zilnic, descărcabile. N-am găsit un API documentat.

## Alte surse, nefolosite încă

- data.gov.ro: portalul de date deschise al statului.
- ANRE: comparatorul de oferte la energie și gaz, lista furnizorilor.
- Electricity Maps: intensitatea CO2 pe țară. Are nivel gratuit, cu cont.
- Seturi de imagini cu defecte pe linii electrice (izolatori), utile dacă tema e despre inspecții cu drone. De căutat dacă e nevoie.

## Ce nu avem

- Date reale de la contoarele PPC. Dacă tema cere așa ceva, PPC ar trebui să dea un set de date. Altfel generăm date sintetice la 15 minute și le etichetăm clar ca sintetice.
