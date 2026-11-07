"""Scrie scenele filmului, varianta 3 (36 s, 120 BPM): presentation/video/compositions/c1..c7 și index.html.

Reguli (abilitățile hyperframes, motion-doctrine, apple-design, launch-video, oversized-cursor, apple-launch-film):
- un rând mare pe cadru, cuvinte de zi cu zi; curentul filmului e spre STÂNGA (ieșire la stânga, intrare din dreapta, din mers);
- obiectele 3D (Blender, Codex Astra) intră rotindu-se din foile de 30 de cadre;
- cursorul mare intră de jos, cu vârful pe țintă, iar clicul pornește următorul pas în același cadru;
- cifrele nu se scriu aici: scripts/cifre_film.py le pune din reports/.
Rulare: python3 presentation/scripts/build_film_v3.py
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
# Consola în scena 5: card la 74% din cadru, centrat, sus la 60 px ("Un clic." încape dedesubt, în zona sigură de 80%).
CS = 0.74
CX, CY = (1920 - CS * 1920) / 2, 60
# Logoul din antetul consolei: centrul la (40, 31), lățimea 27 px în consolă.
LX, LY, LS = CX + CS * 40, CY + CS * 31, CS * 27 / 300
COMP = ROOT / "presentation" / "video" / "compositions"

BASE_CSS = """
    #root { position: absolute; inset: 0; overflow: hidden; background: var(--ground); }
    .clipbox { position: absolute; inset: 0; }
    .ln { position: absolute; left: 0; right: 0; display: block; text-align: center; white-space: nowrap;
          font-weight: 650; letter-spacing: -0.04em; line-height: 1.02; color: var(--ink); }
    .ln span { display: inline-block; }
    .xl { font-size: 176px; }
    .l2 { font-size: 150px; }
    .obj { position: absolute; background-repeat: no-repeat; background-size: 600% 500%; background-position: 0% 0%; }
    .cursor { position: absolute; left: 0; top: 0; width: 134px; height: 134px; z-index: 20;
              filter: drop-shadow(0 4px 6px rgba(0,0,0,.3)); }
    .note { position: absolute; left: 0; right: 0; bottom: 62px; text-align: center; font-size: 28px; font-weight: 500; color: var(--muted); }
"""

JS_HELPERS = """
      const IN = (tl, sel, at) => tl.fromTo(sel, { x: 150, opacity: 0, filter: "blur(10px)" }, { x: 0, opacity: 1, filter: "blur(0px)", duration: 0.34, ease: "power4.out" }, at);
      const OUT = (tl, sel, at) => tl.to(sel, { x: -150, opacity: 0, filter: "blur(10px)", duration: 0.18, ease: "power4.in" }, at);
      const SPIN = (tl, id, at, dur) => {
        const el = document.getElementById(id), p = { f: 0 };
        tl.fromTo(p, { f: 0 }, { f: 29, duration: dur, ease: "power2.out", onUpdate: () => {
          const i = Math.round(p.f), c = i % 6, r = Math.floor(i / 6);
          el.style.backgroundPosition = (c * 20) + "% " + (r * 25) + "%";
        } }, at);
      };
"""


def scene(cid: str, dur: float, css: str, body: str, js: str, comment: str) -> str:
    return f"""<template>
  <!-- {comment} -->
  <style>{BASE_CSS}{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080">
{body}
  </div>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});{JS_HELPERS}{js}
      window.__timelines["{cid}"] = tl;
    }})();
  </script>
</template>
"""


def obj(id_: str, name: str, left: int, top: int, size: int) -> str:
    return (f'<div id="{id_}" class="obj" style="left:{left}px; top:{top}px; width:{size}px; height:{size}px; '
            f'background-image:url(assets/3d/astra/{name}_spin.webp)"></div>')


def words(text: str) -> str:
    return " ".join(f"<span>{w}</span>" for w in text.split(" "))


# ---------------------------------------------------------------- c1: cârligul (0-4 s)
c1 = scene("c1", 4, """
    #c1-l1, #c1-l2 { top: 560px; }
    #c1-l3a { top: 470px; } #c1-l3b { top: 640px; }
""", f"""    <div id="c1-a" class="clip clipbox" data-start="0" data-duration="1.2"><div id="c1-l1" class="ln xl">{words('8 iulie 2025.')}</div></div>
    <div id="c1-b" class="clip clipbox" data-start="1.2" data-duration="1.2"><div id="c1-l2" class="ln xl">{words('Vijelie în Banat.')}</div></div>
    <div id="c1-c" class="clip clipbox" data-start="2.4" data-duration="1.6"><div id="c1-l3a" class="ln l2">{words('Zeci de mii de case')}</div><div id="c1-l3b" class="ln l2">{words('fără curent.')}</div></div>
    <div id="c1-o" class="clip clipbox" data-start="1.2" data-duration="2.8" data-layout-allow-overflow>{obj('c1-storm', 'storm', 730, 40, 460)}</div>
    <p id="c1-ai" class="clip note" data-start="1.2" data-duration="2.65">Obiecte 3D modelate cu AI</p>""", """
      // Primul cadru are deja data pe ecran (miniatura filmului).
      tl.fromTo("#c1-l1", { x: 40, opacity: 1 }, { x: 0, opacity: 1, duration: 0.5, ease: "power4.out" }, 0);
      OUT(tl, "#c1-l1", 1.02);
      IN(tl, "#c1-l2", 1.2); OUT(tl, "#c1-l2", 2.22);
      // Norul de furtună intră rotindu-se, din dreapta sus, și se așază deasupra textului.
      tl.fromTo("#c1-storm", { x: 520, y: -260, scale: 1.2, filter: "blur(12px)" }, { x: 0, y: 0, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }, 1.2);
      SPIN(tl, "c1-storm", 1.2, 0.8);
      tl.to("#c1-storm", { y: -40, scale: 0.8, duration: 0.5, ease: "power3.inOut" }, 2.0);
      IN(tl, "#c1-l3a", 2.4); IN(tl, "#c1-l3b", 2.5);
      OUT(tl, ["#c1-l3a", "#c1-l3b", "#c1-storm"], 3.82);
      tl.fromTo("#c1-ai", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 1.4);
""", "Cârligul: ziua reală (8 iulie 2025, vijelia din Banat; surse în docs/research/B.md). Norul e obiect 3D modelat cu AI.")

# ---------------------------------------------------------------- c2: întrebarea (4-8 s)
c2 = scene("c2", 4, """
    #c2-l1a { top: 500px; } #c2-l1b { top: 670px; }
    #c2-l2 { top: 432px; font-size: 216px; }
""", f"""    <div id="c2-a" class="clip clipbox" data-start="0" data-duration="2"><div id="c2-l1a" class="ln l2">{words('Mâine dimineață')}</div><div id="c2-l1b" class="ln l2">{words('pleacă echipele.')}</div></div>
    <div id="c2-o" class="clip clipbox" data-start="0" data-duration="2" data-layout-allow-overflow>{obj('c2-helmet', 'helmet', 760, 60, 400)}</div>
    <div id="c2-b" class="clip clipbox" data-start="2" data-duration="2"><div id="c2-l2" class="ln">{words('Dar unde?')}</div></div>""", """
      IN(tl, "#c2-l1a", 0.0); IN(tl, "#c2-l1b", 0.1);
      tl.fromTo("#c2-helmet", { x: 600, y: 120, scale: 1.2, filter: "blur(12px)" }, { x: 0, y: 0, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }, 0.0);
      SPIN(tl, "c2-helmet", 0.0, 0.8);
      OUT(tl, ["#c2-l1a", "#c2-l1b", "#c2-helmet"], 1.82);
      // Întrebarea stă nemișcată (liniștea dinaintea răspunsului).
      IN(tl, "#c2-l2", 2.0); OUT(tl, "#c2-l2", 3.82);
""", "Întrebarea: dimineața pleacă echipele; unde le trimiți? Casca e obiect 3D modelat cu AI.")

# ---------------------------------------------------------------- c3: problemele (8-12 s)
# Punctele logoului din scena 4 (unde aterizează obiectele): vezi D1..D3 de mai jos.
D = [(370.9, 450.1), (507.3, 409.1), (589.1, 409.1)]
c3 = scene("c3", 4, """
    .c3-ln { top: 452px; }
""", f"""    <div id="c3-a" class="clip clipbox" data-start="0" data-duration="1"><div id="c3-l1" class="ln xl c3-ln">{words('Stâlpi căzuți.')}</div></div>
    <div id="c3-b" class="clip clipbox" data-start="1" data-duration="1"><div id="c3-l2" class="ln xl c3-ln">{words('Curent furat.')}</div></div>
    <div id="c3-c" class="clip clipbox" data-start="2" data-duration="1.1"><div id="c3-l3" class="ln xl c3-ln">{words('Prea mult soare.')}</div></div>
    <div id="c3-o" class="clip clipbox" data-start="0" data-duration="4" data-layout-allow-overflow>
      {obj('c3-pole', 'transformer', 60, 30, 400)}
      {obj('c3-meter', 'meter', 1480, 50, 340)}
      {obj('c3-solar', 'solar', 1440, 660, 400)}
    </div>
    <p id="c3-ai" class="clip note" data-start="0" data-duration="3.05">Obiecte 3D modelate cu AI</p>""", f"""
      IN(tl, "#c3-l1", 0.0); OUT(tl, "#c3-l1", 0.82);
      IN(tl, "#c3-l2", 1.0); OUT(tl, "#c3-l2", 1.82);
      IN(tl, "#c3-l3", 2.0); OUT(tl, "#c3-l3", 2.95);
      // Stâlpul intră înclinat (căzut), contorul și panoul din dreapta; rămân pe ecran.
      tl.fromTo("#c3-pole", {{ x: -560, y: -200, rotation: -38, filter: "blur(12px)" }}, {{ x: 0, y: 0, rotation: -16, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 0.0);
      SPIN(tl, "c3-pole", 0.0, 0.8);
      tl.fromTo("#c3-meter", {{ x: 560, y: -260, rotation: 20, filter: "blur(12px)" }}, {{ x: 0, y: 0, rotation: 6, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 1.0);
      SPIN(tl, "c3-meter", 1.0, 0.8);
      tl.fromTo("#c3-solar", {{ x: 560, y: 260, rotation: 18, filter: "blur(12px)" }}, {{ x: 0, y: 0, rotation: 4, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 2.0);
      SPIN(tl, "c3-solar", 2.0, 0.8);
      // Cele trei probleme devin cele trei opriri ale traseului din logo (scena 4).
      const into = (sel, cx, cy, tx, ty) => tl.to(sel, {{ x: tx - cx, y: ty - cy, scale: 0.05, rotation: 0, duration: 0.75, ease: "power3.in" }}, 3.1);
      into("#c3-pole", 260, 230, {D[0][0]}, {D[0][1]});
      into("#c3-meter", 1650, 220, {D[1][0]}, {D[1][1]});
      into("#c3-solar", 1640, 860, {D[2][0]}, {D[2][1]});
      tl.to(["#c3-pole", "#c3-meter", "#c3-solar"], {{ opacity: 0, duration: 0.15 }}, 3.82);
      tl.fromTo("#c3-ai", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, 0.2);
""", "Problemele zilei, în cuvinte simple: furtuna (stâlpi căzuți), contoarele manipulate (curent furat), prosumatorii (prea mult soare).")

# ---------------------------------------------------------------- c4: răspunsul (12-15 s)
c4 = scene("c4", 3, """
    #c4-group { position: absolute; inset: 0; transform-origin: 0 0; }
    #c4-mark { position: absolute; left: 330px; top: 300px; width: 300px; height: 191px; overflow: visible; }
    #c4-name { position: absolute; left: 670px; top: 326px; font-size: 150px; font-weight: 650; letter-spacing: -0.04em; line-height: 1; color: var(--ink); white-space: nowrap; }
    #c4-name span, #c4-l2 span { display: inline-block; }
    #c4-l2 { top: 560px; }
""", f"""    <div id="c4-s" class="clip clipbox" data-start="0" data-duration="3" data-layout-allow-overflow>
      <div id="c4-group">
        <svg id="c4-mark" viewBox="10 18 44 28" aria-hidden="true">
          <defs><clipPath id="c4-hz"><rect x="0" y="0" width="64" height="36.2" /></clipPath></defs>
          <g clip-path="url(#c4-hz)"><path id="c4-sun" style="fill: var(--sun)" d="M18 36a14 14 0 0 1 28 0Z" /></g>
          <path id="c4-route" pathLength="1" d="M16 40h12l8-6h12" style="fill: none; stroke: var(--ink); stroke-width: 5; stroke-linecap: round; stroke-linejoin: round" />
          <circle cx="16" cy="40" r="4" style="fill: var(--ink)" /><circle cx="36" cy="34" r="4" style="fill: var(--ink)" /><circle cx="48" cy="34" r="4" style="fill: var(--ink)" />
        </svg>
        <h1 id="c4-name">{words('Tura de mâine')}</h1>
        <div id="c4-l2" class="ln l2">{words('face planul.')}</div>
      </div>
    </div>""", """
      // Cele trei opriri sunt deja pe loc (au venit din scena 3); traseul le leagă, soarele răsare.
      tl.fromTo("#c4-route", { strokeDasharray: "1 1", strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.36, ease: "power2.inOut" }, 0.0);
      tl.fromTo("#c4-sun", { y: 15 }, { y: 0, duration: 0.8, ease: "expo.out" }, 0.15);
      tl.fromTo("#c4-name span", { opacity: 0, filter: "blur(12px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.45, ease: "expo.out", stagger: 0.08 }, 0.25);
      tl.fromTo("#c4-l2 span", { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.4, ease: "expo.out", stagger: 0.08 }, 0.75);
      // Ieșirea: semnul și numele se strâng în antetul consolei din scena 5 (același logo, colțul stânga sus).
      tl.to("#c4-l2", { opacity: 0, filter: "blur(8px)", duration: 0.15, ease: "power3.in" }, 2.55);
      tl.to("#c4-group", { x: %LX% - %LS% * 480, y: %LY% - %LS% * 395.5, scale: %LS%, duration: 0.42, ease: "power3.in" }, 2.58);
""", "Răspunsul: numele produsului; soarele din logo răsare în spatele traseului (singura culoare din cadru).")

c4 = c4.replace("%LX%", f"{LX:.1f}").replace("%LY%", f"{LY:.1f}").replace("%LS%", f"{LS:.4f}")

# ---------------------------------------------------------------- c5: produsul (15-23 s)
# Butonul "Rulează agentul": (1804, 31) în consolă.
BX, BY = CX + CS * 1804, CY + CS * 31
c5 = scene("c5", 8, """
    #c5-cam { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
    #c5-card { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; border-radius: 26px; overflow: hidden;
               box-shadow: 0 34px 90px rgba(11,22,34,.18), 0 8px 22px rgba(11,22,34,.10); }
    #c5-card img { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
    #c5-press { position: absolute; left: 1717px; top: 13px; width: 174px; height: 37px; border-radius: 5px; background: rgba(0,0,0,.35); opacity: 0; }
    #c5-cap1 { top: %CAPTOP%px; font-size: 76px; }
    #c5-pillwrap { position: absolute; left: 0; right: 0; top: 900px; display: flex; justify-content: center; }
    #c5-pill { padding: 26px 52px; border-radius: 999px; background: rgba(255,255,255,.94); box-shadow: 0 18px 50px rgba(11,22,34,.18);
               font-size: 62px; font-weight: 650; letter-spacing: -0.03em; color: var(--ink); white-space: nowrap; }
""", f"""    <div id="c5-s" class="clip clipbox" data-start="0" data-duration="8" data-layout-allow-overflow>
      <div id="c5-cam">
        <div id="c5-card">
          <img id="c5-before" src="assets/ui/consola_fara_trasee@2x.png" alt="" />
          <img id="c5-after" src="assets/ui/consola_cu_trasee@2x.png" alt="" />
          <div id="c5-press"></div>
        </div>
      </div>
      <div id="c5-cap1" class="ln">{words('Un clic.')}</div>
      <div id="c5-pillwrap"><div id="c5-pill">Fiecare echipă știe unde merge.</div></div>
      <img id="c5-cursor" class="cursor" src="assets/ui/cursor.svg" alt="" />
    </div>""", f"""
      const cam = (s, x, y) => ({{ x: x, y: y, scale: s }});
      tl.set("#c5-cam", cam({CS}, {CX}, {CY}), 0);
      tl.fromTo("#c5-card", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.16, ease: "power2.out" }}, 0);
      tl.fromTo("#c5-after", {{ clipPath: "inset(0% 0% 100% 0%)" }}, {{ clipPath: "inset(0% 0% 100% 0%)", duration: 0.01 }}, 0);
      // Cursorul mare intră de jos, vârful ajunge pe "Rulează agentul" (clic pe bătaia de la 16,0 s).
      tl.fromTo("#c5-cursor", {{ x: {BX - 28}, y: 1240 }}, {{ x: {BX - 28}, y: {BY - 15}, duration: 0.7, ease: "power3.out", immediateRender: false }}, 0.25);
      tl.set("#c5-cursor", {{ x: {BX - 28}, y: 1240 }}, 0);
      tl.to("#c5-cursor", {{ scale: 0.84, duration: 0.1, ease: "power2.in", transformOrigin: "21% 11%" }}, 1.0);
      tl.to("#c5-cursor", {{ scale: 1, duration: 0.22, ease: "power2.out", transformOrigin: "21% 11%" }}, 1.1);
      tl.to("#c5-press", {{ opacity: 1, duration: 0.08 }}, 1.0);
      tl.to("#c5-press", {{ opacity: 0, duration: 0.25 }}, 1.12);
      tl.to("#c5-cursor", {{ x: 2100, y: {BY + 140}, duration: 0.55, ease: "power2.in" }}, 1.35);
      tl.fromTo("#c5-cap1 span", {{ opacity: 0, x: 60, filter: "blur(8px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.3, ease: "power4.out", stagger: 0.08 }}, 1.02);
      tl.to("#c5-cap1", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power3.in" }}, 1.62);
      // Clicul pornește planul: camera intră pe hartă, iar traseele echipelor se desenează (de sus în jos).
      tl.to("#c5-cam", {{ ...cam(1.9, 960 - 1.9 * 470, 540 - 1.9 * 420), duration: 1.3, ease: "power3.inOut" }}, 1.55);
      tl.to("#c5-after", {{ clipPath: "inset(0% 0% 0% 0%)", duration: 1.6, ease: "power2.inOut" }}, 1.8);
      tl.to("#c5-cam", {{ ...cam(2.0, 960 - 2.0 * 480, 540 - 2.0 * 420), duration: 4.6, ease: "none" }}, 2.85);
      tl.fromTo("#c5-pill", {{ y: 40, opacity: 0, filter: "blur(10px)" }}, {{ y: 0, opacity: 1, filter: "blur(0px)", duration: 0.4, ease: "expo.out" }}, 3.0);
      // Ieșirea spre stânga (curentul filmului).
      OUT(tl, ["#c5-cam", "#c5-pill"], 7.8);
""", "Produsul: consola reală (http://localhost:3710/, 8 iulie 2025, date sintetice pe hartă reală). Cursorul apasă Rulează agentul, traseele apar.")

c5 = c5.replace("%CAPTOP%", f"{CY + CS * 1080 + 26:.0f}")

# ---------------------------------------------------------------- c6: omul (23-29 s)
# Cardul "Nu sunt sigur": centru (1555, 268) în consolă; butonul "Aprobă": (1308, 314).
S6 = 2.2
AX, AY = 960 + S6 * (1308 - 1555), 540 + S6 * (314 - 268)
c6 = scene("c6", 6, """
    #c6-l1a { top: 400px; } #c6-l1b { top: 570px; }
    #c6-lens { position: absolute; inset: 0; }
    #c6-cam { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
    #c6-cam img { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
    #c6-press { position: absolute; left: 1267px; top: 295px; width: 83px; height: 39px; border-radius: 4px; background: rgba(0,0,0,.4); opacity: 0; }
    #c6-pill { position: absolute; left: 960px; top: 540px; width: 1240px; height: 236px; margin: -118px 0 0 -620px; border-radius: 118px;
               background: var(--ink); box-shadow: 0 26px 64px rgba(11,22,34,.24); transform-origin: 50% 50%; }
    #c6-lab { position: absolute; left: 0; right: 0; top: 486px; height: 108px; display: flex; align-items: center; justify-content: center; gap: 28px;
              font-size: 96px; font-weight: 600; letter-spacing: -0.03em; color: var(--paper); white-space: nowrap; }
    #c6-lab b { display: inline-flex; align-items: center; justify-content: center; width: 88px; height: 88px; border-radius: 50%;
                background: var(--sun); color: var(--ink); font-size: 54px; }
""", f"""    <div id="c6-a" class="clip clipbox" data-start="0" data-duration="2"><div id="c6-l1a" class="ln l2">{words('Când nu e sigur,')}</div><div id="c6-l1b" class="ln l2">{words('întreabă dispecerul.')}</div></div>
    <div id="c6-b" class="clip clipbox" data-start="2" data-duration="4" data-layout-allow-overflow>
      <div id="c6-lens"><div id="c6-cam"><img src="assets/ui/consola_cu_trasee@2x.png" alt="" /><div id="c6-press"></div></div></div>
      <div id="c6-pill"></div>
      <div id="c6-lab"><b>✓</b>Aprobat de dispecer</div>
      <img id="c6-cursor" class="cursor" src="assets/ui/cursor.svg" alt="" />
    </div>""", f"""
      IN(tl, "#c6-l1a", 0.0); IN(tl, "#c6-l1b", 0.1); OUT(tl, ["#c6-l1a", "#c6-l1b"], 1.82);
      // Cardul real din consolă, mare și lizibil.
      tl.fromTo("#c6-cam", {{ x: 960 - 2.6 * 1555, y: 540 - 2.6 * 268, scale: 2.6, opacity: 0 }}, {{ x: 960 - {S6} * 1555, y: 540 - {S6} * 268, scale: {S6}, opacity: 1, duration: 0.4, ease: "expo.out" }}, 2.0);
      tl.set(["#c6-pill", "#c6-lab"], {{ opacity: 0 }}, 0);
      // Cursorul intră de jos și apasă "Aprobă" pe bătaia de la 26,0 s.
      tl.set("#c6-cursor", {{ x: {AX - 28}, y: 1240 }}, 0);
      tl.to("#c6-cursor", {{ x: {AX - 28}, y: {AY - 15}, duration: 0.6, ease: "power3.out" }}, 2.35);
      tl.to("#c6-cursor", {{ scale: 0.84, duration: 0.1, ease: "power2.in", transformOrigin: "21% 11%" }}, 3.0);
      tl.to("#c6-cursor", {{ scale: 1, duration: 0.22, ease: "power2.out", transformOrigin: "21% 11%" }}, 3.1);
      tl.to("#c6-press", {{ opacity: 1, duration: 0.08 }}, 3.0);
      // Clicul aprinde pasul următor: zoom prin buton spre pastila "Aprobat de dispecer".
      tl.to("#c6-cursor", {{ y: 1240, duration: 0.3, ease: "power2.in" }}, 3.22);
      tl.to("#c6-cam", {{ x: 960 - 9 * 1308, y: 540 - 9 * 314, scale: 9, duration: 0.34, ease: "power3.in" }}, 3.2);
      tl.to("#c6-lens", {{ opacity: 0, filter: "blur(10px)", duration: 0.18, ease: "power2.in" }}, 3.38);
      tl.fromTo("#c6-pill", {{ scale: 1.25, opacity: 0, filter: "blur(10px)" }}, {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }}, 3.5);
      tl.fromTo("#c6-lab", {{ scale: 1.2, opacity: 0, filter: "blur(10px)" }}, {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }}, 3.55);
      tl.fromTo("#c6-lab b", {{ scale: 0 }}, {{ scale: 1, duration: 0.32, ease: "back.out(1.7)" }}, 3.65);
      // Pastila crește până acoperă tot: finalul începe pe cerneală (29,0 s).
      tl.to("#c6-lab", {{ opacity: 0, scale: 1.08, duration: 0.15, ease: "power3.in" }}, 5.45);
      tl.to("#c6-pill", {{ scaleX: 2.0, scaleY: 6.0, duration: 0.5, ease: "power3.in" }}, 5.5);
""", "Omul decide: cardul real Nu sunt sigur din consolă; cursorul apasă Aprobă; pastila acoperă ecranul.")

# ---------------------------------------------------------------- c7: rezultatul și logoul (29-36 s)
c7 = scene("c7", 7, """
    #root, #c7-s { background: var(--ink); }
    #c7-s { position: absolute; inset: 0; }
    .p { color: var(--paper); }
    #c7-l1 { top: 452px; }
    #c7-l2a { top: 390px; } #c7-l2b { top: 560px; }
    #c7-src { position: absolute; left: 0; right: 0; top: 760px; text-align: center; font-size: 36px; font-weight: 500; color: var(--paper-2); }
    #c7-lock { position: absolute; inset: 0; }
    #c7-mark { position: absolute; left: 330px; top: 300px; width: 300px; height: 191px; overflow: visible; }
    #c7-name { position: absolute; left: 670px; top: 326px; font-size: 150px; font-weight: 650; letter-spacing: -0.04em; line-height: 1; color: var(--paper); white-space: nowrap; }
    #c7-name span { display: inline-block; }
    #c7-for { position: absolute; left: 0; right: 0; top: 590px; text-align: center; font-size: 52px; font-weight: 600; letter-spacing: -0.02em; color: var(--paper); }
    #c7-team { position: absolute; left: 0; right: 0; top: 676px; text-align: center; font-size: 36px; font-weight: 500; color: var(--paper-2); }
""", f"""    <div id="c7-s" class="clip clipbox" data-start="0" data-duration="7" data-layout-allow-overflow>
      <div id="c7-a" class="clip clipbox" data-start="0" data-duration="1"><div id="c7-l1" class="ln xl p">{words('Aceleași echipe.')}</div></div>
      <div id="c7-b" class="clip clipbox" data-start="1" data-duration="2.8">
        <div id="c7-l2a" class="ln l2 p">{words('Aproape cu jumătate')}</div><div id="c7-l2b" class="ln l2 p">{words('mai mult câștig.')}</div>
        <p id="c7-src" data-value="49">+49% în simulare pe 30 de zile</p>
      </div>
      <div id="c7-c" class="clip clipbox" data-start="3.8" data-duration="3.2">
        <div id="c7-lock">
          <svg id="c7-mark" viewBox="10 18 44 28" aria-hidden="true">
            <defs><clipPath id="c7-hz"><rect x="0" y="0" width="64" height="36.2" /></clipPath></defs>
            <g clip-path="url(#c7-hz)"><path id="c7-sun" style="fill: var(--sun)" d="M18 36a14 14 0 0 1 28 0Z" /></g>
            <path id="c7-route" pathLength="1" d="M16 40h12l8-6h12" style="fill: none; stroke: var(--paper); stroke-width: 5; stroke-linecap: round; stroke-linejoin: round" />
            <circle class="c7-d" cx="16" cy="40" r="4" style="fill: var(--paper)" /><circle class="c7-d" cx="36" cy="34" r="4" style="fill: var(--paper)" /><circle class="c7-d" cx="48" cy="34" r="4" style="fill: var(--paper)" />
          </svg>
          <h1 id="c7-name">{words('Tura de mâine')}</h1>
          <p id="c7-for">Pentru dispecerii Rețele Electrice</p>
          <p id="c7-team">CyberPunks · SmartHack XI 2026 · tema PPC</p>
        </div>
      </div>
    </div>""", """
      IN(tl, "#c7-l1", 0.0); OUT(tl, "#c7-l1", 0.82);
      IN(tl, "#c7-l2a", 1.0); IN(tl, "#c7-l2b", 1.1);
      tl.fromTo("#c7-src", { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power2.out" }, 1.2);
      OUT(tl, ["#c7-l2a", "#c7-l2b", "#c7-src"], 3.62);
      // Logoul: traseul se desenează, soarele răsare pe lovitura finală (32,8 s), apoi pentru cine e și echipa.
      tl.fromTo(".c7-d", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.3, ease: "back.out(1.7)", stagger: 0.1 }, 3.8);
      tl.fromTo("#c7-route", { strokeDasharray: "1 1", strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.4, ease: "power2.inOut" }, 3.85);
      tl.fromTo("#c7-sun", { y: 15 }, { y: 0, duration: 0.9, ease: "expo.out" }, 3.95);
      tl.fromTo("#c7-name span", { opacity: 0, filter: "blur(12px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.5, ease: "expo.out", stagger: 0.08 }, 4.0);
      tl.fromTo("#c7-for", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }, 4.4);
      tl.fromTo("#c7-team", { opacity: 0 }, { opacity: 1, duration: 0.45, ease: "power2.out" }, 4.8);
""", "Rezultatul (din reports/planner/agent_eval.json prin scripts/cifre_film.py; simulare) și logoul, pentru cine e.")

FILES = {"c1-carlig.html": c1, "c2-intrebare.html": c2, "c3-probleme.html": c3, "c4-raspuns.html": c4,
         "c5-produs.html": c5, "c6-om.html": c6, "c7-final.html": c7}
SLOTS = [("c1", "c1-carlig.html", 0, 4), ("c2", "c2-intrebare.html", 4, 4), ("c3", "c3-probleme.html", 8, 4),
         ("c4", "c4-raspuns.html", 12, 3), ("c5", "c5-produs.html", 15, 8), ("c6", "c6-om.html", 23, 6),
         ("c7", "c7-final.html", 29, 7)]


def main() -> None:
    for name, html in FILES.items():
        (COMP / name).write_text(html)
    idx = ROOT / "presentation" / "video" / "index.html"
    s = idx.read_text()
    head, rest = s.split('<div id="root"', 1)
    hosts = "\n".join(
        f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{f}" data-start="{st}" '
        f'data-duration="{du}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>'
        for cid, f, st, du in SLOTS)
    body = f'''<div id="root" data-composition-id="main" data-start="0" data-duration="36" data-width="1920" data-height="1080">
      <div id="bg-ground"></div>
{hosts}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
'''
    head = head.replace("<!-- 120 BPM: o bătaie = 0,5 s = 15 cadre; o măsură = 2 s = 60 de cadre. Vezi STORYBOARD.md. -->",
                        "<!-- Varianta 3, 36 s, 120 BPM: o bătaie = 0,5 s = 15 cadre; o măsură = 2 s. Vezi STORYBOARD.md. -->")
    idx.write_text(head + body)
    print("scrise:", ", ".join(FILES))


if __name__ == "__main__":
    main()
