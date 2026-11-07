# Daybreak, Three.js team: "Planet Daybreak" previs and film (Milestone 1)

Status, 7 Nov 2026: **Milestone 1 (look test)** is done. Six stills with the 2D layer
on, plus a contact sheet. The next step is the animatic, after Teo approves.

Role (parent, 17:40): this Three.js scene is the **previs**. It locks the timing, the
camera path and the whole 2D layer. The final 3D frames will most likely come from
Blender Cycles (the other team), rendered from `camera_path.json`. The film keeps a
clean seam: the 3D layer is a swappable full-frame image sequence, and the 2D layer
reads only `film/assets/tracks.js`.

## Folder map

| Path | What |
|---|---|
| `film/` | The HyperFrames project (30 s, 1920×1080, 30 fps). `index.html` is the root; scenes live in `film/compositions/`. |
| `film/compositions/layer3d.html` | The 3D layer: shows `assets/frames3d/fNNNN.jpg` with frame = round(t × 30). A missing frame falls back to the nearest one. |
| `film/compositions/{storm,probs,ui,routes,ask,dawn,endcard,hud}.html` | The 2D layer, one scene per story beat, cut on the POWER beats. |
| `film/assets/tracks.js` | Generated. Per-frame screen positions of the named 3D anchors, the planet radius in px, and the flat-map drawing at t = 10.1. |
| `film/assets/db2d.js` | 2D helpers: track lookup, plus `DB.drive()`, which updates tracked elements on every render through GSAP modifiers, so it also works on silent seeks. |
| `film/assets/frames3d/` | Generated 3D frames (git-ignored) and `manifest.js`. |
| `film/assets/audio/local/` | Local copy of `power_30s.wav`. Git-ignored, never commit it. |
| `film/stills/` | **Milestone 1 outputs**: `m1_01 … m1_06` PNG at 1920×1080, plus `m1_contact_sheet.jpg`. |
| `camera_path.json` | Generated. Camera and anchors for all 900 frames, for Blender. |
| `planet.html`, `src/planet/*` | The planet previs scene: `painter.js` (flat→sphere bend), `world.js` (layout), `scene.js` (props and state), `timeline.js` (camera keys and events), `main.js` (API). |
| `src/studio.js` | Accumulation renderer, shared with the earlier white-model work. |
| `render/film3d.mjs` | Headless Chrome (Playwright) driver: tracks export, frame renders, probes. |
| `index.html`, `src/main.js`, `src/world.js`, `src/beats.js`, `src/routes.js`, `render/render.mjs` | Earlier white-model work (BRIEF.md), kept as is. Its stills were never finished, because the look changed twice. `gableVolume()` in `src/world.js` is reused by the planet. |
| `render/debug-eval.mjs` | Small debug tool. It loads a page and evaluates an expression. |

## Exact commands

```bash
cd presentation/frames-3d/threejs
npm install                     # three@0.187, playwright-core, gsap@3.15 (uses the installed Google Chrome)

# 1. camera + anchors for all 900 frames  -> camera_path.json, film/assets/tracks.js
node render/film3d.mjs tracks

# 2a. the whole 3D layer (previs quality)  -> film/assets/frames3d/f0000..f0899.jpg + manifest.js
node render/film3d.mjs frames --from 0 --to 899 --step 1 --spp 32 --mblur

# 2b. milestone stills at higher quality (overwrites those frames)
node render/film3d.mjs frames --times 2.0,8.45,10.2,14,23,28.5 --spp 128

# 3. film: check and look
cd film
npx hyperframes lint
npx hyperframes check --json
npx hyperframes snapshot --at 2.0,8.45,10.2,14,23,28.5
npx hyperframes preview --background     # Studio preview with music

# probe one 3D frame without the 2D layer
node render/film3d.mjs probe --t 14 --spp 64 --out /tmp/p.png
```

## Render settings and measured times (M5 Max, Chrome + ANGLE Metal)

- Renderer: progressive accumulation of N raster passes (`src/studio.js`). Each pass
  jitters the key light over a disc (real soft area shadows), uses 2 shadow-casting
  "sky" lights spread over the hemisphere (real sky occlusion), jitters the sub-pixel
  position (AA) and the lens over the aperture (real depth of field), and with `--mblur`
  also jitters the camera over a 180° shutter (camera motion blur). Shadow maps are
  4096 px (key) and 2048 px (sky), with PCF. Tone mapping is AgX, plus a deterministic
  dither.
- Deterministic: no `Date`, timers or `Math.random`. The world comes from seed
  20261107, and every frame is a pure function of t.
- Times:
  - Scene build: about 1 s.
  - 128 spp at 1920×1080: **0.13 s per frame** (the six milestone frames together took
    0.8 s).
  - 32 spp with motion blur, all 900 frames: **29 s of rendering, 38 s wall time**
    including JPEG encoding.
  - `tracks`: a few seconds.
  - HyperFrames `snapshot` of 6 frames: about 1 minute.

## World and camera convention (`camera_path.json`, for Blender)

- **World:** the planet centre is at the origin, +Y is up, and the planet radius is
  1.0. The village is centred on the north pole (+Y).
- **Layout:** the village is laid out flat, in units of 5 m, with the north pole at
  flat (0, 0). It is wrapped onto the sphere at a scale of 1/9 (azimuthal equidistant:
  flat radius r becomes polar angle r/9). The blend factor `f` controls the shape: 1 is
  the planet, 0 is the flat map tangent at y = 1. In between, the sheet curves with
  radius 1/f, which gives the "unroll".
- **Rigid objects:** houses, trees, poles and trucks stay rigid and stand radially on
  the surface. The ground, roads and ribbons bend per vertex.
- **Camera, per frame:**
  - `position` and `target` in world units, world up +Y;
  - `fov`, the vertical field of view in degrees;
  - `shift [sx, sy]`, an off-axis lens shift as a fraction of the half frame (+x moves
    the image content left, +y moves it down). In Blender, with a landscape camera and
    sensor fit Auto or Horizontal: `shift_x = sx / 2` and `shift_y = sy × 0.5 × 9/16`.
    The frustum is left/right = (±1 + sx)·tan(fov/2)·16/9 and
    bottom/top = (±1 + sy)·tan(fov/2), at distance 1;
  - `aperture`, the lens radius in world units.
- **Anchors** (`anchors.<name>.world` and `.px`, with the pixel origin at the top left):
  `fallen_pole`, `meter`, `hot_roof`, `depot`, `unsure_house`, `truck_1..3`, `planet`,
  `sun`, and `pin_<colour>_<k>`. `visible` is false when the anchor faces away from
  the camera.
- **Other fields:** `f` per frame; `sun.position` (the 3D key light comes from there;
  the visible sun disc is drawn in 2D); `key` (light direction, Kelvin, intensity).
- **Swapping the 3D layer for Blender:** render the frames as
  `film/assets/frames3d/fNNNN.jpg` from the same camera, and regenerate `manifest.js`.
  If the camera changes, export a matching `tracks.js` (same format). The 2D layer does
  not change.

## Film timeline as built (beats from `cues_populare.json`, key `power`)

| t (s) | 3D | 2D |
|---|---|---|
| 0–3.3 | The planet fades in from navy, small and far, and the orbit starts. Night, warm windows. | "22:00 · Night shift" clock. The ring text "STORM HITS BANAT." orbits the planet like a Saturn ring: back half dimmed and hidden behind the disc, one word per beat (0.186 / 0.975 / 1.741), the rest of the ring on 2.531. |
| 3.3–6.4 | The cloud slides in. The pole falls on 4.087. Homes go dark in 4 groups (3.297 / 4.087 / 4.876 / 5.642). | "Homes go dark." appears one word per beat, then dims on 5.642. |
| 6.4–9.47 | The orbit speeds up. | Tracked labels on 6.432 / 7.221 / 7.987: "Fallen poles." (orange), "Stolen power." (cyan), "Too much sun." (blue). On 8.777, "Where do crews go first", and the orange thread runs from the fallen pole and curls into the "?". |
| 9.474 | Whip to top-down. The planet unrolls (9.543–9.98). | The console slams in, the "Daybreak" wordmark lands and docks in the header. The cursor clicks "Plan tomorrow" on 9.543, which ignites the PPC map (registered to the flat 3D map: navy disc, cyan roads, white houses, orange depot) and fills the crew cards. |
| 10.3–16.6 | The map rolls back up (10.309–11.099). Three satin ribbons draw from the depot. Pins drop on 12.655 / 13.444 / 14.210 / 15.000. The trucks follow. | "Every crew knows / where to go." Crew chips tracked to the trucks. A ripple ring on each pin. |
| 16.6–20.5 | The camera slows onto the "unsure" house with shallow depth of field. | The "Not sure? It asks you." card pops on 17.345 with Approve / Skip. The cursor enters on 18.111 and clicks Approve on 18.901. The card collapses into the cyan pin that drops on the house, and the orange truck turns into that street. |
| 20.5–25.9 | Daybreak: the warm sun light rises, the windows come back on in a sweep, the camera goes low. | "06:00 · Morning". A PPC-orange sun rises from behind the planet's limb (masked by the disc). On 22.012: "+49%", then "Same crews. More value." and "30-day simulation". |
| 25.9–30 | Fast pull-back, then an ease. The planet shrinks to a point. | Match cut: the planet becomes the orange sun dot (26.9). "Daybreak" on 27.446. "For Rețele Electrice dispatchers" and "CyberPunks · SmartHack 2026" on 28.235, held to 30 s. |

## Honest flaws in Milestone 1

- The 3D is previs, not premium. The houses are simple boxes with tiles but no
  texture. The night ground is dark with faint streaks from the sky shadows. The trees
  are low-poly balls. The cloud is a soft grey blob, not cotton. It does **not** meet
  the concept-sheet bar; that is the Blender layer's job.
- At 8.45 s the cloud covers the fallen pole that its label points to. There is also a
  faint stray horizontal line near the top of that frame (not yet traced; probably the
  cloud's rain or suspension wire).
- The question "Where do crews go first?" is on screen for only 0.7 s before the drop
  (the spec's beats), and the check warns that it is short. The closing line holds
  1.7 s (the spec asks for 1.5 s; the check asks for 2 s).
- The small UI chrome text (tabs, "Ready", the clock label) is under the check's 28 px
  phone floor. That is fine for a projected film, but it is listed.
- The 9.8 s still was taken at 10.2 s, where the unroll is finished. At 9.8 s the map
  is still mid-unroll.
- The real console has no "Plan tomorrow" button (it says "Rulează agentul") and is in
  Romanian. The film uses the spec's English wording, in a simplified layout.
- Not loaded yet for the animatic: `cut-the-curve`, `seam-craft`, `apple-design`,
  `launch-video` and the GSAP skills, plus the seam ledger (`ledger.json`) and the
  seam gate. Milestone 2 does those.
