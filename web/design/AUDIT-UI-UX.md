# Daybreak UI/UX audit

7 November 2026. The product UI is English. Chat and project notes may remain Romanian.

## What was wrong

The earlier pass aligned fonts and colours but kept controls without checking whether they helped a dispatcher. This revision audits the task each element supports.

1. **The desktop header repeated context.** “Consola dispecerului” described the page without helping a decision. Global search competed with page-specific filters and navigation. Both are removed, together with the desktop header. The page now starts 72 px higher. Daybreak remains in the sidebar; mobile retains a compact brand and menu bar.
2. **The workspace mixed operations with presentation tools.** The main menu now has five operational destinations. Activity, models and agent runs sit under “Agent tools”. Demo remains a route but is removed from everyday navigation. Account and data source information stay in the sidebar footer.
3. **The home screen repeated controls and tutorial copy.** Generating another plan belongs in the agent tools, not beside every approval. Home keeps the proposed assignments, the next review case and the plan summary. Empty plans retain a way to run the agent.
4. **Two filters did the same job.** Crews and routes selected the same content and opened the same destination. They are consolidated into one visible option, with old query links retained.
5. **Technical evidence competed with action.** Review pages put reasons and decisions first. Model details and evidence remain available on demand. Operational facts, safety warnings and synthetic-data labels are preserved.
6. **The landing repeated claims and screen previews.** Static mock screens and the unvalidated claim that one rule works in three countries do not demonstrate the actual product. They are removed from the main reading flow. Input requirements, model evidence and the real workspace remain accessible.
7. **Presentation copy and forced scrolling slowed reading.** Landing sections use standard page scrolling. Product copy states what the system does, and avoids claims beyond the available evaluation.
8. **The product mixed languages.** Page copy, navigation, dialogs, accessibility labels, formatting and known generated explanations are presented in English. Contract field names, IDs, links, model outputs and source data remain unchanged. Place names retain their proper spelling. Original research documents may remain in Romanian and are identified as source material.

## Verification

The integrated Next build, TypeScript, ESLint, 76 tests and whitespace checks pass. The landing build also passes; its existing bundle-size warning remains.

Twenty active routes were checked in the browser at 1440 px and 390 px, including the three case types and expanded evidence. All use `lang="en"` and fit without horizontal overflow. Final screenshots were inspected for the landing, plan, review queue and mobile plan. The three original research download links contain non-empty Markdown and explicitly identify the Romanian source language.

Known source templates are translated at display boundaries. Unknown future explanations and user-written notes remain unchanged rather than receiving invented translations. Proper place names retain their original spelling.

Verification is local, against the existing planner API, without running the agent, submitting reviews, approving plans or sending messages. Browser viewport checks are not physical-device testing. Printing and authentication writes were not exercised.

## Scope

No deployment, authentication logic or model/planner changes are authorised by this UI task. The existing black, yellow, Geist and Unbounded identity is retained. This audit does not claim physical-device acceptance or a full accessibility certification.

## 8 November 2026, 03:10 Bucharest: legacy-screen cleanup

This pass follows Teo's screenshots and preserves the original fourteen screens. It uses the captured dispatcher screens in `/tmp/daybreak-v3-dispatcher-*.png` and the current source. Those captures show the pre-change UI; they are not acceptance evidence for the changes below. The main agent owns final browser verification, light/dark and mobile checks, and an isolated production build. No runtime was restarted and no live API was called during this pass.

### Findings and fixes

- Model evaluation used a twelve-column grid with cards occupying only six, three or seven columns. Most model-table cells were deliberately blank, and long metric names shared a narrow label column. Each source now has its own comparison card with the report's primary metric, model value, baseline and direction. The A card also shows the SGCC result separately. The cards follow the current reports rather than copied demonstration numbers.
- The large green percentage looked like an economic result already achieved. The agent comparison is now a secondary, full-width card with simulated RON per day for both strategies. Its label states that these are simulated values, not realised savings or revenue. All strategy outcomes and source totals remain available on demand, with totals distinguished from daily averages.
- Error analysis had a fixed-height vertical scroll inside a card. Each model now has a concise limitation card, expandable failure cases and its complete Romanian source download. Scrolling stays with the page. All A/B/C, simple-baseline, agent and error filters remain. A narrowed filter can use wider cards; a single result fills the grid.
- Full model reports previously shared three narrow columns. Each full report now opens across the page. Metric tables and source comparison charts scroll horizontally within their own region on narrow screens. Full JSON downloads, source data, reproduction commands, the SGCC versus subtle-anomaly distinction, storm PR-AUC and voltage MAE remain accessible. The energy-balance report retains its synthetic-data warning, confusion matrix, fusion caveats and baseline definitions. Missing test counts no longer display an assumed zero.
- Daily plan spent excessive vertical space before routes and the schedule. Summary and approval cards have less padding and shorter copy. The route timeline now follows map and crews before optional alerts and meter evidence. The detail area starts open; the real map, crews, schedule and all existing filters remain available. Approval still comes only from the server audit.
- Review queue reasons were truncated in the narrow list. Location and reason can wrap; only the table scrolls horizontally on a small screen. Case selection, reason filters, pagination and the existing review controls are preserved.
- Decision history devoted nine columns to mixed operational and technical data. Seven visible columns now give more width to the reason; model version, thresholds and the full trace are in the expanded record. Human rows have a restrained highlight and direct author filters use actual record counts. The original events, download and author attribution are unchanged. A human field verdict is not automatically labelled an AI correction.
- Alert cards forced large numbers, icons and several facts into narrow rows. Their fact blocks now respond to the card's width. The full prosumer message opens on demand, with its unsent status and copy action visible. Draft status is distinct from a console alert. Planned message time does not imply delivery. Full alert and message lists remain available, with a single-column reading layout when space is limited.
- Run history still offered a legacy run action that is intentionally denied by the current server action. That control now opens the assistant without an operational write or a success toast. This screen says it shows saved results and recorded report timings. Model scores, stages, current rules, history and read-only parameters remain available. It makes no new-inference claim.
- Assigned content pages now share a 1440 px maximum width, 32 px desktop side padding and 16 px mobile side padding. The shared disclosure control wraps its hint and has a visible keyboard-focus outline. The shared card grid no longer stretches unrelated cards to the tallest report.

### Fourteen-screen inventory

1. Daily plan, `/planificare`, capture `plan`: compacted summary and detail chrome, schedule moved before optional evidence. Map, routes, crews, filters and approval provenance preserved.
2. Review queue, `/coada`, capture `review`: readable wrapping, table-local horizontal scroll and assistant empty-state link. Decision form and permissions preserved.
3. Map and crews, `/harta`, capture `map`: inspected, outside this agent's edit scope. Keep its dense map, region controls, selected case and timeline. No route or operational data removed.
4. Substation overview, `/posturi`, capture `posts`: page width aligned. Map, search, sort and loss filters preserved. The shared list component still needs the width/scroll correction below.
5. Substation detail, `/posturi/[id]`, capture `post`: page width aligned. Balance, meters, voltage, causes, remedies, work and audit sections preserved. The shared section-grid correction is assigned below.
6. Meter work detail, `/lucrari/[id]` for A, capture `work-A`: inspected, outside this agent's edit scope. Primary signal, model evidence, route state and full decision trace remain.
7. Storm work detail, `/lucrari/[id]` for B, capture `work-B`: inspected, outside this agent's edit scope. Keep outage probability distinct from the conditional impact estimates and keep deferred state visible.
8. Voltage work detail, `/lucrari/[id]` for C, capture `work-C`: inspected, outside this agent's edit scope. Preserve voltage units, remedy cost and unsent-message status. The large coloured message wall should become a compact draft preview in the owning component.
9. Decision history, `/jurnal`, capture `history`: reduced table width pressure, clear human authorship and optional technical trace. No historical event was rewritten.
10. Alerts and messages, `/alerte`, capture `alerts`: card-relative fact layout, message disclosure, honest draft/timestamp labels and full lists retained.
11. Model evaluation, `/modele`, capture `models`: separate model/baseline cards, secondary simulation comparison and progressive reports. No mostly blank cross-model matrix or nested vertical error scroll.
12. Work order, `/lucrari` with crew/stop queries, capture `orders`: inspected, outside this agent's edit scope. Keep crew selection, stops, checklist, print and the PDF route `/ordine/[crew]` intact.
13. Run history, `/rulare`, capture `run`: saved-run provenance, assistant handoff and unchanged read-only parameters. No model or planner execution was performed.
14. Presentation, `/demo`, capture `presentation`: inspected, outside this agent's edit scope. All five scenes remain. The map was blank in this capture; that alone does not establish the cause.

The assistant home at `/app` and the complete conversation are retained. Its new photo and manual-correction UI, the operational service and permissions belong to the main/backend agents and were not edited here.

### Handoff for components outside this scope

- `components/posts/posts-screen.tsx`: at the supplied desktop width the list's region, locality, loss and recommendation columns do not fit beside the map, so the recommendation is clipped and only a few of the available rows show inside the fixed-height panel. Give the list more width or move it below the map at this width. Keep search and sort, use readable row heights and pagination instead of a long vertical scroll. Do not remove the underlying records to make the layout fit.
- `components/posts/post-sections.tsx`: the three-column detail grid stretches a missing-series placeholder to the height of the cause list and leaves a large blank panel. Use a content-width two-column overview, an explicit wider chart row and a compact missing-data state. A selected tab should use the available width. This agent did not change the shared component through a brittle page-level CSS override.
- `components/item/layout-c.tsx`: the full prosumer draft appears as a large warning block even when it is only an unsent message. Keep the risk warning separate from a compact draft preview and its full-text disclosure.
- `components/demo/demo-stage.tsx` and `components/plan/plan-map.tsx`: verify map readiness and tile/source errors in `/demo` independently. The map works in the captured `/harta` and `/posturi` screens while the presentation capture is blank. A screenshot captured before map load is also possible. Show a useful loading/failure state if confirmed, rather than an empty map rectangle.
- Human correction needs a prominent, evidence-backed marker on work detail and the primary dashboard when the backend reports an actual correction. It must show the original recommendation, the human replacement and its author/time without relabelling every human action as a correction. The main agent owns that overlay and its permissions.
- Other legacy detail/order wrappers still specify 1520 px. The owning agent can align their content widths with this pass after checking the full-width operational map separately.

### Verification for this pass

Scoped ESLint passes without warnings. `bunx tsc --noEmit --incremental false -p .` passes. The five existing synthetic/pure test files for queue grouping, run-stage counts, map dots, assistant handoff and routing pass: 23 tests and 141 assertions. A separate one-off server-render check with explicitly synthetic model/planner objects confirms primary and SGCC values, PR-AUC, pu units, simulation wording, error-source links, the balance slot and honest missing-report states. It does not read an API or alter data.

The browser, filtered-state layout, keyboard interaction, light/dark rendering and mobile overflow of the changed UI still require the main agent's checks. No Next build, commit, staging, deployment, account/configuration change, operational write or live API request was made by this implementation agent.


## Integrated photo and correction pass, 8 November 2026

The full Assistant remains the main screen. Finding forms now show the selected visit, four explicit outcome cards, optional notes and up to six private photos. Choosing a file does not record a finding. The proposal shows frozen photo previews before Confirm; the saved finding appears on the assigned-work page and dispatcher detail. The file chooser also offers the environment-facing camera on supported devices. Draft cancellation attempts cleanup, while the server protects prepared and attached evidence.

Every valid dispatcher work detail offers Correct AI decision. Its form requires a reason and leads to a server-backed comparison. The requested action is distinct from the planner's actual saved result. The original AI decision is expandable and explicitly unknown when provenance cannot be verified. Work history and activity show the author, time and reason. Ordinary human reviews keep their own label. No view treats a field finding as a repair or case closure.

The substation table now has eight rows per page and local horizontal scrolling, with reset on search/filter. Its two-column detail layout starts cards at their own natural height instead of stretching empty states. Customer message drafts on voltage detail are compact disclosures with an explicit Not sent badge. Maps show a loading state until the map is ready; the presentation's actual map/markers were verified after loading.

### Final local verification

Helium checked the 14 legacy-console views and role-specific pages: 26 page checks across dispatcher, technician and customer, each at 1440×1100 and 390×844, plus the main agent homes and restricted-route redirects. The checks found no page-wide horizontal overflow or rendered error alert. A focused pass exercised all model filters, post pagination, Light/Dark, real map readiness and the new finding layout. Native browser file upload and explicit proposal confirmation persisted private evidence on an isolated complete 689-work copy. The dispatcher could fetch the image; the customer received403 and no image metadata. A dispatcher Defer correction applied R-HUMAN-DEFER, preserved the prediction and remained visible after navigation/reload. Cancel removed an unused uploaded photo.

Evidence: `/tmp/daybreak-v4-full-qa.json`, `/tmp/daybreak-v4-feature-qa.json`, `/tmp/daybreak-v4-focused-qa.json` and their exact screenshots. The JPEG fixture is explicitly synthetic. These are local browser/viewport checks; a physical camera, microphone, print output and deployment/live acceptance are outside this pass.

The final frontend suite passes237 tests (seven opt-in runtime tests skipped), complete TypeScript, ESLint and an isolated Next production build. Backend regression passes87 tests including the legacy-proposal snapshot compatibility check. The main local API was restarted independently and the complete browser pass repeated against3870; the current plan hash was unchanged. Nothing was deployed.
