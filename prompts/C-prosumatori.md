# Firul C: prosumatori, tensiune prea mare în posturile de transformare

Branch: `Teo-C-prosumatori`. Status: `status/Teo-C-prosumatori.md`.

## Ce deții

`src/cyberpunks/c_prosumatori/`, `tests/c/`, `reports/C/`, `docs/data/C.md`, `docs/research/C.md`, `data/samples/C/`, secțiunea C din `Makefile`, `status/Teo-C-prosumatori.md`.

## De ce contează pentru PPC

- ANRE: 359.378 de prosumatori racordați la 30 iunie 2026 (324.535 persoane fizice), circa 3.800 MW instalați, peste 101.000 cu baterii. La prânz tensiunea urcă cu până la 10% în rețeaua de joasă tensiune, iar invertoarele se opresc singure (Știrile PRO TV: zeci de mii de panouri deconectate automat la orele de vârf). Unele posturi sunt aglomerate, altele n-au niciun prosumator. Guvernul pregătește condiții mai stricte de racordare.
- Rețele Electrice a pomenit prosumatorii la platforma GIS nouă; Daniel Albu (PPC) a spus că rețeaua devine bidirecțională.
- Problema nu e în portofoliul AI al PPC. E partea cea mai originală a proiectului.

## Faza 0: cercetare (cel mult 45 de minute, subagenți în paralel), scrisă în `docs/research/C.md`

1. SimBench (`simbench` 1.6.3 și `pandapower` 3.5.6, deja instalate; date ODbL, cod BSD): rețelele de joasă tensiune disponibile (rural, semiurban, urban), profilele de consum și fotovoltaic la 15 minute pe un an, cum rulezi o serie de timp în pandapower și cât durează pe o rețea.
2. Profilul fotovoltaic românesc: PVGIS (https://re.jrc.ec.europa.eu/api/v5_2/seriescalc) sau Open-Meteo (radiație) pentru Ilfov; prognoza pentru scenariul `maine`.
3. Standardul de tensiune (EN 50160, ±10%) și ce poate face distribuitorul: priza transformatorului (fără sarcină, cere o întrerupere scurtă), setări Volt-VAR sau limitarea injecției la invertoare, campanii de măsurători. Cifre românești despre prosumatori pe distribuitori sau județe, dacă există.
4. Literatura despre modele surogat ML pentru circulația de puteri (repere de precizie și viteză).

## Ce construiești

- Populație sintetică de posturi: circa 300 de posturi în Ilfov și București (bbox în `config/area.yaml`), cu poziții pe posturi reale din OpenStreetMap (`power=transformer` sau `power=substation`, ODbL, cu atribuire). Fiecare post e legat de o rețea SimBench, cu număr de prosumatori și puteri realiste pentru România (de exemplu 3-10 kWp pe casă), unele cu baterii. Totul etichetat sintetic.
- Etichete din fizică: circulație de puteri pandapower pe ore (sau la 15 minute), care dă tensiunea maximă pe post și încărcarea transformatorului, în scenarii cu tot mai mulți prosumatori. Simularea grea se face o dată, offline, cu rezultatele în `data/processed/` (ignorat) și o mostră mică în `data/samples/C/`.
- Features: kW fotovoltaic pe kVA de transformator, numărul de prosumatori, radiația prognozată, temperatura, ora, zi lucrătoare sau weekend, consumul estimat, lungimea și impedanța rețelei (din topologie), cota de baterii.
- Baseline: regula kW/kVA sau o regresie liniară simplă pe radiație × putere instalată.
- Model: LightGBM, regresie cuantilă a tensiunii maxime (P10, P50, P90) plus clasificator calibrat pentru P(tensiune > 1,10 pu).
- Evaluare: test pe REȚELE NEVĂZUTE (topologii SimBench lăsate deoparte) și pe luni nevăzute. MAE pe tensiune, pinball loss, acoperirea intervalelor, PR-AUC și recall pe depășiri. Viteza: milisecunde față de circulația de puteri (măsurată). `uv run python -m cyberpunks.c_prosumatori.evaluate` scrie `reports/C/metrics.json` (contractul `ModelReport`) și figurile.
- Analiza erorilor (`reports/C/error_analysis.md`): rețele rurale lungi, zile parțial înnorate, posturi cu baterii, ce ai încercat.
- Robustețe: prognoză incertă (nori), date lipsă, intrări greșite (puteri negative, kVA zero), rețele noi: `abstain` cu motiv.
- Explicabilitate: SHAP ("410 kW de panouri pe un transformator de 250 kVA", "soare 890 W/m²", "duminică, consum mic").
- Acțiuni (`recommended_action`): `adjust_tap` (echipă `lv_grid`, `requires_planned_outage: true`), `measurement_campaign`, `notify_customers` (mesaj PPC Energy pentru prosumatorii de pe post: consum mutat la prânz, legat de oferta Ore Smart), `watchlist`.
- În plus, în modulul tău: un raport de investiții (posturile de modernizat, ordonate) în `reports/C/investitii.md` și o funcție pentru cererile noi de racordare (aprobat / aprobat cu limită de injecție / studiu), cu explicație.
- Valoare: kWh fotovoltaic pierduți prin oprirea invertoarelor × valoare, plus plângeri evitate (`config/economics.yaml`, cheia `voltage`).
- Ieșirea: `uv run python -m cyberpunks.c_prosumatori.predict --scenario <s> --date <d>` scrie `outputs/work_items/<s>/C.jsonl` și `outputs/series/<s>/<id>.json` (tensiunea pe ore, cu intervalul și limita de 1,10). Funcție importabilă: `cyberpunks.c_prosumatori.predict.run(scenario: str, date: str) -> pathlib.Path`.
- Notă: în noiembrie soarele e slab, deci la scenariul `maine` e corect să iasă puține lucrări C, iar agentul trebuie să spună de ce. Scenariul `demo-vara` (data o alege firul B până la 15:00) arată cazul de vârf.
- Model card: `reports/C/model_card.md`.

## Milestones (ora României)

- 14:30 M0: `docs/research/C.md`, prima rețea SimBench simulată, măsurat timpul, status completat.
- 17:30 M1: dataset de antrenare generat, baseline și primul model, `metrics.json` valid, `C.jsonl` valid pentru `demo-vara` și `maine`.
- 21:30 M2: modelul bate baseline-ul pe rețele nevăzute, cuantile, calibrare, SHAP.
- 03:00 M3: analiza erorilor, teste de robustețe în `tests/c/`, raportul de investiții, funcția pentru cereri de racordare.
- 08:00 M4: model card, comenzi reproductibile în `docs/data/C.md`, curățenie.
