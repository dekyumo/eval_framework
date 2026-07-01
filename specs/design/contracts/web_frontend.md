# Contract: Web frontend (SPA)

`frontend/` (React + TypeScript, Vite) built into `web/static/`, served by Flask. This contract exists because gen-1's UI was underspecified: it shipped a pile of server-rendered static pages with a top navbar, showed **raw JSON**, and had **no buttons** to scan, configure, or edit anything. This spec fixes the information architecture and the required interactions. Visual language (colors, fonts, spacing, component look) comes from the Stitch-generated `specs/design/DESIGN.md`; **this file owns structure and behaviour**, `DESIGN.md` owns appearance.

## How to use the mockups (read this before coding the UI)

There are ten reference screens in `specs/design/mockups/NN_*/`, each with a `screen.png` (the render) and a `code.html` (Stitch's static export). Use them like this:

- **`screen.png` is the target look.** **`code.html` is a *structural hint*, not source.** Stitch emits one monolithic HTML file per screen with inlined Tailwind and **hardcoded placeholder data**. Read it to see layout, spacing, and class choices — then **rebuild as typed React components wired to the API**. Do **not** paste it in, do **not** keep its fake data, do **not** let each page carry its own copy of the shell.
- Every screen redraws the left rail / jobs tray / context switcher. That is a Stitch artifact of per-screen generation — in code the **shell exists once** (see Component map) and the mockups are only the *content pane*.
- A mockup shows **one static instance** of each state (one frozen rubric, one crash trace, one FAIL chip). The real components are **driven by the domain type** — see "where the behaviour hides" in the Component map. If you build only what the PNG shows, you've built 1 of N states.
- Mockup ↔ page mapping is listed per page below and in `DESIGN.md`.

## Architecture

```text
React SPA (client-side routing)  ──fetch JSON──▶  Flask /api/*  ──▶  SERVICE LAYER  ──▶  core + storage
```

- **One app, client-side routing.** Not a set of independent pages. A persistent left rail (repo/agent context + nav) and a routed content pane.
- **The API is thin.** Every `/api/*` route is a direct call into a service-layer function (the same functions the chat operator wraps). Routes do no computation, no scoring, no business logic. If a route needs logic that doesn't exist as a service function, add the service function — do not put it in the route.
- **Typed end to end.** Generate/maintain TypeScript types from the Pydantic domain models (e.g. export JSON Schema → `frontend/src/types/`). The UI never invents field names.
- **No raw JSON as a primary view.** JSON is available behind a "view raw" affordance only. Every domain object has a rendered view.

## Stack (locked, minimal)

| Concern | Choice |
| --- | --- |
| Framework | React + TypeScript, Vite |
| Routing | React Router (client-side) |
| Data fetching | TanStack Query (server cache, retries, invalidation) over `fetch` |
| Styling | Tailwind (tokens driven by `DESIGN.md`) |
| Graph | one lib for the agent/lineage DAG (e.g. React Flow); do not hand-roll |
| Charts | one lightweight lib for the response-matrix heatmap + score bars |

No Redux, no SSR, no component-library sprawl. Keep dependencies few.

## Global shell

- **Repo/agent context switcher** (left rail, always visible): the currently selected repo and `AgentTarget`. Everything downstream is scoped to it. Switching re-scopes the whole app.
- **Primary nav**: Agents · Snapshots · Cases · Runs · Campaigns · Compare · Registries (Tags/Metrics/Rubrics/Extractors) · Chat.
- **Async job indicator**: scans, runs, and campaigns are long. Show a jobs tray with live status; never block the whole UI on one request.
- **Empty and error states are first-class.** Every list has a designed empty state with the action that fills it. Errors from the scanner's taxonomy (CallerError / AgentError / FrameworkError) render differently: caller = "fix your input", agent = show the agent traceback, framework = "this is our bug".

## Component map (extract once, reuse everywhere)

The mockups repeat a lot. Build these once and compose pages from them — do not re-implement per screen. This is the single highest-leverage instruction in this file: **most of the UI is a small set of typed primitives.**

### Shell (built once, wraps every route)
- `AppShell` — the left rail + routed `<Outlet/>` + jobs tray. **Every page renders inside this; no page owns a navbar.** (Every mockup shows it; ignore the repetition.)
- `ContextSwitcher` — repo + `AgentTarget` selector at the rail's top; its value scopes all queries (put it in a context/store, key TanStack Query caches by it).
- `NavRail` — Agents · Snapshots · Cases · Runs · Campaigns · Compare · Registries · Chat.
- `JobsTray` — async scan/run/campaign progress, polling `/api/jobs`. Long actions push here; the UI never blocks on them.

### Typed primitives (the behaviour lives in the type, not the page)
| Component | Renders | Driven by | Where it hides / the gotcha |
| --- | --- | --- | --- |
| `ResultView` | one `Result` | `Result.type` | bool→pass/fail pill, enum→chip, int/float→value + fold stats. Mockup 04 shows one of each — build the **switch on type**, not four hand-placed widgets. |
| `AggregateView` | folded `AggregateResult` | `type` | mean/stdev vs proportion vs counts; used in Compare (05) and Run results (04). |
| `TraceView` | `Trace.parts[]` | `MessagePart.kind` | text / tool_call / tool_response / media each a distinct block; **a crash (`exception`) is a first-class red card, not an error toast** (mockups 04, 09). |
| `SplitBadge` | `EvalCase.split` | `split` | `optimisation` = teal outline, `judging` = locked/sacred violet; judging must *look* protected (mockup 03). |
| `BlameTag` | scanner/runner error | error category | caller = amber, agent = rose (+ traceback), framework = violet-magenta. Drives the error states in onboarding (01) and everywhere a job fails. |
| `ConfirmCard` | an `ActionProposal` | — | one component for **both** the chat operator (10) and any UI write button. Summarizes effects; primary "Confirm", ghost "Cancel". See "Write-action confirmation". |
| `DomainRegions` | `AgentDomain` | — | in/margin/ood editable chips (mockup 02); PATCHes the snapshot. |
| `LineageGraph` | `AgentManifest` | edge types | React Flow; nodes = agent/subagent/tool/model/prompt, selected node glows indigo, detail drawer shows fingerprint + source (mockup 02). |
| `ResponseHeatmap` | `ResponseMatrix` | cell value | models × cases, green→red; side panels (difficulty/ability/clusters/thinning) read from `analysis/`, never computed here (mockup 06). |
| `RubricEditor` | `Rubric` | `frozen` | **frozen ⇒ entire form read-only + "Create new version"**; item rows switch control by item type (mockup 07). |
| `ExtractorEditor` | `Extractor` | — | fingerprinted source + "run on sample" preview list of typed results; revise via AGENT4 (mockup 08). |
| `AgreementCard` | human vs LLM `Result`s | item type | confusion matrix + Cohen's κ for bool/enum, correlation for int/float; from `analysis/agreement.py` (mockup 09). |
| `EmptyState` | any empty list | — | names the action that fills it ("No agents yet — Add a repository"). Reused by every list. |

**Rule of thumb for the implementer:** if you're about to write the same chip/badge/bubble markup on a second page, stop and lift it into one of the components above. The type→component switches (`ResultView`, `TraceView`, `RubricEditor`) are exactly the states the static mockups *don't* show; get them right and the rest is layout.

## Pages and required interactions

### 1. Onboarding / Add target (the flow gen-1 lacked)
_Mockup: `mockups/01_add_target_scan_onboarding/`._
`add repo → pick agent → scan`.
- Add a repo by path (validated server-side: exists, is a git repo). No `AGENT_ENTRYPOINT` env var — the path is entered here.
- The UI lists candidate agents in the repo (root + sub-agents the scanner can enumerate) and lets the user pick the `AgentTarget` (or type an `agent_path`).
- Pick a commit (default: HEAD; must be clean — dirty tree shows the `DirtyRepositoryError` inline).
- **Scan button.** Runs the scanner; on success routes to the new snapshot's Agent view.

### 2. Agent / lineage view
_Mockup: `mockups/02_agent_lineage/`._
- The manifest as a **graph**: root agent → sub-agents (`DELEGATES_TO`), tools (`USES_TOOL`), model, prompts. Click a node → detail panel (prompt text + fingerprint, tool signature + source, model id).
- The **commit DAG** for this target (`ON_TOP_OF`), each commit a snapshot; select two → Compare.
- The detected **`AgentDomain`** (description + in/margin/ood regions), **editable inline** and saved back to the snapshot.

### 3. Cases + Eval builder
_Mockup: `mockups/03_eval_case_builder/`._
- Dataset list; a case list filterable by tag / problem_type / domain_position / split.
- **Case editor** (not raw JSON): the multi-turn `conversation`, `domain_position`, `problem_type`, `split`, tags, and attached `metrics`. Intent classification appears here only as an enum metric, never as a core field.
- **Domain × problem builder**: a matrix (domain_position × problem_type) to generate/populate coverage; "copy case" (duplicate-and-edit).
- **Held-out guard (SOUL13)**: `split` is prominent; optimisation vs judging is visually distinct; the UI warns when an optimisation action would read judging cases.

### 4. Run + trace viewer
_Mockup: `mockups/04_trace_viewer_scoring/`._
- Trigger a run (or campaign) from a dataset + snapshot; shows in the jobs tray.
- **Trace viewer**: rendered message parts (text, tool_call, tool_response, media) as a conversation, not JSON. A crash trace shows its exception as a first-class, scorable outcome. Latency/tokens shown.
- Per-run **results** rendered by type (bool → pass/fail, enum → chip, int/float → value + fold stats), with the judge/human rationale.

### 5. Compare
_Mockup: `mockups/05_compare_snapshot_diff/` (note the amber SOUL13 validity-guard banner)._
- Snapshot-vs-snapshot and run-vs-run. Aggregates diffed; regressions surfaced by a **threshold comparison over stored aggregates** (a UI concern, not a bespoke module). Semantic diff of prompts/tools between the two snapshots.

### 6. Campaign + response matrix (SOUL9)
_Mockup: `mockups/06_campaign_response_matrix/`._
- Configure a campaign (dataset + model panel); launch; watch progress.
- **Response-matrix heatmap** (models × cases). Derived views: item difficulty, model ability, co-failure clusters, redundant-pair (thinning) suggestions. These are read from `analysis/`, not computed client-side.

### 7. Editable registries (gen-1 showed these read-only)
_Mockups: `mockups/07_registries_rubrics_frozen/` (frozen rubric = read-only + "new version"), `mockups/08_extractor_authoring/` (AGENT4 draft→run→confirm)._
Full CRUD editors, each rendered (not JSON), each respecting immutability rules from `object_model.md`:
- **Tags**: create / rename / delete-if-unused (count 0).
- **Metrics**: strategy, result_type, enum values, extractor/verifier/rubric refs, ground truth, comparator.
- **Rubrics**: items (name/type/enum/prompt), judge prompt; **frozen rubrics are read-only** — editing offers "create new version".
- **Extractors**: show the fingerprinted source (read-only source, editable via AGENT4 flow), run against a sample trace to preview the value.

### 8. Human eval
_Mockup: `mockups/09_human_evaluation/` (note the "1 of 12 disagreements" triage framing — spend human attention only on disagreements)._
- Present a run + a rubric; capture human `Result`s (source=human) and comments. Show human–LLM agreement (confusion matrix / kappa for bool/enum, correlation for int/float) from `analysis/agreement.py`.

### 9. Chat operator
_Mockup: `mockups/10_chat_operator/` (read tools = inline chips, no confirm; write/expensive = ActionProposal confirm card)._
- The AGENT1 chat pane (streamed). Read tools run freely; **write/expensive tools return an `ActionProposal` that the UI renders as a confirm card** (see `chat_operator.md`) — the human clicks to execute. No silent writes.

## Write-action confirmation (mirror of the chat contract)

Any destructive or expensive action (scan, run, campaign launch, delete, freeze) triggered from the UI shows a confirm step with a clear summary of effects. Cheap reads are immediate. This mirrors the chat operator's read-vs-confirm split so the two clients behave identically against the service layer.

## API shape (sketch)

`/api/repos`, `/api/repos/{id}/agents` (enumerate targets), `/api/scan` (POST target+commit), `/api/snapshots/{id}` (+ `/domain` PATCH), `/api/cases` (CRUD), `/api/datasets`, `/api/runs` (POST + GET trace), `/api/campaigns` (POST + matrix GET), `/api/compare`, `/api/tags|metrics|rubrics|extractors` (CRUD), `/api/human-eval`, `/api/chat` (stream), `/api/jobs` (async status). Each maps 1:1 to a service function.

## Tests

- **Type sync test**: TS types match the exported Pydantic JSON Schema (fails if the domain model drifts).
- **Component tests** (Vitest + Testing Library) for the typed primitives: `TraceView` renders each part kind (incl. a crash card); `ResultView` renders per `type`; `RubricEditor` is read-only + offers "new version" when `frozen`; delete-tag disabled when count > 0; `BlameTag` renders each error category.
- **Shell singleton test**: routed pages render inside a single `AppShell`; no page defines its own navbar (guards against the gen-1 per-page-navbar regression).
- **Flow test**: add repo → pick agent → scan → land on Agent view (mocked API).
- **No-raw-JSON guard**: assert primary object views are rendered components, JSON only behind "view raw".
- **API contract test** (pytest): every `/api/*` route calls a real service function (no logic in routes).

Definition of done: the full loop (add repo → pick agent → scan → build case → run → view trace → score → compare) is doable **entirely in the UI**, with no env vars and no raw-JSON editing, and the type-sync + flow tests pass.
