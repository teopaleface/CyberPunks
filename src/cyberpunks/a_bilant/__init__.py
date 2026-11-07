"""Bilanț pe post: unde se pierde energia.

Pentru fiecare post de transformare și fiecare zi: lipsa = energia ieșită din post (contorul de bilanț) minus suma
contoarelor clienților de sub post. Un model învață pierderea normală a fiecărui post; lipsa peste normal se
diagnostichează (contor de client, furt înainte de contor, pierdere tehnică, client la postul greșit, contorul de
post setat greșit) și devine lucrare pentru echipe.

SIMULARE pe date publice (rețele SimBench, profile SimBench, meteo Open-Meteo), gândită pentru datele PPC.
Problemele sunt ascunse de noi și etichetate din construcție.
"""

LABEL_RO = "Simulare pe date publice, gândită pentru datele PPC"
