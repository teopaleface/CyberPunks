#!/usr/bin/env python3
"""Daybreak: construiește slideurile (HTML 1920x1080) și PDF-ul, cu cifre citite din reports/.

Rulare, din rădăcina repo-ului:  uv run python presentation/scripts/build_slides.py
Cifrele echipei se citesc din reports/ (niciodată scrise de mână). Dacă lipsește fișierul
sau cheia, slideul spune "în lucru". Faptele PPC/presă se verifică prin căutare în memory/
sau docs/research/ (dacă textul nu se mai găsește, slideul spune "în lucru").
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLIDES = ROOT / "presentation" / "slides"
OUT_HTML = SLIDES / "slides.html"
OUT_PDF = ROOT / "presentation" / "exports" / "daybreak-slides.pdf"
FONT_DIR = ROOT / "presentation" / "video" / "assets" / "fonts"
IMG_DIR = ROOT / "presentation" / "frames-3d" / "plates_v3" / "raw_jpg"

WIP = "în lucru"
TABLE: list[tuple[str, str, str]] = []  # (cifra afișată, fișier, cheie)
_json_cache: dict[str, dict | None] = {}
_text_cache: dict[str, str] = {}


# ---------------------------------------------------------------- citire cifre
def load(rel: str):
    if rel not in _json_cache:
        p = ROOT / rel
        try:
            _json_cache[rel] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _json_cache[rel] = None
    return _json_cache[rel]


def dig(rel: str, path: str):
    """path ex.: 'metrics.subtle_precision_at_k'. Întoarce None dacă lipsește."""
    cur = load(rel)
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur if isinstance(cur, (int, float)) and not isinstance(cur, bool) else None


def ro(x: float, dec: int) -> str:
    s = f"{x:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def figure(label: str, rel: str, path: str, fmt) -> str:
    """Citește o cifră, o formatează, o înregistrează în tabel. Lipsă => 'în lucru'."""
    v = dig(rel, path)
    if v is None:
        TABLE.append((f"{label} = {WIP}", rel, path))
        return WIP
    out = fmt(v)
    TABLE.append((f"{label} = {out}", rel, path))
    return out


def derived(label: str, text: str, sources: list[tuple[str, str]]) -> str:
    for rel, path in sources:
        TABLE.append((f"{label} = {text}", rel, path))
    return text


def fact(label: str, needle: str, rel: str) -> str:
    """Fapt extern: apare pe slide doar dacă textul există în fișierul-sursă din memory/ sau docs/."""
    if rel not in _text_cache:
        try:
            _text_cache[rel] = (ROOT / rel).read_text(encoding="utf-8")
        except Exception:
            _text_cache[rel] = ""
    ok = needle in _text_cache[rel]
    TABLE.append((f"{label} = {needle if ok else WIP}", rel, f'text "{needle}"'))
    return needle if ok else WIP


P2 = lambda v: ro(v, 2)  # noqa: E731
P3 = lambda v: ro(v, 3)  # noqa: E731
PCT0 = lambda v: ro(v * 100, 0) + "%"  # noqa: E731


# ---------------------------------------------------------------- HTML helpers
def e(s: str) -> str:
    return html.escape(s, quote=False)


def num(value: str, cls: str = "") -> str:
    """Cifră mare; dacă e 'în lucru' se arată mic."""
    if value == WIP:
        return f'<span class="wip">{WIP}</span>'
    return f'<span class="{cls}">{e(value)}</span>'


SLIDE_NO = 0


def slide(body: str, *, source: str = "", appendix: bool = False, cls: str = "") -> str:
    global SLIDE_NO
    SLIDE_NO += 1
    tag = '<div class="tag">Anexă</div>' if appendix else ""
    src = f'<div class="src">{source}</div>' if source else ""
    return (
        f'<section class="slide {cls}" id="s{SLIDE_NO}">{tag}{body}{src}'
        f'<div class="pg">{SLIDE_NO}</div></section>'
    )


SIM = "simulare pe 30 de zile, date sintetice"


def build() -> str:
    S: list[str] = []

    # ------------------------------------------------ valori
    a_sub = figure("A subtil, Daybreak (precizie în top 1%)", "reports/A/metrics.json", "metrics.subtle_precision_at_k", P2)
    a_sub_b = figure("A subtil, regula VEE", "reports/A/metrics.json", "metrics.subtle_vee_precision_at_k", P2)
    a_sg = figure("A SGCC, Daybreak", "reports/A/metrics.json", "metrics.sgcc_precision_at_k", P2)
    a_sg_b = figure("A SGCC, regula VEE", "reports/A/metrics.json", "metrics.sgcc_vee_precision_at_k", P2)
    b_m = figure("B PR-AUC, Daybreak", "reports/B/metrics.json", "metrics.pr_auc", P2)
    b_b = figure("B PR-AUC, climatologie", "reports/B/metrics.json", "baseline_metrics.pr_auc", P2)
    c_m = figure("C eroare tensiune maximă (pu), Daybreak", "reports/C/metrics.json", "metrics.mae_vmax_pu", P3 if False else (lambda v: ro(v, 4)))
    c_b = figure("C eroare tensiune maximă (pu), metoda simplă", "reports/C/metrics.json", "baseline_metrics.mae_vmax_pu", lambda v: ro(v, 4))
    c_rec = figure("C depășiri 1,10 pu găsite, Daybreak", "reports/C/metrics.json", "metrics.recall_exceed", PCT0)
    c_rec_b = figure("C depășiri 1,10 pu găsite, metoda simplă", "reports/C/metrics.json", "baseline_metrics.recall_exceed", PCT0)
    bl_p = figure("Bilanț precizie@10 cu bilanț", "reports/bilant/metrics.json", "metrics.fuziune_precision_at_10", lambda v: ro(v * 100, 1) + "%")
    bl_pb = figure("Bilanț precizie@10 fără bilanț", "reports/bilant/metrics.json", "baseline_metrics.fuziune_precision_at_10", lambda v: ro(v * 100, 1) + "%")
    bl_f1 = figure("Bilanț diagnostic F1 macro, Daybreak", "reports/bilant/metrics.json", "metrics.diagnoza_macro_f1", P2)
    bl_f1b = figure("Bilanț diagnostic F1 macro, reguli simple", "reports/bilant/metrics.json", "baseline_metrics.diagnoza_macro_f1", P2)
    bl_w = figure("Bilanț deplasări degeaba evitate/zi (K=10)", "reports/bilant/metrics.json", "metrics.fuziune_wasted_trips_avoided_per_day_at_10", P2)

    ev = "reports/planner/agent_eval.json"
    strat = (load(ev) or {}).get("main", {}).get("strategies", {}) if load(ev) else {}
    simple = {k: v for k, v in strat.items() if k != "agent" and isinstance(v, dict) and "net_value_lei_total" in v}
    best = max(simple, key=lambda k: simple[k]["net_value_lei_total"]) if simple and "agent" in strat else None
    BEST_NAMES = {
        "primul_venit": "primul venit, primul servit",
        "top_k_scor": "primii după scor",
        "aleator": "la întâmplare",
        "doar_contoare": "doar contoare",
    }
    if best:
        pre = f"reports/planner/agent_eval.json"
        k = f"main.strategies.{best}"
        a_net = dig(ev, "main.strategies.agent.net_value_lei_total")
        b_net = dig(ev, f"{k}.net_value_lei_total")
        a_km = dig(ev, "main.strategies.agent.km_total")
        b_km = dig(ev, f"{k}.km_total")
        a_w = dig(ev, "main.strategies.agent.useless_visit_rate")
        b_w = dig(ev, f"{k}.useless_visit_rate")
    else:
        a_net = b_net = a_km = b_km = a_w = b_w = None
    if a_net and b_net:
        gain = derived("Agent: valoare netă față de cea mai bună strategie simplă", "+" + ro((a_net / b_net - 1) * 100, 0) + "%",
                       [(ev, "main.strategies.agent.net_value_lei_total"), (ev, f"main.strategies.{best}.net_value_lei_total")])
    else:
        gain = WIP
    if a_km and b_km:
        km_a = derived("Agent km", ro(a_km, 0), [(ev, "main.strategies.agent.km_total")])
        km_b = derived(f"{best} km", ro(b_km, 0), [(ev, f"main.strategies.{best}.km_total")])
        km_pct = derived("Agent km față de cea mai bună strategie simplă", ro((1 - a_km / b_km) * 100, 1) + "%",
                         [(ev, "main.strategies.agent.km_total"), (ev, f"main.strategies.{best}.km_total")])
    else:
        km_a = km_b = km_pct = WIP
    if a_w is not None and b_w is not None:
        w_a = derived("Agent vizite degeaba", ro(a_w * 100, 0) + "%", [(ev, "main.strategies.agent.useless_visit_rate")])
        w_b = derived(f"{best} vizite degeaba", ro(b_w * 100, 0) + "%", [(ev, f"main.strategies.{best}.useless_visit_rate")])
    else:
        w_a = w_b = WIP
    best_name = BEST_NAMES.get(best or "", best or "")
    human = figure("Agent: cazuri trimise la om (30 zile)", ev, "main.strategies.agent.human_review_total", lambda v: ro(v, 0))

    # fapte externe
    f_citiri = fact("PPC: citiri pe zi", "192 de milioane", "memory/08-ppc-workshop-ai.md")
    f_contoare = fact("PPC: contoare inteligente", "Peste 2 milioane", "memory/08-ppc-workshop-ai.md")
    f_km = fact("PPC: km de linii", "136.000 km", "memory/08-ppc-workshop-ai.md")
    f_posturi = fact("PPC: posturi de transformare", "26.000", "memory/08-ppc-workshop-ai.md")
    f_pros = fact("ANRE: prosumatori 31 aug 2026", "385.791", "memory/12-probleme-reale-ppc-2026.md")
    f_mw = fact("ANRE: putere prosumatori", "4.281,86 MW", "memory/12-probleme-reale-ppc-2026.md")
    f_ilfov = fact("ANRE: prosumatori Ilfov", "21.647", "memory/12-probleme-reale-ppc-2026.md")
    f_cr = fact("Furtuna 8 iulie 2025: cod roșu ANM", "cod roșu de vijelii", "docs/research/B.md")
    f_40 = fact("Furtuna: consumatori afectați în Timiș", "40.000 de consumatori", "docs/research/B.md")
    f_80 = fact("Furtuna: echipe pe teren", "80 de echipe", "docs/research/B.md")
    f_881 = fact("Open-Meteo: radiație București 8 iulie 2025", "881 W/m²", "docs/research/B.md")

    def pair(big: str, small: str, label: str, *, accent_cls="") -> str:
        return (
            f'<div class="pair"><div class="p-main">{num(big, "big " + accent_cls)}<div class="cap">Daybreak</div></div>'
            f'<div class="p-vs">față de</div>'
            f'<div class="p-base">{num(small, "mid grey")}<div class="cap">{label}</div></div></div>'
        )

    # ------------------------------------------------ 1 Titlu
    img1 = IMG_DIR / "p11_dawn.jpg"
    S.append(slide(
        f'''<div class="title-grid"><div class="tcol">
        <h1 class="mega">Daybreak</h1>
        <p class="lead">Agentul care planifică unde merg mâine echipele de teren Rețele Electrice.</p>
        <p class="meta">CyberPunks &nbsp;·&nbsp; SmartHack XI 2026 &nbsp;·&nbsp; tema PPC</p></div>
        <div class="imgcol"><img src="../../{img1.relative_to(ROOT).as_posix()}" alt=""></div></div>''',
        source="Produs independent, fără identitate oficială PPC. Imagine generată cu AI.",
        cls="s-title"))

    # ------------------------------------------------ 2 Problema
    S.append(slide(
        f'''<h2>Prea multe date, prea puține răspunsuri.</h2>
        <div class="bignum">{num(f_citiri.replace(" de milioane"," milioane") if f_citiri!=WIP else WIP, "huge")}</div>
        <p class="body">de citiri pe zi de la {e(f_contoare.lower() if f_contoare!=WIP else WIP)} de contoare, pe {e(f_km)} de linii.</p>
        <p class="quote">„Un scor de anomalie de 0,87 nu îi spune unui tehnician unde să meargă mâine dimineață.”</p>''',
        source="Sursa cifrelor: workshopul PPC (memory/08-ppc-workshop-ai.md). Citatul: tema PPC."))

    # ------------------------------------------------ 3 Context 2026 (2b)
    S.append(slide(
        f'''<h2>Rețeaua de joasă tensiune s-a umplut de panouri.</h2>
        <div class="bignum">{num(f_pros, "huge")}</div>
        <p class="body">de prosumatori, {e(f_mw)}. Ilfov e primul județ din țară, cu {e(f_ilfov)}.</p>
        <p class="body grey">Prețuri negative la prânz. Deficit seara, între 18 și 22.</p>''',
        source="ANRE, 31 august 2026, prin memory/12-probleme-reale-ppc-2026.md (neverificat de noi)."))

    # ------------------------------------------------ 4 O zi reală
    S.append(slide(
        f'''<h2>Marți, 8 iulie 2025. Aceeași zi, trei probleme, aceleași echipe.</h2>
        <div class="three">
          <div><div class="k">Furtună</div><p>Cod roșu în Banat. Circa {e(f_40.replace(' de consumatori',''))} de consumatori fără curent în Timiș. {e(f_80)} pe teren.</p></div>
          <div><div class="k">Soare</div><p>{e(f_881)} la prânz în București. Tensiune mare la prosumatori.</p></div>
          <div><div class="k">Contoare</div><p>Contoare stricate sau umblate, undeva printre milioane.</p></div>
        </div>''',
        source="Sursa: docs/research/B.md, secțiunea 3 (ANM, prefectul Timișului, Open-Meteo)."))

    # ------------------------------------------------ 5 Produsul
    S.append(slide(
        '''<h2>Daybreak: date, trei modele, reguli, plan.</h2>
        <div class="flow">
          <div class="st"><div class="n">1</div><div class="t">Datele</div><div class="d">contoare, vreme, rețea</div></div>
          <div class="ar"></div>
          <div class="st"><div class="n">2</div><div class="t">Trei modele și bilanțul</div><div class="d">contoare, furtună, tensiune; energia pe fiecare post</div></div>
          <div class="ar"></div>
          <div class="st"><div class="n">3</div><div class="t">Reguli de decizie</div><div class="d">costă mai puțin decât aduce?</div></div>
          <div class="ar"></div>
          <div class="st"><div class="n">4</div><div class="t">Planul de mâine</div><div class="d">trasee, ordine de lucru, alerte</div></div>
        </div>
        <p class="body unsure">Dacă nu e sigur, întreabă dispecerul.</p>''',
        source="Captura din consolă: la demo."))

    # ------------------------------------------------ 6 Modele față de baseline
    def row(src, what, dm, bm, base, test, unit=""):
        return (f'<tr><td class="r-src">{src}</td><td class="r-what">{what}</td>'
                f'<td class="r-num acc">{e(dm)}{unit}</td><td class="r-num">{e(bm)}{unit}</td>'
                f'<td class="r-base">{base}<br><span class="g2">{test}</span></td></tr>')
    S.append(slide(
        f'''<h2>Fiecare model bate metoda simplă.</h2>
        <table class="tbl"><colgroup><col style="width:210px"><col style="width:520px"><col style="width:220px"><col style="width:220px"><col></colgroup><thead><tr><th></th><th></th><th>Daybreak</th><th>Simplu</th><th></th></tr></thead><tbody>
        {row("A · Contoare", "probleme subtile găsite în primele 1%", a_sub, a_sub_b, "regula de verificare VEE", "Londra, perioadă nouă, date injectate")}
        {row("A · Contoare", "furturi reale găsite în primele 1%", a_sg, a_sg_b, "regula de verificare VEE", "SGCC, clienți nevăzuți, etichete reale")}
        {row("B · Furtună", "PR-AUC, zone în risc", b_m, b_b, "media istorică a lunii", "SUA, anul 2025 nevăzut")}
        {row("C · Tensiune", "eroare la tensiunea maximă (pu)", c_m, c_b, "regresie liniară", "6 rețele nevăzute, sintetice")}
        {row("Bilanț", "precizia verificărilor, top 10", bl_p, bl_pb, "doar scorul contoarelor", "300 de posturi, sintetic")}
        </tbody></table>''',
        source="reports/A, B, C, bilant: metrics.json. Pentru A, B și bilanț, mai mare e mai bine; pentru C, mai mic."))

    # ------------------------------------------------ 7 Bilanț
    S.append(slide(
        f'''<h2>Bilanțul pe post vede ce nu vede niciun contor.</h2>
        <p class="body">Energia care iese din post, minus suma contoarelor clienților. Modelul învață pierderea normală; ce rămâne are o cauză.</p>
        {pair(bl_f1, bl_f1b, "reguli simple")}
        <p class="body grey">F1 la diagnosticul cauzei, 6 clase. Cu bilanț, {e(bl_w)} deplasări degeaba mai puțin pe zi.</p>''',
        source="reports/bilant/metrics.json. Simulare pe date publice, 300 de posturi sintetice, gândită pentru datele PPC."))

    # ------------------------------------------------ 8 Tensiune
    S.append(slide(
        f'''<h2>Peste 1,10 pu, alege cea mai ieftină soluție.</h2>
        {pair(c_m, c_b, "metoda simplă", accent_cls="")}
        <p class="body">Eroarea la tensiunea maximă, în pu. Depășirile găsite: {e(c_rec)} față de {e(c_rec_b)}.</p>
        <p class="body grey">Alte faze, priza transformatorului, mesaje „consumă la prânz”, baterii, limită de export.</p>''',
        source="reports/C/metrics.json. 6 rețele SimBench nevăzute, date sintetice. Efectele sunt calculate fizic (pandapower)."))

    # ------------------------------------------------ 9 Agent
    S.append(slide(
        f'''<h2>Agentul se dovedește.</h2>
        <div class="agent">
          <div class="a-big">{num(gain, "huge")}<div class="cap">valoare netă față de cea mai bună strategie simplă ({e(best_name)})</div></div>
          <div class="a-side">
            <div class="row2"><span class="v">{e(km_a)} km</span><span class="vs">față de {e(km_b)} km, adică {e(km_pct)} mai puțin</span></div>
            <div class="row2"><span class="v">{e(w_a)}</span><span class="vs">vizite degeaba, față de {e(w_b)}</span></div>
          </div>
        </div>''',
        source=f"reports/planner/agent_eval.json, main.strategies. {SIM[0].upper()+SIM[1:]}."))

    # ------------------------------------------------ 10 Nu sunt sigur
    S.append(slide(
        f'''<h2>Când nu e sigur, întreabă.</h2>
        <ul class="list">
          <li><b>Intrare ciudată?</b> Merge în carantină. Exemplu: latitudine 51,5 și scor 1,4.</li>
          <li><b>Lipsește o sursă?</b> Planul merge cu ce are.</li>
          <li><b>Incertitudine mare?</b> Decide omul. {e(human)} cazuri în {e("30 de zile")}.</li>
          <li><b>Fiecare decizie</b> are jurnal: predicția, modelul, regula, pragul.</li>
        </ul>''',
        source=f"reports/planner/agent_eval.json, human_review_total. {SIM[0].upper()+SIM[1:]}."))

    # ------------------------------------------------ 11 Explicabilitate
    S.append(slide(
        '''<h2>Fiecare lucrare vine cu motivul ei.</h2>
        <ul class="list">
          <li>Factorii, în cuvinte simple.</li>
          <li>Cazuri asemănătoare din istoric.</li>
          <li>Regula și pragul care au decis.</li>
          <li>Drumul înapoi până la predicție.</li>
        </ul>''',
        source="Captură din detaliul unei lucrări: la demo."))

    # ------------------------------------------------ 12 PPC
    S.append(slide(
        '''<h2>Ce vrem să confirmăm cu PPC.</h2>
        <ul class="list">
          <li>Există contoare de bilanț în posturi, și la ce procent?</li>
          <li>Lista client → post: e de încredere?</li>
          <li>Cum intră planul în sistemul de lucru al echipelor?</li>
          <li>Ce limite au echipele: abilități, ture, depouri?</li>
        </ul>
        <p class="body grey">Fără contor de bilanț, estimăm energia intrată din model și arătăm unde merită montat primul.</p>''',
        source=""))

    # ------------------------------------------------ Anexă
    S.append(slide(
        f'''<h2>Etică și EU AI Act.</h2>
        <p class="body">Infrastructura critică e „risc ridicat”. Deci: om în buclă, jurnal automat, documentație, date pseudonimizate.</p>
        <p class="body grey">Etichetăm „date sintetice” și „imagine generată cu AI”.</p>''',
        source="Sursa: workshopul PPC, memory/08-ppc-workshop-ai.md.", appendix=True))

    S.append(slide(
        '''<h2>Costuri și scalare.</h2>
        <p class="body">Modelele rulează local (LightGBM, OR-Tools), fără API plătit.</p>
        <p class="body grey">Pe platforma PPC: NiFi sau Airflow la intrare, S3 Bronze și Silver, Spark pe EMR pentru calculele zilnice, Redshift sau Kafka la ieșire. Costul de rulare: calitativ, nemăsurat.</p>''',
        source="Platforma: memory/08-ppc-workshop-ai.md.", appendix=True))

    cmds = []
    for rel, nm in [("reports/A/metrics.json", "A"), ("reports/B/metrics.json", "B"), ("reports/C/metrics.json", "C"),
                    ("reports/bilant/metrics.json", "Bilanț"), ("reports/planner/agent_eval.json", "Agent")]:
        d = load(rel)
        c = d.get("reproduce_cmd") if isinstance(d, dict) else None
        TABLE.append((f"comandă reproducere {nm} = {'citită' if c else WIP}", rel, "reproduce_cmd"))
        cmds.append(f'<div class="cmd"><span class="cn">{nm}</span><code>{e(c) if c else WIP}</code></div>')
    S.append(slide(
        f'''<h2>Reproducere.</h2><div class="cmds">{"".join(cmds)}</div>
        <p class="body grey">Fiecare cifră din prezentare se reface cu o comandă. Repo public, cu tot istoricul.</p>''',
        source="Comenzile sunt citite din câmpul reproduce_cmd al fiecărui raport.", appendix=True))

    img2 = IMG_DIR / "p12_day.jpg"
    S.append(slide(
        f'''<div class="title-grid"><div class="tcol">
        <h2>Ce urmează.</h2>
        <ul class="list tight">
          <li>Calibrare pe istoricul Rețele Electrice.</li>
          <li>Contoare de bilanț în posturi.</li>
          <li>Legătura cu sistemul echipelor.</li>
          <li>Pilot pe un județ.</li>
        </ul></div>
        <div class="imgcol"><img src="../../{img2.relative_to(ROOT).as_posix()}" alt=""></div></div>''',
        source="Imagine generată cu AI.", appendix=True, cls="s-title"))
    return "\n".join(S)


CSS = """
@font-face{font-family:Archivo;src:url('../video/assets/fonts/Archivo-wdth62_125-wght100_900-latin-ext.woff2') format('woff2');font-weight:100 900;font-stretch:62% 125%;unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:Archivo;src:url('../video/assets/fonts/Archivo-wdth62_125-wght100_900-latin.woff2') format('woff2');font-weight:100 900;font-stretch:62% 125%;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@page{size:1920px 1080px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:Archivo,'Helvetica Neue',Arial,sans-serif;color:#0B1622;font-size:38px;line-height:1.3}
.slide{position:relative;width:1920px;height:1080px;overflow:hidden;background:#fff;padding:112px 128px 0 128px;page-break-after:always;break-after:page}
.slide:last-child{page-break-after:auto;break-after:auto}
h1,h2{font-weight:600;letter-spacing:-0.025em;line-height:1.05}
h2{font-size:80px;max-width:1500px;margin-bottom:56px}
.mega{font-size:190px;letter-spacing:-0.035em;font-weight:600;line-height:1}
.lead{font-size:46px;line-height:1.25;color:#0B1622;margin-top:48px;max-width:860px}
.meta{font-size:30px;color:#6B7684;margin-top:56px}
.body{font-size:38px;line-height:1.35;max-width:1400px;margin-top:28px}
.grey{color:#6B7684}
.src{position:absolute;left:128px;right:900px;bottom:56px;font-size:22px;color:#8A93A0;line-height:1.35}
.pg{position:absolute;right:128px;bottom:56px;font-size:22px;color:#8A93A0;font-variant-numeric:tabular-nums}
.tag{position:absolute;left:128px;top:48px;font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#2364D2;font-weight:600}
.huge{font-size:200px;font-weight:600;letter-spacing:-0.035em;line-height:1;color:#2364D2;font-variant-numeric:tabular-nums}
.big{font-size:180px;font-weight:600;letter-spacing:-0.035em;line-height:1;color:#2364D2;font-variant-numeric:tabular-nums}
.mid{font-size:100px;font-weight:600;letter-spacing:-0.03em;line-height:1;font-variant-numeric:tabular-nums}
.wip{font-size:56px;font-weight:500;color:#8A93A0}
.bignum{margin-top:8px}
.quote{font-size:40px;line-height:1.3;margin-top:56px;max-width:1300px;border-left:6px solid #2364D2;padding-left:32px}
.title-grid{position:static}
.title-grid .tcol{padding-top:170px;max-width:960px}
.s-title .imgcol{position:absolute;right:0;top:0;width:700px;height:1080px}
.s-title .pg{display:none}
.s-title .src{right:800px}
.imgcol img{width:100%;height:100%;object-fit:cover;display:block}
.s-title .list{max-width:900px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:72px;margin-top:40px}
.three .k{font-size:30px;font-weight:600;letter-spacing:.02em;color:#2364D2;border-top:3px solid #0B1622;padding-top:20px;margin-bottom:20px}
.three p{font-size:36px;line-height:1.35}
.flow{display:flex;align-items:flex-start;gap:28px;margin-top:40px}
.st{width:360px}
.st .n{font-size:30px;font-weight:600;color:#2364D2;margin-bottom:14px}
.st .t{font-size:44px;font-weight:600;letter-spacing:-0.02em;line-height:1.1;border-top:3px solid #0B1622;padding-top:20px}
.st .d{font-size:30px;color:#6B7684;margin-top:16px;line-height:1.3}
.ar{width:36px;height:3px;background:#0B1622;margin-top:70px;flex:none;position:relative}
.ar:after{content:'';position:absolute;right:0;top:-9px;border-left:16px solid #0B1622;border-top:10px solid transparent;border-bottom:10px solid transparent}
.unsure{margin-top:72px;font-size:44px;font-weight:500;color:#2364D2}
.tbl{border-collapse:collapse;width:100%;margin-top:8px;table-layout:fixed}
.tbl th{font-size:24px;font-weight:600;color:#6B7684;text-align:right;padding:0 0 14px;letter-spacing:.04em;text-transform:uppercase}
.tbl td{padding:22px 0;border-top:2px solid #E3E6EA;vertical-align:middle}
.r-src{font-size:30px;font-weight:600;width:210px}
.r-what{font-size:30px;width:520px;line-height:1.25;padding-right:32px}
.r-num{font-size:60px;font-weight:600;letter-spacing:-0.03em;text-align:right;width:220px;font-variant-numeric:tabular-nums;color:#8A93A0}
.r-num.acc{color:#2364D2}
.tbl td.r-base{font-size:26px;padding-left:64px;line-height:1.3}
.g2{color:#8A93A0}
.pair{display:flex;align-items:flex-end;gap:56px;margin-top:40px}
.pair .cap{font-size:28px;color:#6B7684;margin-top:12px;letter-spacing:0}
.p-vs{font-size:36px;color:#8A93A0;padding-bottom:50px}
.p-base .mid{color:#8A93A0}
.agent{display:grid;grid-template-columns:900px 1fr;gap:80px;margin-top:16px;align-items:end}
.a-big .cap{font-size:34px;color:#6B7684;margin-top:20px;max-width:760px;line-height:1.3}
.row2{border-top:3px solid #0B1622;padding-top:20px;margin-bottom:44px}
.row2 .v{display:block;font-size:80px;font-weight:600;letter-spacing:-0.03em;line-height:1}
.row2 .vs{display:block;font-size:32px;color:#6B7684;margin-top:12px}
.list{list-style:none;font-size:44px;line-height:1.3;max-width:1450px}
.list li{padding:22px 0;border-top:2px solid #E3E6EA}
.list li:first-child{border-top:3px solid #0B1622}
.list b{font-weight:600}
.list.tight li{font-size:40px}
.cmds{margin-top:8px}
.cmd{display:flex;gap:40px;align-items:baseline;padding:20px 0;border-top:2px solid #E3E6EA}
.cmd .cn{width:170px;font-weight:600;font-size:34px}
.cmd code{font-family:'SF Mono',Menlo,monospace;font-size:28px;color:#0B1622}
"""


def find_chrome() -> str | None:
    cands = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Helium.app/Contents/MacOS/Helium",
    ]
    for c in cands:
        if Path(c).exists():
            return c
    for n in ("google-chrome", "chromium", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    return None


def main() -> int:
    body = build()
    SLIDES.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(
        f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><title>Daybreak</title>'
        f'<meta name="viewport" content="width=1920"><style>{CSS}</style></head><body>{body}</body></html>',
        encoding="utf-8",
    )
    print(f"HTML: {OUT_HTML.relative_to(ROOT)}  ({SLIDE_NO} slideuri)")
    chrome = find_chrome()
    if not chrome:
        print("Nu am găsit Chrome; PDF-ul nu s-a exportat.", file=sys.stderr)
        return 1
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--allow-file-access-from-files", "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--virtual-time-budget=10000", f"--print-to-pdf={OUT_PDF}", OUT_HTML.as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    size = OUT_PDF.stat().st_size
    print(f"PDF: {OUT_PDF.relative_to(ROOT)}  ({size/1e6:.2f} MB)\n")
    w = max(len(t[0]) for t in TABLE)
    print(f"{'Cifra':<{w}}  Fișier  ->  cheie")
    for lab, f, k in TABLE:
        print(f"{lab:<{w}}  {f}  ->  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
