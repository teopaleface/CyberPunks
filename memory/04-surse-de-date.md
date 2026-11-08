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

## Seturi de date pentru antrenat modele (adăugate după anunțarea temei)

Tema cere doar date publice sau sintetice, cu sursa citată.

- **Open-Meteo, istoric** (verificat): https://archive-api.open-meteo.com/v1/archive. Vreme orară din trecut, fără cheie, pentru orice coordonate. Exemplu: `?latitude=44.43&longitude=26.10&start_date=2025-01-01&end_date=2025-01-02&hourly=wind_speed_100m,shortwave_radiation`.
- **PVGIS (Comisia Europeană, JRC)** (verificat): https://re.jrc.ec.europa.eu/api/v5_2/seriescalc. Producție solară estimată pe ore pentru un panou, ani întregi, fără cheie.
- **SGCC, furt de energie** (repo verificat): https://github.com/henryRDlab/ElectricityTheftDetection. Fișierele `data.zip`, `data.z01`, `data.z02` (circa 52 MB, arhivă împărțită). 42.372 de clienți, consum zilnic ianuarie 2014-octombrie 2016, 3.615 marcați ca furt, circa 25% valori lipsă. Repo-ul nu are licență explicită. Copie pe Kaggle: https://www.kaggle.com/datasets/bensalem14/sgcc-dataset (de verificat licența). Descriere: https://arxiv.org/pdf/2002.06219
- **Low Carbon London, contoare inteligente** (pagină verificată, redirect): https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households. 5.567 de locuințe, consum la 30 de minute, 2011-2014 (cifre din memorie, de verificat la descărcare).
- **EAGLE-I, întreruperi de curent în SUA**: https://figshare.com/articles/dataset/The_Environment_for_Analysis_of_Geo-Located_Energy_Information_s_Recorded_Electricity_Outages_2014-2022/24237376. Clienți fără curent pe comitat, la 15 minute, 2014-2024.
- **ACN-Data, încărcare mașini electrice (Caltech)** (pagină verificată): https://ev.caltech.edu/dataset. Sesiuni de încărcare, cont gratuit pentru API.
- **Open Power System Data** (verificat): https://data.open-power-system-data.org/time_series/. Serii de timp europene (consum, eolian, solar, prețuri), descărcabile direct.
- **Energy-Charts (Fraunhofer ISE)** (verificat 7 nov.): API fără cheie. Prețuri pentru România: `https://api.energy-charts.info/price?bzn=RO&start=2026-04-27&end=2026-04-27` (în €/MWh, la 15 minute în 2026, orare în 2024). Producție pe tipuri în România (eolian, solar, baterii, nuclear, hidro, gaze) și consum: `https://api.energy-charts.info/public_power?country=ro&start=...&end=...`. Licența: "private and internal use only", interzis uz comercial. Pe 27 apr. 2026 arată 14 intervale negative (minim -1 €/MWh), solar maxim 2.310 MW, baterii 268 MW.
- **SimBench + pandapower** (verificat pe PyPI 7 nov.): `pip install simbench` (1.6.3, Python 3.11+, aduce pandapower 3.5.6). Rețele de referință de la joasă la foarte înaltă tensiune, cu profile reale (Germania) de consum, fotovoltaic și stocare, la 15 minute pe un an. Date sub licență ODbL, cod BSD. Docs: https://simbench.readthedocs.io/
- **ANRE, prosumatori**: 359.378 la 30 iunie 2026 (324.535 persoane fizice, 34.843 firme). Sursă: https://startupcafe.ro/romani-panouri-solare-cati-prosumatori-racordare-retelele-electrice-romania-105065 și https://tvrinfo.ro/revolutia-de-pe-acoperisuri-romania-are-peste-330-000-de-prosumatori-retelele-trebuie-sa-tina-pasul/ (332.684 la final de aprilie, 3.789 MW, peste 101.000 cu baterii). La 30 iunie 2026: 4.019 MW și 127.084 cu baterii (ANRE prin News.ro, verificat de firul C).
- **Prețuri negative în România, 2026 (presă)**: https://balkangreenenergynews.com/record-solar-output-in-romania-pushes-power-prices-into-negative-territory/ și https://www.economica.net/?p=935480
- **Ember, prețuri angro europene**: https://ember-energy.org/data/european-wholesale-electricity-price-data (pagina a refuzat accesul automat, neverificat).
- **UrbanEV, încărcare mașini electrice (Shenzhen)**: https://github.com/IntelligentSystemsLab/UrbanEV (CC0). 1.682 de stații, 24.798 de puncte, ocupare orară pe 275 de zone, sept. 2022-feb. 2023, cu vreme, prețuri (`s_price.csv`), ocupare (`occupancy.csv`), distanțe. Date complete pe Dryad: https://datadryad.org/dataset/doi:10.5061/dryad.np5hqc04z
- **NREL PVDAQ, sisteme fotovoltaice**: https://catalog-old.data.gov/dataset/photovoltaic-data-acquisition-pvdaq-public-datasets (CC BY). Producție și senzori meteo pentru multe sisteme.
- **Acoperiș fotovoltaic cu defecte de umbrire etichetate (Réunion)**: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9800176/ (Data in Brief, 2023, date pe Zenodo). Date de la invertor (AC, DC), radiație, temperaturi.
- **ENTSO-E pentru România**: prețuri PZU și producție pe tipuri. Exportul din site și API-ul cer cont; tokenul de API se cere prin email.

## Ce nu avem

- Date reale de la contoarele PPC. Dacă tema cere așa ceva, PPC ar trebui să dea un set de date. Altfel generăm date sintetice la 15 minute și le etichetăm clar ca sintetice.
