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
