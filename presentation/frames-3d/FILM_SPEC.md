# Daybreak launch film: "Planet Daybreak" (approved by Teo, 17:25, 7 Nov 2026)

This is the master prompt for building the film. Teo approved the concept in
`FILM_IDEAS.md` ("Planet Daybreak", with the night-shift clock, the 2D→3D pop-up map,
the single orange thread and the UI cards in the air). Read that file too.

## 1. One-sentence film

A tiny handmade planet of a Banat village spins in the night: a storm knocks it out,
Daybreak turns the night into one plan, and the sun rises over the planet as every crew
rolls out.

## 2. Hard constraints

- **Length:** exactly 30.000 s, 30 fps, 1920×1080, to the music cut
  `presentation/music/populare/power_30s.wav` (Kanye West, "POWER", instrumental; local
  use only, never commit it, never put it in a versioned export).
- **Beats (seconds, from `presentation/music/populare/cues_populare.json`, key `power`):**
  0.186 0.975 1.741 2.531 3.297 4.087 4.876 5.642 6.432 7.221 7.987 8.777 **9.474 = the
  drums drop** 9.543 10.309 11.099 11.865 12.655 13.444 14.210 15.000 15.766 16.556 17.345
  18.111 18.901 19.690 20.457 21.223 22.012 22.779 23.568 24.334 25.124 25.890 26.680
  27.446 28.235 29.025 29.791. Big hits near 12, 15.5 and 22 s; a short breath near 18.5 s.
  Every cut, pop, click and text entrance lands on a beat (±1 frame).
- **Palette, inspired by PPC (mandatory):** night/void `#000F1E` (PPC navy); hero accent
  `#FA4616` (PPC orange: hi-vis vests, trucks, the orange thread, the sun at daybreak);
  AI/data accent `#00A3E0` (PPC cyan: pins, agent markers, UI highlights, ribbon 2);
  ribbon 3 `#163FE8` (PPC electric blue). Text white `#F5F7FA` on navy. Everything else
  comes from the miniature's own materials (whitewash, terracotta, sunflower yellow,
  walnut). No PPC logo, no PPC font.
- **Look:** the painted 1:87 miniature from `BRIEF_S1.md` (master model maker, real
  macro depth of field), now built on a small sphere. Bans from
  `../frames-codex/v2/BRIEF.md`: no purple/pink mood, no neon, no bloom/glow halos, no
  lens flare, no glassmorphism, no toy-plastic shine, no text in 3D.
- **Text (English only, at most 5 words per line), set in code with Archivo** (local
  font: `presentation/video/assets/fonts/Archivo-*.woff2`, variable width and weight).
- **Truth:** the only number is +49% (from `reports/planner/agent_eval.json`, ~48.9% more
  value than the best simple strategy in a 30-day synthetic simulation); show it as
  "+49%" with the small line "30-day simulation". "Storm hits Banat." refers to the real
  8 July 2025 red-code storm; never invent a count of homes.
- **Motion:** load and follow `motion-doctrine` (one continuous camera, no slides stuck
  together), `cut-the-curve`, `seam-craft`, `oversized-cursor`, `hyperframes`,
  `hyperframes-cli`, `apple-design`, `launch-video`, and the GSAP skills for the 2D layer.
  Feel: After Effects/Premiere: speed ramps, whip transitions with motion blur,
  zoom-throughs, masked text reveals, text on a circular path, rack focus, trim-path line
  draws, 2D labels tracked to 3D points, match cuts on round shapes (planet → sun → the
  "o"). No idle wobble; motion always does something.

## 3. The world

- **Planet:** the village from BRIEF_S1 wrapped around a sphere (the classic tiny-planet
  look): houses, trees, poles stand radially on the surface; the main road and 3–4 side
  streets curve around it; a sunflower field on one side, the depot with five trucks on
  another. The planet floats in navy space; soft, warm studio light on it, so it reads as
  a real model, not a CGI globe.
- **Planet ⇄ flat map morph (the signature):** build the village on a flat plane and wrap
  it onto the sphere with one blend factor (flat position → spherical position, per
  vertex/instance). Factor 1 = planet, 0 = flat map. Animating the factor unrolls the
  planet into a flat map and rolls it back. The flat state is restyled as a clean 2D map
  in PPC colours (navy ground, cyan roads, white house footprints) by crossfading
  materials/overlay, then it matches the real Daybreak UI map.
- **Lights:** each house has a warm window light that can switch off/on individually;
  trucks have headlights; one "sun" light orbits/rises for daybreak; a moon-cool key for
  night.
- **Anchors for 2D:** named 3D points (fallen pole, tampered meter, hot roof, depot, the
  "unsure" house, each truck) whose screen positions drive the 2D labels every frame.

## 4. Timeline (30 s)

| t (s) | 3D | 2D | Sound |
|---|---|---|---|
| 0.0–3.3 | From navy, the planet fades in, small and far; slow orbit begins (orbit 1, night). Moon-cool light, warm windows. | "22:00" small top-left (night-shift clock). "Storm hits Banat." types on a circular path around the planet (ring text), beat by beat. | choir intro |
| 3.3–6.4 | The storm cloud (cotton wool) slides over; a pole snaps (fall on 4.087); houses switch off one by one on 3.297, 4.087, 4.876, 5.642 as they come round the planet's edge. | "Homes go dark." | |
| 6.4–9.47 | Camera speeds up (ramp); three anchors light up. | Tracked labels pop on beats 6.432 / 7.221 / 7.987: "Fallen poles." (orange tick), "Stolen power." (cyan), "Too much sun." (electric blue). On 8.777: "Where do crews go first?" big, centred; the orange thread appears from the fallen pole's wire and curls into the question mark. | build-up |
| 9.474 | **Drop.** Whip to top-down; the planet unrolls into the flat PPC map (factor 1→0 in ~0.6 s, eased). | The flat map snaps into the real Daybreak UI layout (map left, three crew cards right, "Plan tomorrow" button). Oversized cursor already in place clicks on **9.543**. "Daybreak" lands (wordmark, white). | drums |
| 10.3–16.6 | Map rolls back up into the planet (orbit 2, work lights). Three satin ribbons draw along the curved roads from the depot (orange, cyan, electric blue), pins drop on houses on beats 12.655 / 13.444 / 14.210 / 15.000; trucks drive along their ribbons. | "Every crew knows where to go." Small crew chips follow the trucks (tracked): "Crew 1 · 4 stops" style, no other numbers. | big hits 12, 15.5 |
| 16.6–20.5 | Camera slows and racks focus onto one house (the "unsure" one), shallow depth of field. | A card in the air beside the house: "Not sure? It asks you." with buttons "Approve" / "Skip"; oversized cursor clicks Approve on **18.901**; the card collapses into a cyan pin that drops on the house; a truck turns towards it. | breath ~18.5 |
| 20.5–25.9 | Orbit 3, daybreak: the orange sun rises behind the planet's curved horizon; the day/night line sweeps across the village; windows switch back on; long warm shadows. | "06:00" replaces "22:00". On 22.012: "+49%" big (PPC orange), "Same crews. More value." under it, tiny "30-day simulation". | big hit 22 |
| 25.9–30.0 | Camera pulls back fast then eases; the planet shrinks to a bright point that becomes the sun dot above the wordmark (match cut). | "Daybreak" + "For Rețele Electrice dispatchers" + small "CyberPunks · SmartHack 2026". Hold the last 1.5 s. Music ends. | outro |

## 5. Architecture

- One HyperFrames project at `presentation/frames-3d/threejs/film/` (its own project; do
  not touch `presentation/video/`, which belongs to another agent).
- The 3D layer is a Three.js scene (or, if the Blender path wins the look test, a
  rendered image sequence plus a per-frame `tracks.json` of anchor screen positions). The
  2D layer (type, UI, cursor, labels) is HTML/GSAP on the same timeline.
- Deterministic: every frame a pure function of t (seeded PRNG, no Date/timers).
- The UI beat is a faithful, simplified recreation of the real Daybreak console (read the
  real UI in `web/` for structure and wording; English labels; PPC palette for the film).
- Music copy for rendering goes to `film/assets/audio/local/` with its own `.gitignore`
  (`*` and `!.gitignore`).

## 6. Milestones (show Teo at each)

1. **Look test (stills first):** the planet world and six stills at 1920×1080 from the
   timeline, with the 2D text on: t≈1.5 storm/ring text, t≈7.5 tracked problem labels,
   t≈9.8 the unrolled map/UI with cursor, t≈14 ribbons and trucks, t≈23 daybreak +49%,
   t≈28.5 end card. Contact sheet. Stop and report.
2. **Animatic:** full 30 s at 960×540 with music, every beat placed.
3. **Final:** 1920×1080, 30 fps, H.264 yuv420p, AAC, −14 LUFS-ish, to
   `presentation/frames-3d/threejs/film/renders/local/daybreak_30s.mp4` (git-ignored,
   because it contains the commercial track). Also a music-free export for the repo.

## 7. Quality bar (Teo, 17:40: "no slop, as high quality as possible, premium")

- **The bar is `../frames-codex/v7/concepts/concept_sheet.jpg`** (planet_storm, planet_routes,
  popup_map, planet_dawn). The film must look at least that good in every frame. A render
  that looks like a game engine, a toy or a default CGI scene is a fail.
- **Pipeline for premium quality:** the Three.js scene is the previs/animatic (it locks
  timing, camera path and the 2D layer fast). The final 3D layer is rendered in **Blender
  Cycles** from the same camera path: Three.js exports per-frame camera + anchor data as
  `camera_path.json`; Blender imports it and renders the frames; HyperFrames puts the 2D
  layer on top. Swap to Three.js finals only if its renders truly match the bar.
- **Realism levers (Blender):** CC0 PBR textures and HDRIs from Poly Haven (terracotta
  roof tiles, limewash plaster, gravel, asphalt, bark, walnut wood, grass), real hair-
  particle flock grass and moss, foliage with translucency, slightly irregular hand-made
  geometry (no perfect grids, every house a little different, tiles not perfectly aligned),
  real depth of field with a short focus distance, AgX, denoise, enough samples for clean
  shadows. Light like the concept images: warm key, cool fill, navy void.
- **Every still gets a hard review before it is shown:** would a photo editor believe it is
  a photograph of a real handmade model? Any CGI tell (plastic shine, repeated identical
  objects, flat lighting, aliasing, noise) means it is not done.
