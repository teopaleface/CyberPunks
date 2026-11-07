# Daybreak light

A separate visual rework of the supplied `daybreak_v3_draft.mp4`, using the supplied Trust film as a motion and composition reference. It preserves the 52.9-second narration clock. The original MP4 and the presentation worktree were not edited.

The film uses white backgrounds, natural-width Archivo, existing transparent 3D objects and fresh, read-only captures of the real console at `http://localhost:3711`. Captures use a 1920×1080 CSS viewport at 2× pixel density. The console's Romanian labels remain unchanged; the film's narration and headlines are English.

The current scenario contains 689 incoming jobs and 11 crews. Voice lines 4 and 9 were regenerated with the same local Kokoro `af_heart` voice, replacing the stale count and the absolute shortest-route claim. Their speech was independently transcribed with Whisper. Existing narration, music and sound effects were reused. The approval click was aligned to 35.55 seconds.

The approval sequence is an animated demonstration using the real pending screen and an excerpt of the actual success message in `web/components/detail/review-actions.tsx`. No approval, agent execution or API mutation was submitted to the running application.

## Open and render

```sh
cd presentation/daybreak-light
npx -y hyperframes@0.9.19 preview --background --port 3742 --no-open
npx -y hyperframes@0.9.19 check --json
npx -y hyperframes@0.9.19 render --quality delivery --fps 30 -o ../../materiale/daybreak-redesign/daybreak_light_v2.mp4
```

Editable scene files are in `compositions/`. `build.py` regenerates those files and the timing ledger; after running it, stamp the master seams with the installed motion-doctrine skill's `seam-stamp.mjs`. `build_audio.py` uses the original local stems and installed Kokoro model files. All audio containing the original commercial song stays in ignored `assets/local/`; the local MP4 stays in ignored `materiale/`.

## Provenance

- Real UI: root checkout on branch `Teo`, running on port 3711, captured read only during this task. The UI worktree's separate port 3710 was not used in the film.
- 3D objects, Archivo and local GSAP: reused from the existing `Teo-prezentare` film project. Archivo's license accompanies the font files.
- Cursor geometry: adapted from HyperFrames registry's `agent-cursor` component.
- Result: `reports/planner/agent_eval.json`, 30-day synthetic evaluation, 350.5 km/day for the agent versus 514.62 km/day for first come, first served. The approximately 30% headline rounds down from 31.9%.
- Voice: existing local Kokoro-82M / kokoro-onnx setup, `af_heart`, speed 0.93, with short timing adjustments to match the supplied narration slots.

Skills consulted: HyperFrames, HyperFrames CLI and registry, media-use, motion-doctrine, cut-the-curve, seam-craft, oversized-cursor, Apple design, Apple launch film, frontend design, reference-to-motion, GSAP core/timeline/performance/utils, motion-effects and milestone-reveal. Their generic interview and template defaults were replaced by the supplied script, audit and explicit request to make the new version.
