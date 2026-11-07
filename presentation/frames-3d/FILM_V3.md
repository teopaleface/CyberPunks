# Daybreak film v3: the approved script (Teo, 19:20, 7 Nov 2026)

Teo rejected the 30 s animatic ("I don't understand the purpose, what it does, how it works").
This is the approved, concrete script. English voice-over + the same key line on screen +
the POWER instrumental under it. Premium quality is the bar; time budget up to ~5 hours.

## Script (VO = what the voice says; SCREEN = the big on-screen line)

| # | VO | SCREEN | Picture |
|---|---|---|---|
| 1 | A storm hits Banat. | A storm hits Banat. | The tiny-planet village at night, the cotton storm cloud crossing it |
| 2 | Poles fall. Houses go dark. | Poles fall. Houses go dark. | A pole snaps across the road; house windows switch off one by one |
| 3 | Meters get tampered with. Rooftop solar overloads the grid. | Meters get tampered with. / Rooftop solar overloads the grid. | Close: a meter with a magnet on a house wall; then rooftop solar under a blazing sun |
| 4 | Tomorrow, eleven crews must fix five hundred and fifty-six problems. | 11 crews. 556 problems. | Wide planet: 556 problem markers light up; 11 trucks waiting in the depot |
| 5 | Where should each crew go? | Where should each crew go? | Markers blink, trucks stay still (stillness before the drop) |
| 6 | Daybreak plans it for you. | Daybreak | Name lands on the music drop; the planet unfolds into the app's map |
| 7 | It finds the problems, | It finds the problems. | The map (a top-down view of the same village): meter data and weather alerts light up the problem spots |
| 8 | puts the urgent ones first, | Urgent ones first. | Markers re-order and colour by urgency (urgent = PPC orange) |
| 9 | and plans the shortest route for every crew. | The shortest route for every crew. | One coloured route per crew draws across the map; crew cards fill in |
| 10 | Is this meter really tampered with? When Daybreak isn't sure, the dispatcher decides. | Is this meter really tampered with? / Not sure? The dispatcher decides. | Close on the suspicious house; a card "Send a crew? Approve / Skip"; the cursor clicks Approve |
| 11 | Crews leave at daybreak. | Crews leave at daybreak. | Dawn on the planet: the orange sun rises behind the curved horizon, trucks drive out on their routes |
| 12 | Thirty percent less driving. Fewer wasted trips. | 30% less driving. / Fewer wasted trips. | Big numbers; small line "30-day simulation" |
| 13 | Daybreak. Tomorrow's crews, planned tonight. | Daybreak / Tomorrow's crews, planned tonight. | Name, the orange sun dot; small: For Rețele Electrice dispatchers · CyberPunks · SmartHack 2026 |

Facts (do not change): 11 crews and 556 problems are the console's synthetic demo scenario;
30% less driving = 352 vs 515 km/day; fewer wasted trips = 37% vs 63% wasted visits against
the "first come, first served" strategy; both from `reports/planner/agent_eval.json`, a 30-day
synthetic simulation. Always show "30-day simulation" under the numbers.

## Audio (the clock)

- VO: English, calm, confident, premium (Kokoro TTS, local, Apache-2.0). The VO timing drives
  every cut; word timestamps from whisper.cpp (large-v3-turbo, local).
- Music: POWER instrumental (local only, never in git or in versioned exports), ducked under the
  voice; the drum drop lands on line 6 ("Daybreak plans it for you").
- Optional subtle SFX (local, procedural): cursor clicks, clock ticks, pin drops, a whoosh on the
  drop zoom.

## Look

- Same world and quality bar as `../frames-codex/v7/concepts/concept_sheet.jpg` (the
  handmade tiny-planet miniature, PPC palette: navy #000F1E, orange #FA4616, cyan #00A3E0,
  electric blue #163FE8).
- Premium AI plates per scene (consistent village, layered for 2.5D parallax), upscaled for
  crisp 1080p with camera pushes; the real 3D objects (`objects/`) fly over them.
- 2D layer from the style frames (`styleframes/README.md`): big Archivo type in a left column,
  pings + leaders, solid pills, the product window, the cursor, the orange dot.
- Motion rules from `MOTION_SCRIPT.md` (current UP, velocity-matched seams, zoom-through at the
  drop, rack focus into the close-up, inverse zoom for arrivals, stillness before the drop, no
  crossfades/glow/idle wobble). The seven old seams are replaced by this script's scenes.
