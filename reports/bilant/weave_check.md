# Verificarea de realism: curbele posturilor simulate față de posturi reale (Weave, UK)

Sursa reală: Centre for AI and Climate, Weave, consumul contoarelor inteligente însumat pe post la 30 de minute, 2024-02-12 (luni), https://github.com/centre-for-ai-and-climate/lv-feeder-smart-meter-data. Licența nu e declarată: îl folosim doar ca reper pentru forma curbelor, nu ca etichete și nu la antrenare. Comanda: `uv run python -m cyberpunks.a_bilant.weave_check`.

Comparăm 41973 de posturi reale cu cele 300 de posturi simulate ale hărții, pe o zi de luni din februarie (2025-02-10), după forma curbei (normată), nu după nivel: în UK nu toți clienții au contor inteligent.

| măsura | Weave UK (mediană, P10-P90) | simulare (mediană, P10-P90) |
|---|---|---|
| factorul de încărcare (medie / vârf) | 0.57 (0.44-0.67) | 0.51 (0.39-0.67) |
| ponderea nopții 00-06 în consumul zilei | 0.17 (0.12-0.28) | 0.16 (0.11-0.23) |
| seara 17-21 față de prânz 10-14 | 1.55 (1.17-2.06) | 3.67 (0.97-11.38) |

- Ora de vârf cea mai frecventă: 18:00 în datele reale, 19:00 în simulare.
- Figura: `reports/bilant/weave_check.png` (curbele medii normate, cu banda P10-P90).
- Raportul seară/prânz e mai mare în simulare: posturile simulate au mulți prosumatori (Ilfov e primul județ la prosumatori), iar contorul net arată la prânz consumul minus producția panourilor; în datele UK, contorul dă consumul. Numitorul are o limită jos (20% din media zilei).
- Concluzie: simularea e un reper, nu o copie. Profilele SimBench (germane) și consumul românesc diferă de UK, iar diferențele de mai sus spun cât. Modelul învață din formă și din încărcare, deci contează mai ales ca forma să fie plauzibilă. Pe date PPC, curbele vin direct din contoare.
