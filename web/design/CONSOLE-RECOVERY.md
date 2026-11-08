# Console recovery

Source inventory checked on 8 November 2026. The original fourteen draft filenames identify views, not fourteen separate navigation destinations. Their generated text and numbers are not a data source. Existing server queries, work-item records and audit events remain authoritative.

| Original view | Current route | Existing implementation | Access |
| --- | --- | --- | --- |
| 01 Daily plan | `/planificare` | `HomeBoard`, KPIs, next decision, crew assignments, Romania map, route cards, timeline and filters | Authorized dispatcher |
| 02 Agent run | `/rulare` | Current run stages, timings, rules, model scores and human audit | Authorized dispatcher |
| 03 Needs review | `/coada` | Review queue with work-item evidence and human review actions | Authorized dispatcher |
| 04 Substations | `/posturi` | Substation list and filters from the selected scenario | Authorized dispatcher |
| 05 Substation detail | `/posturi/[id]` | `PostSections`, balance and voltage evidence, meter items and crew links | Authorized dispatcher |
| 06 Meter work item A | `/lucrari/[id]` | `layoutA`, series, model explanation, decision and audit | Authorized dispatcher |
| 07 Voltage work item C | `/lucrari/[id]` | `layoutC`, voltage forecast and remedy options | Authorized dispatcher |
| 08 Storm work item B | `/lucrari/[id]` | `layoutB`, weather risk, crew timing and evidence | Authorized dispatcher |
| 09 Journal | `/jurnal` | `JournalTable`, decision filters and `/jurnal/descarca` export | Authorized dispatcher |
| 10 Alerts and messages | `/alerte` | `AlertsBoard`, alert list and notification delivery status | Authorized dispatcher |
| 11 Models | `/modele` | `ModelsBoard`, reports, error analysis, balance and planner evaluation | Authorized dispatcher |
| 12 Work order | `/lucrari?echipa=…&oprire=…`, `/ordine/[crew]` | `OrderPaper`, `OrderSide`, crew/stop selection, browser print and existing PDF endpoint | Authorized dispatcher |
| 13 Presentation | `/demo` | `DemoStage`, scenario-derived scenes and route timeline | Authorized dispatcher |
| 14 Mobile | The same routes | `AppShell`, four frequent destinations and a complete `MobileMenu` | Destinations follow role and permission |

`/harta` is the existing full map and crew timeline with its own navigation item. It retains scenario, region, work-item and substation selection. Both the map and daily plan accept approval only from a human audit event at or after the current plan's creation. A browser cookie cannot mark a plan approved.

`/app` is the full Assistant home for every authenticated role. The daily plan contains no embedded assistant or role workspace. Existing plan controls hand editable requests to the Assistant through the nonvisual bridge; server confirmation remains required.

## Navigation by role

- Authorized dispatcher: Assistant, Daily plan, Needs review, Map & crews, Work orders, Service cases and Substations. Decision history, Alerts, Models, Run history and Presentation remain visible in the secondary group.
- Customer: Assistant, My cases, My connections and Activity. These use `/app`, `/cazuri`, `/conexiuni` and `/activitate`.
- Technician: Assistant, My route, Assigned work, Shared cases and Activity. These use `/app`, `/traseu`, `/sarcini`, `/cazuri` and `/activitate`, with assigned details at `/sarcini/[id]`. Shared cases remain in the complete mobile menu.
- Dispatcher without global console access: Assistant, Shared cases and Activity. Three valid mobile destinations are shown; no global page or counter is substituted as a fourth.

The global views require `mayReadConsole` through the real server gate before data reads. The shell never loads global information implicitly and removes supplied global metadata from restricted accounts. Scoped pages use the authenticated account through the operations API; they do not expose the old scenario-wide views.

## Verification boundary

This inventory was checked against current source. Routing tests execute the actual `/app`, `/planificare`, `/harta` and shell code with isolated synthetic IO, keeping the real authorization policy. They cover role, organization, permission, global serialization, legacy links and human audit approval. They do not establish browser layout or service availability; integrated browser QA and the final production build belong to the parent task.
