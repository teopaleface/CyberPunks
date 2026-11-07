# Daybreak film: motion script (transitions and effects, decided up front)

18:45, 7 Nov. Teo: "think ahead, the effects and transitions must be premium". This file is
the binding motion plan for `threejs/film/`. It applies `motion-doctrine` (vector law, one
current, carriers, causal motion, stillness before climax, no idle wobble) and `cut-the-curve`
(the techniques and their numbers). Write `film/ledger.json` from the seam table below, stamp
the seams, and run the Seam Gate (`node ~/.claude/skills/motion-doctrine/scripts/seam-gate.mjs
verify --ledger ledger.json --project .`); a seam is done only when it passes.

## The current: UP

The film rises from night to daybreak, so the dominant vector is **upward**. Reserved vectors
are spent only on meaning: **Z push (zoom-through)** once, at the drop, when we dive into the
plan; **Z pull (inverse zoom)** for arrivals (the map rolling back into the world, "+49%", the
wordmark); **rack-focus blur-cut** once, at the "ask" close-up. Transition vocabulary = these
three plus hand-authored morphs. No crossfades anywhere.

## Seam ledger (30 fps; times on POWER beats)

| # | t (s) | From → to | Technique | Carrier | Numbers |
|---|---|---|---|---|---|
| 1 | 3.297 | "Storm hits Banat." → "Homes go dark." | waterfall cut UP (per word) | the word group | travel 230 px, exit 0.34 s power4.in + 0.18 s fade, stagger 0.022 s; entry 0.30 s power4.out from opacity 0.35, gaps 0.05 s × 0.84 |
| 2 | 7.987 | three problem labels → "Where do crews go first?" | waterfall cut UP | the labels' word groups | as #1 |
| 3 | 9.474 | planet → product UI | **zoom-through (push)** + morph | the 3 problem objects fly onto the flat map as stop pins | exit planet scale 1→1.2, blur 0→18 px (full frame), 0.2 s power3.in; cut; UI window + wordmark 0.75→1, blur 18→0, 0.5 s expo.out; map unroll (factor 1→0) inside the exit |
| 4 | 11.099 | UI → planet (map rolls back up) | **inverse zoom-through (pull)** + morph | the flat map itself re-wrapping | exit UI 1→0.8, blur 0→18, 0.2 s power3.in; planet arrives 1.25→1, blur 18→0, 0.5 s expo.out; no grow-from-small intros inside cut+0.5 s |
| 5 | 16.556 | planet wide → close on the "unsure" house | **rack-focus blur-cut** (the one visible cut) | the house | outgoing stays opaque; blur spike to 10 px power2.in, cut at peak, 1.06 lens breathing, entry power2.out ≥ exit |
| 6 | 20.457 | ask → dawn | cut-the-curve UP | the sun disc (enters rising) | exit y 0→−230, 0.3 s power4.in, fade done at 30%; entry y +230→0, 0.34 s power4.out from opacity 0.35 |
| 7 | 25.124–25.890 | dawn → end | Z pull: camera pulls back, planet shrinks into the orange dot (morph) | the planet → dot | planet 1→0.06 over 0.77 s power3.in, final 0.15 s swap to the solid #FA4616 dot at small size |

Stage ground (#root) opaque navy everywhere (seam-craft: no white flash).

## Beat by beat: what performs (no idle wobble; every phase has a route)

**0.0–3.3 · Cold open (route: camera with intent + staged reveals)**
- 0.0–0.975: the clock bezel draws itself clockwise from 22 (trim path, 0.8 s power3.out); ticks
  pop in sequence (stagger ≤0.4 s). The planet focuses in inside it (blur 12→0, scale 0.96→1,
  0.9 s expo.out). Camera starts a slow orbit + push (scale 1→1.06 over 9 s, eased).
- "Storm" / "hits" / "Banat." arrive as a **waterfall entry from below** on 0.975 / 1.741 / 2.531
  (binary opacity, power4.out; anchor word heavier: y 70 px, 0.18 s; split "Banat." into
  "Ban" + "at." for the climax).
- The cloud enters from the right and crosses (3D).

**3.3–7.99 · The night (route: sequenced life)**
- On 3.297 / 4.087 / 4.876 one house goes dark each beat: in 3D the windows switch off; in 2D a
  ring collapses onto the house (circle 40→0 px, 0.25 s power3.in) on the same frame (causal).
- The clock **ticks** on each beat: the progress arc and the moon marker step forward with a
  tiny overshoot (back.out(1.6), 0.18 s). The live time label rolls its digits (odometer, 0.2 s).
- 5.642 / 6.432 / 7.221: the 3D objects (pole, meter, solar) **tumble out** of their anchors
  towards camera on curved paths (tumble frames, baked motion blur), at three depths (the
  solar one big and close, half out of frame). Each **lands** on its beat → its leader line
  draws (0.25 s power3.out) → its label snaps in (waterfall entry) → one ping ring fires
  (0→1 scale, 1→0 opacity, 0.5 s expo.out, once). Strict cause → effect, same frame starts.

**8.0–9.47 · The question and the comma**
- 7.987: question arrives (seam #2). The "?" is set in white; its **dot is a solid PPC-orange
  circle** that drops in on 8.777 with a small squash (scale y 0.85 → 1, 0.12 s).
- **8.9–9.474: stillness before climax.** The camera eases to a near stop (speed ramp), the
  clock holds, nothing new enters. Let the music build carry it.

**9.474–11.1 · The drop (route: cursor-led action)**
- Seam #3 on the drop. The three objects shrink and land exactly on the flat map as the pins
  of their stops (carrier), the UI window resolves around them with the giant "Daybreak"
  wordmark and the tagline (waterfall entry, after the seam settles).
- The oversized cursor is already resting on "Plan tomorrow". **Click on 9.543:** button
  squash (0.94, 0.06 s) → spring release (back.out(1.6)) → click rings expand → on the same
  frame the three routes **draw along the map** (trim path, 0.45 s power3.out, staggered
  0.06 s) → stop pins drop with a small bounce (back.out(1.5)) on 10.309.
- Crew cards on the right fill in (waterfall entry, 0.05 s gaps) as their routes complete.

**11.1–16.5 · Every crew knows where to go (route: camera with intent + staged reveals)**
- Seam #4: the map rolls back into the planet (pull).
- Ribbons draw along the curved roads (3D), trucks move along them; crew pills arrive from
  below on 12.655 / 13.444 / 14.210, tied to their trucks by drawn leaders; pins drop on the
  beats with a small bounce. The headline enters as a waterfall entry on 12.655.
- The clock arc **grows continuously** to 01:00 (sequenced UI life).
- Camera: orbit continues and rises (we are now looking down on the plan).

**16.56–20.45 · Not sure? It asks you (route: cursor-led action)**
- Seam #5 (rack focus) into the close-up of the house.
- 16.9: headline waterfall entry (left column, solid navy third). 17.345: the card arrives from
  below (binary opacity, power4.out 0.18 s), the 3D meter spins slowly beside it (spin frames).
- The cursor **enters from off-screen right** (oversized-cursor law), travels an arc to
  "Approve" (0.6 s power2.inOut), then **holds 0.4 s** (dramatic comma).
- **Click on 18.901:** squash → the card **collapses into the cyan pin** (shared-element morph,
  0.35 s power4.in along a path to the house) → the pin hits the house (squash + one ping) →
  the truck turns towards it (3D). Same-frame ignition at every step.

**20.46–25.1 · Daybreak (route: staged reveals)**
- Seam #6 (cut-the-curve UP). The giant orange sun **rises** from behind the planet's horizon
  (y +300→0, 1.2 s power2.out), the day/night line sweeps the village (3D), windows come on.
- The time label rolls 01:00 → 06:00 (odometer, digits staggered).
- **22.012: "+49%" arrives as an inverse zoom-through** (1.25→1, blur 10→0, 0.5 s expo.out)
  while its digits count up from +0% (0.5 s expo.out, tabular figures).
- "Same crews." on 22.779, three PPC-orange 3D hard hats pop in at three depths on 22.779 /
  23.568 / 24.334 (back.out(1.4), 0.2 s); "More value." on 24.334; "30-day simulation" snaps in
  with it (small, muted).

**25.1–30.0 · End (route: arrival + hold)**
- Seam #7: every word exits upward (waterfall cut), the camera pulls back, the planet shrinks
  into the orange dot (25.890).
- **26.680: "Daybreak" arrives as an inverse zoom-through** (1.25→1, blur 10→0, 0.5 s expo.out).
- 27.446: "For Rețele Electrice dispatchers" and the credit line arrive (waterfall entry).
- Hold, completely still, to 30.0 (≥2.5 s). The music ends.

## Effects rules

- **Motion blur:** the 3D layer renders with real motion blur (shutter 0.5). 2D elements get
  blur only at peak velocity, per cut-the-curve (10 px text, 18–20 px full-frame), on the
  wrapper, never on children.
- **Speed ramps** on the camera: fast hook (0–3 s), slow on the night ticks, near stop at
  8.9–9.47, whip at the drop, steady through routes, slow at the ask, rising at dawn, fast
  pull at the end.
- **Banned:** idle float/breathe/pulse loops, glow, bloom, lens flares, film grain overlays,
  light sweeps on type, bounce.out / elastic.out, gradient text, crossfades.
- **Optional SFX** (made locally, no licences): a soft click on each cursor click, a light tick
  on clock ticks, a short whoosh on the drop zoom, a "tock" on pin drops, mixed well under
  POWER (−18 dB relative).
